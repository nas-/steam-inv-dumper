import decimal
import time
from typing import Dict, Union

import pandas as pd
from steampy.client import SteamClient
from steampy.models import Currency
from steampy.utils import GameOptions

import utilities
from database import SteamDatabase
from limiter import SteamLimited
from db.db import init_db,ItemSale

# noinspection SpellCheckingInspection
steam_client: SteamClient = SteamClient('6CD2756FFD4165F0AFAC17FF3AB81997')
# noinspection SpellCheckingInspection
steam_client.login('nasil2nd', 'm4mpleir4ny', 'Steamguard.txt')
steam_market = SteamLimited(steam_client._session, steam_client.steam_guard, steam_client._get_session_id())

database = SteamDatabase('sales.db', 'sales')
DEBUG = False


def main_loop() -> None:
    my_items1: dict = steam_client.get_my_inventory(GameOptions.CS)
    my_items: pd.DataFrame = pd.DataFrame.from_dict(my_items1, orient='index',
                                                    columns=['appid', 'classid', 'instanceid', 'tradable', 'name',
                                                             'name_color',
                                                             'type',
                                                             'market_hash_name', 'commodity',
                                                             'market_tradable_restriction', 'marketable', 'contextid',
                                                             'id',
                                                             'amount'])
    listings: dict = steam_market.get_my_market_listings()
    normalized = pd.json_normalize(list(listings['sell_listings'].values()))
    if normalized.empty:
        listings_sell: pd.DataFrame = pd.DataFrame(columns=['listing_id', 'buyer_pay', 'you_receive',
                                                            'created_on',
                                                            'need_confirmation', 'description.appid',
                                                            'description.contextid', 'description.id',
                                                            'description.classid',
                                                            'description.instanceid', 'description.amount',
                                                            'description.status',
                                                            'description.unowned_id', 'description.name',
                                                            'description.type',
                                                            'description.market_hash_name',
                                                            'description.commodity'])
    else:
        listings_sell: pd.DataFrame = pd.DataFrame.from_records(
            pd.json_normalize(list(listings['sell_listings'].values())),
            columns=['listing_id', 'buyer_pay', 'you_receive',
                     'created_on',
                     'need_confirmation', 'description.appid',
                     'description.contextid', 'description.id',
                     'description.classid',
                     'description.instanceid', 'description.amount',
                     'description.status',
                     'description.unowned_id', 'description.name',
                     'description.type',
                     'description.market_hash_name',
                     'description.commodity'])

    listings_sell['buyer_pay'] = listings_sell['buyer_pay'].apply(utilities.convert_euro_prices)
    listings_sell['you_receive'] = listings_sell['you_receive'].apply(utilities.convert_euro_prices)

    items_to_sell: Dict[str, Dict[str, Union[int, float]]] = {
        "CS:GO Weapon Case 2": {"quantity": 2, "min_price": 2.70},
        'eSports 2013 Winter Case': {"quantity": 2,
                                     "min_price": 1.79}}

    def get_item_price(market_hash_name: str) -> decimal.Decimal:
        decimal.getcontext().prec = 2
        _priceData = steam_market.fetch_price(market_hash_name, game=GameOptions.CS, currency=Currency.EURO)
        try:
            _priceData['lowest_price'] = utilities.convert_euro_prices(_priceData['lowest_price'])
            _priceData['median_price'] = utilities.convert_euro_prices(_priceData['median_price'])
        except KeyError:
            _priceData['lowest_price'] = utilities.convert_euro_prices(_priceData['lowest_price'])
            _priceData['median_price'] = 0
            # TODO Care about this. Don't like to set median price =0
        return max(_priceData['lowest_price'], _priceData['median_price']) - decimal.Decimal('0.01')

    for item in items_to_sell:
        _ItemSaleListings = listings_sell[listings_sell['description.market_hash_name'] == item].sort_values(
            by=['you_receive', 'created_on'])
        _numberToSell = items_to_sell[item]['quantity']
        _min_price = items_to_sell[item]['min_price']
        _ItemInInventory = my_items[(my_items['market_hash_name'] == item) & (my_items['marketable'] == 1)]
        _myListings_min_price = _ItemSaleListings['buyer_pay'].min()

        # TODO pass to database. For each not present, set sold to True.
        # TODO refactor using executemany
        itemsPresent = list(_ItemInInventory['id']) + list(_ItemSaleListings['description.id'])
        items_in_db = database.select_all_ids(item)
        elements_sold = [element for element in items_in_db if element not in itemsPresent]
        print(f'updating {elements_sold} to Sold because they were sold')

        for element in elements_sold:
            database.update_data(item_id=element, sold=True)

        actions = utilities.actions_to_make_list_delist(N_MarketListings=_ItemSaleListings.shape[0],
                                                        N_InInventory=_ItemInInventory.shape[0],
                                                        MinPriceOfMyMarketListings=_myListings_min_price,
                                                        ItemSellingPrice=get_item_price(item),
                                                        N_NumberToSell=_numberToSell, minAllowedPrice=_min_price)
        print(f'{item}  {actions}')

        listItemsToSell = utilities.get_list_items_to_list(item, actions["list"]["qty"], actions["list"]["price"],
                                                           _ItemInInventory)

        if DEBUG:
            for element in listItemsToSell:
                print(f'{item} create_sell_order({str(element["assetsID"])} )'
                      f',money_to_receive={str(int(element["you_receive"]))}')

                database.insert_data(element["assetsID"], item, False, 1, buyer_pays=int(element["buyer_pays"]) / 100,
                                     you_receive=int(element["you_receive"]) / 100)
        else:
            for element in listItemsToSell:
                steam_market.create_sell_order(str(element['assetsID']), game=GameOptions.CS,
                                               money_to_receive=str(int(element['you_receive'])))
                database.insert_data(element["assetsID"], item, False, 1, buyer_pays=int(element["buyer_pays"]) / 100,
                                     you_receive=int(element["you_receive"]) / 100)

        listItemsToDeList = utilities.get_list_items_to_de_list(item, actions["delist"]["qty"], _ItemSaleListings)
        if DEBUG:
            for order in listItemsToDeList:
                print(f'{item} cancel_sell_order({str(order["listing_id"])})')
                database.delete_data(str(order["listing_id"]))

        else:
            for order in listItemsToDeList:
                steam_market.cancel_sell_order(str(order['listing_id']))
                database.delete_data(str(order["itemID"]))

    print('a')


if __name__ == '__main__':
    for i in range(0, 50):
        main_loop()
        time.sleep(1800)
