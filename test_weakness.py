import minescript as ms

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

ms.echo("Full diamond, full health:", measure_toughness('diamond_helmet', 'diamond_chestplate', 'diamond_leggings', 'diamond_boots', 20))
ms.echo("Full iron, full health:", measure_toughness('iron_helmet', 'iron_chestplate', 'iron_leggings', 'iron_boots', 20))
ms.echo("Mixed armor, low health:", measure_toughness('diamond_helmet', 'iron_chestplate', 'None', 'chainmail_boots', 5))
ms.echo("No armor, low health:", measure_toughness('None', 'None', 'None', 'None', 3))
ms.echo("No armor, full health:", measure_toughness('None', 'None', 'None', 'None', 20))
ms.echo("Leather armor (weak target):", measure_toughness('leather_helmet', 'iron_chestplate', 'leather_leggings', 'diamond_boots', 20))