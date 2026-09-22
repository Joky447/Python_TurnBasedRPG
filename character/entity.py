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
