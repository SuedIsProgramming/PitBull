import logging

logger = logging.getLogger('PitBull_log')

import math
import time
import queue
from nbtlib import parse_nbt
from async_look_at_utils import *
import minescript as ms # Minescript must be imported last!

PIT_BOUNDARY = 5 # Pit boundary for running towards pit
EYE_HEIGHT = 1.62  # Player eye height offset
LOOP_RATE = 0.05 # 20 times a second
P_KEY = 80
MY_NAME = 'TheMajesticSiud'

def handle_key_event(event_queue,loc='main'):
    """Check for key press events and return True if one is detected."""
    try:
        event = event_queue.get(block=False)
        if event.type == ms.EventType.KEY:
            if event.key == P_KEY:
                logging.info(f'{loc}:P key detected, stopping')
                return True
    except queue.Empty:
        pass
    return False

def handle_chat_event(event_queue):
    """Check for chat messages and return True if one is detected."""
    try:
        event = event_queue.get(block=False)
        if event.type == ms.EventType.CHAT:
            logging.info(f'Chat message detected: {event.message}')
            return True
    except queue.Empty:
        pass
    return False

def is_in_pit(coordinates, PIT_BOUNDARY = 7, PIT_CENTER = [0,71,0]):
    """Check if the player is within the pit boundaries."""
    x, y, z = coordinates
    x_pit, y_pit, z_pit = PIT_CENTER
    y_from_pit = y - y_pit
    return abs(x) < PIT_BOUNDARY and abs(y_from_pit) < 10 and abs(z) < PIT_BOUNDARY

def player_look_at(coordinates):
    """Look at the specified coordinates, adjusting for player eye height."""
    x, y, z = coordinates
    ms.player_look_at(x, y + EYE_HEIGHT, z)

def sprint_jump_to(coordinates, is_active=True, advance = None):
    """Sprint and jump toward the specified coordinates."""
    smooth_player_look_at_fast_async(coordinates)
    if advance is not None:
        ms.player_press_forward(advance)
    else:
        ms.player_press_forward(is_active)
    ms.player_press_sprint(is_active)
    ms.player_press_jump(is_active)

def run_to_pit(position, event_queue, timeout = 20, PIT_CENTER = [0,71,0], PIT_BOUNDARY = 7):
    """Take gladiator to pit."""


    prev_position = [-6969,0,6969]
    current_position = position
    start_time = time.time()
    
    if is_in_pit(current_position,PIT_BOUNDARY=PIT_BOUNDARY,PIT_CENTER=PIT_CENTER):
        logging.debug('RTP:already in pit, exiting')
        return True

    # Start movement once
    sprint_jump_to(PIT_CENTER, True)
    logging.debug('RTP:sprint + jump + forward are being held down')
    
    while not is_in_pit(current_position,PIT_BOUNDARY=PIT_BOUNDARY,PIT_CENTER=PIT_CENTER):

        x = current_position[0]
        z = current_position[2]
        logging.debug(f'Position is [{x:.1f},{z:.1f}]')

        current_time = time.time()
        if current_time - start_time > timeout:
            logging.error('RTP:COULD NOT RETURN TO PIT IN GIVEN TIMEOUT. STOPPING')
            sprint_jump_to(PIT_CENTER, False)
            logging.debug('RTP:sprint + jump + forward are released')
            break

        handle_chat_event(event_queue)
        # Check for manual stop via key press
        if handle_key_event(event_queue,loc='RTP'):
            sprint_jump_to(PIT_CENTER, False)
            logging.debug('RTP:sprint + jump + forward are released')
            return False

        curr_x, _, curr_z = current_position
        prev_x, _, prev_z = prev_position

        # If I not moving, will attempt to run again
        if current_position == prev_position:
            logging.warning('Not moving, will attempt to run again')
            sprint_jump_to(PIT_CENTER, True)

        # Only update look direction, not movement
        smooth_player_look_at_fast_async(PIT_CENTER)

        # Update position
        prev_position = current_position
        current_position = ms.player_position()
        
        # Check if we've reached the pit
        if is_in_pit(current_position):
            logging.info('RTP:In pit, stopping movement')
            #sprint_jump_to(PIT_CENTER, False)
            #logging.debug('RTP:sprint + jump + forward are released') Dont need to stop once in pit
            return True
        
        time.sleep(LOOP_RATE)
    
    logging.warning('RTP:Either timed out or P key was pressed, either way, stopping')
    return False



def get_item_name(equipment_slot):
    """Safely get item name from equipment slot, return 'None' if empty."""
    if equipment_slot and 'id' in equipment_slot:
        return str(equipment_slot['id']).replace('minecraft:', '')
    return 'None'

