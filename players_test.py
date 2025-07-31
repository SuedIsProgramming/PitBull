from nbtlib import parse_nbt
import os
import minescript as ms

def get_item_name(equipment_slot):
    """Safely get item name from equipment slot, return 'None' if empty."""
    if equipment_slot and 'id' in equipment_slot:
        return str(equipment_slot['id']).replace('minecraft:', '')
    return 'None'

ms.echo('working')
players_info = ms.players(nbt=True)
for player in players_info:
    nbt = parse_nbt(player.nbt)
    
    # Safely get equipment items
    equipment = nbt.get('equipment', {})
    head_item = get_item_name(equipment.get('head'))
    chest_item = get_item_name(equipment.get('chest'))
    legs_item = get_item_name(equipment.get('legs'))
    feet_item = get_item_name(equipment.get('feet'))
    health = player.health
    id = player.name
    
    ms.echo(f'Player at: {player.position} has equipment: {head_item}, {chest_item}, {legs_item}, {feet_item} and has {player.health} health of name {id}')