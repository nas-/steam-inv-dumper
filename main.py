import decimal
import json
import logging
import time
from datetime import datetime
from typing import List

import pandas as pd
from steampy.utils import GameOptions

import utilities
from db.db import ItemSale, init_db
from logger import setup_logging, setup_logging_pre
from steam import SteamClientPatched, SteamLimited

setup_logging_pre()
setup_logging(1)

logger = logging.getLogger(__name__)


def load_config(config: str) -> dict:
    with open(config, 'r') as f:
        return json.loads(f.read())


CONFIG = load_config('config.json')

if CONFIG.get('use_cookies', False):
    try:
        steam_client = SteamClientPatched.from_pickle(CONFIG['username'])
        logger.info('Successfully logged in Steam trough Cookies')
    except ValueError:
        logger.info('Successfully logged in Steam trough Cookies')
        steam_client: SteamClientPatched = SteamClientPatched(CONFIG['apikey'])
        steam_client.login(CONFIG['username'], CONFIG['password'], str(CONFIG['steamguard']))
        steam_client.to_pickle(CONFIG['username'])
else:
    steam_client: SteamClientPatched = SteamClientPatched(CONFIG['apikey'])
    steam_client.login(CONFIG['username'], CONFIG['password'], json.dumps(CONFIG['steamguard']))
    steam_client.to_pickle(CONFIG['username'])

steam_market = SteamLimited(steam_client.session, CONFIG['steamguard'], steam_client.session_id)

DEBUG = True
if DEBUG:
    init_db('sqlite:///sales_debug.sqlite')
    ItemSale.query.delete()
    ItemSale.session.flush()

else:
    init_db()

# database = SteamDatabase('sales.db', 'sales')
decimal.getcontext().prec = 3

items_to_sell = {
    "CS:GO Weapon Case 2": {"quantity": 1, "min_price": 4.40},
    'eSports 2013 Winter Case': {"quantity": 3,
                                 "min_price": 3.00}
}


def dispatch_delists(item: str, toDelist: List, debug: bool) -> None:
    """
    Delists specified items, and updates the DB accordingly.
    :param item: Item name
    :param toDelist: list of dicts of items currently on sale which should be delisted.
    :param debug:debug flag. If debug=false orders are placed.
    :return: None
    """
    if not toDelist:
        return

    for item_id in toDelist:
        if debug:
            logger.debug(f'delist items. Debug is True. Updating database only')
            logger.debug(f'{item} cancel_sell_order({str(item_id["listing_id"])}')
        else:
            logger.debug(f'delist items. Debug is False. Sending cancel order to steam')
            logger.debug(f'{item} - listing_id {str(item_id["listing_id"])}')
            steam_market.cancel_sell_order(str(item_id['listing_id']))
        record = ItemSale.query_ref(item_id=item_id["listing_id"]).first()
        ItemSale.session.delete(record)
    ItemSale.session.flush()


def dispatch_sales(item: str, listItemsToSell: List, debug: bool):
    """
    Creates items listing for every specified item.
    :param item:  Item name
    :param listItemsToSell: List of Dicts containing items to sell, and their prices
    :param debug: Bool. If True, no orders are placed.
    :return:
    """
    if not listItemsToSell:
        return

    for element in listItemsToSell:
        if debug:
            logger.debug(f'{item} create_sell_order({str(element["assetsID"])} )'
                         f',money_to_receive={element["you_receive"]} buyer_pays {element["buyer_pays"]}')
        else:
            logger.debug(f'{item} creating real sell order')
            steam_market.create_sell_order(str(element['assetsID']), game=GameOptions.CS,
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


def get_own_items(game=GameOptions.CS) -> pd.DataFrame:
    """
    Gets *marketable* items in inventory for specified game
    :param game: defaults CSGO
    :return: Dataframe of items in inventory
    """
    items_dict = steam_client.get_my_inventory(game)
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


def get_own_listings() -> pd.DataFrame:
    """
    Gets all items currently listed on the market
    :return: pd.Dataframe containing all the listings
    """
    listings: dict = steam_market.get_my_market_listings()
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

    listings_sell['buyer_pay'] = listings_sell['buyer_pay'].apply(utilities.convert_euro_prices)
    listings_sell['you_receive'] = listings_sell['you_receive'].apply(utilities.convert_euro_prices)
    return listings_sell


def update_sold_items(item: str, _ItemInInventory: pd.DataFrame, _ItemSaleListings: pd.DataFrame) -> None:
    """
    Finds the items which are not in the inventory or on sale anymore, and update the database, setting them all as sold.
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


def main_loop() -> None:
    my_items: pd.DataFrame = get_own_items()
    listings_sell = get_own_listings()

    for item in items_to_sell:
        _ItemSaleListings = listings_sell[listings_sell['market_hash_name'] == item]
        _numberToSell = items_to_sell[item].get('quantity', 0)
        _min_price = items_to_sell[item]['min_price']
        _ItemInInventory = my_items[my_items['market_hash_name'] == item]
        if _ItemSaleListings.empty:
            _myListings_min_price = 0
        else:
            _myListings_min_price = _ItemSaleListings['buyer_pay'].min()

        update_sold_items(item, _ItemInInventory, _ItemSaleListings)
        # TODO see if ItemSellingPrice,minAllowedPrice can be merged here.
        actions = utilities.actions_to_make_list_delist(N_MarketListings=_ItemSaleListings.shape[0],
                                                        N_InInventory=_ItemInInventory.shape[0],
                                                        MinPriceOfMyMarketListings=_myListings_min_price,
                                                        ItemSellingPrice=utilities.get_item_price(steam_market, item),
                                                        N_NumberToSell=_numberToSell,
                                                        minAllowedPrice=_min_price)
        logger.info(f'{item}  {actions}')

        # Items to sell
        listItemsToSell = utilities.get_items_to_list(item, actions["list"]["qty"], actions["list"]["price"],
                                                      _ItemInInventory)
        dispatch_sales(item, listItemsToSell, DEBUG)

        # Items to delete
        listItemsToDeList = utilities.get_items_to_delist(item, actions["delist"]["qty"], _ItemSaleListings)
        dispatch_delists(item, listItemsToDeList, DEBUG)


if __name__ == '__main__':

    for i in range(0, 50):
        main_loop()
        time.sleep(1800)
