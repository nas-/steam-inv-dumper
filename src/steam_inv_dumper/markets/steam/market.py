import json
import logging
from pathlib import Path
from typing import Callable, Type, TypeVar

import requests
from backoff import expo, on_exception
from ratelimit import RateLimitException, limits
from steampy.exceptions import ApiException
from steampy.market import SteamMarket
from steampy.models import Currency, GameOptions

from steam_inv_dumper.markets.interfaces.interfaces import MarketProvider
from steam_inv_dumper.utils.data_structures import MarketEvent

logger = logging.getLogger(__name__)


# TODO: proxy all the calls within a common method, and rate limit that instead.
# TODO: Add a new method, to fetch events from Steam Market History.
# "https://steamcommunity.com/market/myhistory/render/?norender=1&query=&start=1&count=130"


# Else too much risk to forget adding one over here.
K = TypeVar("K", bound="SteamMarketLimited")
T = TypeVar("T", bound="MockedSteamMarket")


class SteamMarketLimited(SteamMarket):
    """
    Patched steam Market class to provide rate-limiting for requests to Steam.
    """

    def __init__(
        self,
        session: requests.Session,
        steamguard: dict,
        session_id: str,
        currency: Currency,
    ) -> None:
        super().__init__(session)
        self._set_login_executed(steamguard=steamguard, session_id=session_id)
        self._currency = currency

    @on_exception(expo, RateLimitException, max_tries=8)
    @limits(calls=1, period=3, storage="ratelimit.sqlite", name="short_range")
    @limits(calls=15, period=60, storage="ratelimit.sqlite", name="hourly")
    def limiter_function(self, func: Callable) -> Callable:
        """
        Rate limit function. To understand if both the limits apply globally, or one is per account.
        """

        def new_func(*args, **kwargs) -> Callable:
            out = func(*args, **kwargs)
            return out

        return new_func

    @property
    def currency(self) -> Currency:
        return self._currency

    def __getattribute__(self, item: str) -> Callable:
        """
        "intercepts" the methods which call the steam market, and apply rate limits to them.
        """
        attribute = super().__getattribute__(item)
        try:
            if (callable(attribute)) & (
                attribute.__name__
                in [
                    "fetch_price",
                    "fetch_price_history",
                    "get_my_market_listings",
                    "create_sell_order",
                    "create_buy_order",
                    "buy_item",
                    "cancel_sell_order",
                    "cancel_buy_order",
                ]
            ):
                return self.limiter_function(attribute)
            else:
                return attribute
        except AttributeError:
            return attribute

    # TODO refactor and add tests
    @staticmethod
    def parse_listings_for_item(req_json: dict) -> list[dict]:
        links = []
        if req_json["success"] and req_json["total_count"] > 0:
            for link in req_json["listinginfo"]:
                if req_json["listinginfo"][link]["price"] == 0:
                    # item was sold.
                    continue
                listingid = req_json["listinginfo"][link]["listingid"]
                assetid = req_json["listinginfo"][link]["asset"]["id"]
                inspect_pres = req_json["listinginfo"][link]["asset"].get("market_actions")
                you_get = req_json["listinginfo"][link].get("converted_price_per_unit", 0)
                fee = req_json["listinginfo"][link].get("converted_fee_per_unit", 0)
                price = you_get + fee
                if inspect_pres:
                    inspect = req_json["listinginfo"][link]["asset"]["market_actions"][0]["link"]
                    insp = inspect.replace(r"%listingid%", listingid).replace("%assetid%", assetid)
                    links.append({"link": insp, "listingid": listingid, "price": price})
        elif not req_json["success"]:
            logger.info(f"{req_json['success']=} {req_json.get('message')=}")
            # TODO raise exception
            pass
        elif req_json["total_count"] == 0:
            # TODO raise exception
            pass
        return links

    def get_item_price(self, market_hash_name: str) -> dict:
        """
        Gets the item int_price from Steam
        :param market_hash_name: Market hash market_hash_name.
        :return:{"success":true,"lowest_price":"6,70€","volume":"7","median_price":"6,70€"}
        """
        # TODO fix this to return data correctly.
        price_data = self.fetch_price(market_hash_name, game=GameOptions.CS, currency=str(self.currency))
        if price_data.get("success") is True:
            return price_data
        raise Exception("Error getting price")

    @classmethod
    def initialize(cls: Type[K], config: dict) -> K:
        return cls(
            session_id=config["session_id"],
            steamguard=config["steamguard"],
            currency=config["currency"],
            session=config["session"],
        )

    def get_market_events(self, start: int = 1, count: int = 100)-> list[MarketEvent]:
        """
        Gets the market events from the Steam Market History.
        :param start: start index.
        :param count: count of events to fetch.
        :return: List of MarketEvent objects.
        """
        url = f"https://steamcommunity.com/market/myhistory/render/?norender=1&query=&start={start}&count={count}"
        response = self._session.get(url)
        if response.status_code != 200:
            raise ApiException("There was a problem getting the listings. http code: %s" % response.status_code)
        res = response.json()
        return self._parse_market_events(response=res)

    def _parse_market_events(self, response: dict)-> list[MarketEvent]:
        """
        Parses the response from the market events endpoint.
        :param response: raw response from the market events endpoint.
        :return: list of MarketEvent objects.
        """
        events = [MarketEvent.from_event(event) for event in response["events"]]

        return events


class MockedSteamMarket:
    def __init__(self) -> None:
        self._test_files_root = Path(__file__).parents[2] / "api_responses"
        self._currency = Currency.EURO

    @classmethod
    def initialize(cls: Type[T], config: dict) -> T:
        return cls()

    def cancel_sell_order(self, sell_listing_id: str) -> None:
        return

    def create_sell_order(self, assetid: str, game: GameOptions, money_to_receive: str) -> dict:
        return {}

    @property
    def currency(self) -> Currency:
        return self._currency

    def get_item_price(self, market_hash_name: str) -> dict:
        file_path = self._test_files_root / "get_item_price.json"
        result = json.loads(file_path.read_text(encoding="utf8"))
        return result

    def get_my_market_listings(self) -> dict:
        file_path = self._test_files_root / "get_my_market_listings.json"
        result = json.loads(file_path.read_text(encoding="utf8"))
        return result

    def get_market_events(self, start: int = 1, count: int = 100):
        response = json.loads(
            Path(
                r"C:\Users\edo\PycharmProjects\steam-inv-dumper\src\steam_inv_dumper\api_responses\myhistory.json"
            ).read_text(encoding="utf8")
        )
        return self._parse_market_events(response=response)

    def _parse_market_events(self, response: dict) -> list[MarketEvent]:
        """
        Parses the response from the market events endpoint.
        :param response: raw response from the market events endpoint.
        :return: list of MarketEvent objects.
        """
        events = [MarketEvent.from_event(event) for event in response["events"]]

        return events


def steam_market_factory(config: dict) -> MarketProvider:
    if config.get("debug", True) is False:
        return SteamMarketLimited.initialize(config=config)
    return MockedSteamMarket.initialize(config=config)
