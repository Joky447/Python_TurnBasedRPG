from character.entity import Entity
from inventory_mechanics.weapon import Weapon
from skills.skill import Skill

class Player(Entity):
    """The Player character (Boy/Girl cosmetic choice)."""
    def __init__(self, name: str, gender: str, weapon: Weapon):
        super().__init__(name, max_hp=80, max_energy=3)
        self.gender = gender
        self.weapon = weapon
        self.equipped_skills: list[Skill] = weapon.skills.copy()
        self.stat_bonus = weapon.stat_bonus
