import decimal
from datetime import datetime
from unittest import TestCase

from db.db import ItemSale, init_db

init_db('sqlite:///sales_test.sqlite')


class TestSteamDatabase(TestCase):
    def tearDown(self) -> None:
        # TODO delete the database
        pass

    def test_select_all_ids(self):
        for_db = ItemSale(
            item_id='12345',
            date=datetime.now(),
            name='casekey1',
            buyer_pays=decimal.Decimal(4.99),
            you_receive=decimal.Decimal(4.30),
            account='nasil2nd'
        )
        ItemSale.session.add(for_db)
        ItemSale.session.flush()
        K = ItemSale.query_ref(item_id='12345').first()
        self.assertEqual(K.item_id, 12345)
        K = ItemSale.query_ref(name='casekey1').first()
        self.assertEqual(K.name, 'casekey1')

        K.buyer_pays = decimal.Decimal(4.51)
        K.you_receive = decimal.Decimal(5.01)
        ItemSale.session.flush()
        K = ItemSale.query_ref(name='casekey1').first()
        self.assertEqual(K.you_receive, decimal.Decimal(5.01))
        self.assertEqual(K.buyer_pays, decimal.Decimal(4.51))
        K.sold = True
        ItemSale.session.flush()
        self.assertEqual(K.sold, True)
        K = ItemSale.query_ref(name='casekey1').first()
        ItemSale.session.delete(K)
        ItemSale.session.flush()
        self.assertEqual(ItemSale.query_ref(name='casekey1').all(), [])

# test_db.query(write_query, list_of_fake_params)
# results = test_db.query(read_query)
# assert results = what_the_results_should_be
