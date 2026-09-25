import math

# Status effects shown in combat. Keys are used in Skill.effects / Skill.self_effects.
STATUS_INFO = {
    "burn":       {"color": (255, 120, 40),  "desc": "Takes damage equal to stacks at turn start, ignoring Block. Then loses 1 stack."},
    "poison":     {"color": (120, 220, 80),  "desc": "Takes damage equal to stacks at turn start, ignoring Block. Then loses 1 stack."},
    "weak":       {"color": (170, 170, 200), "desc": "Deals 25% less damage. Lasts this many turns."},
    "vulnerable": {"color": (230, 80, 200),  "desc": "Takes 50% more damage. Lasts this many turns."},
    "strength":   {"color": (240, 60, 60),   "desc": "Deals +1 damage per stack. Lasts all combat."},
}


class Entity:
    """Base class for both Player and Enemies."""
    def __init__(self, name: str, max_hp: int, max_energy: int = 3):
        self.name = name
        self.max_hp = max_hp
        self.current_hp = max_hp
        self.max_energy = max_energy
        self.energy = max_energy
        self.block = 0
        self.statuses: dict[str, int] = {}
        # Events for the UI (floating numbers, combat log). Drained by CombatState.
        self.events: list[tuple] = []

    # --- Stats -------------------------------------------------------------
    @property
    def stat_bonus(self) -> int:
        """Flat bonus damage added to every hit."""
        return 0

    @property
    def is_alive(self) -> bool:
        return self.current_hp > 0

    def status(self, name: str) -> int:
        return self.statuses.get(name, 0)

    def calculate_damage(self, base: int, target: "Entity | None" = None) -> int:
        """Final damage of one hit from this entity against `target`."""
        dmg = base + self.stat_bonus + self.status("strength")
        if self.status("weak"):
            dmg *= 0.75
        if target is not None and target.status("vulnerable"):
            dmg *= 1.5
        return max(0, math.floor(dmg))

    # --- Actions -----------------------------------------------------------
    def take_damage(self, amount: int, ignore_block: bool = False) -> int:
        """Applies damage after Block absorption. Returns HP actually lost."""
        blocked = 0
        if self.block > 0 and not ignore_block:
            blocked = min(self.block, amount)
            self.block -= blocked
            amount -= blocked
            if blocked:
                self.events.append(("blocked", blocked))

        lost = min(self.current_hp, amount)
        self.current_hp -= lost
        if amount > 0 or not blocked:
            self.events.append(("damage", amount))
        return lost

    def heal(self, amount: int) -> int:
        healed = min(self.max_hp - self.current_hp, amount)
        self.current_hp += healed
        if healed:
            self.events.append(("heal", healed))
        return healed

    def gain_block(self, amount: int):
        self.block += amount
        self.events.append(("block", amount))

    def apply_status(self, name: str, stacks: int):
        self.statuses[name] = self.status(name) + stacks
        self.events.append(("status", name, stacks))

    # --- Turn flow ---------------------------------------------------------
    def start_turn(self):
        """Start of this entity's turn: Block expires, then burn/poison deal damage and lose a stack."""
        self.block = 0
        self.energy = self.max_energy
        for dot in ("burn", "poison"):
            if self.status(dot):
                self.events.append(("dot", dot))
                self.take_damage(self.status(dot), ignore_block=True)
                self._decay(dot)

    def end_turn(self):
        """End of this entity's turn: Weak and Vulnerable lose a stack."""
        for name in ("weak", "vulnerable"):
            self._decay(name)

    def _decay(self, name: str):
        if name in self.statuses:
            self.statuses[name] -= 1
            if self.statuses[name] <= 0:
                del self.statuses[name]

    def reset_combat(self):
        """Clears everything that should not carry over between fights."""
        self.block = 0
        self.energy = self.max_energy
        self.statuses.clear()
        self.events.clear()
