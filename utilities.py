import decimal
import logging
import math
import re
from typing import Dict, List

from pandas import DataFrame
from steampy.models import Currency, GameOptions

logger = logging.getLogger(__name__)
decimal.getcontext().prec = 3


def convert_string_prices(price: str) -> decimal.Decimal:
    """
    Converts string to decimal price
    :param price: price as string
    :return: price as decimal.Decimal
    """
    if not price:
        return decimal.Decimal(0)
    price = str(price)
    pattern = r'\D*(\d*)(\.|,)?(\d*)'

    while True:
        tokens = re.search(pattern, price, re.UNICODE)
        if len(tokens.group(3)) > 2:
            price = price.replace(tokens.group(2), '')
        else:
            decimal_str = tokens.group(1) + '.' + tokens.group(3)
            return decimal.Decimal(decimal_str)


def get_items_to_list(name: str, number: int, price: decimal.Decimal, inventory: DataFrame) -> List[Dict]:
    """
    Gets a list of length "number" of items in inventory to be put on sale
    :param name: Name of item
    :param number: Number of items to list.
    :param price: price of items to list as Decimal.Decimal
    :param inventory: Dataframe containing the inventory
    :return:List of Dicts regarding items to sell.
    """
    # TODO check what exactly is price.
    inventory = inventory[(inventory['market_hash_name'] == name) & (inventory['marketable'] == 1)]
    _assetsID = list(inventory['id'])
    prices = get_steam_fees_object(price)
    return [
        {
            'name': name,
            'assetsID': _assetsID[order_number],
            'you_receive': prices["you_receive"],
            'buyer_pays': prices["money_to_ask"],
        }
        for order_number in range(number)
    ]


def get_items_to_delist(name: str, number_to_remove: int, listings: DataFrame) -> List[Dict[str, str]]:
    """
    Gets a list of length "number" of items on sale to be removed from sale.
    :param name: Name of item
    :param number_to_remove: Number of items to remove.
    :param listings: Dataframe containing the listings.
    :return:List of Dicts regarding items to remove
    """
    listings = listings[listings['market_hash_name'] == name].reset_index(drop=True)
    data = []
    for listing_number in range(number_to_remove):
        temp = listings.loc[listing_number:listing_number, :]
        data.append(
            {'name': name, 'listing_id': temp['listing_id'].values[0], 'itemID': temp['id'].values[0],
             'Unowned_itemID': temp['unowned_id'].values[0]})
    return data


def get_steam_fees_object(price: decimal.Decimal) -> Dict[str, int]:
    """
    Given a price, returns the full set of steam prices (you_receive/money_to_ask/total fees ecc)
    :param price: Price for sale (money_to_ask)
    :return: Dict of different prices (In cents).
    keys='steam_fee', 'publisher_fee', 'amount', 'money_to_ask', 'you_receive'
    """
    decimal.getcontext().prec = 28

    def amount_to_send_desired_received_amt(price_inner: float) -> Dict[str, float]:
        """
        calculate_amount_to_send_for_desired_received_amount
        :param price_inner:
        :return:
        """
        _steamFee = int(math.floor(max(price_inner * 0.05, 1)))
        _pubFee = int(math.floor(max(price_inner * 0.10, 1)))

        return {'steam_fee': _steamFee,
                'publisher_fee': _pubFee,
                'fees': _pubFee + _steamFee,
                'amount': price_inner + _steamFee + _pubFee}

    iterations = 0
    bEverUndershot = False
    price = int(price * 100)
    nEstimatedAmountOfWalletFundsReceivedByOtherParty = round(price / (0.05 + 0.10 + 1), 0)
    fees = amount_to_send_desired_received_amt(nEstimatedAmountOfWalletFundsReceivedByOtherParty)
    while (fees['amount'] != price) & (iterations < 15):
        if fees['amount'] > price:
            if bEverUndershot:
                fees = amount_to_send_desired_received_amt(
                    nEstimatedAmountOfWalletFundsReceivedByOtherParty - 1)
                fees['steam_fee'] += int((price - fees['amount']))
                fees['fees'] += int((price - fees['amount']))
                fees['amount'] = price
                break
            else:
                nEstimatedAmountOfWalletFundsReceivedByOtherParty -= 1
        else:
            bEverUndershot = True
            nEstimatedAmountOfWalletFundsReceivedByOtherParty += 1
        fees = amount_to_send_desired_received_amt(nEstimatedAmountOfWalletFundsReceivedByOtherParty)
        iterations += 1

    intfees = {'steam_fee': int(fees['steam_fee']),
               'publisher_fee': int(fees['publisher_fee']),
               'money_to_ask': int(amount_to_send_desired_received_amt(fees['amount'] - fees['fees'])['amount'])
               }
    intfees['you_receive'] = int(
        intfees['money_to_ask'] - amount_to_send_desired_received_amt(fees['amount'] - fees['fees'])['fees'])

    decimal.getcontext().prec = 3
    return intfees


