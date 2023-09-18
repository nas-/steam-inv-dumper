from decimal import Decimal as D
from unittest import TestCase

from steam_inv_dumper.utils.price_utils import convert_string_prices


class TestConversions(TestCase):
    def test_convert_empty_string(self) -> None:
        price = ""
        decimal_price = convert_string_prices(price)
        self.assertEqual(decimal_price, D("0"))

    def test_convert_string_prices(self) -> None:
        prices = ["2,42€", "2,42pуб.", "2,42USD", "2,42HK$"]
        for price in prices:
            decimal_price = convert_string_prices(price)
            self.assertEqual(decimal_price, D("2.42"))

    def test_convert_string_prices_point_in_between(self) -> None:
        prices = ["4,234.35 €", "4,234.35 pуб.", "4,234.35 USD"]
        prices += ["pуб. 4,234.35 €", "pуб.4,234.35 pуб.", "4,234.35 USD"]
        for price in prices:
            decimal_price = convert_string_prices(price)
            self.assertEqual(decimal_price, D("4234.35"))

    def test_convert_string_prices_no_decimal(self) -> None:
        prices = ["2.--€", "2.-- pуб.", "2.-- USD", "2.-- HK$"]
        prices += ["2.-€", "2.- pуб.", "2.- USD", "2.- HK$"]
        for price in prices:
            decimal_price = convert_string_prices(price)
            self.assertEqual(decimal_price, D("2.00"))

    def test_convert_string_prices_with_space(self) -> None:
        prices = ["2,31 €", "2,31 pуб.", "2,31 USD", "2,31 HK$"]
        for price in prices:
            decimal_price = convert_string_prices(price)
            self.assertEqual(decimal_price, D("2.31"))

    def test_convert_string_prices_inverted(self) -> None:
        prices = ["€ 2,31", "pуб. 2,31", "USD 2,31", "HK$ 2,31"]
        for price in prices:
            decimal_price = convert_string_prices(price)
            self.assertEqual(decimal_price, D("2.31"))
