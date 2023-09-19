import json
import logging
from pathlib import Path
from typing import Callable, Type, TypeVar
from urllib.parse import urlencode

import requests
from backoff import expo, on_exception

# https://github.com/deckar01/ratelimit
# pip install deckar01-ratelimit not pip install ratelimit
# deckar01 contains persistence in fact
from ratelimit import RateLimitException, limits
from steampy.market import SteamMarket
from steampy.models import Currency, GameOptions

from steam_inv_dumper.markets.inferfaces.interfaces import MarketProvider

logger = logging.getLogger(__name__)


# TODO: proxy all the calls within a common method, and rate limit that instead.
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
        self._set_login_executed(steamguard, session_id)
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
    def currency(self):
        return self.currency

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

    # ? @staticmethod
    def get_listings_for_item(self, market_hash_name, count=10, start=0):
        """
        Gets inspect links from listings from market items.
        :param market_hash_name: Market hash market_hash_name of the item.
        :param start: Listing starting at
        :param count: Count of listings tor retrieve
        :return: list of inspects links.
        """
        BASEURL = f"https://steamcommunity.com/market/listings/730/{market_hash_name}/render/?query=&"
        # TODO start-end max =100
        n_requests = (count - start) // 100
        collective = []
        for i in range(n_requests):
            params = {
                "start": start + 100 * i,
                "count": 100 if n_requests > 1 else count,
                "language": "english",
                "currency": self.currency.value,
            }
            params_str = urlencode(params)
            req = requests.get(f"{BASEURL}{params_str}")
            req.raise_for_status()
            collective.append(req.json())
        # TODO raise
        K = {"listinginfo": {}, "assets": {}}
        for i in collective:
            if i["success"]:
                K["total_count"] = i["total_count"]
                K["success"] = True
                K["listinginfo"] = {**K["listinginfo"], **i["listinginfo"]}
                K["assets"] = {**K["assets"], **i["assets"]}
        print(K["success"])
        return K

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
        price_data = self.fetch_price(market_hash_name, game=GameOptions.CS, currency=str(self.currency))
        if price_data.get("success") is True:
            return price_data

    @classmethod
    def initialize(cls: Type[K], config: dict) -> K:
        return cls(
            session_id=config["session_id"],
            steamguard=config["steamguard"],
            currency=config["currency"],
            session=config["session"],
        )


class MockedSteamMarket:
    def __init__(self):
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
        result = json.loads(file_path.read_text())
        return result

    def get_my_market_listings(self) -> dict:
        file_path = self._test_files_root / "get_my_market_listings.json"
        result = json.loads(file_path.read_text())
        return result


def steam_market_factory(config: dict) -> MarketProvider:
    if config.get("debug", True) is False:
        return SteamMarketLimited.initialize(config=config)
    return MockedSteamMarket.initialize(config=config)
