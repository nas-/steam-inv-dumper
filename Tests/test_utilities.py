import decimal
from unittest import TestCase

import pandas as pd

import utilities


class Test(TestCase):
    def test_convert_euro_prices(self):
        price = '2,42€'
        decimal_price = utilities.convert_euro_prices(price)
        self.assertEqual(decimal_price, decimal.Decimal('2.42'))

    def test_convert_euro_prices_no_decimal(self):
        price = '2.--€'
        decimal_price = utilities.convert_euro_prices(price)
        self.assertEqual(decimal_price, decimal.Decimal('2.00'))

    def test_convert_euro_prices_with_space(self):
        price = '2.31 €'
        decimal_price = utilities.convert_euro_prices(price)
        self.assertEqual(decimal_price, decimal.Decimal('2.31'))

    def test_get_steam_fees_object(self):
        price = decimal.Decimal('0.03')
        fees = utilities.get_steam_fees_object(price)
        self.assertEqual(fees["you_receive"], 1)
        self.assertEqual(fees["money_to_ask"], 3)
        self.assertEqual(type(fees["you_receive"]), int)
        self.assertEqual(type(fees["money_to_ask"]), int)

    def test_get_steam_fees_object_round_down_value(self):
        price = decimal.Decimal('0.22')
        fees = utilities.get_steam_fees_object(price)
        self.assertEqual(fees["you_receive"], 19)
        self.assertEqual(fees["money_to_ask"], 21)
        self.assertEqual(type(fees["you_receive"]), int)
        self.assertEqual(type(fees["money_to_ask"]), int)

    def test_get_steam_fees_object_high_value(self):
        price = decimal.Decimal('588.31')
        fees = utilities.get_steam_fees_object(price)
        self.assertEqual(fees["you_receive"], 51159)
        self.assertEqual(fees["money_to_ask"], 58831)
        self.assertEqual(fees["money_to_ask"], 58831)
        self.assertEqual(type(fees["you_receive"]), int)
        self.assertEqual(type(fees["money_to_ask"]), int)

    def test_actions_to_make_list_delist(self):
        decimal.getcontext().prec = 3
        N_MarketListings = 5
        MinPriceOfMyMarketListings = 1.89
        N_NumberToSell = 12
        N_InInventory = 5
        ItemSellingPrice = decimal.Decimal(1.80)
        minAllowedPrice = 1.75
        actions = utilities.actions_to_make_list_delist(N_MarketListings,
                                                        MinPriceOfMyMarketListings,
                                                        N_NumberToSell,
                                                        N_InInventory,
                                                        ItemSellingPrice,
                                                        minAllowedPrice)

        self.assertEqual(actions, {'delist': {'qty': 0, 'price': decimal.Decimal('1.89')},
                                   'list': {'qty': 5, 'price': decimal.Decimal('1.8')}})
        self.assertTrue(N_MarketListings - actions['delist']['qty'] + actions['list']['qty'] <= N_NumberToSell)
        N_InInventory = 0
        actions = utilities.actions_to_make_list_delist(N_MarketListings,
                                                        MinPriceOfMyMarketListings,
                                                        N_NumberToSell,
                                                        N_InInventory,
                                                        ItemSellingPrice,
                                                        minAllowedPrice)
        self.assertEqual(actions, {'delist': {'qty': 5, 'price': decimal.Decimal('1.89')},
                                   'list': {'qty': 0, 'price': decimal.Decimal('1.8')}})
        self.assertTrue(N_MarketListings - actions['delist']['qty'] + actions['list']['qty'] <= N_NumberToSell)
        N_InInventory = 3
        N_NumberToSell = 2
        N_MarketListings = 5
        actions = utilities.actions_to_make_list_delist(N_MarketListings,
                                                        MinPriceOfMyMarketListings,
                                                        N_NumberToSell,
                                                        N_InInventory,
                                                        ItemSellingPrice,
                                                        minAllowedPrice)
        self.assertEqual(actions, {'delist': {'qty': 2, 'price': decimal.Decimal('1.89')},
                                   'list': {'qty': 0, 'price': decimal.Decimal('1.80')}})
        self.assertTrue(N_MarketListings - actions['delist']['qty'] + actions['list']['qty'] <= N_NumberToSell)

    def test_actions_to_make_list_delist_min_allowed_price(self):
        N_MarketListings = 5
        MinPriceOfMyMarketListings = 1.81
        N_NumberToSell = 12
        N_InInventory = 5
        ItemSellingPrice = decimal.Decimal(1.80)
        minAllowedPrice = 12.00
        actions = utilities.actions_to_make_list_delist(N_MarketListings,
                                                        MinPriceOfMyMarketListings,
                                                        N_NumberToSell,
                                                        N_InInventory,
                                                        ItemSellingPrice,
                                                        minAllowedPrice)
        self.assertEqual(actions, {'delist': {'qty': 5, 'price': decimal.Decimal('1.81')},
                                   'list': {'qty': 5, 'price': decimal.Decimal('12.0')}})

    def test_get_list_items_to_list(self):
        test_df = pd.DataFrame(
            data={'market_hash_name': ['aaa', 'bbbb', 'aaa'], 'marketable': [1, 1, 0], "id": ['100', '200', '1000']})
        price = decimal.Decimal(0.1)
        output = utilities.get_items_to_list('aaa', 1, price, test_df)
        self.assertEqual(output, [{'name': 'aaa', 'assetsID': '100', 'you_receive': 8, 'buyer_pays': 10}])
        self.assertEqual(output[0]["you_receive"], utilities.get_steam_fees_object(price)["you_receive"])
        self.assertEqual(output[0]["buyer_pays"], utilities.get_steam_fees_object(price)["money_to_ask"])

    def test_get_list_items_to_de_list(self):
        test_df = pd.DataFrame(
            data={'market_hash_name': ['aaa', 'bbbb', 'aaa'], "listing_id": ['100', '200', '1000'],
                  'id': ['desc1', 'desc2', 'desc3'], 'unowned_id': ['300', '200', '300', ]})
        output = utilities.get_items_to_delist('aaa', 2, test_df)
        self.assertEqual(output[0]['name'] == output[1]['name'] == 'aaa', True)
        self.assertEqual(output, [{'name': 'aaa', 'listing_id': '100', 'itemID': 'desc1', 'Unowned_itemID': '300'},
                                  {'name': 'aaa', 'listing_id': '1000', 'itemID': 'desc3', 'Unowned_itemID': '300'}])

    def test_how_many_can_list(self):
        self.assertEqual(utilities.how_many_can_list(5, 5, 10), 0)
        self.assertEqual(utilities.how_many_can_list(1, 5, 10), 4)
        self.assertEqual(utilities.how_many_can_list(1, 0, 10), 0)
