import os
import math
import time
import random
import logging
import threading
from log_parser import *
import nbtlib as nbt
import minescript as m # Minescript must be imported last!


# TODO: Fix border of pit targetting when nearest enemy is outside of pit. Fix getting stuck behind a wall for too long (perhaps a ban list to target someone else?) Automatic log_parsing

logger = logging.getLogger('PitBull_log') # Setup logging
logging.basicConfig(filename='minescript/pitbull/beta/pitbull_beta.log',
                    encoding='utf-8',
                    filemode='w',
                    level=logging.INFO,
                    format='[%(levelname)s: %(asctime)s] %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')

def player_look_at(coordinates, eye_height=1.62):
    """Look at the specified coordinates, adjusting for player eye height."""
    x, y, z = coordinates
    m.player_look_at(x, y + eye_height, z)

def in_attack_range(position, target, attack_distance):
    x_me, _, z_me = position
    x_targ, _, z_targ = target
    distance = math.hypot(x_me - x_targ, z_me - z_targ)
    return distance < attack_distance

def is_in_pit(pos, pit_center, pit_boundary):
    """Returns true if pos is within boundary of pit center."""
    x, y, z = pos
    center_x, center_y, center_z = pit_center
    
    within_x = abs(x - center_x) <= pit_boundary
    within_y = y - center_y <= 10 # Pit height should be set
    within_z = abs(z - center_z) <= pit_boundary
    
    return within_x and within_y and within_z
        
def task_smooth_look_at(pos, target_pos, steps): 

    x, y, z = pos
    y = y+1.62 # Adjust for camera being at feet
    x_target, y_target, z_target = target_pos

    start_yaw, start_pitch = m.player_orientation()

    # Calculate target yaw and pitch
    dx = x_target - x
    dy = y_target - y
    dz = z_target - z
    
    # Calculate horizontal distance for pitch calculation
    horizontal_distance = math.sqrt(dx**2 + dz**2)
    
    # Calculate target yaw (horizontal rotation)
    target_yaw = math.degrees(math.atan2(-dx, dz))
    
    # Calculate target pitch (vertical rotation)  
    target_pitch = math.degrees(math.atan2(-dy, horizontal_distance))
    
    # Normalize angles to handle wrapping (e.g., 359° to 1°)
    yaw_diff = normalize_angle_difference(target_yaw - start_yaw)
    pitch_diff = normalize_angle_difference(target_pitch - start_pitch)

    rotate_tasks = []

    for step in range(steps + 1):
        dyaw = yaw_diff / steps
        dpitch = pitch_diff / steps 
        current_yaw = start_yaw + (dyaw * step)
        current_pitch = start_pitch + (dpitch * step)
        rotate_tasks.append(m.player_set_orientation.as_task(current_yaw, current_pitch))

    m.run_tasks(rotate_tasks)

def smooth_look_at(pos, target_pos, steps): 

    x, y, z = pos
    x_target, y_target, z_target = target_pos

    start_yaw, start_pitch = m.player_orientation()

    # Calculate target yaw and pitch
    dx = x_target - x
    dy = y_target - y
    dz = z_target - z
    
    # Calculate horizontal distance for pitch calculation
    horizontal_distance = math.sqrt(dx**2 + dz**2)
    
    # Calculate target yaw (horizontal rotation)
    target_yaw = math.degrees(math.atan2(-dx, dz))
    
    # Calculate target pitch (vertical rotation)  
    target_pitch = math.degrees(math.atan2(-dy, horizontal_distance))
    
    # Normalize angles to handle wrapping (e.g., 359° to 1°)
    yaw_diff = normalize_angle_difference(target_yaw - start_yaw)
    pitch_diff = normalize_angle_difference(target_pitch - start_pitch)

    for step in range(steps + 1):
        dyaw = yaw_diff / steps
        dpitch = pitch_diff / steps 
        current_yaw = start_yaw + (dyaw * step)
        current_pitch = start_pitch + (dpitch * step)
        m.player_set_orientation(current_yaw, current_pitch)

def normalize_angle_difference(angle_diff):
    """
    Normalize angle difference to be between -180 and 180 degrees.
    This handles cases where we need to rotate from 350° to 10° (should go +20°, not -340°)
    """
    while angle_diff > 180:
        angle_diff -= 360
    while angle_diff < -180:
        angle_diff += 360
    return angle_diff

def advance():
    task = [m.player_press_forward.as_task(True),
            m.player_press_sprint.as_task(True),
            m.player_press_jump.as_task(True),
            m.player_press_attack.as_task(True),
            m.player_press_attack.as_task(False)]
    
    m.run_tasks(task)     

def get_item_name(equipment_slot):
    """Safely get item name from equipment slot, return 'None' if empty."""
    if equipment_slot and 'id' in equipment_slot:
        return str(equipment_slot['id']).replace('minecraft:', '')
    return 'None'

