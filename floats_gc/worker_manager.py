import json
import logging
import os
from itertools import cycle
from pathlib import Path
from typing import Iterable

import arrow
import gevent.monkey
import vdf

from db.db import init_db
from floats_gc.float_utils import parse_items_cdn
from floats_gc.worker import CSGOWorker

gevent.monkey.patch_all()
# see https://github.com/gevent/gevent/issues/1016#issuecomment-328529454
import requests

logger = logging.getLogger('__name__')

curr_dir = os.path.dirname(__file__)

ITEMS_GAME_URL = 'https://raw.githubusercontent.com/SteamDatabase/GameTracking-CSGO/master/csgo/scripts/items/items_game.txt'
CSGO_ENGLISH_URL = 'https://raw.githubusercontent.com/SteamDatabase/GameTracking-CSGO/master/csgo/resource/csgo_english.txt'
ITEMS_GAME_CDN_URL = 'https://raw.githubusercontent.com/SteamDatabase/GameTracking-CSGO/master/csgo/scripts/items/items_game_cdn.txt'
SCHEMA_URL = 'https://raw.githubusercontent.com/SteamDatabase/SteamTracking/b5cba7a22ab899d6d423380cff21cec707b7c947/ItemSchema/CounterStrikeGlobalOffensive.json'


class FloatManager(object):
    def __init__(self, config: dict = None) -> None:
        if config is None:
            config = {}
        self._bots_login = config.get('float_accounts', [])
        self._timeout = config.get('timeout', 3)
        self._retrieve_game_data(config.get('refresh_game_files', False))
        if not config.get('retrieve_floats', False):
            # nothing to do
            self.workers = []
            return
        self.workers = self._initialize_workers()
        # todo add tests
        # make a CSGOWorker per each bot.

    def process_links(self, link_dict: dict):
        result_list = []
        for single_link in link_dict:
            res = self.give_job(single_link['link'])
            if res.get('success'):
                new_el = {'price': single_link.get('price'), 'lisingid': single_link.get('listingid'), **res['data']}
                result_list.append(new_el)
            else:
                logger.info(f'Error during request {single_link}')
        return result_list

    def give_job(self, url: str) -> dict:
        if not self.workers:
            raise Exception('No bots configured')
        for bot in self.workers:
            if (
                    not bot.busy
                    and bot.last_run + self._timeout < arrow.now().timestamp()
            ):
                logger.debug(f'dispatched job to bot {bot.username}')
                return bot.from_inspect_link(url)

    def _initialize_workers(self) -> Iterable:
        bot_list = []
        if self._bots_login:
            for login in self._bots_login:
                bot = CSGOWorker(login, self.items_game, self.csgo_english, self.items_game_cdn, self.schema)
                bot.start()
                bot_list.append(bot)
        return cycle(bot_list)

    def _retrieve_game_data(self, force_refresh: bool) -> None:  # sourcery skip: last-if-guard
        found_files = True
        # 1 day
        files_stale = arrow.now().timestamp() - Path(
            os.path.join(curr_dir, 'items_game.json')).stat().st_ctime > 24 * 60 * 60
        if not force_refresh and not files_stale:
            try:
                with open(os.path.join(curr_dir, 'items_game.json')) as json_file:
                    self.items_game = json.load(json_file)
                with open(os.path.join(curr_dir, 'csgo_english.json')) as json_file:
                    self.csgo_english = json.load(json_file)
                with open(os.path.join(curr_dir, 'items_game_cdn.json')) as json_file:
                    self.items_game_cdn = json.load(json_file)
                with open(os.path.join(curr_dir, 'schema.json')) as json_file:
                    self.schema = json.load(json_file)
                logger.info('loaded files from disk')
            except FileNotFoundError:
                logger.info('files not found. Downloading')
                found_files = False
        if force_refresh or files_stale or not found_files:
            self._download_game_files()

    def _download_game_files(self):
        items_game = requests.get(ITEMS_GAME_URL)
        csgo_english = requests.get(CSGO_ENGLISH_URL)
        items_game_cdn = requests.get(ITEMS_GAME_CDN_URL)
        schema = requests.get(SCHEMA_URL)
        self.items_game = vdf.loads(items_game.text)['items_game']
        self.csgo_english = vdf.loads(csgo_english.text)['lang']['Tokens']
        self.items_game_cdn = parse_items_cdn(items_game_cdn.text)
        self.schema = schema.json()['result']
        with open(os.path.join(curr_dir, 'items_game.json'), 'w') as outfile:
            json.dump(self.items_game, outfile)
        with open(os.path.join(curr_dir, 'csgo_english.json'), 'w') as outfile:
            json.dump(self.csgo_english, outfile)
        with open(os.path.join(curr_dir, 'items_game_cdn.json'), 'w') as outfile:
            json.dump(self.items_game_cdn, outfile)
        with open(os.path.join(curr_dir, 'schema.json'), 'w') as outfile:
            json.dump(self.schema, outfile)
        logger.info('Ended saving files.')


if __name__ == "__main__":
    from const import links
    init_db('sqlite://')
    logging.basicConfig(format="%(asctime)s | %(name)s | thread:%(thread)s | %(levelname)s | %(message)s",
                        level=logging.INFO)

    with open(Path(os.getcwd()).parent.joinpath('config.json'), 'r') as f:
        config = json.loads(f.read())

    manager = FloatManager(config.get('floats'))
    results = []
    for link in links:
        results.append(manager.give_job(link))

    print(results)
