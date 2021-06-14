import gevent.monkey
gevent.monkey.patch_all()
#see https://github.com/gevent/gevent/issues/1016#issuecomment-328529454
import requests
import vdf

from floats_gc.float_utils import parse_items_cdn
from .worker import CSGOWorker

ITEMS_GAME_URL = 'https://raw.githubusercontent.com/SteamDatabase/GameTracking-CSGO/master/csgo/scripts/items/items_game.txt'
CSGO_ENGLISH_URL = 'https://raw.githubusercontent.com/SteamDatabase/GameTracking-CSGO/master/csgo/resource/csgo_english.txt'
ITEMS_GAME_CDN_URL = 'https://raw.githubusercontent.com/SteamDatabase/GameTracking-CSGO/master/csgo/scripts/items/items_game_cdn.txt'
SCHEMA_URL = 'https://raw.githubusercontent.com/SteamDatabase/SteamTracking/b5cba7a22ab899d6d423380cff21cec707b7c947/ItemSchema/CounterStrikeGlobalOffensive.json'


class FloatManager():
    def __init__(self, bots=None):
        if bots is None:
            bots = []
        self.bots = bots
        self._retrieve_game_data()
        # TODO initialize bots
        # TODO make a sort of Queque for dispatching requests to workers.
        # todo add tests

        # make a CSGOWorker per each bot.

    def _retrieve_game_data(self):
        # todo cache this? Exp for tests.
        items_game = requests.get(ITEMS_GAME_URL)
        csgo_english = requests.get(CSGO_ENGLISH_URL)
        items_game_cdn = requests.get(ITEMS_GAME_CDN_URL)
        schema = requests.get(SCHEMA_URL)
        self.items_game = vdf.loads(items_game.text)['items_game']
        self.csgo_english = vdf.loads(csgo_english.text)['lang']['Tokens']
        self.items_game_cdn = parse_items_cdn(items_game_cdn.text)
        self.schema = schema.json()['result']


