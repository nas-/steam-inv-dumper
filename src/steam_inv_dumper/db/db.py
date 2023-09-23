import logging
from typing import Any, List, Optional, Type, TypeVar

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    case,
    create_engine,
    desc,
    func,
    select,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Query, aliased, relationship, scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool

from steam_inv_dumper.utils.data_structures import (
    MarketEvent,
    MarketEventTypes,
    MyMarketListing,
)

logger = logging.getLogger(__name__)
_DECL_BASE: Any = declarative_base()
_SQL_DOCS_URL = "https://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls"
_DB_URL = "sqlite:///sales.sqlite"
L = TypeVar("L", bound="Listing")
I = TypeVar("I", bound="Item")
E = TypeVar("E", bound="Event")


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
        Item._session = scoped_session(self.session)
        # As the 2 tables are closely related, they are to share the same session.
        Listing.query = Item._session.query_property()
        Item.query = Item._session.query_property()
        Event.query = Item._session.query_property()
        self.Listing = Listing
        self.Item = Item
        self.Event = Event

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
    listings = relationship("Listing", back_populates="item", cascade="all,delete-orphan")

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


class Listing(_DECL_BASE):
    """
    Listing database model for items
    Each item can have multiple listings
    Each listing can have multiple events
    """

    __tablename__ = "listings"
    __table_args__ = (UniqueConstraint("item_id", "listing_id", name="_itemid_sold_onsale"),)

    id = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    listing_id = Column(String, unique=True)
    buyer_pay = Column(Integer, nullable=False)
    you_receive = Column(Integer, nullable=False)
    item_id = Column(String, ForeignKey("items.item_id"))
    currency = Column(String, nullable=False, default="EUR")
    item = relationship("Item", back_populates="listings")
    events = relationship(
        "Event", back_populates="listing", cascade="all,delete-orphan", order_by="desc(Event.event_datetime)"
    )

    def to_json(self) -> dict:
        return {i: k for i, k in vars(self).items() if not i.startswith("_")}

    @hybrid_property
    def listing_status(self):
        if self.events:
            return self.events[0].event_type
        return "ListingCreated"

    @listing_status.expression
    def listing_status(cls):
        return (
            select([Event.event_type])
            .where(Event.listing_id == cls.listing_id)
            .order_by(Event.event_datetime.desc())
            .limit(1)
            .as_scalar()
        )

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
        # Define a subquery to compute the listing_status
        listing_status_subquery = (
            select(
                [
                    Listing.id,
                    case([(Event.event_type.isnot(None), Event.event_type)], else_="ListingCreated").label(
                        "computed_listing_status"
                    ),
                ]
            )
            .outerjoin(Event)
            .group_by(Listing.id, Event.event_type)
            .subquery()
        )
        # Use the subquery in your main query and filter by computed_listing_status
        subq = aliased(listing_status_subquery)
        query = Listing.query.join(subq, Listing.id == subq.c.id)

        if listing_status is not None:
            if any(status not in list(a.name for a in MarketEventTypes) for status in listing_status):
                raise ValueError("Invalid Listing Status")
            filters.append(subq.c.computed_listing_status.in_(listing_status))
        if item_id:
            filters.append(Listing.item_id == item_id)
        return query.filter(*filters).order_by(Listing.id.desc())

    def __repr__(self) -> str:
        return str(self.to_json())

    @classmethod
    def from_my_listing(cls: Type[L], my_listing: MyMarketListing, listing_status: str) -> L:
        return cls(
            listing_id=my_listing.listing_id,
            buyer_pay=my_listing.buyer_pay,
            you_receive=my_listing.you_receive,
            item_id=my_listing.description.id,
            currency=my_listing.description.currency,
        )


class Event(_DECL_BASE):
    """
    Each listing has multiple events connected with it, which can be, created, sold, cancelled.
    Events are stored in the Dataclass MarketEvent.
    listingid: str
    purchaseid: Optional[str]
    event_type: MarketEventTypes
    event_datetime: datetime
    time_event_fraction: int
    steamid_actor: int
    """

    __tablename__ = "events"
    __table_args__ = (UniqueConstraint("listing_id", "event_type", name="_listing_event"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    listing_id = Column(String, ForeignKey("listings.listing_id"))
    purchase_id = Column(String, nullable=True)
    event_type = Column(String, nullable=False)
    event_datetime = Column(DateTime, default=func.current_timestamp(), nullable=False)
    time_event_fraction = Column(Integer, nullable=False)
    steam_id_actor = Column(String, nullable=False)
    listing = relationship("Listing", back_populates="events")
    # item = relationship("Item", secondary="listings", back_populates="events")

    def to_json(self) -> dict:
        return {i: k for i, k in vars(self).items() if not i.startswith("_")}

    @staticmethod
    def query_ref(
        listing_id: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> Query:
        """
        Get all currently active locks for this pair
        :param listing_id: Listing ID to Check for
        :param event_type: Event Type to Check for
        :rtype: object
        """
        filters = []
        if listing_id:
            filters.append(Event.listing_id == listing_id)
        if event_type:
            filters.append(Event.event_type == event_type)
        return Event.query.filter(*filters).order_by(desc("event_datetime"))

    def __repr__(self) -> str:
        return str(self.to_json())

    @classmethod
    def from_market_event(cls, market_event: MarketEvent) -> "Event":
        return cls(
            listing_id=market_event.listingid,
            purchase_id=market_event.purchaseid,
            event_type=market_event.event_type.name,
            event_datetime=market_event.event_datetime,
            time_event_fraction=market_event.time_event_fraction,
            steam_id_actor=market_event.steamid_actor,
        )
