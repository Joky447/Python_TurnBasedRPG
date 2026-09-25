"""Enemy templates per floor, and the factory that builds a scaled Enemy for an encounter."""
import random

from mobs_boss.enemy import Enemy
from skills.skill import Skill as S

F1, F2 = "mobs_boss/floor1/", "mobs_boss/floor2/"

# Sprite sheet layouts: clip -> (path, columns, rows, frame count or None for all)
GOBLIN_ANIM = {
    "idle":   (F1 + "goblin1 idle animation.png", 5, 2, None),
    "attack": (F1 + "goblin1.png", 5, 2, None),
    "hurt":   (F1 + "Goblin 1 Hurting.png", 5, 2, None),
}
ARCHER_ANIM = {
    "attack": (F1 + "goblin2.png", 5, 2, None),
    "hurt":   (F1 + "Goblin 2 Hurting.png", 5, 2, None),
}
SHAMAN_ANIM = {
    "idle":   (F1 + "boss1 idle animation.png", 5, 2, None),
    "attack": (F1 + "boss.png", 5, 2, None),
    "hurt":   (F1 + "Boss1 Hurting.png", 5, 2, None),
}
CASTLE_ARCHER_ANIM = {
    "idle":   (F2 + "knight1 idle animation.png", 5, 2, None),
    "attack": (F2 + "knight1.png", 4, 1, None),
}
KNIGHT_ANIM = {"attack": (F2 + "knight2.png", 4, 1, None)}
PRIEST_ANIM = {"attack": (F2 + "priest3.png", 4, 1, None)}
PALADIN_ANIM = {
    "idle":   (F2 + "Floor 2 Boss idle animation.png", 5, 2, None),
    "attack": (F2 + "floor2boss.png", 5, 2, None),
    "hurt":   (F2 + "Floor 2 Boss Hurting.png", 5, 2, None),
}

# Each template: hp, anim, height (on-screen px), moves (built fresh each time), pattern, tint
TEMPLATES = {
    # ---------- Floor 1: Goblins ----------
    "Goblin": dict(hp=34, anim=GOBLIN_ANIM, height=230, moves=lambda: [
        S("Stab", damage=7),
        S("Frenzy", damage=3, hits=2),
        S("Cower", block=6),
    ]),
    "Goblin Archer": dict(hp=28, anim=ARCHER_ANIM, height=240, moves=lambda: [
        S("Arrow", damage=6),
        S("Poison Arrow", damage=3, element="poison", effects={"poison": 3}),
        S("Aim", self_effects={"strength": 2}, block=3),
    ]),
    "Goblin Warlord": dict(hp=72, anim=GOBLIN_ANIM, height=290, tint=(255, 170, 150), pattern="cycle", moves=lambda: [
        S("War Cry", self_effects={"strength": 2}, block=8),
        S("Cleave", damage=12),
        S("Rend", damage=5, hits=2, effects={"vulnerable": 1}),
    ]),
    "Goblin Shaman": dict(hp=110, anim=SHAMAN_ANIM, height=340, pattern="cycle", moves=lambda: [
        S("Hex", effects={"weak": 2, "vulnerable": 2}),
        S("Green Flame", damage=12, element="poison", effects={"poison": 3}),
        S("Bone Ward", block=14, heal=8),
        S("Skull Barrage", damage=4, hits=3),
    ]),

    # ---------- Floor 2: Castle ----------
    "Castle Archer": dict(hp=44, anim=CASTLE_ARCHER_ANIM, height=270, moves=lambda: [
        S("Volley", damage=4, hits=3),
        S("Crippling Shot", damage=7, effects={"weak": 2}),
        S("Take Cover", block=10),
    ]),
    "Knight": dict(hp=56, anim=KNIGHT_ANIM, height=280, moves=lambda: [
        S("Sword Strike", damage=11),
        S("Shield Wall", block=14),
        S("Pommel Bash", damage=7, effects={"vulnerable": 2}),
    ]),
    "Castle Priest": dict(hp=46, anim=PRIEST_ANIM, height=280, moves=lambda: [
        S("Smite", damage=9, element="holy"),
        S("Blessing", heal=10, self_effects={"strength": 1}),
        S("Judgement", effects={"weak": 2, "vulnerable": 1}, block=6),
    ]),
    "Knight Captain": dict(hp=100, anim=KNIGHT_ANIM, height=320, tint=(255, 215, 150), pattern="cycle", moves=lambda: [
        S("Rally", self_effects={"strength": 3}, block=10),
        S("Crushing Blow", damage=16),
        S("Shield Slam", damage=8, block=8, effects={"weak": 1}),
    ]),
    "The Iron Paladin": dict(hp=160, anim=PALADIN_ANIM, height=350, pattern="cycle", moves=lambda: [
        S("Holy Bulwark", block=20, self_effects={"strength": 2}),
        S("Morningstar", damage=18, element="holy"),
        S("Consecrate", damage=6, hits=2, element="holy", effects={"burn": 3}),
        S("Condemn", effects={"vulnerable": 2, "weak": 2}, heal=12),
    ]),
}

FLOOR_POOLS = {
    1: {"normal": ["Goblin", "Goblin Archer"], "elite": ["Goblin Warlord"], "boss": ["Goblin Shaman"]},
    2: {"normal": ["Castle Archer", "Knight", "Castle Priest"], "elite": ["Knight Captain"], "boss": ["The Iron Paladin"]},
}
# Floors without their own art (yet) reuse earlier enemies, corrupted and stronger.
FLOOR_THEMES = {
    3: ("Cursed", (200, 170, 255)),
    4: ("Abyssal", (150, 200, 255)),
    5: ("Undying", (255, 140, 140)),
}


def create_enemy(floor: int, rank: str = "normal", room: int = 1) -> Enemy:
    """Builds an enemy for `floor` (1-5). rank: normal / elite / boss. room: 1-5 on this floor."""
    base_floor = floor if floor in FLOOR_POOLS else (1 if floor % 2 else 2)
    name = random.choice(FLOOR_POOLS[base_floor][rank])
    t = TEMPLATES[name]

    hp_mult = 1 + 0.25 * (floor - 1) + (0.04 * (room - 1) if rank != "boss" else 0)
    dmg_bonus = (floor - 1) + (1 if rank == "elite" and floor > 1 else 0)
    tint = t.get("tint")
    display_name = name
    if floor in FLOOR_THEMES:
        prefix, tint = FLOOR_THEMES[floor]
        display_name = f"{prefix} {name}"

    return Enemy(
        name=display_name,
        max_hp=int(t["hp"] * hp_mult),
        moves=t["moves"](),
        pattern=t.get("pattern", "random"),
        damage_bonus=dmg_bonus,
        anim=t["anim"],
        height=t["height"],
        tint=tint,
        rank=rank,
    )
