import random

from character.entity import Entity
from skills.skill import Skill


class Enemy(Entity):
    """Enemy with an Intent system.

    The enemy picks its next move (a Skill) at the end of its turn and shows it
    to the player as an intent, so the player can plan around it.
    pattern="cycle"  -> moves are used in order, looping (predictable bosses)
    pattern="random" -> random move, never the same one 3 times in a row
    """
    def __init__(self, name: str, max_hp: int, moves: list[Skill], pattern: str = "random",
                 damage_bonus: int = 0, anim: dict | None = None, height: int = 260,
                 tint=None, rank: str = "normal"):
        super().__init__(name, max_hp, max_energy=0)
        self.moves = moves
        self.pattern = pattern
        self.damage_bonus = damage_bonus
        self.anim = anim or {}                # clip -> sprite sheet layout (see enemy_library)
        self.height = height
        self.tint = tint
        self.rank = rank                      # "normal", "elite" or "boss"
        self.intent: Skill | None = None
        self._history: list[int] = []

    @property
    def stat_bonus(self) -> int:
        return self.damage_bonus

    def decide_intent(self):
        """Selects what action the enemy will take on their next turn."""
        if self.pattern == "cycle":
            idx = len(self._history) % len(self.moves)
        else:
            choices = list(range(len(self.moves)))
            if len(self._history) >= 2 and self._history[-1] == self._history[-2] and len(choices) > 1:
                choices.remove(self._history[-1])
            idx = random.choice(choices)
        self._history.append(idx)
        self.intent = self.moves[idx]

    def intent_kinds(self) -> list[str]:
        """Which icons describe the current intent (attack/defend/buff/debuff/heal)."""
        if not self.intent:
            return []
        m = self.intent
        kinds = []
        if m.damage: kinds.append("attack")
        if m.block: kinds.append("defend")
        if m.heal: kinds.append("heal")
        if m.self_effects: kinds.append("buff")
        if m.effects: kinds.append("debuff")
        return kinds

    def execute_intent(self, target: Entity):
        """Executes the chosen intent against the player."""
        if self.intent:
            self.intent.execute(self, target)
        self.intent = None
