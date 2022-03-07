import logging
import re

import arrow
from csgo.client import CSGOClient
from csgo.enums import ECsgoGCMsg, EGCBaseClientMsg, GCConnectionStatus
# pip install git+https://github.com/wearefair/protobuf-to-dict
from protobuf_to_dict import protobuf_to_dict
from steam.client import SteamClient
from db.db import GCItem

from floats_gc import const
from floats_gc.float_utils import get_skin_data

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

        @client.on('disconnected')
        def client_disconnected() -> None:
            logger.info('Disconnected from GC')
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
                logger.debug('Launching CSGO again')
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
        # Send heartbeat to check if sessions are alive?
        logger.debug('Sending heartbeat')
        self.csgo.send(EGCBaseClientMsg.EMsgGCClientHello)
        self.csgo.wait_event('csgo_welcome')
        logger.debug('received event')

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
            logger.debug(f"found {iteminfo['item_name']=}")
            try:
                special = const.marbles[iteminfo['weapon_type']].get(str(iteminfo['paintseed']))
            except KeyError:
                logger.info('Non-indexed %s | Marble Fade' % iteminfo['weapon_type'])
        elif iteminfo['item_name'] == "Fade" and iteminfo['weapon_type'] in const.fades:
            logger.debug(f"found {iteminfo['item_name']=}")
            info = const.fades[iteminfo['weapon_type']]
            unscaled = const.order[::info[1]].index(iteminfo['paintseed'])
            scaled = unscaled / 1001
            percentage = round(info[0] + scaled * (100 - info[0]))
            special = str(percentage) + "%"
        elif iteminfo['item_name'] in ["Doppler", "Gamma Doppler"]:
            logger.debug(f"found {iteminfo['item_name']=}")
            special = const.doppler.get(iteminfo['paintindex'])
            if not special:
                phases = ['phase1', 'phase2', 'phase3', 'phase4', 'ruby_marbleized', 'sapphire_marbleized',
                          'blackpearl', 'emerald_marbleized']
                url = iteminfo.get('imageurl')
                if url:
                    for phase in phases:
                        if phase in url:
                            logging.info(
                                f"{iteminfo.get('full_item_name')} paintindex {iteminfo['paintindex']} is {phase}")
                            break

        iteminfo['special'] = special
        return iteminfo

    def get_item(self, s: int, a: int, d: int, m: int) -> dict:
        """
        # Get relevant information and returns it.
        :rtype: object
        """
        item_db = GCItem.query_ref(asset_id=str(a)).all()
        if not item_db:
            logger.info(f'Item  {a} not in db')
            self.last_run = arrow.now().timestamp()
            iteminfo = self._send(s, a, d, m)
            item = GCItem(asset_id=a,
                          itemid=iteminfo.get('itemid'),
                          defindex=iteminfo.get('defindex'),
                          paintindex=iteminfo.get('paintindex'),
                          paintwear=iteminfo.get('paintwear'),
                          paintseed=iteminfo.get('paintseed'),
                          killeaterscoretype=iteminfo.get('killeaterscoretype'),
                          killeatervalue=iteminfo.get('killeatervalue'),
                          inventory=iteminfo.get('inventory'),
                          origin=iteminfo.get('origin'),
                          rarity=iteminfo.get('rarity'),
                          quality=iteminfo.get('quality'),
                          )
            GCItem.query.session.add(item)
            GCItem.query.session.flush()
        elif len(item_db) == 1:
            logger.info(f'item {a} was found in DB')
            iteminfo = item_db[0].to_json()
        else:
            logger.info(f'This should not be happening item {a}')
            raise Exception
        return self.parse_item_data(iteminfo)

    def from_inspect_link(self, url: str) -> dict:
        logger.debug(f'Retieving float value trugh account {self._logon_details.get("username")}')
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
            self.busy = False
        return {'success': True, 'data': iteminfo}

    @property
    def username(self) -> str:
        return self._logon_details.get('username', '')
