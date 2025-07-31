import gladiator_utils as utils

import minescript as ms


ms.echo('Begin Gladiator Alpha') 
with ms.EventQueue() as event_queue:
    event_queue.register_key_listener()
    
    while True:

        if utils.handle_key_event(event_queue):
            ms.echo('Stopping due to key press')
            break  # Exit the function instead of break
        
        run_to_pit_worked = utils.run_to_pit(event_queue)
        if not run_to_pit_worked:
            break

        target_name = utils.look_for_weakest(event_queue)
        if target_name is False:
            break
        if target_name is None:
            ms.echo('Could not find weak players in alloted retry_counts')
        else:
            utils.murder(event_queue, target_name)

        


