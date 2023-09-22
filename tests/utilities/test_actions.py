from unittest import TestCase

import hypothesis.strategies as st
from hypothesis import Verbosity, given, settings

from steam_inv_dumper.utils.price_utils import (
    actions_to_make_list_delist,
    determine_delists,
    determine_lists,
)


class TestActions(TestCase):
    def setUp(self) -> None:
        # decimal.getcontext().prec = 3
        pass

    def test_delists_price_lower_than_acceptable(self) -> None:
        market_listings = 3
        min_price_market_listing = 200
        max_on_sale = 5
        tot_in_inventory = [0, 5, 10]
        usual_price = [100, 300, 400]
        min_allowed_price = [100, 300, 400]

        # have 3 item on sale at int_price 2
        # can have max 5 on sale
        # Usual int_price is 1
        # min allowed is 1

        # result delist 3.

        delists = determine_delists(
            market_listings,
            min_price_market_listing,
            max_on_sale,
            tot_in_inventory[0],
            usual_price[0],
            min_allowed_price[0],
        )
        self.assertEqual(delists, 3)

        delists = determine_delists(
            market_listings,
            min_price_market_listing,
            max_on_sale,
            tot_in_inventory[0],
            usual_price[0],
            min_allowed_price[1],
        )
        self.assertEqual(delists, 3)

    def test_make_delists(self) -> None:
        market_listings = [1, 2, 3]
        min_price_market_listing = [100, 200, 200]
        max_on_sale = [0, 5, 50]
        tot_in_inventory = [0, 5, 10]
        usual_price = [100, 200, 200]
        min_allowed_price = [100, 200, 200]

        # have 1 item on sale at int_price 1
        # can have max 0 on sale
        # result delist that

        delists = determine_delists(
            market_listings[0],
            min_price_market_listing[0],
            max_on_sale[0],
            tot_in_inventory[0],
            usual_price[0],
            min_allowed_price[0],
        )
        self.assertEqual(delists, 1)

        # have 1 item on sale at int_price 1
        # can have max 5 on sale, dont have any in inv.
        # result do nothing,as i am lowest int_price already

        delists = determine_delists(
            market_listings[0],
            min_price_market_listing[0],
            max_on_sale[1],
            tot_in_inventory[0],
            usual_price[0],
            min_allowed_price[0],
        )
        self.assertEqual(delists, 0)

        # have 1 item on sale at int_price 1
        # can have max 5 on sale, dont have any in inv.
        # Delist one, as min allowed int_price is 2

        delists = determine_delists(
            market_listings[0],
            min_price_market_listing[0],
            max_on_sale[1],
            tot_in_inventory[0],
            usual_price[0],
            min_allowed_price[1],
        )
        self.assertEqual(delists, 1)

        # have 1 item on sale at int_price 1
        # can have max 5 on sale, dont have any in inv.
        # Delist one, as min allowed int_price is 2

        delists = determine_delists(
            market_listings[0],
            min_price_market_listing[2],
            max_on_sale[0],
            tot_in_inventory[0],
            usual_price[0],
            min_allowed_price[0],
        )
        self.assertEqual(delists, 1)

    def test_actions_to_make_list_delist(self) -> None:
        N_MarketListings = 5
        MinPriceOfMyMarketListings = 189
        N_NumberToSell = 12
        N_InInventory = 5
        ItemSellingPrice = 180
        minAllowedPrice = 175
        actions = actions_to_make_list_delist(
            N_MarketListings,
            MinPriceOfMyMarketListings,
            N_NumberToSell,
            N_InInventory,
            ItemSellingPrice,
            minAllowedPrice,
        )

        self.assertEqual(
            actions,
            {
                "delist": {"qty": 0},
                "list": {"qty": 5, "int_price": 180},
            },
        )
        self.assertTrue(N_MarketListings - actions["delist"]["qty"] + actions["list"]["qty"] <= N_NumberToSell)

    def test_0_in_inv(self) -> None:
        N_MarketListings = 5
        MinPriceOfMyMarketListings = 189
        N_NumberToSell = 12
        ItemSellingPrice = 180
        minAllowedPrice = 175
        N_InInventory = 0
        actions = actions_to_make_list_delist(
            N_MarketListings,
            MinPriceOfMyMarketListings,
            N_NumberToSell,
            N_InInventory,
            ItemSellingPrice,
            minAllowedPrice,
        )
        self.assertEqual(
            actions,
            {
                "delist": {"qty": 5},
                "list": {"qty": 0, "int_price": 180},
            },
        )
        self.assertTrue(N_MarketListings - actions["delist"]["qty"] + actions["list"]["qty"] <= N_NumberToSell)

    def test_to_be_made_valid(self) -> None:
        # Ne ho 5 listati @ 1.89
        # 5 in inv, max on sale 12
        # Prezzo usuale 1.80, minimo=1.75
        # risultato Delista 0,lista 5 a 1.80
        market_listings = 5
        min_price_market_listing = 189
        max_on_sale = 12
        tot_in_inventory = 5
        usual_price = 180
        min_allowed_price = 175

        actions = actions_to_make_list_delist(
            market_listings,
            min_price_market_listing,
            max_on_sale,
            tot_in_inventory,
            usual_price,
            min_allowed_price,
        )

        self.assertEqual(
            actions,
            {
                "delist": {"qty": 0},
                "list": {"qty": 5, "int_price": 180},
            },
        )
        self.assertTrue(market_listings - actions["delist"]["qty"] + actions["list"]["qty"] <= max_on_sale)

    def test_listing_equals_on_sale(self) -> None:
        # Ne ho 5 listati @ 1.89
        # 5 in inv, max on sale 5
        # Prezzo usuale 1.80, minimo=1.75
        # risultato Delista 5,lista 5 a 1.80
        market_listings = 5
        min_price_market_listing = 189
        max_on_sale = 5
        tot_in_inventory = 5
        usual_price = 180
        min_allowed_price = 175
        actions = actions_to_make_list_delist(
            market_listings,
            min_price_market_listing,
            max_on_sale,
            tot_in_inventory,
            usual_price,
            min_allowed_price,
        )

        self.assertEqual(
            actions,
            {
                "delist": {"qty": 5},
                "list": {"qty": 5, "int_price": 180},
            },
        )
        self.assertTrue(market_listings - actions["delist"]["qty"] + actions["list"]["qty"] <= max_on_sale)

        # Ne ho 8 listati @ 1.89
        # 5 in inv, max on sale 5
        # Prezzo usuale 1.80, minimo=1.75
        # risultato Delista 8,lista 5 a 1.80
        market_listings = 8
        min_price_market_listing = 189
        max_on_sale = 5
        tot_in_inventory = 5
        usual_price = 180
        min_allowed_price = 175
        actions = actions_to_make_list_delist(
            market_listings,
            min_price_market_listing,
            max_on_sale,
            tot_in_inventory,
            usual_price,
            min_allowed_price,
        )

        self.assertEqual(
            actions,
            {
                "delist": {"qty": 8},
                "list": {"qty": 5, "int_price": 180},
            },
        )
        self.assertTrue(market_listings - actions["delist"]["qty"] + actions["list"]["qty"] <= max_on_sale)

    def test_same_price(self) -> None:
        tot_in_inventory = 19
        market_listings = 1
        max_on_sale = 1
        min_price_market_listing = 1239
        usual_price = 600
        min_allowed_price = 1240

        actions = actions_to_make_list_delist(
            market_listings,
            min_price_market_listing,
            max_on_sale,
            tot_in_inventory,
            usual_price,
            min_allowed_price,
        )

        self.assertEqual(
            actions,
            {
                "delist": {"qty": 0},
                "list": {"qty": 0, "int_price": 1239},
            },
        )
        self.assertTrue(market_listings - actions["delist"]["qty"] + actions["list"]["qty"] <= max_on_sale)

    def test_delist_all_and_relist(self) -> None:
        # Ne ho 2 listati @ 1.80
        # 3 in inv, max on sale 5
        # Prezzo usuale 1.80, minimo=1.80
        # risultato Delista 0,lista 3 a 1.80
        MinPriceOfMyMarketListings = 180
        ItemSellingPrice = 180
        minAllowedPrice = 180
        N_InInventory = 3
        N_NumberToSell = 5
        N_MarketListings = 2
        # Just list 3 more
        actions = actions_to_make_list_delist(
            N_MarketListings,
            MinPriceOfMyMarketListings,
            N_NumberToSell,
            N_InInventory,
            ItemSellingPrice,
            minAllowedPrice,
        )
        self.assertEqual(
            actions,
            {
                "delist": {"qty": 0},
                "list": {"int_price": 180, "qty": 3},
            },
        )
        self.assertTrue(N_MarketListings - actions["delist"]["qty"] + actions["list"]["qty"] <= N_NumberToSell)

        N_MarketListings = 10
        # Ne ho 10 listati @ 1.80
        # 3 in inv, max on sale 5
        # Prezzo usuale 1.80, minimo=1.80
        # risultato Delista 5,lista 0 a 1.80

        actions = actions_to_make_list_delist(
            N_MarketListings,
            MinPriceOfMyMarketListings,
            N_NumberToSell,
            N_InInventory,
            ItemSellingPrice,
            minAllowedPrice,
        )

        # Questo in realtà è giusto....
        self.assertEqual(
            actions,
            {
                "delist": {"qty": 5},
                "list": {"qty": 0, "int_price": 180},
            },
        )
        self.assertTrue(N_MarketListings - actions["delist"]["qty"] + actions["list"]["qty"] <= N_NumberToSell)

    def test_actions_to_make_list_delist_min_allowed_price(self) -> None:
        N_MarketListings = 5
        MinPriceOfMyMarketListings = 181
        N_NumberToSell = 12
        N_InInventory = 5
        ItemSellingPrice = 180
        minAllowedPrice = 1200
        actions = actions_to_make_list_delist(
            N_MarketListings,
            MinPriceOfMyMarketListings,
            N_NumberToSell,
            N_InInventory,
            ItemSellingPrice,
            minAllowedPrice,
        )
        self.assertEqual(
            actions,
            {
                "delist": {"qty": 5},
                "list": {"qty": 5, "int_price": 1200},
            },
        )


