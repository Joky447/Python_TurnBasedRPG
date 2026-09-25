from character.entity import Entity
from inventory_mechanics.weapon import Weapon
from skills.skill import Skill


class Player(Entity):
    """The Player character (Boy/Girl, Sorcerist/Swordsman)."""
    BASE_MAX_HP = 80

    def __init__(self, name: str, gender: str, char_class: str, weapon: Weapon):
        super().__init__(name, max_hp=self.BASE_MAX_HP, max_energy=3)
        self.gender = gender
        self.char_class = char_class
        self.bonus_damage = 0          # Permanent upgrades from rewards
        self.weapon = None
        self.equipped_skills: list[Skill] = []
        self.equip_weapon(weapon)
        self.current_hp = self.max_hp

    @property
    def stat_bonus(self) -> int:
        return self.weapon.stat_bonus + self.bonus_damage

    def equip_weapon(self, weapon: Weapon):
        """Equips a weapon. Its 4 skills replace the current ones."""
        if self.weapon:
            self.max_hp -= self.weapon.max_hp_bonus
        self.weapon = weapon
        self.max_hp += weapon.max_hp_bonus
        self.current_hp = min(self.current_hp + weapon.max_hp_bonus, self.max_hp)
        self.equipped_skills = [s.copy() for s in weapon.skills]
