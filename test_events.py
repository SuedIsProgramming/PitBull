import time
import queue  # Import queue module
import minescript as ms
from minescript import EventType

with ms.EventQueue() as eq:
    eq.register_key_listener()
    
    while True:
        ATTACK = "key.attack"
        ms.press_key_bind(ATTACK, True)
        ms.press_key_bind(ATTACK, False)
        
        try:
            event = eq.get(block=False)
            if event.type == EventType.KEY:
                ms.echo('Key encountered, stopping...')
                break
        except queue.Empty:  # Catch the specific exception
            pass  # No event available, continue the loop
            
        time.sleep(0.05)