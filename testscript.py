
from skills.skill import Skill
from inventory_mechanics.weapon import Weapon
from character.player import Player
from mobs_boss.enemy import Enemy

if __name__ == "__main__":
    # 1. Define skills for a Starter Broadsword
    slash = Skill(name="Slash", energy_cost=1, damage=8, description="A basic blade attack.")
    parry = Skill(name="Parry", energy_cost=1, block=6, description="Raise guard to gain Block.")
    heavy_strike = Skill(name="Heavy Strike", energy_cost=2, damage=14, description="Powerful blow.")
    second_wind = Skill(name="Second Wind", energy_cost=1, heal=5, block=3, description="Recover HP & Block.")

    # 2. Create Weapon & Player
    starter_sword = Weapon(name="Iron Sword", stat_bonus=2, skills=[slash, parry, heavy_strike, second_wind])
    hero = Player(name="Hero", gender="Boy", weapon=starter_sword)

    # 3. Create Enemy
    goblin = Enemy(name="Goblin Warrior", max_hp=30)
    goblin.decide_intent()

    # 4. Simulate Turn 1
    print(f"--- TURN 1 ---")
    print(f"Enemy Intent: {goblin.intent['desc']} ({goblin.intent['val']})")
    
    # Player uses Skill 1 (Slash)
    hero.equipped_skills[0].execute(hero, goblin)
    
    # Player uses Skill 2 (Parry)
    hero.equipped_skills[1].execute(hero, goblin)

    # Enemy Turn
    goblin.execute_intent(hero)