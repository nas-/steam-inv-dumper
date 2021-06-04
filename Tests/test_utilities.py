import decimal
from decimal import Decimal as D
from unittest import TestCase

import pandas as pd

import utilities


class Test(TestCase):
    def test_convert_string_prices(self):
        prices = ['2,42€', '2,42pуб.', '2,42USD', '2,42HK$']
        prices += ['2.42€', '2.42pуб.', '2.42USD', '2.42HK$']
        for price in prices:
            decimal_price = utilities.convert_string_prices(price)
            self.assertEqual(decimal_price, D('2.42'))

    def test_convert_string_prices_point_in_between(self):
        prices = ['4,234.35 €', '4,234.35 pуб.', '4,234.35 USD']
        prices += ['pуб. 4,234.35 €', 'pуб.4,234.35 pуб.', '4,234.35 USD']
        for price in prices:
            decimal_price = utilities.convert_string_prices(price)
            self.assertEqual(decimal_price, D('4234.35'))

    def test_convert_string_prices_no_decimal(self):
        prices = ['2.--€', '2.-- pуб.', '2.-- USD', '2.-- HK$']
        prices += ['2.-€', '2.- pуб.', '2.- USD', '2.- HK$']
        prices += ['2,--€', '2,-- pуб.', '2,-- USD', '2,-- HK$']
        prices += ['2,-€', '2,-pуб.', '2,-USD', '2,-HK$']
        for price in prices:
            decimal_price = utilities.convert_string_prices(price)
            self.assertEqual(decimal_price, D('2.00'))

    def test_convert_string_prices_with_space(self):
        prices = ['2,31 €', '2,31 pуб.', '2,31 USD', '2,31 HK$']
        prices += ['2.31 €', '2.31 pуб.', '2.31 USD', '2.31HK$']
        for price in prices:
            decimal_price = utilities.convert_string_prices(price)
            self.assertEqual(decimal_price, D('2.31'))

    def test_convert_string_prices_inverted(self):
        prices = ['€ 2,31', 'pуб. 2,31', 'USD 2,31', 'HK$ 2,31']
        prices += ['€ 2.31', 'pуб. 2.31', 'USD 2.31', 'HK$ 2.31']
        for price in prices:
            decimal_price = utilities.convert_string_prices(price)
            self.assertEqual(decimal_price, D('2.31'))

    def test_get_steam_fees_object(self):
        price = D('0.03')
        fees = utilities.get_steam_fees_object(price)
        self.assertEqual(fees["you_receive"], 1)
        self.assertEqual(fees["money_to_ask"], 3)
        self.assertEqual(type(fees["you_receive"]), int)
        self.assertEqual(type(fees["money_to_ask"]), int)

    def test_get_steam_fees_object_round_down_value(self):
        price = D('0.22')
        fees = utilities.get_steam_fees_object(price)
        self.assertEqual(fees["you_receive"], 19)
        self.assertEqual(fees["money_to_ask"], 21)
        self.assertEqual(type(fees["you_receive"]), int)
        self.assertEqual(type(fees["money_to_ask"]), int)

    def test_get_steam_fees_object_high_value(self):
        price = D('588.31')
        fees = utilities.get_steam_fees_object(price)
        self.assertEqual(fees["you_receive"], 51159)
        self.assertEqual(fees["money_to_ask"], 58831)
        self.assertEqual(type(fees["you_receive"]), int)
        self.assertEqual(type(fees["money_to_ask"]), int)

    def test_get_list_items_to_list(self):
        test_df = pd.DataFrame(
            data={'market_hash_name': ['aaa', 'bbbb', 'aaa'], 'marketable': [1, 1, 0], "id": ['100', '200', '1000']})
        price = D(0.1)
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


