import math
import time
import logging
import threading
import minescript as m # Minescript must be imported last!

logger = logging.getLogger('PitBull_log') # Setup logging
logging.basicConfig(filename='minescript/pitbull/beta/pitbull_beta.log',
                    encoding='utf-8',
                    filemode='w',
                    level=logging.INFO,
                    format='[%(levelname)s: %(asctime)s] %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')

def player_look_at(coordinates, eye_height):
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

def sprint_jump(press=True):
    task = [m.player_press_forward.as_task(press),
                m.player_press_sprint.as_task(press),
                m.player_press_jump.as_task(press)]
    
    m.run_tasks(task)  

def run_to_pit(pit_center):
        global in_pit, moving
        not_moving_retries = 0
        while not in_pit:
            current_pos = m.player_position()
            smooth_look_at(current_pos,pit_center,4)
            if moving == False:
                sprint_jump(True)
                moving = True

def aim_at_closest_player(max_find_range):
    global in_pit, moving, errors, SMOOTHING_STEPS
    retries = 0
    while in_pit:
        current_pos = m.player_position()
        players_arr = m.players(max_distance=max_find_range, sort='nearest')
        try:
            closest_player = players_arr[1] # Because 0 is me
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
                raise Exception("Maximum number of retries reached while finding enemies")
            time.sleep(1)
            pass

def aim_at_closest_entity(max_find_range): # For debugging
    global in_pit, moving, errors, SMOOTHING_STEPS
    retries = 0
    while in_pit:
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
                raise Exception("Maximum number of retries reached while finding enemies")
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

def chat_log_thread():
    with m.EventQueue() as event_queue:
        event_queue.register_chat_listener()
        while True:
            event = event_queue.get()
            logging.info(event.message)

# ADJUSTABLE PARAMETERS

PIT_CENTER = [0,71,0]
PIT_BOUNDARY = 20
EYE_HEIGHT = 1.62
MAX_FIND_RANGE = 23
ATTACK_DISTANCE = 2
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

chat_log_thread = threading.Thread(target=chat_log_thread,daemon=True)
chat_log_thread.start()

while True and not errors:

    current_pos = m.player_position()

    if is_in_pit(current_pos,PIT_CENTER,PIT_BOUNDARY): # If in pit
        in_pit = True

        if not swing_thread.is_alive(): # Swing sword
            swing_thread = threading.Thread(target=swing, daemon=True)
            swing_thread.start()

        if not aim_at_closest_player_thread.is_alive(): # Target closest
            aim_at_closest_player_thread = threading.Thread(target=aim_at_closest_player,args=(MAX_FIND_RANGE,),daemon=True)
            aim_at_closest_player_thread.start()

    else: # If not
        in_pit = False

        if not run_to_pit_thread.is_alive(): # Run to pit
                run_to_pit_thread = threading.Thread(target=run_to_pit, args=(PIT_CENTER,),daemon=True)
                run_to_pit_thread.start()



    x1, _, z1 = current_pos
    x2, _, z2 = prev_pos

    if int(x1) == int(x2) and int(z1) == int(z2): # If position has not changed from previous
        moving = False
        not_moving_retries += 1 # Not moving retries (Increments really fast)
    else:
        not_moving_retries = 0

    if not_moving_retries == MAX_RUN_RETRIES:
        raise Exception("Maximum number of retries reached while running to pi")

    prev_pos = current_pos
    
m.execute(r'\respawn')
sprint_jump(False)



# if not aim_at_closest_entity_thread.is_alive(): # FOR DEBUGGING with mobs
#     aim_at_closest_entity_thread = threading.Thread(target=aim_at_closest_entity,args=(MAX_FIND_RANGE,),daemon=True)
#     aim_at_closest_entity_thread.start()