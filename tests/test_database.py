from datetime import datetime
from unittest import TestCase

from steam_inv_dumper.db.db import Database
from steam_inv_dumper.utils.configuration import load_config


class TestSteamDatabase(TestCase):
    def tearDown(self) -> None:
        self.db.Listing.query.delete()
        self.db.Listing.query.session.flush()
        self.db.Item.query.delete()
        self.db.Item.query.session.flush()

    def setUp(self) -> None:
        config = load_config("test_config.json").unwrap()
        self.db = Database(config=config)
        for_db = self.db.Listing(
            item_id="12345",
            created_on=datetime.now(),
            you_receive=1430,
            buyer_pay=1499,
        )
        item_for_db = self.db.Item(item_id="12345", market_hash_name="casekey1")
        self.db.Listing.query.session.add(for_db)
        self.db.Item.query.session.add(item_for_db)
        self.db.Listing.query.session.flush()
        self.db.Item.query.session.flush()
        pass

    def test_is_sold(self):
        K = self.db.Item.query_ref(item_id="12345").first()
        self.assertEqual(K.sold, False)
        K.sold = True
        self.db.Item.query.session.flush()
        K = self.db.Item.query_ref(item_id="12345").first()
        self.assertEqual(K.sold, True)
        K.listings[0].sold = False
        self.db.Item.query.session.flush()

    def test_listing_to_json(self):
        K = self.db.Listing.query_ref(item_id="12345").first()
        item_json = K.to_json()
        self.assertDictEqual(
            item_json,
            {
                "listing_id": K.listing_id,
                "id": K.id,
                "currency": K.currency,
                "item_id": K.item_id,
                "created_on": K.created_on,
                "listing_status": K.listing_status,
                "buyer_pay": K.buyer_pay,
                "you_receive": K.you_receive,
            },
        )

    def test_item_to_json(self):
        K = self.db.Item.query_ref(item_id="12345").first()
        item_json = K.to_json()
        self.assertDictEqual(
            item_json,
            {
                "stale_item_id": K.stale_item_id,
                "sold": K.sold,
                "id": K.id,
                "contextid": K.contextid,
                "item_id": K.item_id,
                "market_hash_name": K.market_hash_name,
                "account": K.account,
                "appid": K.appid,
                "tradable": K.tradable,
                "marketable": K.marketable,
                "commodity": K.commodity,
            },
        )

    def test_select_all_ids(self) -> None:
        K = self.db.Item.query_ref(item_id="12345").first()
        self.assertEqual(K.item_id, "12345")
        K = self.db.Item.query_ref(market_hash_name="casekey1").first()
        self.assertEqual(K.market_hash_name, "casekey1")

        K = self.db.Item.query_ref(market_hash_name="casekey1").first()
        self.assertEqual(K.listings[0].you_receive, 1430)
        self.assertEqual(K.listings[0].buyer_pay, 1499)
        K.sold = True
        self.db.Item.query.session.flush()
        self.assertEqual(K.sold, True)
        K = self.db.Item.query_ref(market_hash_name="casekey1").first()
        self.db.Item.query.session.delete(K)
        self.db.Item.query.session.flush()
        self.assertEqual(self.db.Item.query_ref(market_hash_name="casekey1").all(), [])

    def test_correct_decimal_precison(self) -> None:
        K = self.db.Listing.query_ref(item_id="12345").first()

        self.assertEqual(K.you_receive, 1430)
        self.assertEqual(K.buyer_pay, 1499)
