# # test.py:

import minescript as ms
import math
import time
players = ms.players()

EYE_HEIGHT = 1.62 
ATTACKING_DISTANCE = 1
ATTACK = "key.attack"

def player_look_at(coordinates):
    """Look at the specified coordinates, adjusting for player eye height."""
    x, y, z = coordinates
    ms.player_look_at(x, y + EYE_HEIGHT, z)

def distance_from_me(coordinates):
    x_me, y_me, z_me = ms.player_position()
    x, y, z = coordinates
    distance = math.sqrt((x_me - x)**2 + (y_me - y)**2 + (z_me - z)**2)
    return distance

def sprint_jump_to(coordinates, is_active=True, advance = True):
    """Sprint and jump toward the specified coordinates."""
    player_look_at(coordinates)
    ms.player_press_forward(advance)
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



while True:
    entities = ms.entities(max_distance=15)
    target = None
    for entity in entities:
        ms.echo(entity)
        if entity.name == 'Creeper':
            target = entity
            break
    target_pos = target.position
    sprint_jump_and_attack(target_pos)
    time.sleep(0.05)

# import minescript as ms

# def player_look_at(coord_arr):
#     ms.player_look_at(coord_arr[0],
#                       coord_arr[1]+1.62, # add 1.62 to y direction to obtain an azimuth of 0
#                       coord_arr[2])

# # ATTACK = "key.attack"
# # minescript.press_key_bind(ATTACK, True)

# entities = ms.entities(max_distance = 10, sort = 'nearest')

# entities_loc = tuple([entity.position for entity in entities])

# print(entities_loc)

# ms.echo(f'looking at entity 1: {entities[1].name}')
# player_look_at(entities_loc[1])


# # # Write a message to the chat that only you can see:
# # minescript.echo("Hello, world!")

# # # Write a chat message that other players can see:
# # minescript.chat("Hello, everyone!")

# # # Get your player's current position:
# # x, y, z = minescript.player_position()

# # # Set the block directly beneath your player:
# # x, y, z = int(x), int(y), int(z)
# # minescript.execute(f"setblock {x} {y-1} {z} yellow_concrete")

# # # Print the type of block at a particular location:
# # minescript.echo(minescript.getblock(x, y, z))

# # # Display the contents of your inventory:
# # for item_stack in minescript.player_inventory():
# #   minescript.echo(item_stack.item)

# # # Display the names of nearby entities:
# # for entity in minescript.entities():
# #   minescript.echo(entity.name)