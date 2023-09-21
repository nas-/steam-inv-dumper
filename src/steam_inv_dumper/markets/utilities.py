import logging
from typing import Dict, List

from steam_inv_dumper.utils.data_structures import (
    DelistFromMarket,
    InventoryItem,
    ListOnMarket,
    MarketActionType,
    MyMarketListing,
)
from steam_inv_dumper.utils.price_utils import get_steam_fees_object

logger = logging.getLogger(__name__)


# TODO refactor determine_lists
# TODO Make Dataclasses for list, delists.
# TODO remove asserts


def get_items_to_list(
    market_hash_name: str,
    amount: int,
    price: int,
    inventory: List[InventoryItem],
) -> List[ListOnMarket]:
    """
    Gets a list of length "number" of items in inventory to be put on sale
    :param market_hash_name: market hash market_hash_name of item
    :param amount: Number of items to list.
    :param price: money_to_ask of items to list as Decimal.Decimal
    :param inventory: Dataframe containing the inventory
    :return:List of Dicts regarding items to sell. Prices are in cents.
    """

    inventory = [item for item in inventory if item.marketable is True and item.market_hash_name == market_hash_name]
    inventory = sorted(inventory, key=lambda x: x.id)
    prices = get_steam_fees_object(price=price)

    items_to_list = []
    for item in inventory[:amount]:
        items_to_list.append(
            ListOnMarket.from_dict(
                {
                    "action_type": MarketActionType.PlaceOnMarket,
                    "market_hash_name": item.market_hash_name,
                    "assetsID": item.id,
                    "you_receive": prices["you_receive"],
                    "buyer_pays": prices["money_to_ask"],
                }
            )
        )

    return items_to_list


def get_items_to_delist(market_hash_name: str, amount: int, listings: List[MyMarketListing]) -> List[DelistFromMarket]:
    """
    Gets a list of length "number" of items on sale to be removed from sale.
    :param market_hash_name: market hash market_hash_name of item
    :param amount: Number of items to remove.
    :param listings: Dataframe containing the listings.
    :return:List of Dicts regarding items to remove
    """
    listings = [listing for listing in listings if listing.description.market_hash_name == market_hash_name]

    listings_to_be_removed = []
    for temp in listings[:amount]:
        listings_to_be_removed.append(
            DelistFromMarket.from_dict(
                {
                    "action_type": MarketActionType.RemoveFromMarket,
                    "market_hash_name": temp.description.market_hash_name,
                    "listing_id": temp.listing_id,
                    "itemID": temp.description.id,
                    "Unowned_itemID": temp.description.unowned_id,
                }
            )
        )
    return listings_to_be_removed


def actions_to_make_list_delist(
    num_market_listings: int,
    min_price_mark_listing: int,
    num_to_sell: int,
    num_in_inventory: int,
    item_selling_price: int,
    min_allowed_price: int,
) -> Dict:
    """

    :param num_market_listings: Number of market listings.
    :param min_price_mark_listing:  min price of market lisings.
    :param num_to_sell:  Number to have on sale
    :param num_in_inventory: Number in inventory
    :param item_selling_price: Item usual selling price.
    :param min_allowed_price:  Minimum allowed price
    :return: Actions to make.
    """
    # Ensure min_allowed_price is not an "ambiguous" price
    fees = get_steam_fees_object(min_allowed_price)
    if fees["money_to_ask"] < min_allowed_price:
        min_allowed_price = fees["money_to_ask"]

    item_selling_price = item_selling_price

    amount_to_delist = determine_delists(
        num_market_listings,
        min_price_mark_listing,
        num_to_sell,
        num_in_inventory,
        item_selling_price,
        min_allowed_price,
    )
    actions = {"delist": {"qty": amount_to_delist}}
    num_market_listings -= amount_to_delist

    actions["list"] = determine_lists(
        num_market_listings,
        num_to_sell,
        num_in_inventory,
        item_selling_price,
        min_allowed_price,
    )
    return actions


def determine_delists(
    market_listings: int,
    min_price_market_listing: int,
    max_on_sale: int,
    tot_in_inventory: int,
    usual_price: int,
    min_allowed_price: int,
) -> int:
    """
    Return delist actions
    :param market_listings:
    :param min_price_market_listing:
    :param max_on_sale:
    :param tot_in_inventory:
    :param usual_price:
    :param min_allowed_price:
    """

    if any(x <= 0 for x in [usual_price, min_allowed_price]):
        raise ValueError("Prices must be greater than 0")
    if any(x < 0 for x in [tot_in_inventory, market_listings, max_on_sale]):
        raise ValueError("Amounts must be greater than 0")

    canListMoreItems = tot_in_inventory > 0 and market_listings < max_on_sale
    imLowesPrice = usual_price >= min_price_market_listing >= min_allowed_price

    if market_listings == 0:
        return 0
    if max_on_sale == 0:
        return market_listings

    if min_price_market_listing == min_allowed_price:
        # Returns more than 0 if I have more than allowed listings.
        amount = max(0, market_listings - max_on_sale)
        return amount
    if canListMoreItems:
        # I can list more from inv. No need for delists.
        if min_price_market_listing < min_allowed_price:
            # My listings are lower than min allowed int_price
            return market_listings
        return 0
    # Need to remove some.
    if imLowesPrice:
        amount = market_listings - max_on_sale
        return amount
    amount = market_listings
    return amount


def determine_lists(
    market_listings: int,
    max_on_sale: int,
    tot_in_inventory: int,
    usual_price: int,
    min_allowed_price: int,
) -> dict:
    # Convertions

    if any(x <= 0 for x in [usual_price, min_allowed_price]):
        raise ValueError("Prices must be greater than 0")
    if any(x < 0 for x in [tot_in_inventory, market_listings, max_on_sale]):
        raise ValueError("Amounts must be greater than 0")

    canListMoreItems = tot_in_inventory > 0 and market_listings < max_on_sale

    amount = 0
    if canListMoreItems:
        amount = max_on_sale - market_listings

    price = max(usual_price, min_allowed_price)

    if amount > tot_in_inventory:
        amount = tot_in_inventory

    return {"qty": amount, "int_price": price}


def how_many_can_list(num_market_listings: int, number_to_sell: int, num_in_inventory: int) -> int:
    """
    How many items I can actually list on market to have number_to_sell on sale
    :param num_market_listings: Number of own listing on market.
    :param number_to_sell: Max number on sale
    :param num_in_inventory: Number in inventory
    :return: number that can be listed
    """
    if number_to_sell > num_market_listings:
        toList = number_to_sell - num_market_listings
        return min(toList, num_in_inventory)
    elif number_to_sell == num_market_listings or number_to_sell < num_market_listings:
        return 0
    return 0
