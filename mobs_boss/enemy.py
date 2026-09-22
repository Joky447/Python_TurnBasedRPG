import random
from character.entity import Entity

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
