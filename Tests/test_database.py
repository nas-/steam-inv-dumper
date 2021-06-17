import decimal
import os
from datetime import datetime
from unittest import TestCase

from db.db import ItemSale, init_db


class TestSteamDatabase(TestCase):
    def setUp(self) -> None:
        init_db('sqlite:///sales_test.sqlite')

    def tearDown(self) -> None:
        os.remove('sales_test.sqlite')

    def test_select_all_ids(self) -> None:
        for_db = ItemSale(
            item_id='12345',
            date=datetime.now(),
            name='casekey1',
            buyer_pays=decimal.Decimal('4.99'),
            you_receive=decimal.Decimal('4.30'),
            account='nasil2nd'
        )
        ItemSale.session.add(for_db)
        ItemSale.session.flush()
        K = ItemSale.query_ref(item_id='12345').first()
        self.assertEqual(K.item_id, '12345')
        K = ItemSale.query_ref(name='casekey1').first()
        self.assertEqual(K.name, 'casekey1')

        K = ItemSale.query_ref(name='casekey1').first()
        self.assertEqual(K.you_receive, decimal.Decimal('4.30'))
        self.assertEqual(K.buyer_pays, decimal.Decimal('4.99'))
        K.sold = True
        ItemSale.session.flush()
        self.assertEqual(K.sold, True)
        K = ItemSale.query_ref(name='casekey1').first()
        ItemSale.session.delete(K)
        ItemSale.session.flush()
        self.assertEqual(ItemSale.query_ref(name='casekey1').all(), [])

    def test_correct_decimal_precison(self) -> None:
        for_db = ItemSale(
            item_id='12345',
            date=datetime.now(),
            name='casekey1',
            buyer_pays=decimal.Decimal(14.99).quantize(decimal.Decimal('0.01')),
            you_receive=decimal.Decimal(14.30).quantize(decimal.Decimal('0.01')),
            account='nasil2nd'
        )
        ItemSale.session.add(for_db)
        ItemSale.session.flush()
        K = ItemSale.query_ref(name='casekey1').first()

        self.assertEqual(K.you_receive, decimal.Decimal('14.30'))
        self.assertEqual(K.buyer_pays, decimal.Decimal('14.99'))

# test_db.query(write_query, list_of_fake_params)
# results = test_db.query(read_query)
# assert results = what_the_results_should_be
