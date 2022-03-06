import struct
from typing import Dict, List

FLOATNAMES: List[Dict] = [{'range': [0, 0.07],
                           'name': 'SFUI_InvTooltip_Wear_Amount_0'}, {
                              'range': [0.07, 0.15],
                              'name': 'SFUI_InvTooltip_Wear_Amount_1'}, {
                              'range': [0.15, 0.38],
                              'name': 'SFUI_InvTooltip_Wear_Amount_2'}, {
                              'range': [0.38, 0.45],
                              'name': 'SFUI_InvTooltip_Wear_Amount_3'}, {
                              'range': [0.45, 1.00],
                              'name': 'SFUI_InvTooltip_Wear_Amount_4'}]


def get_wear_name(floatvalue: float, csgo_english: dict) -> str:
    """
    Based on float, gets the correct wear value.
    :param csgo_english: csgo_english vdf parsed
    :param floatvalue: float value of the string, as float
    :return: Wear value, without parenthesis
    # if weapon has no float return ''
    """

    for categ in FLOATNAMES:
        if categ['range'][0] < floatvalue <= categ['range'][1]:
            return csgo_english[categ['name']]
    return ''


def get_full_item_name(iteminfo: dict, csgo_english: dict) -> str:
    """
    Function which adds data to the skin info retrieved from GC
    :param iteminfo: item info dict.
    :type csgo_english: csgo_english vdf parsed
    :rtype: str
    """
    name = ''

    # Default items have the "unique" quality
    if iteminfo['quality'] != 4:
        name += f"{iteminfo['quality_name']}"

    # Patch for items that are stattrak and unusual (ex. Stattrak Karambit)
    if iteminfo.get('killeatervalue') is not None and iteminfo['quality'] != 9:
        name += f" {csgo_english['strange']}"

    name += f" {iteminfo['weapon_type']} "

    if iteminfo['weapon_type'] in ['Sticker', 'Sealed Graffiti']:
        name += f"| {iteminfo['stickers'][0]['name']}"

    # Vanilla items have an item_name of '-'
    if iteminfo["item_name"] and iteminfo["item_name"] != '-':
        name += f"| {iteminfo['item_name']} "

    if iteminfo.get('wear_name') and iteminfo["item_name"] != '-':
        name += f"({iteminfo['wear_name']})"

    return name.strip()


def get_skin_data(iteminfo: dict, items_game: dict, csgo_english: dict, items_game_cdn: dict, schema: dict) -> dict:
    if iteminfo.get('paintwear'):
        floatvalue = struct.unpack('f', struct.pack('i', iteminfo['paintwear']))[0]
        if floatvalue:
            iteminfo['floatvalue'] = floatvalue

    # Get sticker codename/name
    iteminfo['paintindex'] = str(iteminfo['paintindex'])
    iteminfo['defindex'] = str(iteminfo['defindex'])

    stickerKits = items_game['sticker_kits']
    for sticker in iteminfo.get('stickers', []):
        kit = stickerKits[str(sticker['sticker_id'])]
        if not kit:
            continue

        sticker['codename'] = kit['name']
        sticker['material'] = kit['sticker_material']
        name = csgo_english[kit['item_name'].replace('#', '')]
        if sticker.get('tint_id'):
            attrib = f"Attrib_SprayTintValue_{sticker['tint_id']}"
            name += f' ({csgo_english[attrib]})'
        if name:
            sticker['name'] = name

    # Get the skin name
    skin_name = ''

    if iteminfo['paintindex'] in items_game['paint_kits']:
        skin_name = '_' + items_game['paint_kits'][iteminfo['paintindex']]['name']
        if skin_name == '_default':
            skin_name = ''

    # Get the weapon name
    weapon_name = ''
    if iteminfo['defindex'] in items_game['items']:
        weapon_name = items_game['items'][iteminfo['defindex']]['name']

    # Get the image url
    image_name = weapon_name + skin_name

    if image_name in items_game_cdn:
        iteminfo['imageurl'] = items_game_cdn[image_name]

    # Get the paint data and code name
    code_name = ''
    paint_data = {}

    if iteminfo['paintindex'] in items_game['paint_kits']:
        code_name = items_game['paint_kits'][iteminfo['paintindex']]['description_tag'].replace('#', '')
        paint_data = items_game['paint_kits'][iteminfo['paintindex']]

    # Get the min float
    if paint_data and 'wear_remap_min' in paint_data:
        iteminfo['min'] = float(paint_data['wear_remap_min'])
    else:
        iteminfo['min'] = 0.06

    # Get the max float
    if paint_data and 'wear_remap_max' in paint_data:
        iteminfo['max'] = float(paint_data['wear_remap_max'])
    else:
        iteminfo['max'] = 0.8

    weapon_data = {}

    if iteminfo['defindex'] in items_game['items']:
        weapon_data = items_game['items'][iteminfo['defindex']]

    # Get the weapon_hud
    weapon_hud = ''

    if weapon_data != '' and 'item_name' in weapon_data:
        weapon_hud = weapon_data['item_name'].replace('#', '')
    elif iteminfo['defindex'] in items_game['items']:
        # need to find the weapon hud from the prefab
        prefab_val = items_game['items'][iteminfo['defindex']]['prefab']
        weapon_hud = items_game['prefabs'][prefab_val]['item_name'].replace('#', '')
    if weapon_hud in csgo_english and code_name in csgo_english:
        iteminfo['weapon_type'] = csgo_english[weapon_hud]
        iteminfo['item_name'] = csgo_english[code_name]

    # # Get the rarity name (Mil-Spec Grade, Covert etc...)
    rarityKey = ''
    for k, v in items_game['rarities'].items():
        if v['value'] == str(iteminfo['rarity']):
            rarityKey = k
            break

    if rarityKey:
        rarity = items_game['rarities'][rarityKey]

        # Assumes weapons always have a float above 0 and that other items don't
        # Improve weapon check if this isn't robust
        if iteminfo.get('floatvalue', 0) > 0:
            iteminfo['rarity_name'] = csgo_english[rarity['loc_key_weapon']]
        else:
            iteminfo['rarity_name'] = csgo_english[rarity['loc_key']]
    # Get the quality name (Souvenir, Stattrak, etc...)
    qualityKey = ''
    for k, v in items_game['qualities'].items():
        if v['value'] == str(iteminfo['quality']):
            qualityKey = k
            break
    iteminfo['quality_name'] = csgo_english[qualityKey]
    #
    # Get the origin name
    origin = {}
    for w in schema['originNames']:
        if w['origin'] == iteminfo['origin']:
            origin = w
            break

    if origin:
        iteminfo['origin_name'] = origin['name']

    # Get the wear name
    wearName = get_wear_name(iteminfo.get('floatvalue', 0), csgo_english)
    if wearName:
        iteminfo['wear_name'] = wearName

    itemName = get_full_item_name(iteminfo, csgo_english)
    if itemName:
        iteminfo['full_item_name'] = itemName
    return iteminfo


def parse_items_cdn(data: str) -> dict:
    lines = data.split('\n')
    result = {}
    for line in lines:
        kv = line.split('=')
        if len(kv) > 1:
            result[kv[0]] = kv[1]

    return result
