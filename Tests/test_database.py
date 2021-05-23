from unittest import TestCase
from database import SteamDatabase
import decimal

SteamDB = SteamDatabase('.\\sales.db', 'test_sales')


class TestSteamDatabase(TestCase):

    def test_select_all_ids(self):
        db = SteamDB
        db.insert_data('12345', 'casekey1', False, 1, decimal.Decimal(4.99), decimal.Decimal(4.30))
        a = db.select_all_ids('casekey1')
        self.assertEqual(a, ['12345'])
        db.update_data('12345', 'casekey1', buyer_pays=decimal.Decimal(4.51), you_receive=decimal.Decimal(5.01))
        b = db.cursor.execute(f"select group_concat(buyer_pays, ', ') from {db.table} where sold=? and name=?;",
                              (False, 'casekey1',)).fetchall()[0]
        self.assertEqual(b, ('4.51',))
        c = db.cursor.execute(f"select group_concat(you_receive, ', ') from {db.table} where sold=? and name=?;",
                              (False, 'casekey1',)).fetchall()[0]
        self.assertEqual(c, ('5.01',))
        db.update_data('12345', 'casekey1', sold=True)
        d = db.cursor.execute(f"select group_concat(sold, ', ') from {db.table} where sold=? and name=?;",
                              (True, 'casekey1',)).fetchall()[0]
        self.assertEqual(d, ('1',))
        db.delete_data('12345')
        e = db.cursor.execute(f'select count(*) from {db.table}').fetchall()[0]
        self.assertEqual(e, (0,))

# test_db.query(write_query, list_of_fake_params)
# results = test_db.query(read_query)
# assert results = what_the_results_should_be
