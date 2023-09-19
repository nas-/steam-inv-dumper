import decimal
import logging
from typing import Dict, List

from steam_inv_dumper.utils.data_structures import (
    DelistFromMarket,
    InventoryItem,
    ListOnMarket,
    MarketActionType,
    MyMarketListing,
)
from steam_inv_dumper.utils.price_utils import TWODIGITS, get_steam_fees_object

logger = logging.getLogger(__name__)


# TODO refactor determine_lists
# TODO Make Dataclasses for list, delists.
# TODO remove asserts


def get_items_to_list(
    market_hash_name: str,
    amount: int,
    price: decimal.Decimal,
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

    inventory = [
        item
        for item in inventory
        if item.marketable is True and item.market_hash_name == market_hash_name
    ]
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


def get_items_to_delist(
    market_hash_name: str, amount: int, listings: List[MyMarketListing]
) -> List[DelistFromMarket]:
    """
    Gets a list of length "number" of items on sale to be removed from sale.
    :param market_hash_name: market hash market_hash_name of item
    :param amount: Number of items to remove.
    :param listings: Dataframe containing the listings.
    :return:List of Dicts regarding items to remove
    """
    listings = [
        listing
        for listing in listings
        if listing.description.market_hash_name == market_hash_name
    ]

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
    min_price_mark_listing: float,
    num_to_sell: int,
    num_in_inventory: int,
    item_selling_price: decimal.Decimal,
    min_allowed_price: float,
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
    min_allowed_price_dec = decimal.Decimal(min_allowed_price).quantize(TWODIGITS)
    fees = get_steam_fees_object(min_allowed_price_dec)
    if fees.get("money_to_ask") / 100 < min_allowed_price:
        min_allowed_price = fees.get("money_to_ask") / 100

    item_selling_price = item_selling_price.quantize(TWODIGITS)
    actions = {
        "delist": determine_delists(
            num_market_listings,
            min_price_mark_listing,
            num_to_sell,
            num_in_inventory,
            item_selling_price,
            min_allowed_price,
        )
    }
    num_market_listings -= actions["delist"]["qty"]
    assert num_market_listings >= 0

    actions["list"] = determine_lists(
        num_market_listings,
        num_to_sell,
        num_in_inventory,
        item_selling_price,
        min_allowed_price,
    )
    assert num_market_listings + actions["list"]["qty"] <= num_to_sell
    return actions


def determine_delists(
    market_listings: int,
    min_price_market_listing: float,
    max_on_sale: int,
    tot_in_inventory: int,
    usual_price: decimal.Decimal,
    min_allowed_price: float,
) -> Dict:
    """
    Return delist actions
    :param market_listings:
    :param min_price_market_listing:
    :param max_on_sale:
    :param tot_in_inventory:
    :param usual_price:
    :param min_allowed_price:
    """

    # Convertions
    min_price_market_listing_decimal = decimal.Decimal(
        min_price_market_listing
    ).quantize(TWODIGITS)
    usual_price = decimal.Decimal(usual_price).quantize(TWODIGITS)
    min_allowed_price_decimal = decimal.Decimal(min_allowed_price).quantize(TWODIGITS)

    canListMoreItems = tot_in_inventory > 0 and market_listings < max_on_sale
    imLowesPrice = (
        usual_price >= min_price_market_listing_decimal >= min_allowed_price_decimal
    )

    price = min_price_market_listing_decimal
    if market_listings == 0:
        amount = 0
    elif max_on_sale == 0:
        amount = market_listings
    elif price == min_allowed_price_decimal:
        # Returns more than 0 if I have more than allowed listings.
        amount = max(0, market_listings - max_on_sale)
    elif canListMoreItems:
        # I can list more from inv. No need for delists.
        if min_price_market_listing_decimal < min_allowed_price_decimal:
            # My listings are lower than min allowed int_price
            amount = market_listings
        else:
            amount = 0
    else:
        # Need to remove some.
        if imLowesPrice:
            amount = market_listings - max_on_sale
        else:
            amount = market_listings

    # Guard cause. Delistining <0
    if amount < 0:
        amount = 0

    return {"qty": amount, "int_price": price}


def determine_lists(
    market_listings: int,
    max_on_sale: int,
    tot_in_inventory: int,
    usual_price: decimal.Decimal,
    min_allowed_price: float,
) -> dict:
    # Convertions
    usual_price = decimal.Decimal(usual_price).quantize(TWODIGITS)
    min_allowed_price_decimal = decimal.Decimal(min_allowed_price).quantize(TWODIGITS)

    canListMoreItems = tot_in_inventory > 0 and market_listings < max_on_sale

    amount = 0
    if canListMoreItems:
        amount = max_on_sale - market_listings

    price = max(usual_price, min_allowed_price_decimal)

    if amount > tot_in_inventory:
        amount = tot_in_inventory

    assert amount >= 0
    assert price >= min_allowed_price_decimal
    return {"qty": amount, "int_price": price}


def how_many_can_list(
    num_market_listings: int, number_to_sell: int, num_in_inventory: int
) -> int:
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