class TestActions(TestCase):
    def setUp(self) -> None:
        decimal.getcontext().prec = 3

    def test_delists_price_lower_than_acceptable(self):
        market_listings = 3
        min_price_market_listing = 2
        max_on_sale = 5
        tot_in_inventory = [0, 5, 10]
        usual_price = [1, 3, 4]
        min_allowed_price = [1, 3, 4]

        # have 3 item on sale at price 2
        # can have max 5 on sale
        # Usual price is 1
        # min allowed is 1

        # result delist 3.

        delists = utilities.determine_delists(market_listings, min_price_market_listing, max_on_sale,
                                              tot_in_inventory[0], usual_price[0], min_allowed_price[0])
        self.assertEqual(delists, {'qty': 3, 'price': D(2)})

        delists = utilities.determine_delists(market_listings, min_price_market_listing, max_on_sale,
                                              tot_in_inventory[0], usual_price[0], min_allowed_price[1])
        self.assertEqual(delists, {'qty': 3, 'price': D(2)})

    def test_make_delists(self):
        market_listings = [1, 2, 3]
        min_price_market_listing = [1, 2, 3]
        max_on_sale = [0, 5, 50]
        tot_in_inventory = [0, 5, 10]
        usual_price = [1, 2, 3]
        min_allowed_price = [1, 2, 3]

        # have 1 item on sale at price 1
        # can have max 0 on sale
        # result delist that

        delists = utilities.determine_delists(market_listings[0], min_price_market_listing[0], max_on_sale[0],
                                              tot_in_inventory[0], usual_price[0], min_allowed_price[0])
        self.assertEqual(delists, {'qty': 1, 'price': D(1)})

        # have 1 item on sale at price 1
        # can have max 5 on sale, dont have any in inv.
        # result do nothing,as i am lowest price already

        delists = utilities.determine_delists(market_listings[0], min_price_market_listing[0], max_on_sale[1],
                                              tot_in_inventory[0], usual_price[0], min_allowed_price[0])
        self.assertEqual(delists, {'qty': 0, 'price': D(1)})

        # have 1 item on sale at price 1
        # can have max 5 on sale, dont have any in inv.
        # Delist one, as min allowed price is 2

        delists = utilities.determine_delists(market_listings[0], min_price_market_listing[0], max_on_sale[1],
                                              tot_in_inventory[0], usual_price[0], min_allowed_price[1])
        self.assertEqual(delists, {'qty': 1, 'price': D(1)})

        # have 1 item on sale at price 1
        # can have max 5 on sale, dont have any in inv.
        # Delist one, as min allowed price is 2

        delists = utilities.determine_delists(market_listings[0], min_price_market_listing[2], max_on_sale[0],
                                              tot_in_inventory[0], usual_price[0], min_allowed_price[0])
        self.assertEqual(delists, {'qty': 1, 'price': D(3)})

    def test_actions_to_make_list_delist(self):
        N_MarketListings = 5
        MinPriceOfMyMarketListings = 1.89
        N_NumberToSell = 12
        N_InInventory = 5
        ItemSellingPrice = D(1.80)
        minAllowedPrice = 1.75
        actions = utilities.actions_to_make_list_delist(N_MarketListings,
                                                        MinPriceOfMyMarketListings,
                                                        N_NumberToSell,
                                                        N_InInventory,
                                                        ItemSellingPrice,
                                                        minAllowedPrice)

        self.assertEqual(actions, {'delist': {'qty': 0, 'price': D('1.89')},
                                   'list': {'qty': 5, 'price': D('1.80')}})
        self.assertTrue(N_MarketListings - actions['delist']['qty'] + actions['list']['qty'] <= N_NumberToSell)

    def test_0_in_inv(self):
        N_MarketListings = 5
        MinPriceOfMyMarketListings = 1.89
        N_NumberToSell = 12
        ItemSellingPrice = D(1.80)
        minAllowedPrice = 1.75
        N_InInventory = 0
        actions = utilities.actions_to_make_list_delist(N_MarketListings,
                                                        MinPriceOfMyMarketListings,
                                                        N_NumberToSell,
                                                        N_InInventory,
                                                        ItemSellingPrice,
                                                        minAllowedPrice)
        self.assertEqual(actions, {'delist': {'qty': 5, 'price': D('1.89')},
                                   'list': {'qty': 0, 'price': D('1.8')}})
        self.assertTrue(N_MarketListings - actions['delist']['qty'] + actions['list']['qty'] <= N_NumberToSell)

    def test_to_be_made_valid(self):
        # Ne ho 5 listati @ 1.89
        # 5 in inv, max on sale 12
        # Prezzo usuale 1.80, minimo=1.75
        # risultato Delista 0,lista 5 a 1.80
        market_listings = 5
        min_price_market_listing = 1.89
        max_on_sale = 12
        tot_in_inventory = 5
        usual_price = 1.80
        min_allowed_price = 1.75

        actions = utilities.actions_to_make_list_delist(market_listings,
                                                        min_price_market_listing,
                                                        max_on_sale,
                                                        tot_in_inventory,
                                                        usual_price,
                                                        min_allowed_price)

        self.assertEqual(actions, {'delist': {'qty': 0, 'price': D('1.89')},
                                   'list': {'qty': 5, 'price': D('1.80')}})
        self.assertTrue(market_listings - actions['delist']['qty'] + actions['list']['qty'] <= max_on_sale)

    def test_listing_equals_on_sale(self):
        # Ne ho 5 listati @ 1.89
        # 5 in inv, max on sale 5
        # Prezzo usuale 1.80, minimo=1.75
        # risultato Delista 5,lista 5 a 1.80
        market_listings = 5
        min_price_market_listing = 1.89
        max_on_sale = 5
        tot_in_inventory = 5
        usual_price = D(1.80)
        min_allowed_price = 1.75
        actions = utilities.actions_to_make_list_delist(market_listings,
                                                        min_price_market_listing,
                                                        max_on_sale,
                                                        tot_in_inventory,
                                                        usual_price,
                                                        min_allowed_price)

        self.assertEqual(actions, {'delist': {'qty': 5, 'price': D('1.89')},
                                   'list': {'qty': 5, 'price': D('1.80')}})
        self.assertTrue(market_listings - actions['delist']['qty'] + actions['list']['qty'] <= max_on_sale)

        # Ne ho 8 listati @ 1.89
        # 5 in inv, max on sale 5
        # Prezzo usuale 1.80, minimo=1.75
        # risultato Delista 8,lista 5 a 1.80
        market_listings = 8
        min_price_market_listing = 1.89
        max_on_sale = 5
        tot_in_inventory = 5
        usual_price = D(1.80)
        min_allowed_price = 1.75
        actions = utilities.actions_to_make_list_delist(market_listings,
                                                        min_price_market_listing,
                                                        max_on_sale,
                                                        tot_in_inventory,
                                                        usual_price,
                                                        min_allowed_price)

        self.assertEqual(actions, {'delist': {'qty': 8, 'price': D('1.89')},
                                   'list': {'qty': 5, 'price': D('1.80')}})
        self.assertTrue(market_listings - actions['delist']['qty'] + actions['list']['qty'] <= max_on_sale)

    def test_same_price(self):
        tot_in_inventory = 19
        market_listings = 1
        max_on_sale = 1
        min_price_market_listing = D('12.40')
        usual_price = D('6')
        min_allowed_price = D('12.40')

        actions = utilities.actions_to_make_list_delist(market_listings,
                                                        min_price_market_listing,
                                                        max_on_sale,
                                                        tot_in_inventory,
                                                        usual_price,
                                                        min_allowed_price)

        self.assertEqual(actions, {'delist': {'qty': 0, 'price': D('12.4')},
                                   'list': {'qty': 0, 'price': D('12.4')}})
        self.assertTrue(market_listings - actions['delist']['qty'] + actions['list']['qty'] <= max_on_sale)

    def test_delist_all_and_relist(self):
        # Ne ho 2 listati @ 1.80
        # 3 in inv, max on sale 5
        # Prezzo usuale 1.80, minimo=1.80
        # risultato Delista 0,lista 3 a 1.80
        MinPriceOfMyMarketListings = 1.80
        ItemSellingPrice = D(1.80)
        minAllowedPrice = 1.80
        N_InInventory = 3
        N_NumberToSell = 5
        N_MarketListings = 2
        # Just list 3 more
        actions = utilities.actions_to_make_list_delist(N_MarketListings,
                                                        MinPriceOfMyMarketListings,
                                                        N_NumberToSell,
                                                        N_InInventory,
                                                        ItemSellingPrice,
                                                        minAllowedPrice)
        self.assertEqual(actions, {'delist': {'qty': 0, 'price': D('1.80')}, 'list': {'price': D('1.80'), 'qty': 3}})
        self.assertTrue(N_MarketListings - actions['delist']['qty'] + actions['list']['qty'] <= N_NumberToSell)

        N_MarketListings = 10
        # Ne ho 10 listati @ 1.80
        # 3 in inv, max on sale 5
        # Prezzo usuale 1.80, minimo=1.80
        # risultato Delista 5,lista 0 a 1.80

        actions = utilities.actions_to_make_list_delist(N_MarketListings,
                                                        MinPriceOfMyMarketListings,
                                                        N_NumberToSell,
                                                        N_InInventory,
                                                        ItemSellingPrice,
                                                        minAllowedPrice)

        # Questo in realtà è giusto....
        self.assertEqual(actions, {'delist': {'qty': 5, 'price': D('1.80')},
                                   'list': {'qty': 0, 'price': D('1.80')}})
        self.assertTrue(N_MarketListings - actions['delist']['qty'] + actions['list']['qty'] <= N_NumberToSell)

    def test_actions_to_make_list_delist_min_allowed_price(self):
        N_MarketListings = 5
        MinPriceOfMyMarketListings = 1.81
        N_NumberToSell = 12
        N_InInventory = 5
        ItemSellingPrice = D(1.80)
        minAllowedPrice = 12.00
        actions = utilities.actions_to_make_list_delist(N_MarketListings,
                                                        MinPriceOfMyMarketListings,
                                                        N_NumberToSell,
                                                        N_InInventory,
                                                        ItemSellingPrice,
                                                        minAllowedPrice)
        self.assertEqual(actions, {'delist': {'qty': 5, 'price': D('1.81')},
                                   'list': {'qty': 5, 'price': D('12.0')}})
