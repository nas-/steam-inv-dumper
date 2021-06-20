import decimal
import json
import logging
from datetime import datetime
from typing import List

import arrow
import pandas as pd
from steampy.models import GameOptions

from db.db import ItemSale, init_db
from market_sell.steam_classes import SteamClientPatched, SteamLimited
from . import utilities

logger = logging.getLogger(__name__)


class Exchange(object):
    """
    Class representing an exchange. In this case Steam Market.
    """

    def __init__(self, config: dict):
        self._last_run = 0
        self._config = config
        self._initialize_database()
        self._prepare_markets()
        self._heartbeat_interval = config.get('heartbeat_interval')
        self._heartbeat_msg: float = 0
        self._timeout: int = self._config.get('market_sell_timeout')

    def _prepare_markets(self) -> None:
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
                                         self.steam_client.session_id, self.steam_client.currency)

    def _initialize_database(self) -> None:
        debug = self._config.get('debug', True)
        db_url = self._config.get('db_url', True)
        if debug:
            init_db('sqlite:///sales_debug.sqlite')
            ItemSale.query.delete()
            ItemSale.session.flush()
        else:
            init_db(db_url)

    def dispatch_delists(self, item: str, to_delist: List) -> None:
        """
        Delists specified items, and updates the DB accordingly.
        :param item: Item name
        :param to_delist: list of dicts of items currently on sale which should be delisted.
        :return: None
        """
        debug = self._config.get('debug', True)
        if not to_delist:
            return

        for item_dict in to_delist:
            if debug:
                logger.debug(f'delist items. Debug is True. Updating database only')
                logger.debug(f'{item} cancel_sell_order({str(item_dict["listing_id"])}')
            else:
                logger.debug(f'delist items. Debug is False. Sending cancel order to steam')
                logger.debug(f'{item} - listing_id {str(item_dict["listing_id"])}')
                self.steam_market.cancel_sell_order(str(item_dict['listing_id']))
            record = ItemSale.query_ref(name=item, item_id=item_dict["itemID"]).first()
            ItemSale.session.delete(record)
        ItemSale.session.flush()

    def dispatch_sales(self, item: str, item_for_sale_list: List) -> None:
        """
        Creates items listing for every specified item.
        :param item:  Item name
        :param item_for_sale_list: List of Dicts containing items to sell, and their prices, expressed as cents!
        :return:
        """
        if not item_for_sale_list:
            return
        debug = self._config.get('debug', True)
        for element in item_for_sale_list:
            if debug:
                logger.debug(f'{item} create_sell_order({str(element["assetsID"])} )'
                             f',money_to_receive={element["you_receive"]} buyer_pays {element["buyer_pays"]}')
            else:
                logger.debug(f'{item} creating real sell order')
                self.steam_market.create_sell_order(str(element['assetsID']), game=GameOptions.CS,
                                                    money_to_receive=str(int(element['you_receive'])))
                # {'success': True}

            # Element ready for DB
            buyer_pays = decimal.Decimal(element["buyer_pays"] / 100).quantize(decimal.Decimal('0.01'))
            you_receive = decimal.Decimal(element["you_receive"] / 100).quantize(decimal.Decimal('0.01'))
            for_db = ItemSale(
                item_id=element["assetsID"],
                date=datetime.now(),
                name=item,
                sold=False,
                quantity=1,
                buyer_pays=buyer_pays,
                you_receive=you_receive,
                account=f"{self._config['username']}",
                currency=self.steam_market.currency.name
            )
            ItemSale.session.add(for_db)
        ItemSale.session.flush()

    def get_own_items(self, game: GameOptions = GameOptions.CS) -> pd.DataFrame:
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

    # TODO remove some unused columns and/or get rid of dataframe
    def get_own_listings(self) -> pd.DataFrame:
        """
        Gets all items currently listed on the market
        :return: pd.Dataframe containing all the listings
        """
        listings: dict = self.steam_market.get_my_market_listings()

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
        if not listings['sell_listings']:
            listings_sell: pd.DataFrame = pd.DataFrame(columns=columns_to_keep)
        else:
            # ITEMID=listings['sell_listings']['3423280172430835896']['description']['id']
            listings_sell: pd.DataFrame = pd.DataFrame.from_records(
                pd.json_normalize(list(listings['sell_listings'].values())), columns=columns_to_keep)
        listings_sell = listings_sell.rename(rename, axis=1)

        listings_sell['buyer_pay'] = listings_sell['buyer_pay'].apply(utilities.convert_string_prices)
        listings_sell['you_receive'] = listings_sell['you_receive'].apply(utilities.convert_string_prices)
        return listings_sell

    def update_sold_items(self, item: str, items_in_inventory: pd.DataFrame, items_sale_listings: pd.DataFrame) -> None:
        """
        Finds the items which are not in the inventory or on sale anymore, and update the database,
        setting them all as sold.
        :param item: item name
        :param items_in_inventory: dataframe containing all items of this kind in inventory
        :param items_sale_listings: dataframe containing all items of this kind on sale
        """

        items_present = list(items_in_inventory['id']) + list(items_sale_listings['id'])
        items_in_db = ItemSale.query_ref(name=item, sold=False).all()
        elements_sold = [element for element in items_in_db if str(element.item_id) not in items_present]
        if not elements_sold:
            logger.info('no elements are were sold. No need to update DB')
            return
        logger.info(f'updating {" ".join(str(a) for a in elements_sold)} to Sold because they were sold')
        for element in elements_sold:
            element.sold = True
        ItemSale.session.flush()

    @property
    def items_to_sell(self) -> dict:
        return self._config.get('items_to_sell', {})

    def _sell_loop(self) -> None:
        """
        Takes an exchange and runs the CheckSold, update database, sell more items cycle.
        """
        my_items: pd.DataFrame = self.get_own_items()
        listings_sell = self.get_own_listings()
        for item in self._config.get('items_to_sell', []):
            # dataframes
            item_on_sale_listings = listings_sell[listings_sell['market_hash_name'] == item]
            items_in_inventory = my_items[my_items['market_hash_name'] == item]
            min_price_already_on_sale = item_on_sale_listings['buyer_pay'].min()
            # Update sales listings.
            self.update_sold_items(item, items_in_inventory, item_on_sale_listings)
            # define amounts
            amount_in_inventory = items_in_inventory.shape[0]
            amount_to_sell = int(self.items_to_sell[item].get('quantity', 0))
            amount_on_sale = item_on_sale_listings.shape[0]
            # define prices
            # TODO see if item_selling_price,min_allowed_price_decimal can be merged here into a single variable
            min_allowed_price = self.items_to_sell[item]['min_price']
            if item_on_sale_listings.empty:
                min_price_already_on_sale = 0
            sellingPrice = utilities.get_item_price(self.steam_market, item)

            actions = utilities.actions_to_make_list_delist(num_market_listings=amount_on_sale,
                                                            num_in_inventory=amount_in_inventory,
                                                            min_price_mark_listing=min_price_already_on_sale,
                                                            item_selling_price=sellingPrice,
                                                            num_to_sell=amount_to_sell,
                                                            min_allowed_price=min_allowed_price)
            logger.info(f'{item}  {actions}')

            # Items to sell
            listItemsToSell = utilities.get_items_to_list(item, actions["list"]["qty"], actions["list"]["int_price"],
                                                          items_in_inventory)
            self.dispatch_sales(item, listItemsToSell)

            # Items to delete
            listItemsToDeList = utilities.get_items_to_delist(item, actions["delist"]["qty"], item_on_sale_listings)
            self.dispatch_delists(item, listItemsToDeList)

    def run(self) -> None:
        """
        :return:None
        """
        if self._last_run + self._timeout < arrow.now().timestamp():
            self._sell_loop()
            self._last_run = arrow.now().timestamp()

        if self._heartbeat_interval:
            now = arrow.now().timestamp()
            if (now - self._heartbeat_msg) > self._heartbeat_interval:
                logger.info(f"Bot heartbeat.")
                self._heartbeat_msg = now