def has_equipped(player, item_names):
    try:
        parsed_nbt = nbt.parse_nbt(player.nbt)
        equipment = parsed_nbt.get('equipment', {})
        head_item = get_item_name(equipment.get('head'))
        chest_item = get_item_name(equipment.get('chest'))
        legs_item = get_item_name(equipment.get('legs'))
        feet_item = get_item_name(equipment.get('feet'))

        return any(item in [head_item, chest_item, legs_item, feet_item] for item in item_names)
    except Exception as e:
        return True

def sift_weakest(player, sift_level):
    if sift_level == 0:  # Use elif instead of if
        if not has_equipped(player,['golden_helmet','diamond_helmet','diamond_chestplate','diamond_leggings','diamond_boots']):
            return player, sift_level
        else:
            return None, sift_level + 1
    elif sift_level == 1:
        if not has_equipped(player,['golden_helmet','diamond_helmet','diamond_leggings']):
            return player, sift_level
        else:
            return None, sift_level + 1
    elif sift_level == 2:
        if not has_equipped(player,['golden_helmet']):
            return player, sift_level
        else:
            return None, sift_level + 1
    elif sift_level == 3:
        return player, sift_level
        
def sprint_jump(press=True):
    task = [m.player_press_forward.as_task(press),
                m.player_press_sprint.as_task(press),
                m.player_press_jump.as_task(press)]
    
    m.run_tasks(task)  

def run_to_pit(pit_center):
        global in_pit, moving
        not_moving_retries = 0
        while not in_pit and not errors:
            current_pos = m.player_position()
            smooth_look_at(current_pos,pit_center,4)
            if moving == False:
                sprint_jump(True)
                moving = True

def aim_at_closest_player(max_find_range,pit_center,pit_boundary):
    global in_pit, moving, errors, SMOOTHING_STEPS
    retries = 0
    sift_level = 0
    while in_pit and not errors:
        current_pos = m.player_position()
        players_arr = m.players(max_distance=max_find_range, sort='nearest',nbt=True)
        try:
            for player in players_arr[1:]:
                if is_in_pit(player.position,pit_center,pit_boundary):
                    closest_player, sift_level = sift_weakest(player,sift_level)
                    if closest_player is not None:
                        break

            closest_pos = closest_player.position
            smooth_look_at(current_pos,closest_pos,SMOOTHING_STEPS)
            if in_attack_range(current_pos,closest_pos,ATTACK_DISTANCE):
                m.player_press_jump(True)
            else:
                advance()
        except Exception as e:
            retries += 1
            if retries == MAX_ATTACK_RETRIES:
                errors = True
                logger.warning(f'Exception occured: {e}')
                logging.warning("Maximum number of retries reached while finding enemies")
            time.sleep(1)
        sift_level = 0

def aim_at_closest_entity(max_find_range): # For debugging
    global in_pit, moving, errors, SMOOTHING_STEPS
    retries = 0
    while in_pit and not errors:
        current_pos = m.player_position()
        entities_arr = m.entities(max_distance=max_find_range, sort='nearest')
        try:
            closest_player = entities_arr[1] # Because 0 is me
            closest_pos = closest_player.position
            smooth_look_at(current_pos,closest_pos,SMOOTHING_STEPS)
            if in_attack_range(current_pos,closest_pos,ATTACK_DISTANCE):
                m.player_press_jump(True)
            else:
                advance()
        except IndexError:
            retries += 1
            if retries == MAX_ATTACK_RETRIES:
                errors = True
                logging.warning("Maximum number of retries reached while finding enemies")
            time.sleep(1)
            pass

def swing():
    global in_pit

    interval = 0.0667  # seconds
    next_run = time.time()

    while in_pit:
        m.player_press_attack(True)
        m.player_press_attack(False)
        
        next_run += interval
        sleep_time = next_run - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            logging.warning('Swing interval is below 15 CPS!')

def swing_and_block():
    global in_pit

    interval = 0.0667  # seconds
    next_run = time.time()

    while in_pit:
        if random.random() < 0.2:
            task = [m.player_press_attack.as_task(True),
                    m.player_press_use.as_task(True),
                    m.player_press_attack.as_task(False),
                    m.player_press_use.as_task(False)]
            m.run_tasks(task)  
        else:
            m.player_press_attack(True)
            m.player_press_attack(False)

        next_run += interval
        sleep_time = next_run - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            logging.warning('Swing interval is below 15 CPS!')

def chat_log(): # Maybe can morph both of these into one?
    with m.EventQueue() as event_queue:
        event_queue.register_chat_listener()
        while True and not errors:
            event = event_queue.get()
            logging.info(event.message)

