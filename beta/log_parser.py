import re
from datetime import datetime
from typing import Dict, Any

def analyze_pitbull_log(log_file_path: str) -> Dict[str, Any]:
    """
    Analyzes a PitBull log file and calculates combat statistics.
    
    Args:
        log_file_path: Path to the log file
        
    Returns:
        Dictionary containing all calculated statistics
    """
    stats = {
        'deaths': 0,
        'kills': 0,
        'assists': 0,
        'total_gold': 0.0,
        'total_exp': 0,
        'gold_pickups': 0.0,
        'bounties_claimed': 0.0,
        'executions': 0,
        'session_duration_minutes': 0.0,
        'session_duration_total': '',
        'exp_per_minute': 0.0,
        'gold_per_minute': 0.0,
        'kda_ratio': 0.0,
        'kill_death_ratio': 0.0,
        'timestamps': []
    }
    
    # Regex patterns for different events
    patterns = {
        'death': r'Â§cÂ§lDEATH!',
        'kill': r'Â§aÂ§lKILL!',
        'xp_from_kill': r'Â§b\+(\d+)XP',
        'gold_from_kill': r'Â§6\+Â§6([\d.]+)g',
        'assist': r'Â§aÂ§lASSIST!',
        'gold_pickup': r'GOLD PICKUP!.*?([\d.]+)g',
        'bounty_claimed': r'BOUNTY CLAIMED!.*?for ([\d,]+)g',
        'execution': r'EXECUTED!',
        'timestamp': r'\[INFO: (\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2} [AP]M)\]'
    }
    
    try:
        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
            
        # Extract timestamps to calculate session duration
        timestamp_matches = re.findall(patterns['timestamp'], content)
        if timestamp_matches:
            stats['timestamps'] = timestamp_matches
            start_time = datetime.strptime(timestamp_matches[0], '%m/%d/%Y %I:%M:%S %p')
            end_time = datetime.strptime(timestamp_matches[-1], '%m/%d/%Y %I:%M:%S %p')
            duration_seconds = (end_time - start_time).total_seconds()
            stats['session_duration_minutes'] = duration_seconds / 60
            
            # Format total time as HH:MM:SS
            hours = int(duration_seconds // 3600)
            minutes = int((duration_seconds % 3600) // 60)
            seconds = int(duration_seconds % 60)
            stats['session_duration_total'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # Count deaths and executions
        regular_deaths = len(re.findall(patterns['death'], content))
        executions = len(re.findall(patterns['execution'], content))
        stats['deaths'] = regular_deaths + executions  # Executions count as deaths
        stats['executions'] = executions
        
        # Count kills
        stats['kills'] = len(re.findall(patterns['kill'], content))
        
        # Count assists  
        stats['assists'] = len(re.findall(patterns['assist'], content))
        
        # Extract XP and gold from combat (kills and assists)
        # We need to find lines that contain either KILL or ASSIST to avoid interference
        lines = content.split('\n')
        for line in lines:
            if 'Â§aÂ§lKILL!' in line or 'Â§aÂ§lASSIST!' in line:
                print(f"DEBUG - Processing line: {line}")  # Debug output
                
                # Extract XP from this combat line
                xp_match = re.search(patterns['xp_from_kill'], line)
                if xp_match:
                    xp_value = int(xp_match.group(1))
                    print(f"DEBUG - Found XP: {xp_value}")  # Debug output
                    stats['total_exp'] += xp_value
                else:
                    print("DEBUG - No XP match found")  # Debug output
                
                # Extract gold from this combat line  
                gold_match = re.search(patterns['gold_from_kill'], line)
                if gold_match:
                    gold_value = float(gold_match.group(1))
                    print(f"DEBUG - Found gold: {gold_value}")  # Debug output
                    stats['total_gold'] += gold_value
                else:
                    print("DEBUG - No gold match found")  # Debug output
                print("---")  # Separator
        
        # Count gold pickups (separate from combat gold to avoid interference)
        gold_pickup_matches = re.findall(patterns['gold_pickup'], content)
        for gold in gold_pickup_matches:
            pickup_amount = float(gold)
            stats['gold_pickups'] += pickup_amount
            stats['total_gold'] += pickup_amount
        
        # Count bounty claims
        bounty_matches = re.findall(patterns['bounty_claimed'], content)
        for bounty in bounty_matches:
            bounty_amount = float(bounty.replace(',', ''))
            stats['bounties_claimed'] += bounty_amount
            stats['total_gold'] += bounty_amount
        
        # Calculate rates and ratios
        if stats['session_duration_minutes'] > 0:
            stats['exp_per_minute'] = stats['total_exp'] / stats['session_duration_minutes']
            stats['gold_per_minute'] = stats['total_gold'] / stats['session_duration_minutes']
        
        if stats['deaths'] > 0:
            stats['kill_death_ratio'] = stats['kills'] / stats['deaths']
            stats['kda_ratio'] = (stats['kills'] + stats['assists']) / stats['deaths']
        else:
            # Handle case where no deaths occurred
            stats['kill_death_ratio'] = stats['kills'] if stats['kills'] > 0 else 0
            stats['kda_ratio'] = (stats['kills'] + stats['assists']) if (stats['kills'] + stats['assists']) > 0 else 0
            
    except FileNotFoundError:
        print(f"Error: Could not find log file at {log_file_path}")
        return stats
    except Exception as e:
        print(f"Error reading log file: {e}")
        return stats
    
    return stats

def print_stats_report(stats: Dict[str, Any]) -> None:
    """Prints a formatted report of the statistics."""
    
    print("=" * 50)
    print("PITBULL PERFORMANCE REPORT")
    print("=" * 50)
    
    # Combat Stats
    print(f"Deaths:           {stats['deaths']} (includes {stats['executions']} executions)")
    print(f"Kills:            {stats['kills']}")
    print(f"Assists:          {stats['assists']}")
    print()
    
    # Ratios
    print(f"Kill/Death Ratio: {stats['kill_death_ratio']:.2f}")
    print(f"KDA Ratio:        {stats['kda_ratio']:.2f}")
    print()
    
    # Economy
    print(f"Total Gold:       {stats['total_gold']:.2f}g")
    print(f"  - From Kills:   {stats['total_gold'] - stats['gold_pickups'] - stats['bounties_claimed']:.2f}g")
    print(f"  - From Pickups: {stats['gold_pickups']:.2f}g") 
    print(f"  - From Bounties:{stats['bounties_claimed']:.2f}g")
    print(f"Total EXP:        {stats['total_exp']}")
    print()
    
    # Rates
    if stats['session_duration_minutes'] > 0:
        print(f"Session Duration: {stats['session_duration_total']} ({stats['session_duration_minutes']:.1f} minutes)")
        print(f"EXP/minute:       {stats['exp_per_minute']:.1f}")
        print(f"Gold/minute:      {stats['gold_per_minute']:.1f}g")
        print()
        
        # Additional useful rates
        print(f"Kills/minute:     {stats['kills'] / stats['session_duration_minutes']:.2f}")
        print(f"Deaths/minute:    {stats['deaths'] / stats['session_duration_minutes']:.2f}")
    
    print("=" * 50)

# Example usage:
if __name__ == "__main__":
    # Replace with your actual log file path
    log_path = r"pitbull\beta\log_parser.py"
    
    results = analyze_pitbull_log(log_path)
    print_stats_report(results)
    
    # You can also access individual stats:
    # print(f"You earned {results['total_gold']:.2f} gold this session!")

# import re
# from datetime import datetime
# from typing import Dict, Any

# def analyze_pitbull_log(log_file_path: str) -> Dict[str, Any]:
#     """
#     Analyzes a PitBull log file and calculates combat statistics.
    
#     Args:
#         log_file_path: Path to the log file
        
#     Returns:
#         Dictionary containing all calculated statistics
#     """
#     stats = {
#         'deaths': 0,
#         'kills': 0,
#         'assists': 0,
#         'total_gold': 0.0,
#         'total_exp': 0,
#         'gold_pickups': 0.0,
#         'bounties_claimed': 0.0,
#         'executions': 0,
#         'session_duration_minutes': 0.0,
#         'session_duration_total': '',
#         'exp_per_minute': 0.0,
#         'gold_per_minute': 0.0,
#         'kda_ratio': 0.0,
#         'kill_death_ratio': 0.0,
#         'timestamps': []
#     }
    
#     # Regex patterns for different events
#     patterns = {
#         'death': r'Â§cÂ§lDEATH!',
#         'kill': r'Â§aÂ§lKILL!',
#         'xp_from_kill': r'Â§b\+(\d+)XP',
#         'gold_from_kill': r'Â§6\+Â§6([\d.]+)g',
#         'assist': r'Â§aÂ§lASSIST!',
#         'gold_pickup': r'GOLD PICKUP!.*?([\d.]+)g',
#         'bounty_claimed': r'BOUNTY CLAIMED!.*?for ([\d,]+)g',
#         'execution': r'EXECUTED!',
#         'timestamp': r'\[INFO: (\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2} [AP]M)\]'
#     }
    
#     try:
#         with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as file:
#             content = file.read()
            
#         # Extract timestamps to calculate session duration
#         timestamp_matches = re.findall(patterns['timestamp'], content)
#         if timestamp_matches:
#             stats['timestamps'] = timestamp_matches
#             start_time = datetime.strptime(timestamp_matches[0], '%m/%d/%Y %I:%M:%S %p')
#             end_time = datetime.strptime(timestamp_matches[-1], '%m/%d/%Y %I:%M:%S %p')
#             duration_seconds = (end_time - start_time).total_seconds()
#             stats['session_duration_minutes'] = duration_seconds / 60
            
#             # Format total time as HH:MM:SS
#             hours = int(duration_seconds // 3600)
#             minutes = int((duration_seconds % 3600) // 60)
#             seconds = int(duration_seconds % 60)
#             stats['session_duration_total'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
#         # Count deaths and executions
#         regular_deaths = len(re.findall(patterns['death'], content))
#         executions = len(re.findall(patterns['execution'], content))
#         stats['deaths'] = regular_deaths + executions  # Executions count as deaths
#         stats['executions'] = executions
        
#         # Count kills
#         stats['kills'] = len(re.findall(patterns['kill'], content))
        
#         # Count assists  
#         stats['assists'] = len(re.findall(patterns['assist'], content))
        
#         # Extract XP and gold from combat (kills and assists)
#         # We need to find lines that contain either KILL or ASSIST to avoid interference
#         lines = content.split('\n')
#         for line in lines:
#             if 'Â§aÂ§lKILL!' in line or 'Â§aÂ§lASSIST!' in line:
#                 # Extract XP from this combat line
#                 xp_match = re.search(patterns['xp_from_kill'], line)
#                 if xp_match:
#                     stats['total_exp'] += int(xp_match.group(1))
                
#                 # Extract gold from this combat line  
#                 gold_match = re.search(patterns['gold_from_kill'], line)
#                 if gold_match:
#                     stats['total_gold'] += float(gold_match.group(1))
        
#         # Count gold pickups (separate from combat gold to avoid interference)
#         gold_pickup_matches = re.findall(patterns['gold_pickup'], content)
#         for gold in gold_pickup_matches:
#             pickup_amount = float(gold)
#             stats['gold_pickups'] += pickup_amount
#             stats['total_gold'] += pickup_amount
        
#         # Count bounty claims
#         bounty_matches = re.findall(patterns['bounty_claimed'], content)
#         for bounty in bounty_matches:
#             bounty_amount = float(bounty.replace(',', ''))
#             stats['bounties_claimed'] += bounty_amount
#             stats['total_gold'] += bounty_amount
        
#         # Calculate rates and ratios
#         if stats['session_duration_minutes'] > 0:
#             stats['exp_per_minute'] = stats['total_exp'] / stats['session_duration_minutes']
#             stats['gold_per_minute'] = stats['total_gold'] / stats['session_duration_minutes']
        
#         if stats['deaths'] > 0:
#             stats['kill_death_ratio'] = stats['kills'] / stats['deaths']
#             stats['kda_ratio'] = (stats['kills'] + stats['assists']) / stats['deaths']
#         else:
#             # Handle case where no deaths occurred
#             stats['kill_death_ratio'] = stats['kills'] if stats['kills'] > 0 else 0
#             stats['kda_ratio'] = (stats['kills'] + stats['assists']) if (stats['kills'] + stats['assists']) > 0 else 0
            
#     except FileNotFoundError:
#         print(f"Error: Could not find log file at {log_file_path}")
#         return stats
#     except Exception as e:
#         print(f"Error reading log file: {e}")
#         return stats
    
#     return stats

# def print_stats_report(stats: Dict[str, Any]) -> None:
#     """Prints a formatted report of the statistics."""
    
#     print("=" * 50)
#     print("PITBULL PERFORMANCE REPORT")
#     print("=" * 50)
    
#     # Combat Stats
#     print(f"Deaths:           {stats['deaths']} (includes {stats['executions']} executions)")
#     print(f"Kills:            {stats['kills']}")
#     print(f"Assists:          {stats['assists']}")
#     print()
    
#     # Ratios
#     print(f"Kill/Death Ratio: {stats['kill_death_ratio']:.2f}")
#     print(f"KDA Ratio:        {stats['kda_ratio']:.2f}")
#     print()
    
#     # Economy
#     print(f"Total Gold:       {stats['total_gold']:.2f}g")
#     print(f"  - From Kills:   {stats['total_gold'] - stats['gold_pickups'] - stats['bounties_claimed']:.2f}g")
#     print(f"  - From Pickups: {stats['gold_pickups']:.2f}g") 
#     print(f"  - From Bounties:{stats['bounties_claimed']:.2f}g")
#     print(f"Total EXP:        {stats['total_exp']}")
#     print()
    
#     # Rates
#     if stats['session_duration_minutes'] > 0:
#         print(f"Session Duration: {stats['session_duration_total']} ({stats['session_duration_minutes']:.1f} minutes)")
#         print(f"EXP/minute:       {stats['exp_per_minute']:.1f}")
#         print(f"Gold/minute:      {stats['gold_per_minute']:.1f}g")
#         print()
        
#         # Additional useful rates
#         print(f"Kills/minute:     {stats['kills'] / stats['session_duration_minutes']:.2f}")
#         print(f"Deaths/minute:    {stats['deaths'] / stats['session_duration_minutes']:.2f}")
    
#     print("=" * 50)

# # Example usage:
# if __name__ == "__main__":
#     # Replace with your actual log file path
#     log_path = r"pitbull\beta\log_parser.py"
    
#     results = analyze_pitbull_log(log_path)
#     print_stats_report(results)
    
#     # You can also access individual stats:
#     # print(f"You earned {results['total_gold']:.2f} gold this session!")


# r"pitbull\beta\log_parser.py"