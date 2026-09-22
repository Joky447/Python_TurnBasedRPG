from skills.skill import Skill

class Weapon:
    """Weapons dictate stat boosts and grant a set of up to 4 skills."""
    def __init__(self, name: str, stat_bonus: int, skills: list[Skill]):
        self.name = name
        self.stat_bonus = stat_bonus  # Bonus damage added to attacks
        self.skills = skills[:4]     # Strictly cap at 4 skills
