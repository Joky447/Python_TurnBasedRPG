import copy

ELEMENT_COLORS = {
    "physical": (200, 200, 200),
    "fire":     (255, 120, 40),
    "ice":      (120, 200, 255),
    "poison":   (120, 220, 80),
    "arcane":   (190, 120, 255),
    "holy":     (255, 230, 120),
}


class Skill:
    """Represents an individual action/attack a character (or enemy) can take.

    effects      -> statuses applied to the target, e.g. {"burn": 3}
    self_effects -> statuses applied to the user,   e.g. {"strength": 1}
    """
    def __init__(self, name: str, energy_cost: int = 0, damage: int = 0, hits: int = 1,
                 block: int = 0, heal: int = 0, element: str = "physical",
                 effects: dict | None = None, self_effects: dict | None = None,
                 description: str = ""):
        self.name = name
        self.energy_cost = energy_cost
        self.damage = damage
        self.hits = hits
        self.block = block
        self.heal = heal
        self.element = element
        self.effects = effects or {}
        self.self_effects = self_effects or {}
        self.description = description
        self.upgraded = False
        self.power = 0          # floor tier of an empowered skill (from post-boss rewards)

    # --- Info --------------------------------------------------------------
    @property
    def color(self):
        return ELEMENT_COLORS.get(self.element, ELEMENT_COLORS["physical"])

    @property
    def is_attack(self) -> bool:
        return self.damage > 0

    def summary(self, user=None, target=None) -> str:
        """Short auto-generated rules text. Shows real numbers when `user` is given."""
        parts = []
        if self.damage:
            dmg = user.calculate_damage(self.damage, target) if user else self.damage
            parts.append(f"Deal {dmg}" + (f" x{self.hits}" if self.hits > 1 else "")
                         + ("" if self.element == "physical" else f" {self.element}") + " dmg")
        if self.block:
            parts.append(f"Gain {self.block} Block")
        if self.heal:
            parts.append(f"Heal {self.heal}")
        for name, n in self.effects.items():
            parts.append(f"Apply {n} {name.title()}")
        for name, n in self.self_effects.items():
            parts.append(f"Gain {n} {name.title()}")
        return ". ".join(parts) + "." if parts else self.description

    # --- Use ---------------------------------------------------------------
    def can_use(self, user) -> bool:
        return user.energy >= self.energy_cost

    def execute(self, user, target) -> bool:
        """Applies the skill's effects to the user and target."""
        if not self.can_use(user):
            return False
        user.energy -= self.energy_cost

        if self.block:
            user.gain_block(self.block)
        if self.damage:
            for _ in range(self.hits):
                if not target.is_alive:
                    break
                target.take_damage(user.calculate_damage(self.damage, target))
        if self.heal:
            user.heal(self.heal)
        if target.is_alive:
            for name, stacks in self.effects.items():
                target.apply_status(name, stacks)
        for name, stacks in self.self_effects.items():
            user.apply_status(name, stacks)
        return True

    # --- Progression -------------------------------------------------------
    def copy(self) -> "Skill":
        return copy.deepcopy(self)

    def empower(self, level: int):
        """Scales the skill for later floors: +30% numbers per level and +1 effect stack every 2 levels.
        Used for skills won from bosses, so they keep up with the enemies."""
        if level <= self.power:
            return
        mult = (1 + 0.3 * level) / (1 + 0.3 * self.power)
        extra = level // 2 - self.power // 2
        self.power = level
        self.damage = round(self.damage * mult)
        self.block = round(self.block * mult)
        self.heal = round(self.heal * mult)
        self.effects = {k: v + extra for k, v in self.effects.items()}
        self.self_effects = {k: v + extra for k, v in self.self_effects.items()}

    def upgrade(self):
        """Improves this skill once (+). Numbers grow by roughly a third."""
        if self.upgraded:
            return
        self.upgraded = True
        self.name += "+"
        if self.damage:
            self.damage += max(2, self.damage // 3)
        if self.block:
            self.block += max(2, self.block // 3)
        if self.heal:
            self.heal += max(2, self.heal // 3)
        self.effects = {k: v + 1 for k, v in self.effects.items()}
        self.self_effects = {k: v + 1 for k, v in self.self_effects.items()}
