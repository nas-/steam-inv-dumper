import decimal
import json
import logging
import time
from datetime import datetime
from typing import List

import pandas as pd
from steampy.utils import GameOptions

import utilities
from configuration import load_config
from db.db import ItemSale, init_db
from logger import setup_logging, setup_logging_pre
from steam import SteamClientPatched, SteamLimited

logger = logging.getLogger(__name__)

items_to_sell = {
    "CS:GO Weapon Case 2": {"quantity": 0, "min_price": 12.40},
    'eSports 2013 Winter Case': {"quantity": 0,
                                 "min_price": 5.00}
}


class Exchange(object):
    def __init__(self, config):
        decimal.getcontext().prec = 3
        self._config = load_config(config)
        self._initialize_logging()
        self._initialize_database()
        self._prepare_markets()

    def _prepare_markets(self):
        if self._config.get('use_cookies', False):
            try:
                self.steam_client = SteamClientPatched.from_pickle(self._config['username'])
                logger.info('Successfully logged in Steam trough Cookies')
            except ValueError:
                logger.info('Did not manage to log into Steam trough Cookies')
                self.steam_client: SteamClientPatched = SteamClientPatched(self._config['apikey'])
                self.steam_client.login(self._config['username'], self._config['password'],
                                        json.dumps(self._config['steamguard']))
                self.steam_client.to_pickle(self._config['username'])
        else:
            self.steam_client: SteamClientPatched = SteamClientPatched(self._config['apikey'])
            self.steam_client.login(self._config['username'], self._config['password'],
                                    json.dumps(self._config['steamguard']))
            self.steam_client.to_pickle(self._config['username'])

        self.steam_market = SteamLimited(self.steam_client.session, self._config['steamguard'],
                                         self.steam_client.session_id)

    def _initialize_database(self):
        debug = self._config.get('debug', True)
        if debug:
            init_db('sqlite:///sales_debug.sqlite')
            ItemSale.query.delete()
            ItemSale.session.flush()
        else:
            init_db()

    def dispatch_delists(self, item: str, toDelist: List) -> None:
        """
        Delists specified items, and updates the DB accordingly.
        :param item: Item name
        :param toDelist: list of dicts of items currently on sale which should be delisted.
        :return: None
        """
        debug = self._config.get('debug', True)
        if not toDelist:
            return

        for item_id in toDelist:
            if debug:
                logger.debug(f'delist items. Debug is True. Updating database only')
                logger.debug(f'{item} cancel_sell_order({str(item_id["listing_id"])}')
            else:
                logger.debug(f'delist items. Debug is False. Sending cancel order to steam')
                logger.debug(f'{item} - listing_id {str(item_id["listing_id"])}')
                self.steam_market.cancel_sell_order(str(item_id['listing_id']))
            record = ItemSale.query_ref(item_id=item_id["listing_id"]).first()
            ItemSale.session.delete(record)
        ItemSale.session.flush()

    def dispatch_sales(self, item: str, listItemsToSell: List):
        """
        Creates items listing for every specified item.
        :param item:  Item name
        :param listItemsToSell: List of Dicts containing items to sell, and their prices
        :return:
        """
        if not listItemsToSell:
            return
        debug = self._config.get('debug', True)
        for element in listItemsToSell:
            if debug:
                logger.debug(f'{item} create_sell_order({str(element["assetsID"])} )'
                             f',money_to_receive={element["you_receive"]} buyer_pays {element["buyer_pays"]}')
            else:
                logger.debug(f'{item} creating real sell order')
                self.steam_market.create_sell_order(str(element['assetsID']), game=GameOptions.CS,
                                                    money_to_receive=str(int(element['you_receive'])))
            # Element ready for DB
            for_db = ItemSale(
                item_id=element["assetsID"],
                date=datetime.now(),
                name=item,
                buyer_pays=decimal.Decimal(element["buyer_pays"] / 100) + 0,
                you_receive=decimal.Decimal(element["you_receive"] / 100) + 0,
                account='nasil2nd'
            )
            ItemSale.session.add(for_db)
        ItemSale.session.flush()

    def get_own_items(self, game=GameOptions.CS) -> pd.DataFrame:
        """
        Gets *marketable* items in inventory for specified game
        :param game: defaults CSGO
        :return: Dataframe of items in inventory
        """
        items_dict = self.steam_client.get_my_inventory(game)
        columns = ['appid',
                   'classid',
                   'instanceid',
                   'tradable',
                   'name',
                   'name_color',
                   'type',
                   'market_hash_name',
                   'commodity',
                   'market_tradable_restriction',
                   'marketable',
                   'contextid',
                   'id',
                   'amount']
        items = pd.DataFrame.from_dict(items_dict, orient='index', columns=columns)
        items = items[items['marketable'] == 1]
        return items

    def get_own_listings(self) -> pd.DataFrame:
        """
        Gets all items currently listed on the market
        :return: pd.Dataframe containing all the listings
        """
        listings: dict = self.steam_market.get_my_market_listings()
        normalized = pd.json_normalize(list(listings['sell_listings'].values()))
        columns_to_keep = [
            'listing_id',
            'buyer_pay',
            'you_receive',
            'created_on',
            'need_confirmation',
            'description.appid',
            'description.contextid',
            'description.id',
            'description.classid',
            'description.instanceid',
            'description.amount',
            'description.status',
            'description.unowned_id',
            'description.name',
            'description.type',
            'description.market_hash_name',
            'description.commodity'
        ]
        rename = {'description.appid': 'appid',
                  'description.contextid': 'contextid',
                  'description.id': 'id',
                  'description.classid': 'classid',
                  'description.instanceid': 'instanceid',
                  'description.amount': 'amount',
                  'description.status': 'status',
                  'description.unowned_id': 'unowned_id',
                  'description.name': 'name',
                  'description.type': 'type',
                  'description.market_hash_name': 'market_hash_name',
                  'description.commodity': 'commodity'}
        if normalized.empty:
            listings_sell: pd.DataFrame = pd.DataFrame(columns=columns_to_keep)
        else:
            listings_sell: pd.DataFrame = pd.DataFrame.from_records(
                pd.json_normalize(list(listings['sell_listings'].values())), columns=columns_to_keep)
        listings_sell = listings_sell.rename(rename, axis=1)

        listings_sell['buyer_pay'] = listings_sell['buyer_pay'].apply(utilities.convert_string_prices)
        listings_sell['you_receive'] = listings_sell['you_receive'].apply(utilities.convert_string_prices)
        return listings_sell

    def update_sold_items(self, item: str, _ItemInInventory: pd.DataFrame, _ItemSaleListings: pd.DataFrame) -> None:
        """
        Finds the items which are not in the inventory or on sale anymore, and update the database,
        setting them all as sold.
        :param item: item name
        :param _ItemInInventory: dataframe containing all items of this kind in inventory
        :param _ItemSaleListings: dataframe containing all items of this kind on sale
        """
        itemsPresent = list(_ItemInInventory['id']) + list(_ItemSaleListings['id'])
        items_in_db = ItemSale.query_ref(name=item).all()
        elements_sold = [element for element in items_in_db if element.item_id not in itemsPresent]
        if not elements_sold:
            logger.info('no elements are were sold. No need to update DB')
            return
        logger.info(f'updating {" ".join(str(a) for a in elements_sold)} to Sold because they were sold')
        for element in elements_sold:
            element.sold = True
        ItemSale.session.flush()

    def _initialize_logging(self):
        setup_logging_pre()
        setup_logging(1)


