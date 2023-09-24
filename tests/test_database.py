from datetime import datetime
from unittest import TestCase

from constants import (
    DESCRIPTION,
    TEST_EVENTS_KWARGS,
    TEST_ITEM_KWARGS,
    TEST_LISTING_KWARGS,
)

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
    maxDiff = None

    def tearDown(self) -> None:
        clean_all_db(self.db)

    def setUp(self) -> None:
        config = load_config("test_config.json").unwrap()
        self.db = Database(config=config)
        clean_all_db(self.db)
        events = [self.db.Event(**event) for event in TEST_EVENTS_KWARGS]
        self.db.Item.query.session.add(self.db.Item(**TEST_ITEM_KWARGS))
        self.db.Listing.query.session.add(self.db.Listing(**TEST_LISTING_KWARGS))
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
                "account": "",
                "amount": 1,
                "appid": "730",
                "background_color": "",
                "classid": "123456789",
                "commodity": True,
                "contextid": "2",
                "instanceid": "2022",
                "item_id": "12345",
                "market_hash_name": "casekey1",
                "market_name": "",
                "market_tradable_restriction": 0,
                "marketable": True,
                "name_color": "",
                "original_amount": None,
                "owner": None,
                "sold": False,
                "stale_item_id": False,
                "status": None,
                "tradable": True,
                "type": "",
                "unowned_contextid": None,
                "unowned_id": None,
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

        for_db = self.exchange.database.Listing(
            item_id="12345",
            listing_id=None,
            you_receive=1430,
            buyer_pay=1499,
            currency="USD",
        )
        self.exchange.database.Item.query.session.add(self.exchange.database.Item(**TEST_ITEM_KWARGS))
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
