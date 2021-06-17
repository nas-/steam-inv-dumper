import json
import logging
import os
from itertools import cycle
from typing import Iterable

import arrow
import gevent.monkey
import vdf

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

links = [
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3416524772981168370A22686847911D12423745728461811906',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539622084A22686179973D7677589001441014956',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539566104A22686115401D12127781071334167050',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539547764A22686066208D12127781071334167050',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539549524A22686079942D12127781071334167050',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539536564A22686049452D12127781071334167050',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539551424A22686081324D9251008032410572398',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539553844A22686094424D12127781071334167050',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539554884A22686095882D14720024592732813316',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539552604A22686089271D12127781071334167050',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539752004A22686290354D12127781071334167050',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539750264A22686305457D12127781071334167050',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539993404A22686404598D12127781071334167050',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539790324A22686357169D14720024592732813316',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539967884A22686404483D14720024592732813316',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539968884A22686404491D14720024592732813316',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539966564A22686404482D12127781071334167050',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539991224A22686404602D12127781071334167050',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539972044A22686404511D14720024592732813316',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539965204A22686404475D16610511604854691940',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539977924A22686404558D12127781071334167050',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539982244A22686404576D12127781071334167050',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539980084A22686404567D12127781071334167050',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539987004A22686404613D12127781071334167050',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539973484A22686404528D14720024592732813316',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539964124A22686404474D14720024592732813316',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539975404A22686404535D14720024592732813316',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539961464A22686404469D17009685289481549356',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539970124A22686404504D14720024592732813316',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539984584A22686404588D14720024592732813316',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3409769373539989124A22686404609D12127781071334167050',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3410895273446006645A22685711220D16747867107881032844',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3424406072328735557A22686310669D14720024592732813316',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3426657872142201699A22450678289D7837635817249988224',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3421028372610864214A22685837855D14720024592732813316',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3405265773915363020A22686127745D16747867107881032844',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3405265773915806720A22618881255D16747867107881032844',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3412021173353698666A22686601944D16747867107881032844',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3419902472704101433A22685919916D16747867107881032844',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3410895273446276965A22686003060D16747867107881032844',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3424406072328738237A22686289308D14720024592732813316',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3437914967663502797A21298765837D7837635817249988224',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3414272973166951088A22686239417D12127781071334167050',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3414272973167304568A22686667738D12127781071334167050',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M5447647758491552896A22682940488D12127781071334167050',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M5447647758491465876A22682859494D12127781071334167050',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M5447647758491401056A22682783238D12127781071334167050',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M5447647758492231796A22683773278D14720024592732813316',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M5447647758491962336A22683469499D12127781071334167050',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M5447647758493208536A22684735233D12127781071334167050',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3423280172420828436A22685217819D12127781071334167050',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3423280172421778796A22686279530D14720024592732813316',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4942118698626451867A22667500454D5675670839710226666',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4942118698626452047A22666771307D5485989820274503840',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4942118698626451727A22667724273D5675670839710226666',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4942118698626422887A22668495092D202354534152674312',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4942118698626422967A22668495088D5210257996486857386',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4942118698626421827A22668495139D14438578539535816398',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4942118698626422067A22668495130D14438578539535816398',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4942118698626422127A22668495123D622249012115200070',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4942118698626422587A22668495096D12396736782999377988',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4942118698626422667A22668495095D5210257996486857386',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4942118698626421607A22668495157D622249012115200070',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4942118698626453407A22663877604D5675670839710226666',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4942118698626453587A22663012971D5675670839710226666',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4942118698626420727A22669383752D11819169734763232782',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4942118698626420807A22668495199D16747867107881032844',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4942118698626421027A22668495181D16747867107881032844',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4942118698626421207A22668495170D16747867107881032844',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4942118698626419287A22674038470D317610187157584960',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4942118698626420187A22670508966D11819169734763232782',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4942118698626420927A22668495193D16747867107881032844',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4942118698626421087A22668495177D16747867107881032844',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4942118698626421307A22668495168D16304194667821577446',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4942118698626419587A22672175707D317610187157584960',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4942118698626419947A22671426032D317610187157584960',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4942118698626420427A22670281114D317610187157584960',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4942118698626411607A22674558571D5098825086972760174',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M5448773658398068557A22675166674D317610187157584960',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M5448773658398068697A22675106076D317610187157584960',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M5448773658398068137A22680002522D14720024592732813316',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3437914967661403457A22460390417D16747867107881032844',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3422152368966545723A18640817450D16747867107881032844',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4938740998902306964A22676903312D16747867107881032844',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4659517821083188692A22676725072D16747867107881032844',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3439040867562898038A22519124388D16747867107881032844',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3433411368034538493A7601849946D16747867107881032844',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3435663167827092235A22496458397D7837635817249988224',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3421026469053790182A21103442486D16747867107881032844',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4660643720986015333A22671258893D16747867107881032844',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4660643720986015533A22671258737D16747867107881032844',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M5451025458195915899A22641624618D16747867107881032844',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4506395433348482160A16219818328D16747867107881032844',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3432285468118695912A21177416341D16747867107881032844',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4659517821081410272A15549336740D16747867107881032844',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M5449899558292433718A22667952956D5485989820274503840',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M5449899558292433678A22667950716D5485989820274503840',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3419900569143559101A21071176352D16747867107881032844',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M3416524772979460450A22684968677D14720024592732813316',
    'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M5411618961473173830A22684764602D14720024592732813316']


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

    def give_job(self, url: str) -> dict:
        if not self.workers:
            return
            # raise Exception('No bots configured')
        for bot in self.workers:
            if (
                    not bot.busy
                    and bot.last_run + self._timeout < arrow.now().timestamp()
            ):
                logger.info(f'dispatched job to bot {bot.username}')
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
        if not force_refresh:
            try:
                with open(os.path.join(curr_dir, 'items_game.json')) as json_file:
                    self.items_game = json.load(json_file)
                with open(os.path.join(curr_dir, 'csgo_english.json')) as json_file:
                    self.csgo_english = json.load(json_file)
                with open(os.path.join(curr_dir, 'items_game_cdn.jsonj')) as json_file:
                    self.items_game_cdn = json.load(json_file)
                with open(os.path.join(curr_dir, 'schema.json')) as json_file:
                    self.schema = json.load(json_file)
                logger.info('loaded files from disk')
            except FileNotFoundError:
                logger.info('files not found. Downloading')
                found_files = False
        if force_refresh or not found_files:
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
            with open(os.path.join(curr_dir, 'items_game_cdn.jsonj'), 'w') as outfile:
                json.dump(self.items_game_cdn, outfile)
            with open(os.path.join(curr_dir, 'schema.json'), 'w') as outfile:
                json.dump(self.schema, outfile)
            logger.info('Ended saving files.')


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s | %(name)s | thread:%(thread)s | %(levelname)s | %(message)s",
                        level=logging.INFO)
    bots = [
        {
            "username": "nasdevtest",
            "password": "97Sxoz@^htWRKT$unc!i"
        },
        {
            "username": "nasdevtest1",
            "password": "97Sxoz@^htWRKT$unc!i"
        },
        {
            "username": "nasdevtest2",
            "password": "97Sxoz@^htWRKT$unc!i"
        }]
    manager = FloatManager(bots)
    results = []
    for link in links:
        results.append(manager.give_job(link))

    print(results)