class TestListDelists(TestCase):
    @given(
        st.integers(),  # market_listings
        st.integers(),  # max_on_sale
        st.integers(),  # tot_in_inventory
        st.integers(),  # usual_price
        st.integers(),  # min_allowed_price
    )
    @settings(verbosity=Verbosity.verbose)
    def test_determine_lists(self, market_listings, max_on_sale, tot_in_inventory, usual_price, min_allowed_price):
        try:
            a = determine_lists(
                market_listings,
                max_on_sale,
                tot_in_inventory,
                usual_price,
                min_allowed_price,
            )
            self.assertIsInstance(a["int_price"], int)
            self.assertGreater(a["int_price"], 0)
            self.assertGreaterEqual(a["int_price"], min_allowed_price)
            self.assertGreaterEqual(a["qty"], 0)
            self.assertTrue(a["qty"] <= tot_in_inventory)
            self.assertTrue(a["qty"] + market_listings <= max_on_sale or a["qty"] == 0)

        except ValueError as e:
            self.assertTrue("Prices must be greater than 0" in str(e) or "Amounts must be greater than 0" in str(e))

    @given(
        st.integers(),  # market_listings
        st.integers(),  # min_price_market_listing
        st.integers(),  # max_on_sale
        st.integers(),  # tot_in_inventory
        st.integers(),  # usual_price
        st.integers(),  # min_allowed_price
    )
    @settings(verbosity=Verbosity.verbose)
    def test_determine_delists(
        self, market_listings, min_price_market_listing, max_on_sale, tot_in_inventory, usual_price, min_allowed_price
    ):
        try:
            a = determine_delists(
                min_price_market_listing=min_price_market_listing,
                market_listings=market_listings,
                max_on_sale=max_on_sale,
                tot_in_inventory=tot_in_inventory,
                usual_price=usual_price,
                min_allowed_price=min_allowed_price,
            )
            self.assertGreaterEqual(a, 0)
        except ValueError as e:
            self.assertTrue("Prices must be greater than 0" in str(e) or "Amounts must be greater than 0" in str(e))
