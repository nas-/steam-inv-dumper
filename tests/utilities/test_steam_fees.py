from decimal import Decimal as D
from unittest import TestCase

from steam_inv_dumper.utils.price_utils import get_steam_fees_object


class TestSteamFeeObjects(TestCase):
    def test_get_steam_fees_object(self) -> None:
        price = D("0.03")
        fees = get_steam_fees_object(price)
        self.assertEqual(fees["you_receive"], 1)
        self.assertEqual(fees["money_to_ask"], 3)
        self.assertEqual(type(fees["you_receive"]), int)
        self.assertEqual(type(fees["money_to_ask"]), int)

    def test_get_steam_fees_object_round_down_value(self) -> None:
        price = D("0.22")
        fees = get_steam_fees_object(price)
        self.assertEqual(fees["you_receive"], 19)
        self.assertEqual(fees["money_to_ask"], 21)
        self.assertEqual(type(fees["you_receive"]), int)
        self.assertEqual(type(fees["money_to_ask"]), int)

    def test_get_steam_fees_object_high_value(self) -> None:
        price = D("588.31")
        fees = get_steam_fees_object(price)
        self.assertEqual(fees["you_receive"], 51159)
        self.assertEqual(fees["money_to_ask"], 58831)
        self.assertEqual(type(fees["you_receive"]), int)
        self.assertEqual(type(fees["money_to_ask"]), int)
