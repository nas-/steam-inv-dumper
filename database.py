import datetime
import decimal
import sqlite3
from typing import List


class SteamDatabase(object):
    def __init__(self, database_name: str, table: str):
        self.connection = sqlite3.connect(database_name)
        self.cursor = self.connection.cursor()
        self.table = table
        try:
            self.cursor.execute(f'CREATE TABLE {self.table} (id text,date int, name text,sold bool, qty real,'
                                'buyer_pays real, you_receive real)')
        except sqlite3.OperationalError:
            print('table is already present')

    def select_all_ids(self, item: str) -> List:
        t = (False, item,)
        data = self.cursor.execute(f"select group_concat(id, ', ') from {self.table} where sold=? and name=?;",
                                   t).fetchall()[0]
        if data[0]:
            return [element.strip() for element in data[0].split(',')]
        else:
            return []

    def insert_data(self, item_id: str, name: str, sold: bool, quantity: int, buyer_pays: float,
                    you_receive: float) -> None:
        if isinstance(buyer_pays, decimal.Decimal):
            buyer_pays = float(buyer_pays)
        if isinstance(you_receive, decimal.Decimal):
            you_receive = float(you_receive)
        t = (item_id, datetime.datetime.now().timestamp(), name, sold, quantity, buyer_pays, you_receive)
        self.cursor.execute(f"INSERT INTO {self.table} VALUES (?,?,?,?,?,?,?)", t)
        print(f'inserted {item_id} {name} successfully!')
        self.connection.commit()

    def delete_data(self, item_id: str) -> None:
        t = (item_id,)
        self.cursor.execute(f"DELETE FROM {self.table} where id=?;", t)
        print(f'removed {item_id} successfully!')
        self.connection.commit()

    def update_data(self, item_id: str, name: str = None, sold: bool = None, buyer_pays: decimal.Decimal = None,
                    you_receive: decimal.Decimal = None) -> None:
        if isinstance(buyer_pays, decimal.Decimal):
            buyer_pays = float(buyer_pays)
        if isinstance(you_receive, decimal.Decimal):
            you_receive = float(you_receive)
        if name is None:
            t = (datetime.datetime.now().timestamp(), sold, item_id,)
            self.cursor.execute(f"UPDATE {self.table} SET date=?,sold=? WHERE id = ?;", t)
        elif sold is None:
            t = (datetime.datetime.now().timestamp(), buyer_pays, you_receive, item_id, name,)
            self.cursor.execute(f"UPDATE {self.table} SET date=?,buyer_pays = ?,you_receive=? WHERE id = ? and name=?;",
                                t)
        elif buyer_pays is None:
            t = (datetime.datetime.now().timestamp(), sold, item_id, name,)
            self.cursor.execute(f"UPDATE {self.table} SET date=?,sold = ? WHERE id = ? and name=?;", t)
        else:
            t = (datetime.datetime.now().timestamp(), sold, buyer_pays, you_receive, item_id, name,)
            self.cursor.execute(
                f"UPDATE {self.table} SET date=?,sold = ?, buyer_pays = ?,you_receive=?  WHERE id = ? and name=?;", t)
        print(f'updated {item_id} {name} successfully!')
        self.connection.commit()


if __name__ == '__main__':

    A = SteamDatabase('sales.db', 'sales')
    A.insert_data('12345', 'casekey1', False, 1, decimal.Decimal(4.99), decimal.Decimal(4.30))
    for row in A.cursor.execute(f'SELECT * FROM {A.table}'):
        print(row)
    A.update_data('12345', 'casekey1', buyer_pays=decimal.Decimal(4.51), you_receive=decimal.Decimal(5.01))
    for row in A.cursor.execute(f'SELECT * FROM {A.table}'):
        print(row)
    A.update_data('12345', 'casekey1', sold=True)
    for row in A.cursor.execute(f'SELECT * FROM {A.table}'):
        print(row)

    A.delete_data('12345')
    for row in A.cursor.execute(f'SELECT * FROM {A.table}'):
        print(row)

# # Insert a row of data

# c.execute("INSERT INTO stocks VALUES ('2006-01-05','BUY','RHAT',100,35.14)")
#
# # Save (commit) the changes
# conn.commit()
#
# # We can also close the connection if we are done with it.
# # Just be sure any changes have been committed or they will be lost.
# conn.close()
