import logging

logger = logging.getLogger('PitBull_log') # Setup logging
logging.basicConfig(filename='minescript/PitBull.log',
                    encoding='utf-8',
                    filemode='w',
                    level=logging.DEBUG,
                    format='[%(levelname)s: %(asctime)s] %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')

import time
from pitbull_utils import *
from pitbull.pitbull_alpha.async_look_at_utils import *
import minescript as ms # Minescript must be imported last!

P_KEY = 80 # Found at (https://www.glfw.org/docs/3.4/group__keys.html)

# Adjustable Parameters
MAX_TARGET_RETRIES = 10 # Maximum retries while looking for players
MAX_TARGET_DISTANCE = 20 # Maximum volume to scan for targets
RUN_TO_PIT_TIMEOUT = 20 # Seconds before timeout in run_to_pit()
TOUGHNESS_THRESHOLD = 15 + 10 # Corresponds to chainmail boots + pants + maybe iron chestplate
ATTACKING_DISTANCE = 2.5 # Distance at which to attack target
RETRY_WAIT_TIME = 1 # Wait time before retrying to search in seconds
PIT_CENTER = [0,71,0]
PIT_BOUNDARY = 20 # How large is the pit

logging.info('Begin PitBull Alpha')

with ms.EventQueue() as event_queue:

    logging.debug('Initialized EventQueue')
    event_queue.register_key_listener()
    logging.debug('Initialized key listener')
    event_queue.register_chat_listener()
    logging.debug('Intitialized chat listener')

    moving = False
    target_retries = 0
    logging.info('Entering main loop')
    while True:
        loop_start_t = time.time()
        if target_retries >= MAX_TARGET_RETRIES:
            logging.warning('MAX TARGET RETRIES REACHED, STOPPING')
            sprint_jump_to(PIT_CENTER, False)
            logging.debug('RTP:sprint + jump + forward are released')
            break
        
        handle_chat_event(event_queue)
        if handle_key_event(event_queue):
            sprint_jump_to(PIT_CENTER, False)
            logging.debug('RTP:sprint + jump + forward are released')
            break

        position = ms.player_position()
        # logging.debug(f'height is: y={position[1]:.1f}')
        # if position[1] > 90: # If above pit, make pit boundary smaller to increase time falling:
        #     logging.debug('Above pit, will make pit boundary smaller')
        #     PIT_BOUNDARY = 1
        # else:
        #     PIT_BOUNDARY = 10
        if not is_in_pit(position,PIT_BOUNDARY=PIT_BOUNDARY,PIT_CENTER=PIT_CENTER):
            logging.info('Not in pit! Will begin run_to_pit()')
            run_to_pit_success = run_to_pit(position,event_queue,timeout=RUN_TO_PIT_TIMEOUT,PIT_BOUNDARY = PIT_BOUNDARY)
            if not run_to_pit_success:
                #ms.execute('/respawn')
                break
        else:
            moving = False
            target_pos = find_weakest_target(MAX_TARGET_DISTANCE,PIT_CENTER=PIT_CENTER,target_closest=True)# find_weakest_target(MAX_TARGET_DISTANCE,TOUGHNESS_THRESHOLD,PIT_CENTER=PIT_CENTER)
            if target_pos is not None:
                    target_retries = 0 # Reset target retries
                    if distance_from_me_2d(target_pos) > ATTACKING_DISTANCE:
                        logging.info('Target is too far away, running closer')
                        if moving == False: # If I am not moving, advance
                            sprint_jump_to(target_pos,advance=True)
                            logging.debug('Not moving: sprint + jump + forward are being held down')
                            ms.player_press_attack(True)
                            ms.player_press_attack(False)
                            moving = True
                        else: # If I am already moving, swing
                            logging.debug('Moving, no need to refire sprint_jump_to()')
                            smooth_player_look_at_fast_async(target_pos)
                            ms.player_press_attack(True)
                            ms.player_press_attack(False)
                    else: 
                        logging.info('Target is within reach, attacking')
                        sprint_jump_to(target_pos,advance=False)
                        logging.debug('sprint + jump are being held down')
                        ms.player_press_attack(True)
                        ms.player_press_attack(False)
                        moving = False
            else:
                target_retries += 1
                ms.player_press_forward(False)
                ms.player_press_sprint(False)
                ms.player_press_jump(False)
                logging.debug('sprint + jump + forward are released')
                moving = False
                logging.debug('Sleeping for a second')
                time.sleep(RETRY_WAIT_TIME)
        
        loop_end_t = time.time()

        logging.debug(f'Loop time = {loop_end_t-loop_start_t} s')
        # time.sleep(LOOP_RATE)

        