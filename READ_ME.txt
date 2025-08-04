ALPHA WORKFLOW:

> Setup event_queue:
>> Register_key_listener() # Will make it so event.get() will get latest event of keystroke

While True:

	> If event is registered, break

	> worked = run_to_pit(event_queue):

		>> get at current position
		>> If gladiator is in pit: return True
		>> Hold down run, jump, forward
		>> While gladiator is not in pit:

			>>> If event is registered: Release run, jumo, forward and return False
			>>> update look direction
			>>> update current position
			>>> If gladiator is in pit: Release run, jump, forward and break
			>>> wait 0.1 seconds

		>> return True
	
	> If not worked: break
 
	> target_name = look_for_weakest(event_queue):
		
		>> retry count = 0
		>> While retry count > maximum retries:
			>>> If event is registered: return False
			>>> Obtain players info
			>>> For players:
				>>>> if name of player is not my name:
					>>>>> Obtain nbt data from players: helmet, chest plate, pants, shoes, health, name
					>>>>> measure toughness using measure_toughness() function
					>>>>> if toughness < some threshold: return name
			>>> else if for loop exhausted: 
				>>>> retry count += 1
				>>>> Wait 1 second
		>> /respawn # This means that the while loop exhausted. Could not find weak players in 10 retries, probably due to dead server
		>> return None
	> If target_name is Flase: break
	> If target_name is None: print(could not find weak players)
	> If target_name is not None: murder(event_queue, target_name)

		>> Go into how murder works
		
BETA WORKFLOW:

Pitbull Beta uses threading to mainstream a lot of these features. The workflow is pretty explanatory from just reading the documentation. So far, Pitbull Beta has the same functionalities
as PitBull alpha but flows much quicker. Pitbull Beta also reads ALL chat messages, allowing for potential log scraping for session analyses

