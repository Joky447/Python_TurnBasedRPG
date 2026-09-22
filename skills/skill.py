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
