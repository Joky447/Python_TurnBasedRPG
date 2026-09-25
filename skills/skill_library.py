"""All player skills. Use get_skill(name) to get a fresh, independent copy."""
import random

from skills.skill import Skill

_SKILLS = {s.name: s for s in [
    # --- Swordsman ---
    Skill("Slash", 1, damage=8, description="A basic blade attack."),
    Skill("Parry", 1, block=6, description="Raise your guard."),
    Skill("Heavy Strike", 2, damage=14, description="A powerful overhead blow."),
    Skill("Second Wind", 1, heal=5, block=3, description="Catch your breath."),
    Skill("Twin Cut", 1, damage=4, hits=2, description="Two quick slashes."),
    Skill("Shield Bash", 1, damage=5, block=5, description="Hit and guard at once."),
    Skill("Sunder", 2, damage=9, effects={"vulnerable": 2}, description="Crack their armor."),
    Skill("Battle Cry", 1, self_effects={"strength": 2}, description="Steel your resolve."),
    Skill("Flame Slash", 1, damage=6, element="fire", effects={"burn": 3}, description="A burning cut."),
    Skill("Frost Edge", 1, damage=7, element="ice", effects={"weak": 2}, description="A chilling strike."),
    Skill("Venom Stab", 1, damage=4, element="poison", effects={"poison": 4}, description="A poisoned thrust."),
    Skill("Whirlwind", 3, damage=6, hits=3, description="Spin with your blade."),
    Skill("Iron Wall", 2, block=15, description="An impenetrable stance."),
    Skill("Holy Blade", 2, damage=10, heal=4, element="holy", description="A blessed strike."),

    # --- Sorcerist ---
    Skill("Fireball", 2, damage=14, element="fire", effects={"burn": 2}, description="High damage fire spell."),
    Skill("Mana Shield", 1, block=8, element="arcane", description="Block with mana."),
    Skill("Magic Missile", 1, damage=3, hits=2, element="arcane", description="Quick magic bolts."),
    Skill("Heal", 2, heal=14, element="holy", description="Restore health."),
    Skill("Ignite", 1, element="fire", effects={"burn": 5}, description="Set the enemy ablaze."),
    Skill("Frost Nova", 1, damage=5, block=4, element="ice", effects={"weak": 1}, description="Freeze the air around you."),
    Skill("Ice Lance", 2, damage=12, element="ice", effects={"weak": 2}, description="A piercing shard of ice."),
    Skill("Toxic Cloud", 1, element="poison", effects={"poison": 6}, description="A choking miasma."),
    Skill("Hex", 1, element="arcane", effects={"vulnerable": 2, "weak": 1}, description="A crippling curse."),
    Skill("Arcane Surge", 1, element="arcane", self_effects={"strength": 2}, description="Amplify your magic."),
    Skill("Chain Lightning", 3, damage=7, hits=3, element="arcane", description="Lightning that strikes thrice."),
    Skill("Meteor", 3, damage=26, element="fire", effects={"burn": 3}, description="Call down the sky."),
    Skill("Radiance", 2, heal=8, block=8, element="holy", description="Bathe in light."),
]}

CLASS_SKILL_POOLS = {
    "Swordsman": ["Slash", "Parry", "Heavy Strike", "Second Wind", "Twin Cut", "Shield Bash", "Sunder",
                  "Battle Cry", "Flame Slash", "Frost Edge", "Venom Stab", "Whirlwind", "Iron Wall", "Holy Blade"],
    "Sorcerist": ["Fireball", "Mana Shield", "Magic Missile", "Heal", "Ignite", "Frost Nova", "Ice Lance",
                  "Toxic Cloud", "Hex", "Arcane Surge", "Chain Lightning", "Meteor", "Radiance"],
}


def get_skill(name: str) -> Skill:
    return _SKILLS[name].copy()


def random_skills(char_class: str, count: int, exclude: list[str] = ()) -> list[Skill]:
    """Random distinct skills for a class, skipping names the player already has."""
    base_excluded = {n.rstrip("+") for n in exclude}
    pool = [n for n in CLASS_SKILL_POOLS[char_class] if n not in base_excluded]
    return [get_skill(n) for n in random.sample(pool, min(count, len(pool)))]
