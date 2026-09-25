from skills.skill import Skill


class Weapon:
    """Weapons dictate stat boosts and grant a set of up to 4 skills."""
    def __init__(self, name: str, stat_bonus: int, skills: list[Skill], description: str = "", max_hp_bonus: int = 0, tier: int = 0):
        self.name = name
        self.stat_bonus = stat_bonus      # Bonus damage added to attacks
        self.skills = skills[:4]          # Strictly cap at 4 skills
        self.description = description
        self.max_hp_bonus = max_hp_bonus
        self.tier = tier                  # 0 starter, 1 upgraded, 2 legendary (changes hero outfit)
