from unittest import TestCase

from data import listings

from steam_inv_dumper.markets.steam.market import SteamMarketLimited


class TestSteamLimited(TestCase):
    def test_parse_listings_for_item(self):
        links = SteamMarketLimited.parse_listings_for_item(listings)
        self.assertTrue(isinstance(links, list))
        self.assertTrue(len(links) == 10)
        for link in links:
            self.assertTrue(isinstance(link, dict))
            self.assertTrue(isinstance(link["link"], str))
            self.assertTrue(link["link"].startswith("steam://rungame"))
            self.assertTrue(isinstance(link["price"], int))
            self.assertTrue(isinstance(link["listingid"], str))
