import decimal
import logging
from datetime import datetime
from typing import Any, Optional

import sqlalchemy.types as types
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
    desc,
)
from sqlalchemy.exc import NoSuchModuleError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Query, relationship, scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)

_DECL_BASE: Any = declarative_base()
_SQL_DOCS_URL = "https://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls"
_DB_URL = "sqlite:///sales.sqlite"


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
    if db_url == "sqlite://":
        kwargs.update(
            {
                "connect_args": {"check_same_thread": False},
                "poolclass": StaticPool,
                "echo": False,
            }
        )

    try:
        engine = create_engine(db_url, **kwargs)
    except NoSuchModuleError:
        raise Exception

    # https://docs.sqlalchemy.org/en/13/orm/contextual.html#thread-local-scope
    # Scoped sessions proxy requests to the appropriate thread-local session.
    # We should use the scoped_session object - not a seperately initialized version

    Listing._session = scoped_session(
        sessionmaker(bind=engine, autoflush=True, autocommit=True)
    )
    Listing.query = Listing._session.query_property()
    Item.query = Listing._session.query_property()
    GCItem.query = Listing._session.query_property()
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


class GCItem(_DECL_BASE):
    """
    Item database model.
    caches response from GC
    """

    __tablename__ = "GC_items"
    # 'itemid': 22657987550, 'defindex': 507, 'paintindex': 0, 'rarity': 6, 'quality': 3,
    # 'paintwear': 1060247478, 'paintseed': 137, 'killeaterscoretype': 0, 'killeatervalue': 0,
    # 'inventory': 3221225482, 'origin': 8
    id = Column(Integer, primary_key=True)
    asset_id = Column(String, nullable=False)  # Parameter A
    itemid = Column(Integer, nullable=False)
    defindex = Column(Integer)
    paintindex = Column(Integer)
    paintwear = Column(Integer)
    paintseed = Column(Integer)
    killeaterscoretype = Column(Integer)
    killeatervalue = Column(Integer)
    inventory = Column(Integer)
    origin = Column(Integer)
    rarity = Column(Integer)
    quality = Column(Integer)

    def to_json(self):
        return {i: k for i, k in vars(self).items() if not i.startswith("_")}

    def __repr__(self) -> str:
        return str(self.to_json())

    @staticmethod
    def query_ref(
        item_id: Optional[str] = None, asset_id: Optional[str] = None
    ) -> Query:
        """
        Get all currently active locks for this pair
        :param asset_id:  assetid to check for. Parameter A
        :param item_id: Itemid to Check for
        :rtype: Query
        """
        filters = []

        if item_id:
            filters.append(GCItem.itemid == item_id)
        if asset_id:
            filters.append(GCItem.asset_id == asset_id)
        return GCItem.query.filter(*filters)


class Item(_DECL_BASE):
    """
    Item database model.
    contains all items in inventory
    """

    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    item_id = Column(String, nullable=False, unique=True)
    market_hash_name = Column(String, nullable=False)
    account = Column(String, nullable=False, default="")
    appid = Column(String, nullable=False, default="730")
    contextid = Column(String, nullable=False, default="2")
    # Bool fields
    tradable = Column(Boolean, nullable=False, default=False)
    marketable = Column(Boolean, nullable=False, default=False)
    commodity = Column(Boolean, nullable=False, default=False)
    sold = Column(Boolean, nullable=False, default=False)
    stale_item_id = Column(Boolean, nullable=False, default=False)
    listings = relationship("Listing", back_populates="item")

    @staticmethod
    def query_ref(
        market_hash_name: Optional[str] = None,
        item_id: Optional[str] = None,
        sold: Optional[bool] = None,
    ) -> Query:
        """
        Get all currently active locks for this pair
        :param sold: if should search only sold items
        :param item_id: Itemid to Check for
        :rtype: object
        :param market_hash_name: Skin to check for.
        """

        filters = []
        if sold is not None:
            filters.append(Item.sold == sold)
        if market_hash_name:
            filters.append(Item.market_hash_name == market_hash_name)
        if item_id:
            filters.append(Item.item_id == item_id)
        return Item.query.filter(*filters)

    def to_json(self):
        return {i: k for i, k in vars(self).items() if not i.startswith("_")}

    def is_sold(self):
        return any(listing.sold for listing in self.listings)

    def __repr__(self) -> str:
        return str(self.to_json())


class Listing(_DECL_BASE):
    """
    Listing database model.
    id text,date int, name text,sold bool, qty real,'
                                'buyer_pays real, you_receive real
    """

    __tablename__ = "sales"
    __table_args__ = (
        UniqueConstraint("item_id", "sold", "on_sale", name="_itemid_sold_onsale"),
    )

    id = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    listing_id = Column(String, unique=True)
    item_id = Column(String, ForeignKey("items.item_id"))
    date = Column(DateTime, nullable=False)
    sold = Column(Boolean, nullable=False, default=False)
    on_sale = Column(Boolean, nullable=False, default=False)
    buyer_pays = Column(SqliteNumeric(12, 3), nullable=False)
    you_receive = Column(SqliteNumeric(12, 3), nullable=False)
    currency = Column(String, nullable=False, default="EUR")

    item = relationship("Item", back_populates="listings")

    def to_json(self):
        return {i: k for i, k in vars(self).items() if not i.startswith("_")}

    @staticmethod
    def query_ref(
        item_id: Optional[str] = None,
        sold: Optional[bool] = None,
        on_sale: Optional[bool] = None,
    ) -> Query:
        """
        Get all currently active locks for this pair
        :param on_sale: is item on sale or not
        :param sold: if should search only sold items
        :param item_id: Itemid to Check for
        :rtype: object

        """

        filters = []
        if on_sale is not None:
            filters.append(Listing.on_sale == on_sale)
        if sold is not None:
            filters.append(Listing.sold == sold)
        if item_id:
            filters.append(Listing.item_id == item_id)
        return Listing.query.filter(*filters).order_by(desc("date"))

    def __repr__(self) -> str:
        return str(self.to_json())


if __name__ == "__main__":
    init_db(_DB_URL)
    # id = Column(Integer, primary_key=True)
    # item_id = Column(String, nullable=False)
    # market_hash_name = Column(String, nullable=False)
    # account = Column(String, nullable=False, default='')
    # appid = Column(String, nullable=False, default='730')
    # contextid = Column(String, nullable=False, default='2')
    # # Bool fields
    # tradable = Column(Boolean, nullable=False)
    # marketable = Column(Boolean, nullable=False)
    # commodity = Column(Boolean, nullable=False)
    # listings = relationship("Listing", back_populates="item")

    for _ in range(5):
        b = Item(item_id=f"12345{_}", market_hash_name="test", account="nas")
        Item.query.session.add(b)
    Item.query.session.flush()
    for _ in range(5):
        a = Listing(
            date=datetime.now(),
            item_id="12345",
            buyer_pays=decimal.Decimal(1.02),
            you_receive=2,
        )
        Listing.query.session.add(a)
    Listing.query.session.flush()
    Item.query_ref(item_id="12345").all()
    pass
