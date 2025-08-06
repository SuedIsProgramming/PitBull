import re
import logging

logger = logging.getLogger('PitBull_log') # Setup logging

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
        'bounty_claimed': r'BOUNTY CLAIMED! \[\d+\] TheMajesticSiud killed.*?for ([\d,]+)g',
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
                # Extract XP from this combat line
                xp_match = re.search(patterns['xp_from_kill'], line)
                if xp_match:
                    stats['total_exp'] += int(xp_match.group(1))
                
                # Extract gold from this combat line  
                gold_match = re.search(patterns['gold_from_kill'], line)
                if gold_match:
                    stats['total_gold'] += float(gold_match.group(1))
        
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

# def echo_stats_report(stats: Dict[str, Any]) -> None:
#     """Prints a formatted report of the statistics."""
    
#     m.echo("=" * 50)
#     m.echo("PITBULL PERFORMANCE REPORT")
#     m.echo("=" * 50)
    
#     # Combat Stats
#     m.echo(f"Deaths:           {stats['deaths']} (includes {stats['executions']} executions)")
#     m.echo(f"Kills:            {stats['kills']}")
#     m.echo(f"Assists:          {stats['assists']}")
#     m.echo()
    
#     # Ratios
#     m.echo(f"Kill/Death Ratio: {stats['kill_death_ratio']:.2f}")
#     m.echo(f"KDA Ratio:        {stats['kda_ratio']:.2f}")
#     m.echo()
    
#     # Economy
#     m.echo(f"Total Gold:       {stats['total_gold']:.2f}g")
#     m.echo(f"  - From Kills:   {stats['total_gold'] - stats['gold_pickups'] - stats['bounties_claimed']:.2f}g")
#     m.echo(f"  - From Pickups: {stats['gold_pickups']:.2f}g") 
#     m.echo(f"  - From Bounties:{stats['bounties_claimed']:.2f}g")
#     m.echo(f"Total EXP:        {stats['total_exp']}")
#     m.echo()
    
#     # Rates
#     if stats['session_duration_minutes'] > 0:
#         m.echo(f"Session Duration: {stats['session_duration_total']} ({stats['session_duration_minutes']:.1f} minutes)")
#         m.echo(f"EXP/minute:       {stats['exp_per_minute']:.1f}")
#         m.echo(f"Gold/minute:      {stats['gold_per_minute']:.1f}g")
#         m.echo()
        
#         # Additional useful rates
#         m.echo(f"Kills/minute:     {stats['kills'] / stats['session_duration_minutes']:.2f}")
#         m.echo(f"Deaths/minute:    {stats['deaths'] / stats['session_duration_minutes']:.2f}")
    
#     m.echo("=" * 50)

def log_stats_report(stats: Dict[str, Any]) -> None:
    """Prints a formatted report of the statistics."""
    
    logging.info("=" * 50)
    logging.info("PITBULL PERFORMANCE REPORT")
    logging.info("=" * 50)
    
    # Combat Stats
    logging.info(f"Deaths:           {stats['deaths']} (includes {stats['executions']} executions)")
    logging.info(f"Kills:            {stats['kills']}")
    logging.info(f"Assists:          {stats['assists']}")
    logging.info('\n')
    
    # Ratios
    logging.info(f"Kill/Death Ratio: {stats['kill_death_ratio']:.2f}")
    logging.info(f"KDA Ratio:        {stats['kda_ratio']:.2f}")
    logging.info('\n')
    
    # Economy
    logging.info(f"Total Gold:       {stats['total_gold']:.2f}g")
    logging.info(f"  - From Kills:   {stats['total_gold'] - stats['gold_pickups'] - stats['bounties_claimed']:.2f}g")
    logging.info(f"  - From Pickups: {stats['gold_pickups']:.2f}g") 
    logging.info(f"  - From Bounties:{stats['bounties_claimed']:.2f}g")
    logging.info(f"Total EXP:        {stats['total_exp']}")
    logging.info('\n')
    
    # Rates
    if stats['session_duration_minutes'] > 0:
        logging.info(f"Session Duration: {stats['session_duration_total']} ({stats['session_duration_minutes']:.1f} minutes)")
        logging.info(f"EXP/minute:       {stats['exp_per_minute']:.1f}")
        logging.info(f"Gold/minute:      {stats['gold_per_minute']:.1f}g")
        logging.info('\n')
        
        # Additional useful rates
        logging.info(f"Kills/minute:     {stats['kills'] / stats['session_duration_minutes']:.2f}")
        logging.info(f"Deaths/minute:    {stats['deaths'] / stats['session_duration_minutes']:.2f}")
    
    logging.info("=" * 50)

# # Example usage:
# if __name__ == "__main__":
#     # Try different possible paths for your log file:
#     import os
#     os.chdir(r'C:\Users\Santi\curseforge\minecraft\Instances\Minescript\minescript\pitbull\beta')
#     possible_paths = [
#         "pitbull_beta.log",
#         "minescript/pitbull_beta.log", 
#         "../pitbull_beta.log",
#         "logs/pitbull_beta.log"
#     ]
    
#     log_path = None
#     for path in possible_paths:
#         if os.path.exists(path):
#             log_path = path
#             print(f"Found log file at: {path}")
#             break
    
#     if log_path is None:
#         print("Could not find pitbull_beta.log file. Please specify the correct path.")
#         print("Current directory contents:")
#         print(os.listdir("."))
#         log_path = input("Enter the full path to your pitbull_beta.log file: ")
    
#     results = analyze_pitbull_log(log_path)
#     print_stats_report(results)
    
    # You can also access individual stats:
    # print(f"You earned {results['total_gold']:.2f} gold this session!")