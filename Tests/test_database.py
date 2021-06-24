import decimal
import os
from datetime import datetime
from sqlite3 import IntegrityError
from unittest import TestCase

from db.db import Listing, Item, init_db

TWODIGITS = decimal.Decimal('0.01')


class TestSteamDatabase(TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        os.remove('sales_test.sqlite')

    @classmethod
    def setUpClass(cls) -> None:
        init_db('sqlite:///sales_test.sqlite')
        for_db = Listing(
            item_id='12345',
            date=datetime.now(),
            you_receive=decimal.Decimal(14.30).quantize(decimal.Decimal('0.01')),
            buyer_pays=decimal.Decimal(14.99).quantize(decimal.Decimal('0.01')),
        )
        item_for_db = Item(item_id='12345', market_hash_name='casekey1')
        Listing.query.session.add(for_db)
        Item.query.session.add(item_for_db)
        Listing.query.session.flush()
        Item.query.session.flush()

    def test_is_sold(self):
        K = Item.query_ref(item_id='12345').first()
        self.assertEqual(K.is_sold(), False)
        K.listings[0].sold = True
        Item.query.session.flush()
        K = Item.query_ref(item_id='12345').first()
        self.assertEqual(K.is_sold(), True)
        K.listings[0].sold = False
        Item.query.session.flush()

    def test_listing_to_json(self):
        K = Listing.query_ref(item_id='12345').first()
        item_json = K.to_json()
        self.assertDictEqual(item_json, {
            'listing_id': K.listing_id,
            'on_sale': K.on_sale,
            'id': K.id,
            'currency': K.currency,
            'item_id': K.item_id,
            'date': K.date,
            'sold': K.sold,
            'buyer_pays': K.buyer_pays,
            'you_receive': K.you_receive

        })

    def test_item_to_json(self):
        K = Item.query_ref(item_id='12345').first()
        item_json = K.to_json()
        self.assertDictEqual(item_json, {
            'stale_item_id': K.stale_item_id,
            'sold': K.sold,
            'id': K.id,
            'contextid': K.contextid,
            'item_id': K.item_id,
            'market_hash_name': K.market_hash_name,
            'account': K.account,
            'appid': K.appid,
            'tradable': K.tradable,
            'marketable': K.marketable,
            'commodity': K.commodity

        })

    # def test_item_id_constrain(self):
    #     item_for_db = Item(item_id='12345', market_hash_name='casekey1')
    #     Item.query.session.add(item_for_db)
    #     self.assertRaises(IntegrityError, Item.query.session.flush())

    def test_select_all_ids(self) -> None:
        K = Item.query_ref(item_id='12345').first()
        self.assertEqual(K.item_id, '12345')
        K = Item.query_ref(market_hash_name='casekey1').first()
        self.assertEqual(K.market_hash_name, 'casekey1')

        K = Item.query_ref(market_hash_name='casekey1').first()
        self.assertEqual(K.listings[0].you_receive, decimal.Decimal('14.30').quantize(TWODIGITS))
        self.assertEqual(K.listings[0].buyer_pays, decimal.Decimal('14.99').quantize(TWODIGITS))
        K.sold = True
        Item.query.session.flush()
        self.assertEqual(K.sold, True)
        K = Item.query_ref(market_hash_name='casekey1').first()
        Item.query.session.delete(K)
        Item.query.session.flush()
        self.assertEqual(Item.query_ref(market_hash_name='casekey1').all(), [])

    def test_correct_decimal_precison(self) -> None:
        K = Listing.query_ref(item_id='12345').first()

        self.assertEqual(K.you_receive, decimal.Decimal('14.30').quantize(TWODIGITS))
        self.assertEqual(K.buyer_pays, decimal.Decimal('14.99').quantize(TWODIGITS))

# test_db.query(write_query, list_of_fake_params)
# results = test_db.query(read_query)
# assert results = what_the_results_should_be
