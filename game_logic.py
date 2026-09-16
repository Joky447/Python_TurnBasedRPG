import random

class Skill:
    """Represents an individual action/attack a character can take."""
    def __init__(self, name: str, energy_cost: int, damage: int = 0, block: int = 0, heal: int = 0, description: str = ""):
        self.name = name
        self.energy_cost = energy_cost
        self.damage = damage
        self.block = block
        self.heal = heal
        self.description = description

    def execute(self, user, target):
        """Applies the skill's effects to the user and target."""
        if user.energy < self.energy_cost:
            print(f"Not enough energy to use {self.name}!")
            return False

        user.energy -= self.energy_cost

        # Apply Block
        if self.block > 0:
            user.block += self.block
            print(f"{user.name} gained {self.block} Block!")

        # Apply Damage
        if self.damage > 0:
            user_total_damage = self.damage + user.stat_bonus
            target.take_damage(user_total_damage)

        # Apply Heal
        if self.heal > 0:
            user.heal(self.heal)

        return True


class Weapon:
    """Weapons dictate stat boosts and grant a set of up to 4 skills."""
    def __init__(self, name: str, stat_bonus: int, skills: list[Skill]):
        self.name = name
        self.stat_bonus = stat_bonus  # Bonus damage added to attacks
        self.skills = skills[:4]     # Strictly cap at 4 skills


class Entity:
    """Base class for both Player and Enemies."""
    def __init__(self, name: str, max_hp: int, max_energy: int = 3):
        self.name = name
        self.max_hp = max_hp
        self.current_hp = max_hp
        self.max_energy = max_energy
        self.energy = max_energy
        self.block = 0
        self.stat_bonus = 0

    def take_damage(self, amount: int):
        """Calculates damage after Block absorption."""
        if self.block > 0:
            if self.block >= amount:
                self.block -= amount
                print(f"{self.name}'s Block absorbed all {amount} damage!")
                return
            else:
                amount -= self.block
                print(f"{self.name}'s Block absorbed {self.block} damage!")
                self.block = 0

        self.current_hp = max(0, self.current_hp - amount)
        print(f"{self.name} took {amount} damage! Current HP: {self.current_hp}/{self.max_hp}")

    def heal(self, amount: int):
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        print(f"{self.name} healed for {amount}! HP: {self.current_hp}/{self.max_hp}")

    def reset_turn(self):
        """Reset temporary stats at turn start."""
        self.energy = self.max_energy
        self.block = 0  # Block expires at the start of your turn


class Player(Entity):
    """The Player character (Boy/Girl cosmetic choice)."""
    def __init__(self, name: str, gender: str, weapon: Weapon):
        super().__init__(name, max_hp=80, max_energy=3)
        self.gender = gender
        self.weapon = weapon
        self.equipped_skills: list[Skill] = weapon.skills.copy()
        self.stat_bonus = weapon.stat_bonus


class Enemy(Entity):
    """Enemy with an Intent system."""
    def __init__(self, name: str, max_hp: int):
        super().__init__(name, max_hp, max_energy=3)
        self.intent = None

    def decide_intent(self):
        """Selects what action the enemy will take on their turn."""
        actions = [
            {"type": "attack", "val": random.randint(6, 10), "desc": "Attack"},
            {"type": "defend", "val": random.randint(5, 8), "desc": "Defend"}
        ]
        self.intent = random.choice(actions)

    def execute_intent(self, target: Entity):
        """Executes the chosen intent against the player."""
        if not self.intent:
            return

        if self.intent["type"] == "attack":
            print(f"\n{self.name} executes intent: {self.intent['desc']} for {self.intent['val']} damage!")
            target.take_damage(self.intent["val"])
        elif self.intent["type"] == "defend":
            self.block += self.intent["val"]
            print(f"\n{self.name} executes intent: Gains {self.intent['val']} Block!")
        
        self.intent = None

        