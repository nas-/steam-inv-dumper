import logging
import re
import time

import arrow
import vdf
from csgo.client import CSGOClient
from csgo.enums import ECsgoGCMsg, EGCBaseClientMsg, GCConnectionStatus
# pip install git+https://github.com/wearefair/protobuf-to-dict
from protobuf_to_dict import protobuf_to_dict
from steam.client import SteamClient

from floats_gc import const
from floats_gc.float_utils import get_skin_data, parse_items_cdn

logger = logging.getLogger("CSGO Worker")


class CSGOWorker(object):
    def __init__(self, logon_details: dict, items_game: dict, csgo_english: dict, items_game_cdn: dict,
                 schema: dict) -> None:
        self.items_game = items_game
        self.csgo_english = csgo_english
        self.items_game_cdn = items_game_cdn
        self.schema = schema
        self.steam = client = SteamClient()
        self.steam.cm_servers.bootstrap_from_webapi()
        self.csgo = cs = CSGOClient(self.steam)

        self.request_method = ECsgoGCMsg.EMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockRequest
        self.response_method = ECsgoGCMsg.EMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockResponse
        self._logon_details = dict(logon_details)
        self.busy = True
        self.logged_in = False
        self.last_run = arrow.now().timestamp()

        @client.once('channel_secured')
        def send_login() -> None:
            logger.debug('Send login')
            if client.relogin_available:
                client.relogin()
            elif self._logon_details is not None:
                client.login(**self._logon_details)

        @client.once('logged_on')
        def start_csgo() -> None:
            logger.debug('Logged into Steam - start CSGO')
            self.csgo.launch()

        @cs.once('ready')
        def gc_ready() -> None:
            logger.debug('Launched CSGO')
            pass

        @client.on('disconnected')
        def client_disconnected() -> None:
            logger.info(f'Disconneced from GC')
            logger.debug(f'{client.connected=}')
            logger.debug(f'{client.connection.connected=}')
            if client.relogin_available:
                client.relogin()
            elif self._logon_details is not None:
                client.login(**self._logon_details)
            self.steam.wait_event('logged_on', 60)

        @cs.on('connection_status')
        def cs_connection_changed(changed: GCConnectionStatus) -> None:
            logger.info(f'Connection changed into {changed.name}')
            if changed.name == 'NO_SESSION':
                logger.debug(f'Launching CSGO again')
                self.csgo.exit()
                self.csgo.launch()
                self.csgo.wait_event('ready', 60)

    def _send(self, s: int, a: int, d: int, m: int) -> dict:
        """
        # Send the item to the game coordinator and return the response data without modifications.
        :param s: SteamID (0 if in market)
        :param a: AssetID Id of the asset.
        :param d: DickID -
        :param m: MarketID - Present if element is in market, else 0
        :return:
        """
        # Send heartbeath to check if sessions are alive?
        logger.debug(f'Sending hearthbeat')
        self.csgo.send(EGCBaseClientMsg.EMsgGCClientHello)
        self.csgo.wait_event('csgo_welcome')
        logger.debug(f'received event')

        self.csgo.send(self.request_method, {
            'param_s': s,
            'param_a': a,
            'param_d': d,
            'param_m': m,
        })
        resp = self.csgo.wait_event(self.response_method, timeout=50)

        if resp is None:
            logger.info('CSGO failed to respond')
            raise TypeError

        iteminfo = resp[0].iteminfo
        return protobuf_to_dict(iteminfo)

    def start(self, username: str = None, password: str = None, two_factor_code: str = None) -> None:
        """
        Starts the worker.Preferably, the accounts should not have steamguard both mobile and auth.
        :param username:
        :param password:
        :param two_factor_code:
        """
        if username:
            self._logon_details['username'] = username
        if password:
            self._logon_details['password'] = password
        if two_factor_code:
            self._logon_details['two_factor_code'] = two_factor_code

        # self.steam.connect()
        self.steam.reconnect()
        self.steam.wait_event('logged_on', 60)
        # self._logon_details = None
        self.csgo.wait_event('ready', 60)
        self.logged_in = True
        self.busy = False

    # CLI login
    def cli_login(self) -> None:
        self.steam.cli_login()
        self.csgo.wait_event('ready', 60)

    def close(self) -> None:
        """
        Closes the connection to steam.
        """
        if self.steam.connected:
            self.steam.logout()
            logger.info('Logged out of Steam')

    def parse_item_data(self, iteminfo: dict) -> dict:
        """
        # Lookup the weapon name/skin and special attributes. Return the relevant data formatted as JSON
        Iteminfo is proto returned by GC.
        :param iteminfo:
        :return:
        """

        iteminfo = get_skin_data(iteminfo, self.items_game, self.csgo_english, self.items_game_cdn, self.schema)

        special = None
        if iteminfo['item_name'] == "Marble Fade":
            logger.info(f"found {iteminfo['item_name']=}")
            try:
                special = const.marbles[iteminfo['weapon_type']].get(str(iteminfo['paintseed']))
            except KeyError:
                logger.info('Non-indexed %s | Marble Fade' % iteminfo['weapon_type'])
        elif iteminfo['item_name'] == "Fade" and iteminfo['weapon_type'] in const.fades:
            logger.info(f"found {iteminfo['item_name']=}")
            info = const.fades[iteminfo['weapon_type']]
            unscaled = const.order[::info[1]].index(iteminfo['paintseed'])
            scaled = unscaled / 1001
            percentage = round(info[0] + scaled * (100 - info[0]))
            special = str(percentage) + "%"
        elif iteminfo['item_name'] in ["Doppler", "Gamma Doppler"]:
            logger.info(f"found {iteminfo['item_name']=}")
            special = const.doppler[iteminfo['paintindex']]

        iteminfo['special'] = special
        return iteminfo

    def get_item(self, s: int, a: int, d: int, m: int) -> dict:
        """
        # Get relevant information and returns it.
        :rtype: object
        """
        iteminfo = self._send(s, a, d, m)
        return self.parse_item_data(iteminfo)

    def from_inspect_link(self, url: str) -> dict:
        logger.info(f'Retieving float value trugh account {self._logon_details.get("username")}')
        self.busy = True
        match = re.search(r'([SM])(\d+)A(\d+)D(\d+)$', url)
        if match.group(1) == 'S':
            s = int(match.group(2))
            m = 0
        else:
            s = 0
            m = int(match.group(2))
        a = int(match.group(3))
        d = int(match.group(4))

        try:
            iteminfo = self.get_item(s, a, d, m)
        except TypeError:
            logger.info('Failed response')
            # TODO raise a proper exception maybe? Else add a status Success or Status Fail request.
            return {'success': False, 'data': 'Invalid link or Steam is slow.'}
        finally:
            self.last_run = arrow.now().timestamp()
            self.busy = False
        return {'success': True, 'data': iteminfo}

    @property
    def username(self) -> str:
        return self._logon_details.get('username', '')


