"""Weapon definitions per class. Each call builds a fresh Weapon with fresh skills."""
import random

from inventory_mechanics.weapon import Weapon
from skills.skill_library import get_skill

# name: (class, stat_bonus, max_hp_bonus, skills, description)
_WEAPONS = {
    "Iron Sword":     ("Swordsman", 2, 0, ["Slash", "Parry", "Heavy Strike", "Second Wind"], "A reliable blade."),
    "Flame Brand":    ("Swordsman", 2, 0, ["Flame Slash", "Parry", "Heavy Strike", "Battle Cry"], "Its edge never cools."),
    "Frostbite":      ("Swordsman", 1, 5, ["Frost Edge", "Iron Wall", "Twin Cut", "Second Wind"], "Numbs all it touches."),
    "Viper Fang":     ("Swordsman", 1, 0, ["Venom Stab", "Twin Cut", "Parry", "Sunder"], "Drips with venom."),
    "Crusader Blade": ("Swordsman", 3, 10, ["Holy Blade", "Shield Bash", "Sunder", "Whirlwind"], "Blessed by the old order."),

    "Novice Staff":   ("Sorcerist", 1, 0, ["Fireball", "Mana Shield", "Magic Missile", "Heal"], "A student's first staff."),
    "Ember Staff":    ("Sorcerist", 2, 0, ["Fireball", "Ignite", "Mana Shield", "Arcane Surge"], "Warm to the touch."),
    "Glacier Wand":   ("Sorcerist", 1, 5, ["Ice Lance", "Frost Nova", "Mana Shield", "Heal"], "Frost gathers on its tip."),
    "Tome of Blight": ("Sorcerist", 1, 0, ["Toxic Cloud", "Hex", "Magic Missile", "Radiance"], "Its pages rot."),
    "Storm Scepter":  ("Sorcerist", 3, 5, ["Chain Lightning", "Meteor", "Radiance", "Hex"], "Crackles with power."),
}

STARTING_WEAPONS = {"Swordsman": "Iron Sword", "Sorcerist": "Novice Staff"}


def get_weapon(name: str) -> Weapon:
    _, bonus, hp, skills, desc = _WEAPONS[name]
    tier = 0 if name in STARTING_WEAPONS.values() else (2 if bonus >= 3 else 1)
    return Weapon(name, bonus, [get_skill(s) for s in skills], desc, hp, tier)


def random_weapons(char_class: str, count: int, exclude: str = "") -> list[Weapon]:
    pool = [n for n, data in _WEAPONS.items() if data[0] == char_class and n != exclude]
    return [get_weapon(n) for n in random.sample(pool, min(count, len(pool)))]
