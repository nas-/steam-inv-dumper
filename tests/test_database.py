from datetime import datetime
from unittest import TestCase

from utilities.constants import DESCRIPTION

from steam_inv_dumper.db.db import Database
from steam_inv_dumper.markets.exchange import Exchange
from steam_inv_dumper.utils.configuration import load_config
from steam_inv_dumper.utils.data_structures import (
    MarketEvent,
    MarketEventTypes,
    MyMarketListing,
)


def clean_all_db(db: Database) -> None:
    db.Event.query.delete()
    db.Event.query.session.flush()
    db.Listing.query.delete()
    db.Listing.query.session.flush()
    db.Item.query.delete()
    db.Item.query.session.flush()


class TestSteamDatabase(TestCase):
    def tearDown(self) -> None:
        clean_all_db(self.db)

    def setUp(self) -> None:
        config = load_config("test_config.json").unwrap()
        self.db = Database(config=config)
        clean_all_db(self.db)

        itemid = "12345"
        listing_id = "123456789"
        item_for_db = self.db.Item(item_id=itemid, market_hash_name="casekey1")
        for_db = self.db.Listing(
            item_id=itemid,
            listing_id=listing_id,
            you_receive=1430,
            buyer_pay=1499,
        )
        events = [
            self.db.Event(
                listing_id=listing_id,
                event_type="ListingCreated",
                event_datetime=datetime(year=2023, month=1, day=1),
                time_event_fraction=1234,
                steam_id_actor="123456789",
            ),
            self.db.Event(
                listing_id=listing_id,
                event_type="ListingSold",
                event_datetime=datetime(year=2023, month=1, day=2),
                time_event_fraction=1234,
                steam_id_actor="233432432423",
            ),
        ]
        self.db.Item.query.session.add(item_for_db)
        self.db.Listing.query.session.add(for_db)
        self.db.Event.query.session.add_all(events)
        self.db.Item.query.session.flush()
        self.db.Listing.query.session.flush()
        self.db.Event.query.session.flush()
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


class TestListingIdAddedLater(TestCase):
    def tearDown(self) -> None:
        clean_all_db(self.exchange.database)

    def setUp(self) -> None:
        config = load_config("test_config.json").unwrap()
        db = Database(config=config)
        self.exchange = Exchange(config=config, database=db, inventory_provider=None, market_provider=None)
        clean_all_db(self.exchange.database)

        itemid = "12345"
        item_for_db = self.exchange.database.Item(item_id=itemid, market_hash_name="casekey1")
        for_db = self.exchange.database.Listing(
            item_id=itemid,
            listing_id=None,
            you_receive=1430,
            buyer_pay=1499,
            currency="USD",
        )
        self.exchange.database.Item.query.session.add(item_for_db)
        self.exchange.database.Listing.query.session.add(for_db)
        self.exchange.database.Item.query.session.flush()
        self.exchange.database.Listing.query.session.flush()
        self.exchange.database.Event.query.session.flush()

    def test_listing_id_added_later(self):
        market_events = [
            MarketEvent(
                listingid="100",
                event_type=MarketEventTypes.ListingCreated,
                event_datetime=datetime(year=2023, month=1, day=1),
                time_event_fraction=1234,
                steamid_actor=123456789,
                purchaseid=None,
            ),
            MarketEvent(
                listingid="100",
                event_type=MarketEventTypes.ListingSold,
                event_datetime=datetime(year=2023, month=1, day=2),
                time_event_fraction=1234,
                steamid_actor=233432432423,
                purchaseid="1234",
            ),
        ]

        my_listings: list[MyMarketListing] = [
            MyMarketListing.from_dict(
                {
                    "listing_id": "100",
                    "unowned_id": "300",
                    "buyer_pay": 0,
                    "you_receive": 0,
                    "created_on": "",
                    "need_confirmation": True,
                    "description": {
                        **DESCRIPTION,
                        "market_hash_name": "aaa",
                        "id": "12345",
                        "unowned_id": "300",
                    },
                }
            )
        ]
        self.exchange._update_listing_ids(items_sale_listings=my_listings)

        self.assertEqual(self.exchange.database.Listing.query_ref(item_id="12345").first().listing_id, "100")
        self.exchange._update_events(market_events=market_events)
        event_types = [x.event_type for x in self.exchange.database.Event.query.all() if x.listing_id == "100"]
        self.assertEqual(event_types, [MarketEventTypes.ListingCreated.name, MarketEventTypes.ListingSold.name])
