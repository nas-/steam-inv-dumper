from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Protocol

from steam_inv_dumper.utils.price_utils import TWODIGITS, convert_string_prices


class MarketActionType(Enum):
    PlaceOnMarket = "PlaceOnMarket"
    RemoveFromMarket = "RemoveFromMarket"


@dataclass
class ListOnMarket:
    action_type: MarketActionType.PlaceOnMarket
    assetsID: str
    name: str
    you_receive: int
    buyer_pays: int

    @classmethod
    def from_dict(cls, dictionary: dict):
        return cls(
            action_type=dictionary["action_type"],
            assetsID=dictionary["assetsID"],
            name=dictionary["name"],
            you_receive=int(dictionary["you_receive"]),
            buyer_pays=int(dictionary["buyer_pays"]),
        )


@dataclass
class DelistFromMarket:
    action_type: MarketActionType.RemoveFromMarket
    name: str
    itemID: str
    Unowned_itemID: str
    listing_id: str

    @classmethod
    def from_dict(cls, dictionary: dict):
        return cls(
            action_type=dictionary["action_type"],
            name=dictionary["name"],
            itemID=dictionary["itemID"],
            Unowned_itemID=dictionary["Unowned_itemID"],
            listing_id=dictionary["listing_id"],
        )


@dataclass
class InventoryItem:
    appid: int
    classid: str
    amount: str
    instanceid: str
    currency: int
    background_color: str
    tradable: int
    name: str
    name_color: str
    type: str
    market_name: str
    market_hash_name: str
    commodity: int
    market_tradable_restriction: int
    marketable: int
    contextid: str
    id: str

    @classmethod
    def from_inventory(cls, dictionary):
        """Make an inventory Item from API response."""
        return cls(
            currency=dictionary["currency"],
            appid=dictionary["appid"],
            contextid=dictionary["contextid"],
            id=dictionary["id"],
            classid=dictionary["classid"],
            instanceid=dictionary["instanceid"],
            amount=dictionary["amount"],
            background_color=dictionary["background_color"],
            tradable=bool(dictionary["tradable"]),
            name=dictionary["name"],
            name_color=dictionary["name_color"],
            type=dictionary["type"],
            market_name=dictionary["market_name"],
            market_hash_name=dictionary["market_hash_name"],
            commodity=bool(dictionary["commodity"]),
            market_tradable_restriction=dictionary["market_tradable_restriction"],
            marketable=bool(dictionary["marketable"]),
        )


@dataclass
class Description:
    appid: int
    classid: str
    amount: str
    contextid: str
    currency: int
    id: str
    instanceid: str
    original_amount: str
    status: int
    unowned_id: str
    unowned_contextid: str
    background_color: str
    tradable: bool
    name: str
    name_color: str
    type: str
    market_name: str
    market_hash_name: str
    commodity: bool
    market_tradable_restriction: int
    marketable: bool
    owner: int

    @classmethod
    def from_my_listing_dict(cls, dictionary):
        return cls(
            currency=dictionary["currency"],
            appid=dictionary["appid"],
            contextid=dictionary["contextid"],
            id=dictionary["id"],
            classid=dictionary["classid"],
            instanceid=dictionary["instanceid"],
            amount=dictionary["amount"],
            status=dictionary["status"],
            original_amount=dictionary["original_amount"],
            unowned_id=dictionary["unowned_id"],
            unowned_contextid=dictionary["unowned_contextid"],
            background_color=dictionary["background_color"],
            tradable=bool(dictionary["tradable"]),
            name=dictionary["name"],
            name_color=dictionary["name_color"],
            type=dictionary["type"],
            market_name=dictionary["market_name"],
            market_hash_name=dictionary["market_hash_name"],
            commodity=bool(dictionary["commodity"]),
            market_tradable_restriction=dictionary["market_tradable_restriction"],
            marketable=bool(dictionary["marketable"]),
            owner=dictionary["owner"],
        )


@dataclass
class MyMarketListing:
    """
    The price of this is in full values.
    Not in cents.

    """

    listing_id: str
    buyer_pay: Decimal
    you_receive: Decimal
    created_on: str
    need_confirmation: bool
    description: Description

    @classmethod
    def from_dict(cls, dictionary):
        return cls(
            listing_id=dictionary["listing_id"],
            buyer_pay=convert_string_prices(dictionary["buyer_pay"]),
            you_receive=convert_string_prices(dictionary["you_receive"]),
            created_on=dictionary["created_on"],
            need_confirmation=dictionary["need_confirmation"],
            description=Description.from_my_listing_dict(dictionary["description"]),
        )


@dataclass
class MarketListing:
    listingid: str
    price: Decimal
    fee: Decimal
    currencyid: int
    converted_price: Decimal
    converted_fee: Decimal
    converted_currencyid: int
    asset: Description

    @classmethod
    def from_dict(cls, listing_info: dict, asset_info: dict):
        """Asset info is the full dict of dicts..."""
        object_id = listing_info["asset"]["id"]
        return cls(
            listingid=listing_info["listingid"],
            price=Decimal.from_float(listing_info["price"] / 100).quantize(TWODIGITS),
            fee=Decimal(listing_info["fee"] / 100).quantize(TWODIGITS),
            currencyid=listing_info["currencyid"],
            converted_price=Decimal(listing_info["converted_price"] / 100).quantize(
                TWODIGITS
            ),
            converted_fee=Decimal(listing_info["converted_fee"] / 100).quantize(
                TWODIGITS
            ),
            converted_currencyid=listing_info["converted_currencyid"],
            asset=Description.from_my_listing_dict(asset_info[object_id]),
        )


class ActualExchange(Protocol):
    def login(self):
        pass

    def get_own_items(self, game):
        pass

    def get_own_listings(self):
        pass

    def run(self):
        pass
