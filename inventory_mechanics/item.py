"""Equipment items. Every item fills one of five slots and adds stat bonuses.

Weapons are items too: a Weapon also carries the 4 skills the character
fights with, and those skills (including learned or upgraded ones) stay on
the weapon when it is swapped out.
"""
import uuid

from skills.skill import Skill
from skills.skill_library import get_skill

ITEM_TYPES = ("Helmet", "Armor", "Weapon", "Shield", "Wings")
STATS = ("damage", "max_hp", "max_energy", "block")
STAT_LABELS = {"damage": "Damage", "max_hp": "Max HP", "max_energy": "Energy", "block": "Block per turn"}


class Item:
    def __init__(self, name: str, type: str, stat_bonus: dict | None = None, icon_path: str | None = None,
                 description: str = "", skills: list[Skill] | None = None, char_class: str | None = None,
                 tier: int = 0, id: str | None = None, set_name: str | None = None):
        if type not in ITEM_TYPES:
            raise ValueError(f"Item type must be one of {ITEM_TYPES}, got {type!r}")
        self.id = id or uuid.uuid4().hex[:12]
        self.name = name
        self.type = type
        self.stat_bonus = {k: v for k, v in (stat_bonus or {}).items() if v}
        self.icon_path = icon_path
        self.description = description
        self.skills = (skills or [])[:4]      # Weapons only: the 4 combat skills
        self.char_class = char_class          # Weapons only: which class can wield it
        self.tier = tier                      # Weapons: 0 = starter, 1+ = upgraded (great sword / great wand)
        self.set_name = set_name              # the class set this item belongs to, if any

    def bonus(self, stat: str) -> int:
        return self.stat_bonus.get(stat, 0)

    def stat_lines(self) -> list[str]:
        return [f"+{v} {STAT_LABELS[k]}" for k, v in self.stat_bonus.items()]

    def can_equip(self, char_class: str) -> bool:
        return self.char_class in (None, char_class)

    # --- Save / load ------------------------------------------------------
    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "type": self.type, "stat_bonus": self.stat_bonus,
                "icon_path": self.icon_path, "description": self.description, "char_class": self.char_class,
                "tier": self.tier, "set_name": self.set_name, "skills": [{"name": s.name.rstrip("+"), "upgraded": s.upgraded, "power": s.power}
                                  for s in self.skills]}

    @classmethod
    def from_dict(cls, data: dict) -> "Item":
        skills = []
        for s in data.get("skills", []):
            skill = get_skill(s["name"])
            skill.empower(s.get("power", 0))
            if s.get("upgraded"):
                skill.upgrade()
            skills.append(skill)
        return cls(data["name"], data["type"], data.get("stat_bonus"), data.get("icon_path"),
                   data.get("description", ""), skills, data.get("char_class"), data.get("tier", 0), data.get("id"),
                   data.get("set_name"))
