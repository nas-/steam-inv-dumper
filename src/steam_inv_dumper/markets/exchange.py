import logging
from typing import List

import arrow
from sqlalchemy.exc import IntegrityError
from steampy.models import GameOptions

from steam_inv_dumper.db.db import Database
from steam_inv_dumper.markets.interfaces.interfaces import (
    InventoryProvider,
    MarketProvider,
)
from steam_inv_dumper.utils.data_structures import (
    DelistFromMarket,
    InventoryItem,
    ListOnMarket,
    MarketEvent,
    MarketEventTypes,
    MyMarketListing,
)
from steam_inv_dumper.utils.price_utils import (
    actions_to_make_list_delist,
    get_items_to_delist,
    get_items_to_list,
)
from steam_inv_dumper.utils.steam_prices_utils import convert_string_prices

logger = logging.getLogger(__name__)


class Exchange:
    """
    Class representing an exchange. In this case Steam Market.
    """

    def __init__(
        self, config: dict, inventory_provider: InventoryProvider, market_provider: MarketProvider, database: Database
    ):
        # TODO move those somewere else.
        self._last_run = 0
        self._config = config
        self._heartbeat_interval = config.get("heartbeat_interval", 100)
        self._heartbeat_msg = 0
        self._timeout = self._config.get("market_sell_timeout", 300)

        self.inventory_provider = inventory_provider
        self.market_provider = market_provider
        self.database = database

    @property
    def is_testing(self) -> bool:
        return self._config["debug"] is True

    @property
    def items_to_sell(self) -> dict:
        return self._config.get("items_to_sell", {})

    def get_own_items(self, game: GameOptions = GameOptions.CS) -> List[InventoryItem]:
        """
        Gets *marketable* items in inventory for specified game
        :param game: defaults CSGO
        :return: List of Inventory items.
        """
        items_dict = self.inventory_provider.get_my_inventory(game=game)

        items = [InventoryItem.from_my_listing_dict(listing_vars) for listing_id, listing_vars in items_dict.items()]
        items = [item for item in items if item.marketable is True]

        return items

    def get_item_price(self, market_hash_name: str) -> int:
        """
        Gets the item int_price from Steam
        :param market_hash_name: Market hash market_hash_name.
        :return: int. price in cents
        """
        price_data = self.market_provider.get_item_price(
            market_hash_name=market_hash_name,
        )
        try:
            price_data["lowest_price"] = convert_string_prices(price_data["lowest_price"])
            price_data["median_price"] = convert_string_prices(price_data["median_price"])
        except KeyError:
            price_data["lowest_price"] = convert_string_prices(price_data["lowest_price"])
            price_data["median_price"] = 0
        return max(price_data["lowest_price"], price_data["median_price"]) - 1

    def get_own_listings(self) -> List[MyMarketListing]:
        """
        Gets all items currently listed on the market
        :return: List of My Market listings
        """

        listings = self.market_provider.get_my_market_listings()

        listings_sell = [
            MyMarketListing.from_dict(listing_vars) for listing_id, listing_vars in listings["sell_listings"].items()
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
        # TODO think deeply how to do the business logic.
        # TODO is this always needed?
        my_items = self.get_own_items()
        self._update_items_in_database(inventory_items_list=my_items)

        my_listings = self.get_own_listings()
        self._add_all_listings(items_sale_listings=my_listings)
        self._update_sold_items(items_sale_listings=my_listings)

        # TODO basically this is all business logic. I need to move it away...
        for market_hash_name, sell_options in self._config.get("items_to_sell", {}).items():
            # dataframes
            item_on_sale_listings = [
                listing for listing in my_listings if listing.description.market_hash_name == market_hash_name
            ]
            items_in_inventory = [my_item for my_item in my_items if my_item.market_hash_name == market_hash_name]
            if item_on_sale_listings:
                min_price_already_on_sale = min([i.buyer_pay for i in item_on_sale_listings])
            else:
                min_price_already_on_sale = 0
            selling_price = self.get_item_price(market_hash_name=market_hash_name)

            sell_params = {
                "num_in_inventory": len(items_in_inventory),
                "num_to_sell": int(sell_options.get("quantity", 0)),
                "num_market_listings": len(item_on_sale_listings),
                "min_allowed_price": sell_options["min_price"],
                "min_price_mark_listing": min_price_already_on_sale,
                "item_selling_price": selling_price,
            }

            # TODO refactor with DataClasses.
            actions = actions_to_make_list_delist(**sell_params)
            logger.info(f"{market_hash_name}  {actions}")

            # Items to sell
            list_items_to_sell = get_items_to_list(
                market_hash_name=market_hash_name,
                amount=actions["list"]["qty"],
                price=actions["list"]["int_price"],
                inventory=items_in_inventory,
            )
            self.dispatch_sales(item_for_sale_list=list_items_to_sell)

            # Items to delete
            list_items_to_delist = get_items_to_delist(
                market_hash_name=market_hash_name,
                amount=actions["delist"]["qty"],
                listings=item_on_sale_listings,
            )
            self.dispatch_delists(to_delist=list_items_to_delist)
        # Cleanup Block
        my_new_listings = self.get_own_listings()
        self._update_listing_ids(items_sale_listings=my_new_listings)
        market_events: List[MarketEvent] = self.market_provider.get_market_events()
        self._update_events(market_events=market_events)

    def _update_listing_ids(self, items_sale_listings: list[MyMarketListing]) -> None:
        """
        Updates the database with the newly created listing_IDs.
        :param items_sale_listings: dataframe containing all items on sale
        """

        for listing in items_sale_listings:
            listings_in_db = self.database.Listing.query_ref(
                item_id=listing.description.item_id, listing_status=[MarketEventTypes.ListingCreated.name]
            ).first()
            if listings_in_db.listing_id is None:
                listings_in_db.listing_id = listing.listing_id
                self.database.Item.query.session.flush()
        pass

    def _add_all_listings(self, items_sale_listings: list[MyMarketListing]) -> None:
        """
        Finds the items which are not in the inventory or on sale anymore, and update the database,
        setting them all as sold.
        :param items_sale_listings: dataframe containing all items of this kind on sale
        """

        for listing in items_sale_listings:
            listings_in_db = self.database.Listing.query_ref(item_id=listing.description.item_id).all()
            if not listings_in_db:
                for_db = self.database.Listing.from_my_listing(
                    my_listing=listing, listing_status=MarketEventTypes.ListingCreated.name
                )
                self.database.Listing.query.session.add(for_db)
        self.database.Item.query.session.flush()
        pass

    def _update_sold_items(self, items_sale_listings: list[MyMarketListing]) -> None:
        """
        Finds the items which are not in the inventory or on sale anymore, and update the database,
        setting them all as sold.
        :param items_sale_listings: dataframe containing all items of this kind on sale
        """

        items_in_listings = [item.description.item_id for item in items_sale_listings]
        listings_in_db = self.database.Listing.query_ref(listing_status=[MarketEventTypes.ListingCreated.name]).all()
        for item_in_db in listings_in_db:
            # The item is still listed. So not sold.
            if item_in_db.item_id not in items_in_listings:
                logger.info(f"Updating {item_in_db.item_id} {item_in_db.item.market_hash_name} to sold")
                # item was sold.
                item_in_db.item.sold = True
        pass

    def _update_items_in_database(self, inventory_items_list: list[InventoryItem]) -> None:
        for item in inventory_items_list:
            items_already_in_db = self.database.Item.query_ref(item_id=item.item_id).all()
            if len(items_already_in_db) == 1:
                continue
            item_for_db = self.database.Item.from_item_dataclass(item=item, account=self._config["username"])
            self.database.Item.query.session.add(item_for_db)
        self.database.Item.query.session.flush()

    def dispatch_delists(self, to_delist: list[DelistFromMarket]) -> None:
        """
        Delists specified items, and updates the DB accordingly.
        :param to_delist: list of dicts of items currently on sale which should be delisted.
        :return: None
        """
        if not to_delist:
            return

        for item in to_delist:
            if self.is_testing:
                logger.debug("delist items. Debug is True. Updating database only")
                logger.debug(f"{item.market_hash_name} cancel_sell_order({item.listing_id}")
            else:
                logger.debug("delist items. Debug is False. Sending cancel order to steam")
                logger.debug(f"{item.market_hash_name} - listing_id {item.listing_id}")
                self.market_provider.cancel_sell_order(sell_listing_id=item.listing_id)
            record = self.database.Listing.query_ref(item_id=item.itemID).first()

            # delete this instead?
            record.listing_status = "CANCELLED"
            record.item.stale_item_id = True

        self.database.Listing.query.session.flush()

    def dispatch_sales(self, item_for_sale_list: List[ListOnMarket]) -> None:
        """
        Creates items listing for every specified item.
        :param item_for_sale_list: List of Dicts containing items to sell, and their prices, expressed as cents!
        :return:
        """
        if not item_for_sale_list:
            return
        for element in item_for_sale_list:
            if self.is_testing:
                logger.debug(
                    f"{element.market_hash_name} create_sell_order({element.assetsID} )"
                    f",money_to_receive={element.you_receive} buyer_pays {element.buyer_pays}"
                )
            else:
                logger.debug(f"{element.market_hash_name} creating real sell order")
                self.market_provider.create_sell_order(
                    assetid=element.assetsID,
                    game=GameOptions.CS,
                    money_to_receive=element.you_receive,
                )

            buyer_pays = int(element.buyer_pays)
            you_receive = int(element.you_receive)

            listing_already_in_db = self.database.Listing.query_ref(
                item_id=element.assetsID, listing_status=[MarketEventTypes.ListingCreated.name]
            ).all()
            if len(listing_already_in_db) == 1:
                continue

            for_db = self.database.Listing(
                # listing_id
                buyer_pay=buyer_pays,
                you_receive=you_receive,
                item_id=element.assetsID,
                currency=self.market_provider.currency.name,
            )
            self.database.Listing.query.session.add(for_db)
        self.database.Listing.query.session.flush()

    def _update_events(self, market_events: list[MarketEvent]) -> None:
        """
        Updates the database with the market events.
        :param market_events:
        :return:
        """
        listing_id_to_update = [a.listing_id for a in self.database.Listing.query.all()]

        for event in market_events:
            if event.listingid in listing_id_to_update:
                try:
                    event_already_in_db = self.database.Event.query_ref(
                        listing_id=event.listingid, event_type=event.event_type.name
                    ).all()
                except IntegrityError as e:
                    logger.debug(f"Integrity error {e}")
                    continue
                if len(event_already_in_db) == 1:
                    continue
                for_db = self.database.Event.from_market_event(market_event=event)
                self.database.Event.query.session.add(for_db)
        self.database.Event.query.session.flush()