def key_listener():
    global errors, P_KEY
    with m.EventQueue() as event_queue:
        event_queue.register_key_listener()
        while True and not errors:
            event = event_queue.get()
            if event.key == P_KEY:
                errors = True
                logging.warning("P key has been pressed, stopping...")

def pitters_greater_than_threshold(pitters_threshold,pit_center,pit_boundary):
    pitters_arr = m.players(position=pit_center,max_distance=pit_boundary)
    pitters = len(pitters_arr) - 2 # -1 for indexing -1 for me
    return pitters >= pitters_threshold

def shimmy(pit_center):
    x,y,z = pit_center
    y=y+20
    player_look_at([x,y,z],eye_height=EYE_HEIGHT)
    m.player_press_left(True)
    time.sleep(random.random())
    m.player_press_left(False)
    time.sleep(2*random.random())
    m.player_press_right(True)
    time.sleep(random.random())
    m.player_press_right(False)
    time.sleep(2*random.random())

# ADJUSTABLE PARAMETERS

P_KEY = 80 # Found at (https://www.glfw.org/docs/3.4/group__keys.html)
PIT_CENTER_CASTLE = [0,71,0]
PIT_CENTER_MESA = [0,82,0]
PIT_BOUNDARY = 20
PITTERS_THRESHOLD = 5
EYE_HEIGHT = 1.62
MAX_FIND_RANGE = 23
ATTACK_DISTANCE = 2.3
MAX_ATTACK_RETRIES = 10
MAX_RUN_RETRIES = 500
SMOOTHING_STEPS = 8

# INITIALIZE VARIABLES

in_pit = False
errors = False
moving = False
prev_pos = [-69,-69,-69]

swing_thread = threading.Thread()
aim_at_closest_player_thread = threading.Thread()
aim_at_closest_entity_thread = threading.Thread()
run_to_pit_thread = threading.Thread()

# Initialize chat_log_thread
chat_log_thread = threading.Thread(target=chat_log,daemon=True)
chat_log_thread.start()

# Initialize key_listener:
key_listener_thread = threading.Thread(target=key_listener,daemon=True)
key_listener_thread.start()

while True and not errors:

    current_pos = m.player_position()

    if is_in_pit(current_pos,PIT_CENTER_MESA,PIT_BOUNDARY): # If in pit
        in_pit = True

        if not swing_thread.is_alive(): # Swing sword
            swing_thread = threading.Thread(target=swing, daemon=True)
            swing_thread.start()

        if not aim_at_closest_player_thread.is_alive(): # Target closest
            aim_at_closest_player_thread = threading.Thread(target=aim_at_closest_player,args=(MAX_FIND_RANGE,PIT_CENTER_MESA,PIT_BOUNDARY),daemon=True)
            aim_at_closest_player_thread.start()

    else: # If not
        in_pit = False
        if pitters_greater_than_threshold(PITTERS_THRESHOLD,PIT_CENTER_MESA,PIT_BOUNDARY):
            if not run_to_pit_thread.is_alive(): # Run to pit
                    run_to_pit_thread = threading.Thread(target=run_to_pit, args=(PIT_CENTER_MESA,),daemon=True)
                    run_to_pit_thread.start()
        else:
            time.sleep(0.1)
            sprint_jump(False)
            shimmy(PIT_CENTER_MESA)



    x1, _, z1 = current_pos
    x2, _, z2 = prev_pos

    if int(x1) == int(x2) and int(z1) == int(z2): # If position has not changed from previous
        moving = False
        not_moving_retries += 1 # Not moving retries (Increments really fast)
    else:
        not_moving_retries = 0

    if not_moving_retries == MAX_RUN_RETRIES:
        logging.warning("Maximum number of retries reached while running to pi")

    prev_pos = current_pos
    # logging.info(threading.active_count()) Gorgeous thread debugging
    # logging.info('==================================================================================================')
    # for thread in threading.enumerate():
    #     logging.info((f"- {thread.name} (Daemon: {thread.daemon}, Alive: {thread.is_alive()})"))
    # logging.info('==================================================================================================')

    log_path = r"C:\Users\Santi\curseforge\minecraft\Instances\Minescript\minescript\pitbull\beta\pitbull_beta.log"  # If in same directory as script
    # log_path = "minescript/pitbull_beta.log"  # If in minescript folder
    # log_path = "/full/path/to/pitbull_beta.log"  # Full absolute path

m.execute('/respawn')
time.sleep(0.1) # For respawn time
sprint_jump(False)

session_results = analyze_pitbull_log(log_path)
log_stats_report(session_results)
print_stats_report(session_results)
# if not aim_at_closest_entity_thread.is_alive(): # FOR DEBUGGING with mobs
#     aim_at_closest_entity_thread = threading.Thread(target=aim_at_closest_entity,args=(MAX_FIND_RANGE,),daemon=True)
#     aim_at_closest_entity_thread.start()