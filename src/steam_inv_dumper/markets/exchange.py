import decimal
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List

import arrow
import pandas as pd
from steampy.models import GameOptions

from steam_inv_dumper.db.db import Item, Listing, init_db
from steam_inv_dumper.markets.steam.client import SteamClientPatched
from steam_inv_dumper.markets.steam.market import SteamMarketLimited
from steam_inv_dumper.markets.utilities import (
    actions_to_make_list_delist,
    get_items_to_delist,
    get_items_to_list,
)
from steam_inv_dumper.utils.data_structures import InventoryItem, MyMarketListing
from steam_inv_dumper.utils.price_utils import convert_string_prices

TWODIGITS = decimal.Decimal("0.01")

logger = logging.getLogger(__name__)


class Exchange:
    """
    Class representing an exchange. In this case Steam Market.
    """

    def __init__(self, config: dict):
        self._last_run = 0
        self._config = config
        self._test_files_root = Path(__file__).parents[1] / "api_responses"
        self._heartbeat_interval = config.get("heartbeat_interval")
        self._heartbeat_msg: float = 0
        self._timeout: int = self._config.get("market_sell_timeout")

        if self.is_testing is False:
            self._initialize_database()
            self._prepare_markets()

    @property
    def is_testing(self):
        return self._config["debug"] is True

    @property
    def items_to_sell(self) -> dict:
        return self._config.get("items_to_sell", {})

    def _prepare_markets(self) -> None:
        if self._config.get("use_cookies", False):
            try:
                self.steam_client = SteamClientPatched.from_pickle(
                    self._config["username"]
                )
                logger.info("Successfully logged in Steam trough Cookies")
            except ValueError:
                logger.info("Did not manage to log into Steam trough Cookies")
                self._login_and_save_cookies()
        else:
            self._login_and_save_cookies()
        self.steam_market = SteamMarketLimited(
            self.steam_client.session,
            self._config["steamguard"],
            self.steam_client.session_id,
            self.steam_client.currency,
        )

    def _login_and_save_cookies(self):
        self.steam_client: SteamClientPatched = SteamClientPatched(
            self._config["apikey"]
        )
        self.steam_client.login(
            self._config["username"],
            self._config["password"],
            json.dumps(self._config["steamguard"]),
        )
        self.steam_client.to_pickle(self._config["username"])

    def _initialize_database(self) -> None:
        debug = self._config.get("debug", True)
        db_url = self._config.get("db_url", True)
        if debug:
            init_db("sqlite:///sales_debug.sqlite")
            # Listing.query.delete()
            # Listing.query.session.flush()
            # Item.query.delete()
            # Item.query.session.flush()
        else:
            init_db(db_url)

    def get_own_items(self, game: GameOptions = GameOptions.CS) -> List[InventoryItem]:
        """
        Gets *marketable* items in inventory for specified game
        :param game: defaults CSGO
        :return: List of Inventory items.
        """
        items_dict = self._get_test_or_prod_result(
            api_path="get_my_inventory", game=game
        )

        items = [
            InventoryItem.from_inventory(listing_vars)
            for listing_id, listing_vars in items_dict.items()
        ]
        items = [item for item in items if item.marketable is True]

        return items

    def get_item_price(self, market_hash_name: str) -> decimal.Decimal:
        """
        Gets the item int_price from Steam
        :param market_hash_name: Market hash name.
        :return: Decimal.
        """
        price_data = self._get_test_or_prod_result(
            api_path="get_item_price", market_hash_name=market_hash_name
        )
        try:
            price_data["lowest_price"] = convert_string_prices(
                price_data["lowest_price"]
            )
            price_data["median_price"] = convert_string_prices(
                price_data["median_price"]
            )
        except KeyError:
            price_data["lowest_price"] = convert_string_prices(
                price_data["lowest_price"]
            )
            price_data["median_price"] = 0
        return max(
            price_data["lowest_price"], price_data["median_price"]
        ) - decimal.Decimal("0.01")

    def _get_test_or_prod_result(self, api_path: str, *args, **kwargs) -> dict:
        """
        Returns the results, calling the API if in production or getting the static file if in testing mode.
        :param api_path: str name of the file, or method to call
        :return:
        """
        if self.is_testing:
            file_path = self._test_files_root / f"{api_path}.json"
            result = json.loads(file_path.read_text())
        else:
            result = getattr(self.steam_market, api_path)(*args, **kwargs)
        return result

    # TODO remove some unused columns and/or get rid of dataframe
    def get_own_listings(self) -> List[MyMarketListing]:
        """
        Gets all items currently listed on the market
        :return: List of My Market listings
        """

        listings = self._get_test_or_prod_result("get_my_market_listings")

        listings_sell = [
            MyMarketListing.from_dict(listing_vars)
            for listing_id, listing_vars in listings["sell_listings"].items()
        ]
        return listings_sell

    def run(self) -> None:
        """
        :return:None
        """
        if self._last_run + self._timeout < arrow.now().timestamp():
            self._sell_loop()
            self._last_run = arrow.now().timestamp()

        if self._heartbeat_interval:
            now = arrow.now().timestamp()
            if (now - self._heartbeat_msg) > self._heartbeat_interval:
                logger.info("Bot heartbeat.")
                self._heartbeat_msg = now

    def _sell_loop(self) -> None:
        """
        Takes an exchange and runs the CheckSold, update database, sell more items cycle.
        Item_id s change when you remove the item from the market.
        """
        my_listings = self.get_own_listings()
        # if not self.is_testing:
        #     self._update_sold_items(my_listings)
        # TODO is this always needed?
        my_items = self.get_own_items()
        # if not self.is_testing:
        #     self._update_items_in_database(my_items)

        for item in self._config.get("items_to_sell", []):
            # dataframes
            item_on_sale_listings = [
                listing
                for listing in my_listings
                if listing.description.market_hash_name == item
            ]
            items_in_inventory = [
                my_item for my_item in my_items if my_item.market_hash_name == item
            ]
            if item_on_sale_listings:
                min_price_already_on_sale = min(
                    [i.buyer_pay for i in item_on_sale_listings]
                )
            else:
                min_price_already_on_sale = 0

            # Update sales listings.
            # define amounts
            amount_in_inventory = len(items_in_inventory)
            amount_to_sell = int(self.items_to_sell[item].get("quantity", 0))
            amount_on_sale = len(item_on_sale_listings)
            # define prices
            # TODO see if item_selling_price,min_allowed_price_decimal can be merged here into a single variable
            min_allowed_price = self.items_to_sell[item]["min_price"]
            sellingPrice = self.get_item_price(market_hash_name=item)

            # TODO refactor with DataClasses.
            actions = actions_to_make_list_delist(
                num_market_listings=amount_on_sale,
                num_in_inventory=amount_in_inventory,
                min_price_mark_listing=min_price_already_on_sale,
                item_selling_price=sellingPrice,
                num_to_sell=amount_to_sell,
                min_allowed_price=min_allowed_price,
            )
            logger.info(f"{item}  {actions}")

            # Items to sell
            listItemsToSell = get_items_to_list(
                item,
                actions["list"]["qty"],
                actions["list"]["int_price"],
                inventory=items_in_inventory,
            )
            if not self.is_testing:
                self.dispatch_sales(item, listItemsToSell)

            # Items to delete
            listItemsToDeList = get_items_to_delist(
                item, actions["delist"]["qty"], item_on_sale_listings
            )
            if not self.is_testing:
                self.dispatch_delists(item, listItemsToDeList)
            pass

    def _update_sold_items(self, items_sale_listings: pd.DataFrame) -> None:
        """
        Finds the items which are not in the inventory or on sale anymore, and update the database,
        setting them all as sold.
        :param items_sale_listings: dataframe containing all items of this kind on sale
        """

        items_in_listings = list(items_sale_listings["id"])
        items_in_listings = [str(i) for i in items_in_listings]
        listings_in_db = Listing.query_ref(sold=False, on_sale=True).all()
        for item in listings_in_db:
            # The item is still listed. So not sold.
            if item.item_id in items_in_listings:
                if not item.listing_id:
                    logger.info(f"Updating {item.item.market_hash_name} listing_id")
                    listing_id = (
                        items_sale_listings[items_sale_listings["id"] == item.item_id]
                        .iloc[0]
                        .listing_id
                    )
                    item.listing_id = listing_id
            else:
                logger.info(f"Updating {item.item.market_hash_name} to sold")
                # item was sold.
                item.sold = True
                item.on_sale = False
                item.item.sold = True
                item.item.stale_item_id = True

        Listing.query.session.flush()
        Item.query.session.flush()

    def _update_items_in_database(self, itemDF):
        for item in itemDF.itertuples():
            items_already_in_db = Item.query_ref(
                market_hash_name=item.market_hash_name, item_id=item.id
            ).all()
            if len(items_already_in_db) == 1:
                continue
            item_for_db = Item(
                item_id=item.id,
                market_hash_name=item.market_hash_name,
                account=self._config["username"],
                appid="730",
                contextid="2",
                tradable=bool(item.tradable),
                marketable=bool(item.marketable),
                commodity=bool(item.commodity),
            )
            Item.query.session.add(item_for_db)
        Item.query.session.flush()

    def dispatch_delists(self, item: str, to_delist: List) -> None:
        """
        Delists specified items, and updates the DB accordingly.
        :param item: Item name
        :param to_delist: list of dicts of items currently on sale which should be delisted.
        :return: None
        """
        debug = self._config.get("debug", True)
        if not to_delist:
            return

        for item_dict in to_delist:
            if debug:
                logger.debug("delist items. Debug is True. Updating database only")
                logger.debug(f'{item} cancel_sell_order({str(item_dict["listing_id"])}')
            else:
                logger.debug(
                    "delist items. Debug is False. Sending cancel order to steam"
                )
                logger.debug(f'{item} - listing_id {str(item_dict["listing_id"])}')
                self.steam_market.cancel_sell_order(str(item_dict["listing_id"]))
            record = Listing.query_ref(item_id=item_dict["itemID"]).first()

            # delete this instead?
            record.on_sale = False
            record.item.stale_item_id = True

        Listing.query.session.flush()

    def dispatch_sales(self, item: str, item_for_sale_list: List) -> None:
        """
        Creates items listing for every specified item.
        :param item:  Item name
        :param item_for_sale_list: List of Dicts containing items to sell, and their prices, expressed as cents!
        :return:
        """
        if not item_for_sale_list:
            return
        debug = self._config.get("debug", True)
        for element in item_for_sale_list:
            if debug:
                logger.debug(
                    f'{item} create_sell_order({str(element["assetsID"])} )'
                    f',money_to_receive={element["you_receive"]} buyer_pays {element["buyer_pays"]}'
                )
            else:
                logger.debug(f"{item} creating real sell order")
                self.steam_market.create_sell_order(
                    str(element["assetsID"]),
                    game=GameOptions.CS,
                    money_to_receive=str(int(element["you_receive"])),
                )
                # {'success': True}

            # Element ready for DB
            buyer_pays = decimal.Decimal(element["buyer_pays"] / 100).quantize(
                decimal.Decimal("0.01")
            )
            you_receive = decimal.Decimal(element["you_receive"] / 100).quantize(
                decimal.Decimal("0.01")
            )
            for_db = Listing(
                item_id=element["assetsID"],
                date=datetime.now(),
                sold=False,
                on_sale=True,
                buyer_pays=buyer_pays,
                you_receive=you_receive,
                currency=self.steam_market.currency.name,
            )
            Listing.query.session.add(for_db)
        Listing.query.session.flush()
