from typing import Protocol, Type, TypeVar

from steampy.models import Currency, GameOptions

T = TypeVar("T", bound="InventoryProvider")
W = TypeVar("W", bound="MarketProvider")


class InventoryProvider(Protocol):
    @classmethod
    def initialize(cls: Type[T], config: dict) -> T:
        pass

    def get_my_inventory(self, game: GameOptions) -> dict:
        pass

    @property
    def market_params(self) -> dict:
        pass


class MarketProvider(Protocol):
    @classmethod
    def initialize(cls: Type[W], config: dict) -> W:
        pass

    def cancel_sell_order(self, sell_listing_id: str) -> None:
        pass

    def create_sell_order(self, assetid: str, game: GameOptions, money_to_receive: str) -> dict:
        pass

    @property
    def currency(self) -> Currency:
        pass

    def get_item_price(self, market_hash_name: str) -> dict:
        pass

    def get_my_market_listings(self) -> dict:
        pass