def measure_toughness(head_item, chest_item, legs_item, feet_item, health):
    """
    Calculate a toughness value based on armor protection and health.
    Lower values = weaker/more vulnerable player
    Higher values = more protected/stronger player
    
    Armor protection values (defense points):
    - Diamond: Head=3, Chest=8, Legs=6, Feet=3 (Total: 20)
    - Iron: Head=2, Chest=6, Legs=5, Feet=2 (Total: 15) 
    - Chainmail: Head=2, Chest=5, Legs=4, Feet=1 (Total: 12)
    - None/Air: 0 protection
    """
    
    # Armor protection values by type and slot
    armor_protection = {
        'diamond_helmet': 30,
        'diamond_chestplate': 80,
        'diamond_leggings': 100,
        'diamond_boots': 30,
        
        'iron_helmet': 2,
        'iron_chestplate': 6,
        'iron_leggings': 5,
        'iron_boots': 2,
        
        'chainmail_helmet': 2,
        'chainmail_chestplate': 5,
        'chainmail_leggings': 4,
        'chainmail_boots': 1,
    }
    total_protection = 0
    for item in [head_item, chest_item, legs_item, feet_item]:
        if item and item != 'None':
            
            if 'leather' in item:
                total_protection += 50
            else:
                total_protection += armor_protection.get(item, 0)

    logging.debug(f'MT:Total protection is: {total_protection} and health is {health}')

    if health is None: # Required, because when you kill a player, their health will be None for a split second
        health = 0

    toughness_score = total_protection * (health/20) # Should modify later

    return round(toughness_score, 3)

def find_weakest_target(MAX_TARGET_DISTANCE=20, TOUGHNESS_THRESHOLD=25,PIT_CENTER=[0,71,0],target_closest=False):

    players_info = ms.players(nbt=True,max_distance=MAX_TARGET_DISTANCE,sort='nearest')
    for player in players_info:
        if player.name != MY_NAME:
            try:
                nbt = parse_nbt(player.nbt)
                
                # Safely get equipment items
                equipment = nbt.get('equipment', {})
                head_item = get_item_name(equipment.get('head'))
                chest_item = get_item_name(equipment.get('chest'))
                legs_item = get_item_name(equipment.get('legs'))
                feet_item = get_item_name(equipment.get('feet'))
                health = player.health
                name = player.name
                position = player.position

                if target_closest:
                    return position
                else:
                    # Evaluate player toughness
                    toughness = measure_toughness(head_item, chest_item, legs_item, feet_item, health)
                    logging.info(f'FWT:toughness of player: {name} is {toughness} with equipment: {head_item}, {chest_item}, {legs_item}, {feet_item} and health: {health}')
                    if toughness < TOUGHNESS_THRESHOLD:
                        logging.info(f'FWT:Since toughness is less than threshold, setting {name} as target')
                        return position
                
            except Exception as e:
                logging.warning(f'FWT:NBT parsing failed for player {player.name}: {type(e).__name__}. Skipping player.')
                continue

    logging.info('FWT:Cannot find weak players. Wait 1 second before trying again')
    smooth_player_look_at_fast_async(PIT_CENTER)
    #ms.execute('/respawn')
    return None

def find_weakest_entity(MAX_TARGET_DISTANCE=20, TOUGHNESS_THRESHOLD=25,PIT_CENTER=[0,71,0]):

    entities_info = ms.entities(nbt=True,max_distance=MAX_TARGET_DISTANCE,sort='nearest')
    for entity in entities_info:
        if entity.name != MY_NAME:
            nbt = parse_nbt(entity.nbt)
            
            # Safely get equipment items
            equipment = nbt.get('equipment', {})
            head_item = get_item_name(equipment.get('head'))
            chest_item = get_item_name(equipment.get('chest'))
            legs_item = get_item_name(equipment.get('legs'))
            feet_item = get_item_name(equipment.get('feet'))
            health = entity.health
            name = entity.name
            position = entity.position

            # Evaluate player toughness
            toughness = measure_toughness(head_item, chest_item, legs_item, feet_item, health)
            #ms.echo(f'Aiming at: {name} with {toughness} toughness with equipment: {head_item}, {chest_item}, {legs_item}, {feet_item} and health: {health}')
            logging.info(f'FWT:toughness of player: {name} is {toughness} with equipment: {head_item}, {chest_item}, {legs_item}, {feet_item} and health: {health}')
            if toughness < TOUGHNESS_THRESHOLD:
                logging.info(f'FWT:Since toughness is less than threshold, setting {name} as target')
                return position
            
    logging.info('FWT:Cannot find weak players. Wait 1 second before trying again')
    smooth_player_look_at_fast_async(PIT_CENTER)
    ms.execute('/respawn')
    return None

def distance_from_me_2d(coordinates):
    x_me, y_me, z_me = ms.player_position()
    x, y, z = coordinates
    distance = math.sqrt((x_me - x)**2 + (z_me - z)**2)
    return distance

    