import pickle as cpickle

import bs4
import requests
from steampy.client import SteamClient
from steampy.models import Currency, SteamUrl

from steam_inv_dumper.utils.price_utils import convert_string_prices


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
    def from_pickle(cls, filename):
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
