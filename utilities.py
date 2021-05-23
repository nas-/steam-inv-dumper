import decimal
import logging
import math
import re
from typing import Dict, List, Union

from pandas import DataFrame
from steampy.models import Currency, GameOptions

logger = logging.getLogger(__name__)


def convert_euro_prices(price: str) -> decimal.Decimal:
    price = str(price)
    pattern = r'\D?(\d*)(\.|,)?(\d*)'
    tokens = re.search(pattern, price, re.UNICODE)
    decimal_str = tokens.group(1) + '.' + tokens.group(3)
    return decimal.Decimal(decimal_str)


def get_list_items_to_list(name: str, number: int, price: decimal.Decimal, inventory: DataFrame) -> List[
    Dict[str, Union[Union[str, int]]]]:
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


def get_list_items_to_de_list(name: str, number_to_remove: int, listings: DataFrame) -> List[Dict[str, str]]:
    listings = listings[listings['market_hash_name'] == name].reset_index(drop=True)
    data = []
    for listing_number in range(number_to_remove):
        temp = listings.loc[listing_number:listing_number, :]
        data.append(
            {'name': name, 'listing_id': temp['listing_id'].values[0], 'itemID': temp['id'].values[0],
             'Unowned_itemID': temp['unowned_id'].values[0]})
    return data


def get_steam_fees_object(price: decimal.Decimal) -> Dict[str, int]:
    decimal.getcontext().prec = 28

    def calculate_amount_to_send_for_desired_received_amount(price_inner: float) -> Dict[str, float]:
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
    fees = calculate_amount_to_send_for_desired_received_amount(nEstimatedAmountOfWalletFundsReceivedByOtherParty)
    while (fees['amount'] != price) & (iterations < 15):
        if fees['amount'] > price:
            if bEverUndershot:
                fees = calculate_amount_to_send_for_desired_received_amount(
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
        fees = calculate_amount_to_send_for_desired_received_amount(nEstimatedAmountOfWalletFundsReceivedByOtherParty)
        iterations += 1
    intfees = {'steam_fee': int(fees['steam_fee']), 'publisher_fee': int(fees['publisher_fee']),
               'amount': int(fees['amount']), 'money_to_ask': int(
            calculate_amount_to_send_for_desired_received_amount(fees['amount'] - fees['fees'])['amount'])}
    intfees['you_receive'] = int(intfees['money_to_ask'] - calculate_amount_to_send_for_desired_received_amount(
        fees['amount'] - fees['fees'])['fees'])

    return intfees


def actions_to_make_list_delist(N_MarketListings: int, MinPriceOfMyMarketListings: float, N_NumberToSell: int,
                                N_InInventory: int, ItemSellingPrice: decimal.Decimal, minAllowedPrice: float) -> \
        Dict[str, Union[Dict[str, Union[Union[int, decimal.Decimal]]], Dict[str, Union[int, decimal.Decimal]]]]:
    decimal.getcontext().prec = 2
    N_MarketListings = 0 if math.isnan(N_MarketListings) else N_MarketListings
    # TODO remove that str abomination.....
    MinPriceOfMyMarketListings = decimal.Decimal(str(0 if math.isnan(MinPriceOfMyMarketListings)
                                                     else MinPriceOfMyMarketListings))

    N_NumberToSell = 0 if math.isnan(N_NumberToSell) else N_NumberToSell
    ItemSellingPrice = decimal.Decimal(0 if math.isnan(ItemSellingPrice) else ItemSellingPrice)
    minAllowedPrice = decimal.Decimal.from_float(0 if math.isnan(minAllowedPrice) else minAllowedPrice)

    _selling_price = decimal.Decimal.max(ItemSellingPrice, minAllowedPrice)

    if MinPriceOfMyMarketListings > _selling_price:
        should_list = how_many_can_list(N_MarketListings, N_NumberToSell, N_InInventory)
        if should_list == 0:
            can_list = min(N_InInventory, N_NumberToSell)
            if can_list > should_list:
                return {'delist': {"qty": can_list - should_list, "price": MinPriceOfMyMarketListings},
                        'list': {"qty": can_list, "price": _selling_price}}
            elif can_list == should_list:

                return {'delist': {"qty": N_MarketListings, "price": MinPriceOfMyMarketListings},
                        'list': {"qty": 0, "price": _selling_price}}

            else:

                raise RuntimeError("You should have never reached this point", N_MarketListings,
                                   MinPriceOfMyMarketListings, N_NumberToSell, N_InInventory, ItemSellingPrice,
                                   minAllowedPrice)

        elif should_list > 0:
            return {'delist': {"qty": 0, "price": MinPriceOfMyMarketListings},
                    'list': {"qty": should_list, "price": _selling_price}}
    elif MinPriceOfMyMarketListings == _selling_price:
        should_list = how_many_can_list(N_MarketListings, N_NumberToSell, N_InInventory)
        return {'delist': {"qty": 0, "price": MinPriceOfMyMarketListings},
                'list': {"qty": should_list, "price": _selling_price}}
    elif MinPriceOfMyMarketListings < _selling_price:
        should_list = how_many_can_list(N_MarketListings, N_NumberToSell, N_InInventory)
        return {'delist': {"qty": N_MarketListings, "price": MinPriceOfMyMarketListings},
                'list': {"qty": should_list, "price": _selling_price}}


def how_many_can_list(N_MarketListings, N_NumberToSell, N_InInventory):
    if N_NumberToSell > N_MarketListings:
        toList = N_NumberToSell - N_MarketListings
        return min(toList, N_InInventory)
    elif N_NumberToSell == N_MarketListings or N_NumberToSell < N_MarketListings:
        return 0


def get_item_price(steam_market, market_hash_name: str) -> decimal.Decimal:
    _priceData = steam_market.fetch_price(market_hash_name, game=GameOptions.CS, currency=Currency.EURO)
    try:
        _priceData['lowest_price'] = convert_euro_prices(_priceData['lowest_price'])
        _priceData['median_price'] = convert_euro_prices(_priceData['median_price'])
    except KeyError:
        _priceData['lowest_price'] = convert_euro_prices(_priceData['lowest_price'])
        _priceData['median_price'] = 0
        # TODO Care about this. Don't like to set median price =0
    return max(_priceData['lowest_price'], _priceData['median_price']) - decimal.Decimal('0.01')
