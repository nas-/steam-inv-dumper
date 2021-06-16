from unittest import TestCase
from floats_gc.float_utils import get_skin_data, parse_items_cdn
from floats_gc.worker_manager import FloatManager

kara_marble_fn_ff1 = {'itemid': 22156537897, 'defindex': 507, 'paintindex': 413, 'rarity': 6, 'quality': 3,
                      'paintwear': 1024596584, 'paintseed': 412, 'inventory': 72, 'origin': 8}
kara_marble_fn_ff1_parsed = {'itemid': 22156537897, 'defindex': '507', 'paintindex': '413', 'rarity': 6, 'quality': 3,
                             'paintwear': 1024596584, 'paintseed': 412, 'inventory': 72, 'origin': 8,
                             'floatvalue': 0.0356697142124176,
                             'imageurl': 'http://media.steampowered.com/apps/730/icons/econ/default_generated/weapon_knife_karambit_am_marble_fade_light_large.e5d0f471cc4aad8ddd6ede429afe8cd2d80c1cf2.png',
                             'min': 0.0, 'max': 0.08, 'weapon_type': 'Karambit', 'item_name': 'Marble Fade',
                             'rarity_name': 'Covert', 'quality_name': '★', 'origin_name': 'Found in Crate',
                             'wear_name': 'Factory New', 'full_item_name': '★ Karambit | Marble Fade (Factory New)'}
graffiti = {'itemid': 20810249592, 'defindex': 1348, 'paintindex': 0, 'rarity': 1, 'quality': 4,
            'stickers': [{'slot': 0, 'sticker_id': 1700, 'tint_id': 8}], 'inventory': 245, 'origin': 24}
graffiti_parsed = {'itemid': 20810249592, 'defindex': '1348', 'paintindex': '0', 'rarity': 1, 'quality': 4,
                   'stickers': [{'slot': 0, 'sticker_id': 1700, 'tint_id': 8, 'codename': 'spray_std_crown',
                                 'material': 'default/crown', 'name': 'King Me (Jungle Green)'}], 'inventory': 245,
                   'origin': 24, 'min': 0.06, 'max': 0.8, 'weapon_type': 'Sealed Graffiti', 'item_name': '-',
                   'rarity_name': 'Base Grade', 'quality_name': 'Unique', 'origin_name': 'Level Up Reward',
                   'full_item_name': 'Sealed Graffiti | King Me (Jungle Green)'}
stat_aug = {'itemid': 16188702872, 'defindex': 8, 'paintindex': 708, 'rarity': 3, 'quality': 9, 'paintwear': 1053882559,
            'paintseed': 781, 'killeaterscoretype': 0, 'killeatervalue': 7, 'inventory': 397, 'origin': 8}
stat_aug_parsed = {'itemid': 16188702872, 'defindex': '8', 'paintindex': '708', 'rarity': 3, 'quality': 9,
                   'paintwear': 1053882559, 'paintseed': 781, 'killeaterscoretype': 0, 'killeatervalue': 7,
                   'inventory': 397, 'origin': 8, 'floatvalue': 0.40814778208732605,
                   'imageurl': 'http://media.steampowered.com/apps/730/icons/econ/default_generated/weapon_aug_hy_aug_torn_orange_light_large.53b51a022d38ea39eff5ffbed92551dc741e17c3.png',
                   'min': 0.0, 'max': 0.55, 'weapon_type': 'AUG', 'item_name': 'Amber Slipstream',
                   'rarity_name': 'Mil-Spec Grade', 'quality_name': 'StatTrak™', 'origin_name': 'Found in Crate',
                   'wear_name': 'Well-Worn', 'full_item_name': 'StatTrak™ AUG | Amber Slipstream (Well-Worn)',
                   'special': None}
st_karmabit = {'itemid': 22657987550, 'defindex': 507, 'paintindex': 0, 'rarity': 6, 'quality': 3, 'paintwear': 1060247478, 'paintseed': 137, 'killeaterscoretype': 0, 'killeatervalue': 0, 'inventory': 3221225482, 'origin': 8}
st_krambit_parsed = {'itemid': 22657987550, 'defindex': '507', 'paintindex': '0', 'rarity': 6, 'quality': 3, 'paintwear': 1060247478, 'paintseed': 137, 'killeaterscoretype': 0, 'killeatervalue': 0, 'inventory': 3221225482, 'origin': 8, 'floatvalue': 0.6956743001937866, 'imageurl': 'http://media.steampowered.com/apps/730/icons/econ/weapons/base_weapons/weapon_knife_karambit.8b491b581a4b9c7b5298071425f2b29a39a2a12f.png', 'min': 0.06, 'max': 0.8, 'weapon_type': 'Karambit', 'item_name': '-', 'rarity_name': 'Covert', 'quality_name': '★', 'origin_name': 'Found in Crate', 'wear_name': 'Battle-Scarred', 'full_item_name': '★ StatTrak™ Karambit'}
fm = FloatManager()


# karambit marble fade FN FFI
class TestCSGOWorker(TestCase):
    maxDiff = None

    def test_parse_item_data(self):
        data = get_skin_data(kara_marble_fn_ff1, fm.items_game, fm.csgo_english, fm.items_game_cdn, fm.schema)

        self.assertDictEqual(data, kara_marble_fn_ff1_parsed)

        graff = get_skin_data(graffiti, fm.items_game, fm.csgo_english, fm.items_game_cdn, fm.schema)
        self.assertDictEqual(graff, graffiti_parsed)
        kara = get_skin_data(st_karmabit, fm.items_game, fm.csgo_english, fm.items_game_cdn, fm.schema)
        self.assertDictEqual(st_krambit_parsed, kara)
