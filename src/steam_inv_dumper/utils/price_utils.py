import math
import re
from typing import Dict


def convert_string_prices(price: str) -> int:
    """
    Converts string to decimal int_price
    :param price: int_price as string
    :return: int_price as decimal.Decimal
    """
    if not price:
        return 0
    price = str(price)
    pattern = r"\D*(\d*)(\.|,)?(\d*)"

    while True:
        tokens = re.search(pattern, price, re.UNICODE)
        if len(tokens.group(3)) > 2:
            price = price.replace(tokens.group(2), "")
        else:
            hundreds = int(tokens.group(1)) * 100
            cents_as_string = tokens.group(3)
            if not cents_as_string:
                cents = 0
            else:
                cents = int(cents_as_string)
            return hundreds + cents


def amount_to_send_desired_received_amt(price_inner: float) -> Dict[str, float]:
    """
    calculate_amount_to_send_for_desired_received_amount
    :param price_inner:
    :return:
    """
    _steamFee = int(math.floor(max(price_inner * 0.05, 1)))
    _pubFee = int(math.floor(max(price_inner * 0.10, 1)))

    return {
        "steam_fee": _steamFee,
        "publisher_fee": _pubFee,
        "fees": _pubFee + _steamFee,
        "amount": price_inner + _steamFee + _pubFee,
    }


def get_steam_fees_object(price: int) -> Dict[str, int]:
    """
    Given an int_price as Decimal, returns the full set of steam prices (you_receive/money_to_ask/total fees ecc)
    :param price: Price for sale (money_to_ask)
    :return: Dict of different prices - in cents.
    keys='steam_fee', 'publisher_fee', 'amount', 'money_to_ask', 'you_receive'
    """

    iterations = 0
    bEverUndershot = False
    int_price = int(price)

    nEstimatedAmountOfWalletFundsReceivedByOtherParty = round(int_price / (0.05 + 0.10 + 1), 0)
    fees = amount_to_send_desired_received_amt(nEstimatedAmountOfWalletFundsReceivedByOtherParty)
    while (fees["amount"] != int_price) & (iterations < 15):
        if fees["amount"] > int_price:
            if bEverUndershot:
                fees = amount_to_send_desired_received_amt(nEstimatedAmountOfWalletFundsReceivedByOtherParty - 1)
                fees["steam_fee"] += int((int_price - fees["amount"]))
                fees["fees"] += int((int_price - fees["amount"]))
                fees["amount"] = int_price
                break
            else:
                nEstimatedAmountOfWalletFundsReceivedByOtherParty -= 1
        else:
            bEverUndershot = True
            nEstimatedAmountOfWalletFundsReceivedByOtherParty += 1
        fees = amount_to_send_desired_received_amt(nEstimatedAmountOfWalletFundsReceivedByOtherParty)
        iterations += 1

    intfees = {
        "steam_fee": int(fees["steam_fee"]),
        "publisher_fee": int(fees["publisher_fee"]),
        "money_to_ask": int(amount_to_send_desired_received_amt(fees["amount"] - fees["fees"])["amount"]),
    }
    intfees["you_receive"] = int(
        intfees["money_to_ask"] - amount_to_send_desired_received_amt(fees["amount"] - fees["fees"])["fees"]
    )

    return intfees
