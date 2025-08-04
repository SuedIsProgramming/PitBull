import os
import time
import math
import queue
import logging
from nbtlib import parse_nbt
from minescript import EventType
import minescript as ms

logger = logging.getLogger('PitBully_log')

# Configuration
PIT_CENTER = [0, 0, 0]
PIT_BOUNDARY = 5
LOOP_RATE = 0.1  # 10 times per second
EYE_HEIGHT = 1.62  # Player eye height offset
P_KEY = 80 # Found at (https://www.glfw.org/docs/3.4/group__keys.html)
TOUGHNESS_THRESHOLD = 15 + 10 # Corresponds to chainmail boots + pants + maybe iron chestplate
ATTACKING_DISTANCE = 1
MAX_WEAKNESS_RETRIES = 10
COMBAT_DISTANCE = 15
ATTACK = "key.attack"
MY_NAME = 'TheMajesticSiud'

def player_look_at(coordinates):
    """Look at the specified coordinates, adjusting for player eye height."""
    x, y, z = coordinates
    ms.player_look_at(x, y + EYE_HEIGHT, z)

def distance_from_me(coordinates):
    x_me, y_me, z_me = ms.player_position()
    x, y, z = coordinates
    distance = math.sqrt((x_me - x)**2 + (y_me - y)**2 + (z_me - z)**2)
    return distance

def sprint_jump_to(coordinates, is_active=True, advance = None):
    """Sprint and jump toward the specified coordinates."""
    player_look_at(coordinates)
    if advance:
        ms.player_press_forward(advance)
    else:
        ms.player_press_forward(is_active)
    ms.player_press_sprint(is_active)
    ms.player_press_jump(is_active)

def sprint_jump_and_attack(coordinates, is_active=True):
    player_look_at(coordinates)
    
    if distance_from_me(coordinates) > ATTACKING_DISTANCE:
        sprint_jump_to(coordinates, is_active, advance=True)
        ms.press_key_bind(ATTACK, is_active)
    else:
        sprint_jump_to(coordinates, is_active, advance=False)
        ms.press_key_bind(ATTACK, is_active)

def is_in_pit(coordinates):
    """Check if the player is within the pit boundaries."""
    x, y, z = coordinates
    return abs(x) < PIT_BOUNDARY and abs(z) < PIT_BOUNDARY

def handle_key_event(event_queue):
    """Check for key press events and return True if one is detected."""
    try:
        event = event_queue.get(block=False)
        if event.type == EventType.KEY:
            ms.echo(f'Key press detected: {event.key}')
            return True
    except queue.Empty:
        pass
    return False

def handle_chat_event(event_queue):
    """Check for key press events and return True if one is detected."""
    try:
        event = event_queue.get(block=False)
        if event.type == EventType.CHAT:
            ms.echo(f'Chat message detected: {event.message}')
            return True
    except queue.Empty:
        pass
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
        'diamond_helmet': 3,
        'diamond_chestplate': 8,
        'diamond_leggings': 6,
        'diamond_boots': 3,
        
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
            # Remove minecraft: prefix if present
            if 'leather' in item.lower():
                total_protection += 50
            else:
                total_protection += armor_protection.get(item, 0)

    toughness_score = total_protection + (health * 0.5)

    return round(toughness_score, 3)

# MAIN STEPS

def run_to_pit(event_queue):
    """Take gladiator to pit."""
    
    start_time = time.time()
    
    # Start movement once
    
    sprint_jump_to(PIT_CENTER, True)
    
    while not is_in_pit(current_position):
        # Check for manual stop via key press
        if handle_key_event(event_queue):
            ms.echo('Stopping due to key press')
            sprint_jump_to(PIT_CENTER, False, False)
            return False
        
        # Only update look direction, not movement
        player_look_at(PIT_CENTER)
        
        # Update position
        current_position = ms.player_position()
        
        # Check if we've reached the pit
        if is_in_pit(current_position):
            ms.echo('I am in the pit! Stopping movement')
            sprint_jump_to(PIT_CENTER, False)
            break
        
        time.sleep(LOOP_RATE)
    
    ms.echo('Gladiator is in pit')
    return True

def look_for_weakest(event_queue):
    retry_count = 0
    while retry_count < MAX_WEAKNESS_RETRIES:
        # Check for manual stop via key press
        if handle_key_event(event_queue):
            ms.echo('Stopping due to key press')
            return False # Exit the function instead of break
        
        players_info = ms.players(nbt=True,max_distance=COMBAT_DISTANCE,sort='nearest')
        for player in players_info:
            if player.name != MY_NAME:
                nbt = parse_nbt(player.nbt)
                
                # Safely get equipment items
                equipment = nbt.get('equipment', {})
                head_item = get_item_name(equipment.get('head'))
                chest_item = get_item_name(equipment.get('chest'))
                legs_item = get_item_name(equipment.get('legs'))
                feet_item = get_item_name(equipment.get('feet'))
                health = player.health
                name = player.name

                # Evaluate player toughness
                toughness = measure_toughness(head_item, chest_item, legs_item, feet_item, health)
                ms.echo(f'toughness of player: {name} is {toughness}')
                if toughness < TOUGHNESS_THRESHOLD:
                    ms.echo(f'Since toughness is less than threshold, setting as target')
                    return name
        else:
            ms.echo('Cannot find weak players. Wait 1 second before trying again')
            retry_count += 1
            # ms.execute('/respawn')
            time.sleep(1)

    ms.execute('/respawn')
    return None

def murder(event_queue, target):
    players_info = ms.players(nbt=True,max_distance=COMBAT_DISTANCE,sort='nearest')
    target_player = None
    for player in players_info:
        if player.name == target.name:
            target_player = player
            break
    else: # Even if you break out of a for loop, this else will not activate. Else only activate if the for loop has been exhausted natuarlly
        ms.echo('Target not found, looking for new one')
        return False
    
    target_coords = target_player.position

    while distance_from_me(target_coords) < COMBAT_DISTANCE:
        # Check for manual stop via key press
        if handle_key_event(event_queue):
            ms.echo('Stopping due to key press')
            sprint_jump_and_attack(TARGET_POSITION, False)
            return  # Exit the function instead of break
        
        sprint_jump_and_attack(target_coords,True)
        time.sleep(LOOP_RATE)