if __name__ == '__main__':
    import requests

    k = requests.get(
        'https://raw.githubusercontent.com/SteamDatabase/GameTracking-CSGO/master/csgo/scripts/items/items_game.txt')
    y = requests.get(
        'https://raw.githubusercontent.com/SteamDatabase/GameTracking-CSGO/master/csgo/resource/csgo_english.txt')
    z = requests.get(
        'https://raw.githubusercontent.com/SteamDatabase/GameTracking-CSGO/master/csgo/scripts/items/items_game_cdn.txt')
    schema_url = 'https://raw.githubusercontent.com/SteamDatabase/SteamTracking/b5cba7a22ab899d6d423380cff21cec707b7c947/ItemSchema/CounterStrikeGlobalOffensive.json'
    items_game = vdf.loads(k.text)['items_game']
    csgo_english = vdf.loads(y.text)['lang']['Tokens']
    items_game_cdn = parse_items_cdn(z.text)
    schema = requests.get(schema_url).json()['result']

    logging.basicConfig(format="%(asctime)s | %(name)s | thread:%(thread)s | %(levelname)s | %(message)s",
                        level=logging.DEBUG)
    logger = logging.getLogger('__name__')

    logger.debug('starting')
    logon_details = {'username': 'nasdevtest1',
                     'password': '97Sxoz@^htWRKT$unc!i'}
    worker = CSGOWorker(logon_details, items_game, csgo_english, items_game_cdn, schema)
    worker.start()

    el1 = worker.from_inspect_link(
        'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M5451025458192283279A22657987550D11819743846578888255')

    print(el1)
    time.sleep(300)
    el1 = worker.from_inspect_link(
        'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M5451025458192283279A22657987550D11819743846578888255')

    print(el1)

    el1 = worker.from_inspect_link(
        'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M5451025458192283279A22657987550D11819743846578888255')

    print(el1)
