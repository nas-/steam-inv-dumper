import logging
from datetime import datetime
from typing import Any, List, Optional, Type, TypeVar

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
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Query, relationship, scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool

from steam_inv_dumper.utils.data_structures import MyMarketListing

logger = logging.getLogger(__name__)
_DECL_BASE: Any = declarative_base()
_SQL_DOCS_URL = "https://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls"
_DB_URL = "sqlite:///sales.sqlite"


class Database:
    def __init__(self, config: dict):
        # Take care of thread ownership if in-memory db

        db_url = config["db_url"]

        schema = "test_steam" if config.get("debug", True) is True else "prod_steam"

        kwargs = {"connect_args": {"options": f"-csearch_path={schema}"}}

        if db_url == "sqlite://":
            kwargs.update(
                {
                    "connect_args": {"check_same_thread": False},
                    "poolclass": StaticPool,
                    "echo": False,
                }
            )
        self.engine = create_engine(db_url, encoding="utf-8", **kwargs)  # echo=True for debugging
        self.base = _DECL_BASE

        self.session = sessionmaker(bind=self.engine, autoflush=True, autocommit=True)
        Listing._session = scoped_session(self.session)
        # As the 2 tables are closely related, they are to share the same session.
        Listing.query = Listing._session.query_property()
        Item.query = Listing._session.query_property()
        self.Listing = Listing
        self.Item = Item

        self.base.metadata.create_all(self.engine)


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

    def to_json(self) -> dict:
        return {i: k for i, k in vars(self).items() if not i.startswith("_")}

    def __repr__(self) -> str:
        return str(self.to_json())


L = TypeVar("L", bound="Listing")


class Listing(_DECL_BASE):
    """
    Listing database model.
    id text,date int, market_hash_name text,sold bool, qty real,'
                                'buyer_pays real, you_receive real
    """

    __tablename__ = "listings"
    __table_args__ = (UniqueConstraint("item_id", "listing_id", name="_itemid_sold_onsale"),)

    id = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    listing_id = Column(String, unique=True)
    buyer_pay = Column(Integer, nullable=False)
    you_receive = Column(Integer, nullable=False)
    item_id = Column(String, ForeignKey("items.item_id"))
    created_on = Column(DateTime, default=func.current_timestamp(), nullable=False)
    currency = Column(String, nullable=False, default="EUR")
    listing_status = Column(String, nullable=True)
    item = relationship("Item", back_populates="listings")

    def to_json(self) -> dict:
        return {i: k for i, k in vars(self).items() if not i.startswith("_")}

    @staticmethod
    def query_ref(
        item_id: Optional[str] = None,
        listing_status: Optional[List[str]] = None,
    ) -> Query:
        """
        Get all currently active locks for this pair
        :param listing_status: Listing Statuses
        :param item_id: Itemid to Check for
        :rtype: object

        """
        filters = []
        if listing_status is not None:
            statuses = [status.upper() for status in listing_status]
            filters.append(Listing.listing_status.in_(statuses))
        if item_id:
            filters.append(Listing.item_id == item_id)
        return Listing.query.filter(*filters).order_by(desc("created_on"))

    def __repr__(self) -> str:
        return str(self.to_json())

    @classmethod
    def from_my_listing(cls: Type[L], my_listing: MyMarketListing, listing_status: str) -> L:
        created_on = my_listing.created_on if isinstance(my_listing.created_on, datetime) else None

        return cls(
            listing_id=my_listing.listing_id,
            buyer_pay=my_listing.buyer_pay,
            you_receive=my_listing.you_receive,
            item_id=my_listing.description.id,
            created_on=created_on,
            currency=my_listing.description.currency,
            listing_status=listing_status,
        )
