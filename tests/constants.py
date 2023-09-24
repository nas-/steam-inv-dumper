from datetime import datetime

DESCRIPTION = {
    "currency": "currency",
    "appid": "appid",
    "contextid": "contextid",
    "id": "id",
    "classid": "classid",
    "instanceid": "instanceid",
    "amount": "amount",
    "status": "status",
    "original_amount": "original_amount",
    "unowned_id": "unowned_id",
    "unowned_contextid": "unowned_contextid",
    "background_color": "background_color",
    "tradable": "tradable",
    "market_hash_name": "market_hash_name",
    "name_color": "name_color",
    "type": "type",
    "market_name": "market_name",
    "commodity": "commodity",
    "market_tradable_restriction": "market_tradable_restriction",
    "marketable": "marketable",
    "owner": "owner",
}

TEST_ITEM_KWARGS = dict(
    amount=1,
    appid="730",
    background_color="",
    classid="123456789",
    commodity=True,
    contextid="2",
    item_id="12345",
    instanceid="2022",
    market_hash_name="casekey1",
    market_name="",
    market_tradable_restriction=0,
    marketable=True,
    name_color="",
    tradable=True,
    type="",
)


TEST_LISTING_KWARGS = dict(
    item_id="12345",
    listing_id="123456789",
    you_receive=1430,
    buyer_pay=1499,
)

TEST_EVENTS_KWARGS = [
    dict(
        listing_id="123456789",
        event_type="ListingCreated",
        event_datetime=datetime(year=2023, month=1, day=1),
        time_event_fraction=1234,
        steam_id_actor="123456789",
    ),
    dict(
        listing_id="123456789",
        event_type="ListingSold",
        event_datetime=datetime(year=2023, month=1, day=2),
        time_event_fraction=1234,
        steam_id_actor="233432432423",
    ),
]
