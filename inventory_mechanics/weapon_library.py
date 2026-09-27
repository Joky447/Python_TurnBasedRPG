"""Weapons and boss drops. Each call builds a fresh Item with fresh skills."""
import os
import re

import assets

from inventory_mechanics.item import Item
from skills.skill_library import get_skill

ICON_DIR = "items/"   # optional art for other items: items/<item name>.png (drawn placeholder icons otherwise)

# name: (class, damage, max_hp, skills, description)
_WEAPONS = {
    "Iron Sword":     ("Swordsman", 2, 0, ["Slash", "Parry", "Heavy Strike", "Second Wind"], "A reliable metal blade."),
    "Aurora Greatsword": ("Swordsman", 4, 5, ["Heavy Strike", "Whirlwind", "Parry", "Sunder"],
                          "The blade of the Aurora Knight set."),

    "Novice Staff":   ("Sorcerist", 1, 0, ["Fireball", "Mana Shield", "Magic Missile", "Heal"], "A student's first wand."),
    "Astral Wand":    ("Sorcerist", 4, 5, ["Fireball", "Ice Lance", "Mana Shield", "Arcane Surge"],
                       "The wand of the Astral Sage set."),
    "Astral Scythe":  ("Sorcerist", 6, 5, ["Chain Lightning", "Meteor", "Hex", "Radiance"],
                       "The final form of the Astral Sage set."),
}

STARTING_WEAPONS = {"Swordsman": "Iron Sword", "Sorcerist": "Novice Staff"}
# Only the starting weapons and the prepared floor rewards below exist; no other items are made.


def get_weapon(name: str, gender: str | None = None) -> Item:
    char_class, dmg, hp, skills, desc = _WEAPONS[name]
    tier = 0 if name in STARTING_WEAPONS.values() else (2 if dmg >= 3 else 1)
    stats = {"damage": dmg, "max_hp": hp, "max_energy": 1 if name == "Astral Scythe" else 0}
    return Item(name, "Weapon", stats, icon_for(name, gender, char_class), desc,
                [get_skill(s) for s in skills], char_class, tier, set_name=set_of(name, char_class))


# The prepared reward for each floor, per class, given right before that floor's boss
# (art in character/<...> inventory/).
# These are also the outfit pieces: great weapon -> armor -> helmet -> shield.
# floor: (name, type, stats, description) -- a name found in _WEAPONS is a weapon.
_GEAR = {
    "Swordsman": {
        1: ("Aurora Greatsword",),
        2: ("Aurora Plate", "Armor", {"max_hp": 20, "block": 2}, "Armor of the Aurora Knight set."),
        3: ("Aurora Helm", "Helmet", {"max_hp": 10, "block": 2}, "Helm of the Aurora Knight set."),
        4: ("Aurora Aegis", "Shield", {"block": 4, "max_hp": 5}, "Shield of the Aurora Knight set."),
        5: ("Aurora Wings", "Wings", {"max_energy": 1, "damage": 2}, "The final form of the Aurora Knight set."),
    },
    "Sorcerist": {
        1: ("Astral Wand",),
        2: ("Astral Robes", "Armor", {"max_hp": 15, "damage": 1}, "Robes of the Astral Sage set."),
        3: ("Astral Mask", "Helmet", {"max_hp": 8, "damage": 1}, "Mask of the Astral Sage set."),
        4: ("Astral Aura", "Shield", {"block": 3, "max_hp": 5}, "Aura of the Astral Sage set."),
        5: ("Astral Scythe",),
    },
}
# The girl swordsman's helmet is a mask
_NAME_BY_GENDER = {("Girl", "Swordsman", "Aurora Helm"): "Aurora Mask"}

# Each class's floor rewards form one set. The set's pieces only work while its weapon is
# equipped; with the starting weapon they are disabled (see Player.item_active).
SET_NAMES = {"Swordsman": "Aurora Knight", "Sorcerist": "Astral Sage"}

# Older saves used these names
RENAMED = {"Great Sword": "Aurora Greatsword", "Knight's Armor": "Aurora Plate", "Frost King's Helm": "Aurora Helm",
           "Frost King's Mask": None, "Grove Shield": "Aurora Aegis", "Seraph Wings": "Aurora Wings",
           "Great Wand": "Astral Wand", "Arcane Robes": "Astral Robes", "Grove Aura": "Astral Aura",
           "Infernal Scythe": "Astral Scythe"}


def current_name(name: str, char_class: str, gender: str | None) -> str:
    """An item's name in this version of the game (older saves used other names)."""
    if name == "Frost King's Mask":
        return "Aurora Mask" if char_class == "Swordsman" else "Astral Mask"
    return RENAMED.get(name) or name


def set_of(name: str, char_class: str | None) -> str | None:
    """The set an item belongs to, or None for the starting weapons."""
    if char_class and any(_floor_of(name, char_class, g) is not None for g in ("Boy", "Girl")):
        return SET_NAMES.get(char_class)
    return None

# Item art: one folder per character; each file has its floor number in the name
# (e.g. "reward before fighting floor 2 boss.png"), so files can be renamed freely.
_ICON_FOLDERS = {("Boy", "Swordsman"): "character/boy sword inventory/",
                 ("Girl", "Swordsman"): "character/girl sword inventory/",
                 ("Boy", "Sorcerist"): "character/boymage inventory/",
                 ("Girl", "Sorcerist"): "character/girl mage inventory/"}


def _art_by_floor(folder: str) -> dict[int, str]:
    full = os.path.join(assets.BASE_DIR, folder)
    found = {}
    if os.path.isdir(full):
        for file in sorted(os.listdir(full)):
            digits = re.findall(r"[1-5]", file)
            if file.lower().endswith(".png") and digits:
                found.setdefault(int(digits[0]), folder + file)
    return found


def _floor_of(name: str, char_class: str, gender: str | None) -> int | None:
    for floor, gear in _GEAR.get(char_class, {}).items():
        if _NAME_BY_GENDER.get((gender, char_class, gear[0]), gear[0]) == name:
            return floor
    return None


def is_known_item(name: str, char_class: str, gender: str | None) -> bool:
    """True for the starting weapons and the prepared floor rewards: the only items in the game."""
    return name in STARTING_WEAPONS.values() or _floor_of(name, char_class, gender) is not None


def icon_for(name: str, gender: str | None, char_class: str | None) -> str:
    """This character's art for a floor reward, or items/<name>.png for the starting weapons."""
    folder = _ICON_FOLDERS.get((gender, char_class))
    floor = _floor_of(name, char_class, gender) if folder else None
    art = _art_by_floor(folder).get(floor) if floor else None
    return art or ICON_DIR + name + ".png"


def floor_gear(floor: int, char_class: str, gender: str) -> Item | None:
    """The gear item found on `floor` by this character."""
    gear = _GEAR.get(char_class, {}).get(floor)
    if not gear:
        return None
    if len(gear) == 1:
        return get_weapon(gear[0], gender)
    name, kind, stats, desc = gear
    name = _NAME_BY_GENDER.get((gender, char_class, name), name)
    return Item(name, kind, stats, icon_for(name, gender, char_class), desc, char_class=char_class,
                set_name=SET_NAMES.get(char_class))
