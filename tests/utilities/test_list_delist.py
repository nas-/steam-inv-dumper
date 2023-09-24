from unittest import TestCase

from constants import DESCRIPTION

from steam_inv_dumper.utils.data_structures import (
    DelistFromMarket,
    InventoryItem,
    MarketActionType,
    MyMarketListing,
)
from steam_inv_dumper.utils.price_utils import (
    get_items_to_delist,
    get_items_to_list,
    how_many_can_list,
)
from steam_inv_dumper.utils.steam_prices_utils import get_steam_fees_object


class TestItemListDelist(TestCase):
    def test_get_list_items_to_list(self) -> None:
        items = []
        items.append(
            InventoryItem.from_my_listing_dict(
                {
                    **DESCRIPTION,
                    "market_hash_name": "aaa",
                    "marketable": True,
                    "id": "100",
                }
            )
        )
        items.append(
            InventoryItem.from_my_listing_dict(
                {
                    **DESCRIPTION,
                    "market_hash_name": "bbbb",
                    "marketable": True,
                    "id": "200",
                }
            )
        )
        items.append(
            InventoryItem.from_my_listing_dict(
                {
                    **DESCRIPTION,
                    "market_hash_name": "aaa",
                    "marketable": False,
                    "id": "1000",
                }
            )
        )

        price = 10
        output = get_items_to_list(market_hash_name="aaa", amount=1, price=price, inventory=items)

        self.assertEqual(len(output), 1)
        self.assertEqual(
            [
                {
                    "market_hash_name": output[0].market_hash_name,
                    "item_id": output[0].item_id,
                    "you_receive": output[0].you_receive,
                    "buyer_pays": output[0].buyer_pays,
                }
            ],
            [
                {
                    "market_hash_name": "aaa",
                    "item_id": "100",
                    "you_receive": "8",
                    "buyer_pays": "10",
                }
            ],
        )
        self.assertEqual(output[0].you_receive, str(get_steam_fees_object(price)["you_receive"]))
        self.assertEqual(
            output[0].buyer_pays,
            str(get_steam_fees_object(price)["money_to_ask"]),
        )

    def test_get_list_items_to_de_list(self) -> None:
        data = []
        data.append(
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
                        "id": "desc1",
                        "unowned_id": "300",
                    },
                }
            )
        )
        data.append(
            MyMarketListing.from_dict(
                {
                    "listing_id": "200",
                    "unowned_id": "200",
                    "buyer_pay": 0,
                    "you_receive": 0,
                    "created_on": "",
                    "need_confirmation": True,
                    "description": {
                        **DESCRIPTION,
                        "market_hash_name": "bbbb",
                        "id": "desc2",
                    },
                }
            )
        )
        data.append(
            MyMarketListing.from_dict(
                {
                    "listing_id": "1000",
                    "unowned_id": "300",
                    "buyer_pay": 0,
                    "you_receive": 0,
                    "created_on": "",
                    "need_confirmation": True,
                    "description": {
                        **DESCRIPTION,
                        "market_hash_name": "aaa",
                        "id": "desc3",
                        "unowned_id": "300",
                    },
                }
            )
        )

        output = get_items_to_delist("aaa", 2, data)

        self.assertEqual(all(a.market_hash_name == "aaa" for a in output), True)
        self.assertEqual(
            output,
            [
                DelistFromMarket(
                    action_type=MarketActionType.RemoveFromMarket,
                    market_hash_name="aaa",
                    item_id="desc1",
                    unowned_id="300",
                    listing_id="100",
                ),
                DelistFromMarket(
                    action_type=MarketActionType.RemoveFromMarket,
                    market_hash_name="aaa",
                    item_id="desc3",
                    unowned_id="300",
                    listing_id="1000",
                ),
            ],
        )

    def test_how_many_can_list(self) -> None:
        self.assertEqual(how_many_can_list(5, 5, 10), 0)
        self.assertEqual(how_many_can_list(1, 5, 10), 4)
        self.assertEqual(how_many_can_list(1, 0, 10), 0)