# TODO refactor with PEP8. Fix type hints.
def actions_to_make_list_delist(N_MarketListings: int, MinPriceOfMyMarketListings: float, N_NumberToSell: int,
                                N_InInventory: int, ItemSellingPrice: decimal.Decimal, minAllowedPrice: float) -> Dict:
    actions = {'delist': determine_delists(N_MarketListings, MinPriceOfMyMarketListings, N_NumberToSell, N_InInventory,
                                           ItemSellingPrice, minAllowedPrice)}
    N_MarketListings -= actions['delist']['qty']
    assert N_MarketListings >= 0

    actions['list'] = determine_lists(N_MarketListings, MinPriceOfMyMarketListings, N_NumberToSell, N_InInventory,
                                      ItemSellingPrice, minAllowedPrice)
    assert N_MarketListings + actions['list']['qty'] <= N_NumberToSell
    return actions


def determine_delists(market_listings, min_price_market_listing, max_on_sale, tot_in_inventory, usual_price,
                      min_allowed_price):
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
    min_price_market_listing = decimal.Decimal(min_price_market_listing) + 0
    usual_price = decimal.Decimal(usual_price) + 0
    min_allowed_price = decimal.Decimal(min_allowed_price) + 0

    canListMoreItems = tot_in_inventory > 0 and market_listings < max_on_sale
    imLowesPrice = usual_price >= min_price_market_listing >= min_allowed_price

    price = min_price_market_listing
    if market_listings == 0:
        amount = 0
    elif max_on_sale == 0:
        amount = market_listings
    elif price == min_allowed_price:
        # Returns more than 0 if I have more than allowed listings.
        amount = max(0, market_listings - max_on_sale)
    elif canListMoreItems:
        # I can list more from inv. No need for delists.
        if min_price_market_listing < min_allowed_price:
            # My listings are lower than min allowed price
            amount = market_listings
        else:
            amount = 0
    else:
        # Need to remove some.
        if imLowesPrice:
            amount = market_listings - max_on_sale
        else:
            amount = market_listings

    # Guard cause. Delisining <0
    if amount < 0:
        amount = 0

    return {'qty': amount, 'price': price}


# TODO remove unused parameter.
def determine_lists(market_listings, min_price_market_listing, max_on_sale, tot_in_inventory, usual_price,
                    min_allowed_price):
    # Convertions
    usual_price = decimal.Decimal(usual_price) + 0
    min_allowed_price = decimal.Decimal(min_allowed_price) + 0

    canListMoreItems = tot_in_inventory > 0 and market_listings < max_on_sale

    amount = 0
    if canListMoreItems:
        amount = min(tot_in_inventory, max_on_sale - market_listings)

    price = max(usual_price, min_allowed_price)
    assert amount >= 0
    assert price >= min_allowed_price
    return {'qty': amount, 'price': price}


# TODO refactor with PEP8.
def how_many_can_list(N_MarketListings, N_NumberToSell, N_InInventory):
    """
    How many items I can actually list on market to have N_NumberToSell on sale
    :param N_MarketListings:
    :param N_NumberToSell:
    :param N_InInventory:
    :return: number that can be listed
    """
    if N_NumberToSell > N_MarketListings:
        toList = N_NumberToSell - N_MarketListings
        return min(toList, N_InInventory)
    elif N_NumberToSell == N_MarketListings or N_NumberToSell < N_MarketListings:
        return 0


def get_item_price(steam_market, market_hash_name: str) -> decimal.Decimal:
    """
    Gets the item price from Steam
    :param steam_market: Instance of Steam Market.
    :param market_hash_name: Market hash name.
    :return: Decimal.
    """
    price_data = steam_market.fetch_price(market_hash_name, game=GameOptions.CS, currency=steam_market.currency)
    try:
        price_data['lowest_price'] = convert_string_prices(price_data['lowest_price'])
        price_data['median_price'] = convert_string_prices(price_data['median_price'])
    except KeyError:
        price_data['lowest_price'] = convert_string_prices(price_data['lowest_price'])
        price_data['median_price'] = 0
        # TODO Care about this. Don't like to set median price =0
    return max(price_data['lowest_price'], price_data['median_price']) - decimal.Decimal('0.01')


class PriceOverview:
    """Represents the data received from https://steamcommunity.com/market/priceoverview.
    Attributes
    -------------
    currency: :class:`str`
        The currency identifier for the item eg. "$" or "£".
    volume: :class:`int`
        The volume of last 24 hours.
    lowest_price: :class:`decimal.Decimal`
        The lowest price currently present on the market.
    median_price: :class:`decimal.Decimal`
        The median price observed by the market.
    """
    __slots__ = ("currency", "volume", "lowest_price", "median_price")

    def __init__(self, data, currency):
        lowest_price = data.get('lowest_price', '')
        median_prince = data.get('median_price', '')
        self.lowest_price = convert_string_prices(lowest_price)
        self.median_price = convert_string_prices(median_prince)
        self.volume = data.get('volume', 0)
        self.currency = currency

    def __repr__(self) -> str:
        resolved = [f"{attr}={getattr(self, attr)!r}" for attr in self.__slots__]
        return f"<PriceOverview {' '.join(resolved)}>"


if __name__ == '__main__':
    a = {"success": True}
    c = PriceOverview(a, Currency.RUB)
    print(c)
