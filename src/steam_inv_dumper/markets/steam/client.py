import json
import logging
import pickle as cpickle
from pathlib import Path
from typing import Type, TypeVar

import bs4
import requests
from steampy.client import SteamClient
from steampy.models import Currency, GameOptions, SteamUrl

from steam_inv_dumper.markets.inferfaces.interfaces import InventoryProvider
from steam_inv_dumper.utils.price_utils import convert_string_prices

logger = logging.getLogger(__name__)


T = TypeVar("T", bound="SteamClientPatched")
M = TypeVar("M", bound="MockedSteamClient")


class SteamClientPatched(SteamClient):
    """
    Patched steam Client class to provide to_pickle and from_pickle functions
    And custom functions that are better than the ones provided by Steampy.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.currency = None

    def to_pickle(self, filename: str) -> None:
        """
        Dumps the class to Pickle for easier re-logins.
        """
        with open(f"{filename}.pkl", "wb") as file:
            cpickle.dump(self, file)

    @classmethod
    def from_pickle(cls: Type[T], filename: str) -> T:
        """
        Method to reload the class from its own pickle file
        """
        try:
            with open(f"{filename}.pkl", "rb") as file:
                a = cpickle.load(file)
        except FileNotFoundError:
            raise ValueError("The session files are not present")
        if a.is_session_alive():
            return a
        else:
            raise ValueError("The session files are corrupted or something.")

    @property
    def session(self) -> requests.Session:
        """
        Return session used in steam
        """
        return self._session

    @property
    def session_id(self) -> str:
        """
        Return SessionID used by Steam
        """
        return self._get_session_id()

    def login(self, *args, **kwargs) -> None:
        super(SteamClientPatched, self).login(*args, **kwargs)
        balance, currency = self.get_wallet_balance_and_currency()
        self.currency = currency

    def get_wallet_balance_and_currency(self) -> tuple:
        """
        Returns wallet and balance in one request.
        """
        url = SteamUrl.STORE_URL + "/account/history/"
        response = self._session.get(url)
        response_soup = bs4.BeautifulSoup(response.text, "html.parser")
        balance_string = response_soup.find(id="header_wallet_balance").string

        balance = convert_string_prices(balance_string)
        choices = {"pуб.": Currency.RUB, "€": Currency.EURO, "USD": Currency.USD}
        currency = [key for key in choices if key in balance_string]
        return balance, choices.get(currency[0], "")

    @staticmethod
    def _login_and_save_cookies(config: dict) -> "SteamClientPatched":
        steam_client = SteamClientPatched(config["apikey"])
        steam_client.login(
            config["username"],
            config["password"],
            json.dumps(config["steamguard"]),
        )
        steam_client.to_pickle(config["username"])
        return steam_client

    @classmethod
    def initialize(cls: Type[T], config: dict) -> T:
        if config.get("use_cookies", False):
            try:
                steam_client = SteamClientPatched.from_pickle(config["username"])
                logger.info("Successfully logged in Steam trough Cookies")
            except ValueError:
                logger.info("Did not manage to log into Steam trough Cookies")
                steam_client = SteamClientPatched._login_and_save_cookies(config=config)
        else:
            steam_client = SteamClientPatched._login_and_save_cookies(config=config)
        return steam_client

    @property
    def market_params(self) -> dict:
        return {
            "session": self.session,
            "session_id": self.session_id,
            "currency": self.currency,
        }


class MockedSteamClient:
    def __init__(self):
        self._test_files_root = Path(__file__).parents[2] / "api_responses"
        self.currency = Currency.EURO

    @classmethod
    def initialize(cls: Type[M], config: dict) -> M:
        return cls()

    def get_my_inventory(self, game: GameOptions) -> dict:
        file_path = self._test_files_root / "get_my_inventory.json"
        result = json.loads(file_path.read_text())
        return result

    @property
    def market_params(self) -> dict:
        return {
            "currency": self.currency,
        }


def steam_client_factory(config: dict) -> InventoryProvider:
    if config.get("debug", True) is False:
        return SteamClientPatched.initialize(config=config)
    return MockedSteamClient.initialize(config=config)
