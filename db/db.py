import datetime
import decimal
import logging
from typing import Any, Dict, Optional

import sqlalchemy.types as types
from sqlalchemy import (Boolean, Column, DateTime, Integer, String,
                        create_engine)
from sqlalchemy.exc import NoSuchModuleError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Query, scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)

_DECL_BASE: Any = declarative_base()
_SQL_DOCS_URL = 'http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls'
_DB_URL = 'sqlite:///sales.sqlite'


# TODO make so that cancelled orders show up in db.

def init_db(db_url: str = _DB_URL) -> None:
    """
    Initializes this module with the given config,
    registers all known command handlers
    and starts polling for message updates
    :param db_url: Database to use
    :return: None
    """
    if db_url is None:
        db_url = _DB_URL

    kwargs = {}

    # Take care of thread ownership if in-memory db
    if db_url == 'sqlite://':
        kwargs.update({
            'connect_args': {'check_same_thread': False},
            'poolclass': StaticPool,
            'echo': False,
        })

    try:
        engine = create_engine(db_url, **kwargs)
    except NoSuchModuleError:
        raise Exception
    ItemSale.session = scoped_session(sessionmaker(bind=engine, autoflush=True, autocommit=True))

    ItemSale.query = ItemSale.session.query_property()
    _DECL_BASE.metadata.create_all(engine)


# noinspection PyAbstractClass
class SqliteNumeric(types.TypeDecorator):
    impl = types.String

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(types.VARCHAR(100))

    def process_bind_param(self, value, dialect):
        return str(value)

    def process_result_value(self, value, dialect):
        return decimal.Decimal(value)


class ItemSale(_DECL_BASE):
    """
    ItemSale database model.
    id text,date int, name text,sold bool, qty real,'
                                'buyer_pays real, you_receive real
    """
    __tablename__ = 'sales'
    id = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    item_id = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    name = Column(String, nullable=False)
    sold = Column(Boolean, nullable=False, default=False)
    quantity = Column(Integer, nullable=False, default=1)
    buyer_pays = Column(SqliteNumeric(12, 3), nullable=False)
    you_receive = Column(SqliteNumeric(12, 3), nullable=False)
    currency = Column(String, nullable=False, default='EUR')
    account = Column(String, nullable=False, default='')

    def to_json(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'item_id': self.item_id,
            'date': self.date,
            'name': self.name,
            'sold': self.sold,
            'quantity': self.quantity,
            'buyer_pays': self.buyer_pays,
            'you_receive': self.you_receive

        }

    @staticmethod
    def query_ref(name: Optional[str] = None, item_id: Optional[str] = None, sold: Optional[bool] = None) -> Query:
        """
        Get all currently active locks for this pair
        :param sold: if should search only sold items
        :param item_id: Itemid to Check for
        :rtype: object
        :param name: Skin to check for.
        """

        filters = []
        if sold is not None:
            filters.append(ItemSale.sold == sold)
        if name:
            filters.append(ItemSale.name == name)
        if item_id:
            filters.append(ItemSale.item_id == item_id)
        return ItemSale.query.filter(
            *filters
        )

    def __repr__(self) -> str:
        return str(self.to_json())


if __name__ == '__main__':
    init_db(_DB_URL)
    a = ItemSale(date=datetime.datetime.now(), item_id=12345, name='test1', quantity=1,
                 buyer_pays=decimal.Decimal(1.02),
                 you_receive=2)
    ItemSale.session.add(a)
    ItemSale.session.flush()
    k = ItemSale.query_ref('test1')
    pass
