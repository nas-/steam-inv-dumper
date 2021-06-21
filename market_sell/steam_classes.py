import logging
import pickle as cpickle
from typing import Callable
from urllib.parse import urlencode

import bs4
import requests
from backoff import expo, on_exception
# https://github.com/deckar01/ratelimit
# pip install deckar01-ratelimit not pip install ratelimit
# deckar01 contains persistence in fact
from ratelimit import RateLimitException, limits
from steampy.client import SteamClient
from steampy.market import SteamMarket
from steampy.models import Currency, SteamUrl

from .utilities import convert_string_prices

logger = logging.getLogger(__name__)


class SteamLimited(SteamMarket):
    """
    Patched steam Market class to provide rate-limiting for requests to Steam.
    """

    def __init__(self, session: requests.Session, steamguard: dict, session_id: str, currency: Currency) -> None:
        super().__init__(session)
        self._set_login_executed(steamguard, session_id)
        self.currency = currency

    @on_exception(expo, RateLimitException, max_tries=8)
    @limits(calls=1, period=3, storage='ratelimit.sqlite', name='short_range')
    @limits(calls=15, period=60, storage='ratelimit.sqlite', name='hourly')
    def limiter_function(self, func: Callable) -> Callable:
        """
        Rate limit function. To understand if both the limits apply globally, or one is per account.
        """

        def new_func(*args, **kwargs) -> Callable:
            out = func(*args, **kwargs)
            return out

        return new_func

    def __getattribute__(self, item: str) -> Callable:
        """
        "intercepts" the methods which call the steam market, and apply rate limits to them.
        """
        attribute = super().__getattribute__(item)
        try:
            if (callable(attribute)) & (
                    attribute.__name__ in ['fetch_price', 'fetch_price_history', 'get_my_market_listings',
                                           'create_sell_order', 'create_buy_order', 'buy_item', 'cancel_sell_order',
                                           'cancel_buy_order']):
                return self.limiter_function(attribute)
            else:
                return attribute
        except AttributeError:
            return attribute

    # ? @staticmethod
    def get_listings_for_item(self, market_hash_name, count=10, start=0):
        """
        Gets inspect links from listings from market items.
        :param market_hash_name: Market hash name of the item.
        :param start: Listing starting at
        :param count: Count of listings tor retrieve
        :return: list of inspects links.
        """
        BASEURL = f'https://steamcommunity.com/market/listings/730/{market_hash_name}/render/?query=&'
        # TODO start-end max =100
        params = {'start': start, 'count': count, 'language': 'english', 'currency': self.currency.value}
        params_str = urlencode(params)
        req = requests.get(f'{BASEURL}{params_str}')
        # TODO raise
        req.raise_for_status()
        return req.json()

    @staticmethod
    def parse_listings_for_item(req_json: dict) -> list[dict]:
        links = []
        if req_json['success'] and req_json['total_count'] > 0:
            for link in req_json['listinginfo']:
                listingid = req_json['listinginfo'][link]['listingid']
                assetid = req_json['listinginfo'][link]['asset']['id']
                inspect_pres = req_json['listinginfo'][link]['asset'].get('market_actions')
                you_get = req_json['listinginfo'][link]['converted_price_per_unit']
                fee = req_json['listinginfo'][link]['converted_fee_per_unit']
                price = you_get + fee
                if inspect_pres:
                    inspect = req_json['listinginfo'][link]['asset']['market_actions'][0]['link']
                    insp = inspect.replace(r'%listingid%', listingid).replace('%assetid%', assetid)
                    links.append({'link': insp, 'listingid': listingid, 'price': price})
        elif not req_json['success']:
            # TODO raise exception
            pass
        elif req_json['total_count'] == 0:
            # TODO raise exception
            pass
        return links


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
        with open(f'{filename}.pkl', 'wb') as file:
            cpickle.dump(self, file)

    @classmethod
    def from_pickle(cls, filename):
        """
        Method to reload the class from its own pickle file
        """
        try:
            with open(f'{filename}.pkl', 'rb') as file:
                a = cpickle.load(file)
        except FileNotFoundError:
            raise ValueError('The session files are not present')
        if a.is_session_alive():
            return a
        else:
            raise ValueError('The session files are corrupted or something.')

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
        url = SteamUrl.STORE_URL + '/account/history/'
        response = self._session.get(url)
        response_soup = bs4.BeautifulSoup(response.text, "html.parser")
        balance_string = response_soup.find(id='header_wallet_balance').string

        balance = convert_string_prices(balance_string)
        choices = {'pуб.': Currency.RUB, '€': Currency.EURO, 'USD': Currency.USD}
        currency = [key for key in choices if key in balance_string]
        return balance, choices.get(currency[0], '')
