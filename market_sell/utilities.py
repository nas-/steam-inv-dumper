import decimal
import logging
import math
import re
from typing import Dict, List

from pandas import DataFrame
from steampy.models import Currency, GameOptions

logger = logging.getLogger(__name__)
# decimal.getcontext().prec = 3
TWODIGITS = decimal.Decimal('0.01')


def convert_string_prices(price: str) -> decimal.Decimal:
    """
    Converts string to decimal int_price
    :param price: int_price as string
    :return: int_price as decimal.Decimal
    """
    if not price:
        return decimal.Decimal(0).quantize(TWODIGITS)
    price = str(price)
    pattern = r'\D*(\d*)(\.|,)?(\d*)'

    while True:
        tokens = re.search(pattern, price, re.UNICODE)
        if len(tokens.group(3)) > 2:
            price = price.replace(tokens.group(2), '')
        else:
            decimal_str = tokens.group(1) + '.' + tokens.group(3)
            return decimal.Decimal(decimal_str).quantize(TWODIGITS)


def get_items_to_list(name: str, number: int, price: decimal.Decimal, inventory: DataFrame) -> List[Dict]:
    """
    Gets a list of length "number" of items in inventory to be put on sale
    :param name: market hash name of item
    :param number: Number of items to list.
    :param price: money_to_ask of items to list as Decimal.Decimal
    :param inventory: Dataframe containing the inventory
    :return:List of Dicts regarding items to sell. Prices are in cents.
    """
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
    :param name: market hash name of item
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
    Given a int_price as Decimal, returns the full set of steam prices (you_receive/money_to_ask/total fees ecc)
    :param price: Price for sale (money_to_ask)
    :return: Dict of different prices - in cents.
    keys='steam_fee', 'publisher_fee', 'amount', 'money_to_ask', 'you_receive'
    """

    #decimal.getcontext().prec = 28

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
    int_price = int(price * 100)
    nEstimatedAmountOfWalletFundsReceivedByOtherParty = round(int_price / (0.05 + 0.10 + 1), 0)
    fees = amount_to_send_desired_received_amt(nEstimatedAmountOfWalletFundsReceivedByOtherParty)
    while (fees['amount'] != int_price) & (iterations < 15):
        if fees['amount'] > int_price:
            if bEverUndershot:
                fees = amount_to_send_desired_received_amt(
                    nEstimatedAmountOfWalletFundsReceivedByOtherParty - 1)
                fees['steam_fee'] += int((int_price - fees['amount']))
                fees['fees'] += int((int_price - fees['amount']))
                fees['amount'] = int_price
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

    #decimal.getcontext().prec = 3
    return intfees


# TODO refactor with PEP8. Fix type hints.
def actions_to_make_list_delist(num_market_listings: int, min_price_mark_listing: float, num_to_sell: int,
                                num_in_inventory: int, item_selling_price: decimal.Decimal,
                                min_allowed_price: float) -> Dict:
    item_selling_price = item_selling_price.quantize(TWODIGITS)
    actions = {'delist': determine_delists(num_market_listings, min_price_mark_listing, num_to_sell, num_in_inventory,
                                           item_selling_price, min_allowed_price)}
    num_market_listings -= actions['delist']['qty']
    assert num_market_listings >= 0

    actions['list'] = determine_lists(num_market_listings, num_to_sell, num_in_inventory, item_selling_price,
                                      min_allowed_price)
    assert num_market_listings + actions['list']['qty'] <= num_to_sell
    return actions


def determine_delists(market_listings: int, min_price_market_listing: float, max_on_sale: int,
                      tot_in_inventory: int, usual_price: decimal.Decimal,
                      min_allowed_price: float) -> Dict:
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
    min_price_market_listing_decimal = decimal.Decimal(min_price_market_listing).quantize(TWODIGITS)
    usual_price = decimal.Decimal(usual_price).quantize(TWODIGITS)
    min_allowed_price_decimal = decimal.Decimal(min_allowed_price).quantize(TWODIGITS)

    canListMoreItems = tot_in_inventory > 0 and market_listings < max_on_sale
    imLowesPrice = usual_price >= min_price_market_listing_decimal >= min_allowed_price_decimal

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

    # Guard cause. Delisining <0
    if amount < 0:
        amount = 0

    return {'qty': amount, 'int_price': price}


def determine_lists(market_listings: int, max_on_sale: int, tot_in_inventory: int, usual_price: decimal.Decimal,
                    min_allowed_price: float) -> dict:
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
    return {'qty': amount, 'int_price': price}


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


def get_item_price(steam_market, market_hash_name: str) -> decimal.Decimal:
    """
    Gets the item int_price from Steam
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
    return max(price_data['lowest_price'], price_data['median_price']) - decimal.Decimal('0.01')


# Remove?
class PriceOverview:
    """Represents the data received from https://steamcommunity.com/market/priceoverview.
    Attributes
    -------------
    currency: :class:`str`
        The currency identifier for the item eg. "$" or "£".
    volume: :class:`int`
        The volume of last 24 hours.
    lowest_price: :class:`decimal.Decimal`
        The lowest int_price currently present on the market.
    median_price: :class:`decimal.Decimal`
        The median int_price observed by the market.
    """
    __slots__ = ("currency", "volume", "lowest_price", "median_price")

    def __init__(self, data: dict, currency: Currency):
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
