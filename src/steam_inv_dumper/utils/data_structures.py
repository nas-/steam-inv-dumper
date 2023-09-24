from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Literal, Optional, Type, TypeVar

from steam_inv_dumper.utils.steam_prices_utils import convert_string_prices

T = TypeVar("T", bound="ListOnMarket")
V = TypeVar("V", bound="DelistFromMarket")
X = TypeVar("X", bound="InventoryItem")
L = TypeVar("L", bound="MyMarketListing")
P = TypeVar("P", bound="MarketListing")
M = TypeVar("M", bound="MarketEvent")


class MarketActionType(Enum):
    PlaceOnMarket = "PlaceOnMarket"
    RemoveFromMarket = "RemoveFromMarket"


@dataclass
class ListOnMarket:
    action_type: Literal[MarketActionType.PlaceOnMarket]
    assetsID: str  # TODO change to item_id
    buyer_pays: str
    market_hash_name: str
    you_receive: str

    @classmethod
    def from_dict(cls: Type[T], dictionary: dict) -> T:
        if isinstance(dictionary["you_receive"], float):
            raise Exception("Needs to be int, or str")
        if isinstance(dictionary["buyer_pays"], float):
            raise Exception("Needs to be int, or str")

        return cls(
            action_type=dictionary["action_type"],
            assetsID=dictionary["assetsID"],
            market_hash_name=dictionary["market_hash_name"],
            you_receive=str(dictionary["you_receive"]),
            buyer_pays=str(dictionary["buyer_pays"]),
        )


@dataclass
class DelistFromMarket:
    action_type: Literal[MarketActionType.RemoveFromMarket]
    itemID: str
    listing_id: str
    market_hash_name: str
    Unowned_itemID: str

    @classmethod
    def from_dict(cls: Type[V], dictionary: dict) -> V:
        return cls(
            action_type=dictionary["action_type"],
            market_hash_name=dictionary["market_hash_name"],
            itemID=dictionary["itemID"],
            Unowned_itemID=dictionary["Unowned_itemID"],
            listing_id=dictionary["listing_id"],
        )


@dataclass
class InventoryItem:
    amount: str
    appid: int
    background_color: str
    classid: str
    commodity: bool
    contextid: str
    instanceid: str
    item_id: str
    market_hash_name: str
    market_name: str
    market_tradable_restriction: int
    marketable: bool
    name_color: str
    original_amount: Optional[str]
    owner: Optional[int]
    status: Optional[int]
    tradable: bool
    type: str
    unowned_contextid: Optional[str]
    unowned_id: Optional[str]

    @classmethod
    def from_my_listing_dict(cls: Type[X], dictionary: dict) -> X:
        return cls(
            amount=dictionary["amount"],
            appid=dictionary["appid"],
            background_color=dictionary["background_color"],
            classid=dictionary["classid"],
            commodity=bool(dictionary["commodity"]),
            contextid=dictionary["contextid"],
            instanceid=dictionary["instanceid"],
            item_id=dictionary["id"],
            market_hash_name=dictionary["market_hash_name"],
            market_name=dictionary["market_name"],
            market_tradable_restriction=dictionary["market_tradable_restriction"],
            marketable=bool(dictionary["marketable"]),
            name_color=dictionary["name_color"],
            original_amount=dictionary.get("original_amount"),
            owner=dictionary.get("owner"),
            status=dictionary.get("status"),
            tradable=bool(dictionary["tradable"]),
            type=dictionary["type"],
            unowned_contextid=dictionary.get("unowned_contextid"),
            unowned_id=dictionary.get("unowned_id"),
        )

    @classmethod
    def from_item(cls: Type[X], item: "Item") -> X:
        return cls(
            amount=item.amount,
            appid=int(item.appid),
            background_color=item.background_color,
            classid=item.classid,
            commodity=bool(item.commodity),
            contextid=item.contextid,
            item_id=str(item.item_id),
            instanceid=item.instanceid,
            market_hash_name=item.market_hash_name,
            market_name=item.market_name,
            market_tradable_restriction=item.market_tradable_restriction,
            marketable=bool(item.marketable),
            name_color=item.name_color,
            original_amount=item.original_amount,
            owner=item.owner,
            status=item.status,
            tradable=bool(item.tradable),
            type=item.type,
            unowned_contextid=item.unowned_contextid,
            unowned_id=item.unowned_id,
        )


# TODO merge with Generic Market Listing

@dataclass
class MyMarketListing:
    """
    The price of this is in full values.
    Not in cents.

    """

    buyer_pay: int
    created_on: str
    description: InventoryItem
    listing_id: str
    need_confirmation: bool
    you_receive: int

    @classmethod
    def from_dict(cls: Type[L], dictionary: dict) -> L:
        return cls(
            listing_id=dictionary["listing_id"],
            buyer_pay=convert_string_prices(dictionary["buyer_pay"]),
            you_receive=convert_string_prices(dictionary["you_receive"]),
            created_on=dictionary["created_on"],
            need_confirmation=dictionary["need_confirmation"],
            description=InventoryItem.from_my_listing_dict(dictionary["description"]),
        )

    @classmethod
    def from_listing(cls: Type[L], listing: "Listing") -> L:
        return cls(
            listing_id=listing.listing_id,
            buyer_pay=listing.buyer_pay,
            you_receive=listing.you_receive,
            # TODO Remove created on
            created_on="",
            need_confirmation=False,
            description=InventoryItem.from_item(listing.item),
        )


@dataclass
class MarketListing:
    asset: InventoryItem
    converted_currencyid: int
    converted_fee: int
    converted_price: int
    currencyid: int
    fee: int
    listingid: str
    price: int

    @classmethod
    def from_dict(cls: Type[P], listing_info: dict, asset_info: dict) -> P:
        """Asset info is the full dict of dicts..."""
        object_id = listing_info["asset"]["id"]
        return cls(
            listingid=listing_info["listingid"],
            price=listing_info["price"],
            fee=listing_info["fee"],
            currencyid=listing_info["currencyid"],
            converted_price=listing_info["converted_price"],
            converted_fee=listing_info["converted_fee"],
            converted_currencyid=listing_info["converted_currencyid"],
            asset=InventoryItem.from_my_listing_dict(asset_info[object_id]),
        )


class MarketEventTypes(Enum):
    ListingCreated = 1
    ListingCancelled = 2
    ListingSold = 3


@dataclass
class MarketEvent:
    event_datetime: datetime
    event_type: MarketEventTypes
    listingid: str
    purchaseid: Optional[str]
    steamid_actor: int
    time_event_fraction: int

    @classmethod
    def from_event(cls: Type[M], dictionary: dict) -> M:
        """
        Create a market event from a raw dictionary.
        :param dictionary: raw dictionary from the API
        :return: MarketEvent
        """
        return cls(
            listingid=dictionary["listingid"],
            purchaseid=dictionary.get("purchaseid"),
            event_type=MarketEventTypes(dictionary["event_type"]),
            event_datetime=datetime.utcfromtimestamp(dictionary["time_event"]),
            time_event_fraction=dictionary["time_event_fraction"],
            steamid_actor=dictionary["steamid_actor"],
        )
