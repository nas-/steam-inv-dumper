from datetime import datetime

from steam_inv_dumper.utils.data_structures import MarketEvent, MarketEventTypes


def test__parse_market_events():
    market_event_dict = {
        "listingid": "1234",
        "event_type": 2,
        "time_event": 1640000221,
        "time_event_fraction": 367000000,
        "steamid_actor": "4331",
        "date_event": "20 Dec",
    }
    market_event = MarketEvent.from_event(market_event_dict)
    assert market_event.listingid == "1234"
    assert market_event.event_type == MarketEventTypes.ListingCancelled
    assert market_event.event_datetime == datetime.utcfromtimestamp(1640000221)
    assert market_event.time_event_fraction == 367000000
    assert market_event.steamid_actor == "4331"
    assert market_event.purchaseid is None
