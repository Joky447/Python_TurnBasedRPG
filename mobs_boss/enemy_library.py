"""Enemy templates per floor, and the factory that builds a scaled Enemy for an encounter."""
import os
import random

import assets
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
    "attack": (F2 + "knight 1 attack.png", 4, 2, None, 3, True),
}
KNIGHT_ANIM = {"attack": (F2 + "knight 2 attack.png", 4, 2, None, 3, True)}
PRIEST_ANIM = {"attack": (F2 + "priest attack 4.png", "auto", 1, None, 0, True)}
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
    "Castle Archer": dict(sheet=(F2 + "knight 1 attack.png", 3), idle=(F2 + "knight1 idle animation.png", 5, 2),
                          hp=44, anim=CASTLE_ARCHER_ANIM, height=270, moves=lambda: [
        S("Volley", damage=4, hits=3),
        S("Crippling Shot", damage=7, effects={"weak": 2}),
        S("Take Cover", block=10),
    ]),
    "Knight": dict(sheet=(F2 + "knight 2 attack.png", 3), hp=56, anim=KNIGHT_ANIM, height=280, moves=lambda: [
        S("Sword Strike", damage=11),
        S("Shield Wall", block=14),
        S("Pommel Bash", damage=7, effects={"vulnerable": 2}),
    ]),
    "Castle Priest": dict(sheet=(F2 + "priest attack 4.png", 0, "auto", 1), hp=46, anim=PRIEST_ANIM, height=280, moves=lambda: [
        S("Smite", damage=9, element="holy"),
        S("Blessing", heal=10, self_effects={"strength": 1}),
        S("Judgement", effects={"weak": 2, "vulnerable": 1}, block=6),
    ]),
    "Knight Captain": dict(sheet=(F2 + "knight 2 attack.png", 3), sheet_tint=(255, 215, 150), hp=100, anim=KNIGHT_ANIM, height=320, tint=(255, 215, 150), pattern="cycle", moves=lambda: [
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

# ---------- Floors 3-5 ----------
# sheet = (attack sheet, rest frame): the drawn 4x2 attack sheet and which of its 8
# frames is the calm standing pose. The idle and hurt animations are generated from
# that pose by tools/make_enemy_anims.py and saved next to it as
# "<sheet name> idle.png" / "<sheet name> hurt.png".
# Without a sheet, an enemy looks for "<art> idle/attack/hurt.png" (5x2 sheets),
# and failing that uses its tinted stand-in sprite.
F3, F4, F5 = "mobs_boss/floor3/", "mobs_boss/floor4/", "mobs_boss/floor5/"
ICE, FOREST, FIRE = (165, 205, 255), (150, 235, 150), (255, 150, 110)

TEMPLATES.update({
    # ---------- Floor 3: Frozen Peaks ----------
    "Frostbite Goblin": dict(sheet=(F3 + "new goblin1 attack.png", 3), hp=46, art=F3 + "frostbite goblin", anim=GOBLIN_ANIM, tint=ICE, height=240, moves=lambda: [
        S("Ice Shiv", damage=8, element="ice"),
        S("Flurry", damage=3, hits=3, element="ice"),
        S("Frost Hide", block=9),
    ]),
    "Ice Archer": dict(sheet=(F3 + "new frost archer 2 attack.png", 3), hp=40, art=F3 + "ice archer", anim=CASTLE_ARCHER_ANIM, tint=ICE, height=270, moves=lambda: [
        S("Frost Arrow", damage=7, element="ice", effects={"weak": 1}),
        S("Hail Volley", damage=3, hits=3, element="ice"),
        S("Take Aim", self_effects={"strength": 2}, block=4),
    ]),
    "Frost Knight": dict(sheet=(F3 + "frost knight 3 attack.png", 7), hp=54, art=F3 + "frost knight", anim=KNIGHT_ANIM, tint=ICE, height=285, moves=lambda: [
        S("Glacier Cleave", damage=12, element="ice"),
        S("Ice Wall", block=15),
        S("Numbing Strike", damage=7, element="ice", effects={"weak": 2}),
    ]),
    "Snow Witch": dict(sheet=(F3 + "queen ice spell attack.png", 4), hp=90, art=F3 + "snow witch", anim=PRIEST_ANIM, tint=ICE, height=320, pattern="cycle", moves=lambda: [
        S("Blizzard", damage=5, hits=2, element="ice", effects={"weak": 2}),
        S("Frozen Veil", block=14, heal=8),
        S("Icicle Lance", damage=15, element="ice"),
    ]),
    "Glacius, the Frost King": dict(sheet=(F3 + "Glacius, Frost King attack.png", 3), hp=170, art=F3 + "glacius", anim=PALADIN_ANIM, tint=ICE, height=360,
                                    pattern="cycle", moves=lambda: [
        S("Winter's Grasp", effects={"weak": 2, "vulnerable": 2}, block=12),
        S("Avalanche", damage=20, element="ice"),
        S("Frozen Throne", block=22, self_effects={"strength": 2}),
        S("Shatter", damage=7, hits=3, element="ice"),
    ]),

    # ---------- Floor 4: Enchanted Forest ----------
    "Thorn Sprite": dict(sheet=(F4 + "thorn sprite attack animation.png", 4), hp=44, art=F4 + "thorn sprite", anim=ARCHER_ANIM, tint=FOREST, height=230, moves=lambda: [
        S("Thorn Dart", damage=5, element="poison", effects={"poison": 3}),
        S("Bramble Shot", damage=4, hits=2),
        S("Leaf Veil", block=10),
    ]),
    "Mushroom Brute": dict(sheet=(F4 + "mushroom brute attack animate.png", 3), hp=58, art=F4 + "mushroom brute", anim=GOBLIN_ANIM, tint=FOREST, height=250, moves=lambda: [
        S("Cap Slam", damage=13),
        S("Spore Cloud", element="poison", effects={"poison": 5, "weak": 1}),
        S("Regrow", heal=10, block=5),
    ]),
    "Crystal Golem": dict(sheet=(F3 + "crystal golem attackk.png", 3), hp=66, art=F4 + "crystal golem", anim=KNIGHT_ANIM, tint=(160, 220, 255), height=300, moves=lambda: [
        S("Crystal Fist", damage=14),
        S("Prism Shell", block=18),
        S("Shard Burst", damage=5, hits=2, effects={"vulnerable": 2}),
    ]),
    "Forest Druid": dict(sheet=(F4 + "Forest druid attck.png", 3), hp=50, art=F4 + "forest druid", anim=PRIEST_ANIM, tint=FOREST, height=290, moves=lambda: [
        S("Vine Lash", damage=10),
        S("Nature's Blessing", heal=12, self_effects={"strength": 1}),
        S("Entangle", effects={"weak": 2, "poison": 3}),
    ]),
    "Treant Guardian": dict(sheet=(F4 + "treant attack animte.png", 3), hp=110, art=F4 + "treant guardian", anim=GOBLIN_ANIM, tint=(140, 200, 120), height=330,
                            pattern="cycle", moves=lambda: [
        S("Take Root", block=16, self_effects={"strength": 2}),
        S("Branch Sweep", damage=8, hits=2),
        S("Crushing Trunk", damage=18),
    ]),
    "Sylvara, Queen of the Grove": dict(sheet=(F4 + "Nature Queen Sprite Animation Sheet.png", 3), hp=180, art=F4 + "sylvara", anim=SHAMAN_ANIM, tint=FOREST, height=370,
                                        pattern="cycle", moves=lambda: [
        S("Wild Growth", heal=15, block=12),
        S("Poison Bloom", damage=8, element="poison", effects={"poison": 6}),
        S("Thornstorm", damage=6, hits=3),
        S("Grove's Wrath", damage=22, effects={"vulnerable": 1}),
    ]),

    # ---------- Floor 5: Volcanic Fortress ----------
    "Magma Imp": dict(sheet=(F5 + "Magma Imp Pixel-Art Attack Sprite Sheet.png", 3), hp=48, art=F5 + "magma imp", anim=GOBLIN_ANIM, tint=FIRE, height=230, moves=lambda: [
        S("Ember Claw", damage=8, element="fire", effects={"burn": 2}),
        S("Frenzy", damage=4, hits=3),
        S("Cackle", self_effects={"strength": 2}),
    ]),
    "Cinder Stalker": dict(sheet=(F5 + "cinder stalker.png", 3), hp=46, art=F5 + "cinder stalker", anim=ARCHER_ANIM, tint=FIRE, height=175, moves=lambda: [
        S("Fire Arrow", damage=7, element="fire", effects={"burn": 3}),
        S("Smoke Screen", block=12, effects={"weak": 1}),
        S("Rain of Cinders", damage=3, hits=4, element="fire"),
    ]),
    "Ash Archer": dict(sheet=(F5 + "Ashen Hooded Archer Sprite Sheet.png", 3), hp=50, art=F5 + "ash archer", anim=CASTLE_ARCHER_ANIM, tint=(200, 170, 160), height=270, moves=lambda: [
        S("Ash Volley", damage=5, hits=3),
        S("Blinding Ash", damage=6, effects={"weak": 2}),
        S("Take Cover", block=12),
    ]),
    "Obsidian Knight": dict(sheet=(F5 + "obsidian knight..png", 3), hp=64, art=F5 + "obsidian knight", anim=KNIGHT_ANIM, tint=(150, 120, 140), height=290, moves=lambda: [
        S("Obsidian Blade", damage=14),
        S("Volcanic Guard", block=18),
        S("Molten Edge", damage=8, element="fire", effects={"burn": 3}),
    ]),
    "Flame Priest": dict(sheet=(F5 + "flame priest.png", 3), hp=52, art=F5 + "flame priest", anim=PRIEST_ANIM, tint=FIRE, height=290, moves=lambda: [
        S("Fire Bolt", damage=11, element="fire"),
        S("Dark Rite", heal=12, self_effects={"strength": 2}),
        S("Immolate", element="fire", effects={"burn": 6, "vulnerable": 1}),
    ]),
    "Infernal Warlord": dict(sheet=(F5 + "Infernal Warlord.png", 3), hp=120, art=F5 + "infernal warlord", anim=KNIGHT_ANIM, tint=(255, 120, 90), height=340,
                             pattern="cycle", moves=lambda: [
        S("Warlord's Roar", self_effects={"strength": 3}, block=12),
        S("Hellfire Cleave", damage=12, element="fire", effects={"burn": 3}),
        S("Execute", damage=22),
    ]),
    "Ignis, the Demon Lord": dict(sheet=(F5 + "Ignis the Demon Lord.png", 3), hp=200, art=F5 + "ignis", anim=SHAMAN_ANIM, tint=(255, 110, 80), height=390,
                                  pattern="cycle", moves=lambda: [
        S("Infernal Pact", self_effects={"strength": 3}, block=20),
        S("Meteor Storm", damage=7, hits=3, element="fire", effects={"burn": 3}),
        S("Soul Sear", effects={"weak": 2, "vulnerable": 2}, heal=15),
        S("Apocalypse", damage=28, element="fire"),
    ]),
})

# Enemies that fight up close: they dash to the hero when they attack, like the Swordsman does.
# (Archers, priests, witches, druids and other casters attack from where they stand.)
MELEE = {"Goblin", "Goblin Warlord", "Knight", "Knight Captain", "The Iron Paladin",
         "Frostbite Goblin", "Frost Knight", "Mushroom Brute", "Crystal Golem", "Treant Guardian",
         "Magma Imp", "Cinder Stalker", "Obsidian Knight", "Infernal Warlord", "Ignis, the Demon Lord"}

FLOOR_POOLS = {
    1: {"normal": ["Goblin", "Goblin Archer"], "elite": [], "boss": ["Goblin Shaman"]},
    2: {"normal": ["Castle Archer", "Knight", "Castle Priest"], "elite": [], "boss": ["The Iron Paladin"]},
    3: {"normal": ["Frostbite Goblin", "Ice Archer", "Frost Knight"], "elite": ["Snow Witch"],
        "boss": ["Glacius, the Frost King"]},
    4: {"normal": ["Thorn Sprite", "Mushroom Brute", "Crystal Golem", "Forest Druid"], "elite": ["Treant Guardian"],
        "boss": ["Sylvara, Queen of the Grove"]},
    5: {"normal": ["Magma Imp", "Cinder Stalker", "Ash Archer", "Obsidian Knight", "Flame Priest"],
        "elite": ["Infernal Warlord"], "boss": ["Ignis, the Demon Lord"]},
}


def own_art(art_base: str | None) -> dict:
    """Animation spec for an enemy's own art files, if any of them exist."""
    if not art_base:
        return {}
    spec = {}
    for clip in ("idle", "attack", "hurt"):
        rel = f"{art_base} {clip}.png"
        if os.path.exists(assets.path(rel)):
            spec[clip] = (rel, 5, 2, None)
    return spec


GENERATED_FRAMES = 8


def generated_path(sheet_path: str, clip: str) -> str:
    """Where the generated idle/hurt sheet for a drawn attack sheet is saved."""
    return f"{sheet_path[:-4]} {clip}.png"


def sheet_layout(sheet):
    """(path, rest frame, cols, rows) for a template's sheet=(path, rest[, cols, rows])."""
    path, rest, *grid = sheet
    cols, rows = grid if grid else (4, 2)
    return path, rest, cols, rows


def sheet_art(sheet, idle=None) -> dict:
    """Animation spec for a drawn attack sheet plus its generated (or drawn) idle and hurt.

    Drawn sheets are cleaned of spill-over from neighbouring frames and every frame
    is lined up on the character's own feet (see assets.load_frames).
    """
    if not sheet or not os.path.exists(assets.path(sheet[0])):
        return {}
    path, rest, cols, rows = sheet_layout(sheet)
    spec = {"attack": (path, cols, rows, None, rest, True)}
    for clip in ("idle", "hurt"):
        gen = generated_path(path, clip)
        if os.path.exists(assets.path(gen)):
            spec[clip] = (gen, GENERATED_FRAMES, 1, None, 0, "first-body")
    if idle and os.path.exists(assets.path(idle[0])):
        spec["idle"] = (*idle, None, 0, True)
    return spec


# Each fight on a floor is a little tougher than the one before it
HP_PER_ENCOUNTER = 0.08
DAMAGE_PER_ENCOUNTER = 1
# (Regular and elite fights only: the boss always comes last and keeps its designed stats.)


def create_enemy(floor: int, name: str, rank: str = "normal", encounter: int = 1) -> Enemy:
    """Builds enemy `name` for `floor`, scaled by floor and by its fight number on the floor."""
    t = TEMPLATES[name]

    step = encounter - 1 if rank != "boss" else 0
    hp_mult = 1 + 0.25 * (floor - 1) + HP_PER_ENCOUNTER * step
    dmg_bonus = (floor - 1) + DAMAGE_PER_ENCOUNTER * step

    # Prefer the enemy's own art; otherwise use its tinted stand-in
    anim, tint = sheet_art(t.get("sheet"), t.get("idle")) or own_art(t.get("art")), t.get("sheet_tint")
    if not anim:
        anim, tint = t["anim"], t.get("tint")

    enemy = Enemy(
        name=name,
        max_hp=int(t["hp"] * hp_mult),
        moves=t["moves"](),
        pattern=t.get("pattern", "random"),
        damage_bonus=dmg_bonus,
        anim=anim,
        height=t["height"],
        tint=tint,
        rank=rank,
    )
    enemy.melee = name in MELEE
    return enemy