def main_loop(exchange) -> None:
    my_items: pd.DataFrame = exchange.get_own_items()
    listings_sell = exchange.get_own_listings()

    for item in items_to_sell:
        _ItemSaleListings = listings_sell[listings_sell['market_hash_name'] == item]
        _numberToSell = items_to_sell[item].get('quantity', 0)
        _min_price = items_to_sell[item]['min_price']
        _ItemInInventory = my_items[my_items['market_hash_name'] == item]
        if _ItemSaleListings.empty:
            _myListings_min_price = 0
        else:
            _myListings_min_price = _ItemSaleListings['buyer_pay'].min()

        exchange.update_sold_items(item, _ItemInInventory, _ItemSaleListings)
        # TODO see if ItemSellingPrice,minAllowedPrice can be merged here into a single variable
        sellingPrice = utilities.get_item_price(exchange.steam_market, item)
        actions = utilities.actions_to_make_list_delist(N_MarketListings=_ItemSaleListings.shape[0],
                                                        N_InInventory=_ItemInInventory.shape[0],
                                                        MinPriceOfMyMarketListings=_myListings_min_price,
                                                        ItemSellingPrice=sellingPrice,
                                                        N_NumberToSell=_numberToSell,
                                                        minAllowedPrice=_min_price)
        logger.info(f'{item}  {actions}')

        # Items to sell
        listItemsToSell = utilities.get_items_to_list(item, actions["list"]["qty"], actions["list"]["price"],
                                                      _ItemInInventory)
        exchange.dispatch_sales(item, listItemsToSell)

        # Items to delete
        listItemsToDeList = utilities.get_items_to_delist(item, actions["delist"]["qty"], _ItemSaleListings)
        exchange.dispatch_delists(item, listItemsToDeList)


if __name__ == '__main__':
    exchange = Exchange('config.json')
    exchange.steam_client.get_wallet_balance_and_currency()

    for i in range(0, 50):
        main_loop(exchange)
        time.sleep(1800)
