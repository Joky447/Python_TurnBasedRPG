from character.entity import Entity
from inventory_mechanics.item import ITEM_TYPES, Item
from inventory_mechanics.weapon_library import (STARTING_WEAPONS, SET_NAMES, current_name, get_weapon, icon_for,
                                                is_known_item)
from skills.skill import Skill

# Stats before any equipment
CLASS_BASE_STATS = {
    "Swordsman": {"max_hp": 80, "max_energy": 3, "damage": 0, "block": 0},
    "Sorcerist": {"max_hp": 70, "max_energy": 3, "damage": 0, "block": 0},
}


class Player(Entity):
    """A playable character (Boy/Girl, Sorcerist/Swordsman) with 5 equipment slots and an inventory."""

    def __init__(self, name: str, gender: str, char_class: str, weapon: Item):
        base = CLASS_BASE_STATS[char_class]
        super().__init__(name, max_hp=base["max_hp"], max_energy=base["max_energy"])
        self.gender = gender
        self.char_class = char_class
        self.bonus_damage = 0          # Permanent upgrades from rewards
        self.damage = 0
        self.base_block = 0            # Block gained at the start of each of your turns
        self.cleared_floors: set[int] = set()   # floors whose boss this character has beaten (rematches open)
        self.inventory: list[Item] = []
        self.equipped_helmet: Item | None = None
        self.equipped_armor: Item | None = None
        self.equipped_weapon: Item | None = None
        self.equipped_shield: Item | None = None
        self.equipped_wings: Item | None = None
        self.equip_item(weapon)
        self.current_hp = self.max_hp

    # --- Equipment ----------------------------------------------------------
    @staticmethod
    def slot_attr(item_type: str) -> str:
        return f"equipped_{item_type.lower()}"

    def equipped(self, item_type: str) -> Item | None:
        return getattr(self, self.slot_attr(item_type))

    def equipped_items(self) -> list[Item]:
        return [i for i in (self.equipped(t) for t in ITEM_TYPES) if i]

    def equip_item(self, item: Item) -> bool:
        """Puts `item` in its slot. Whatever was there goes back to the inventory."""
        if not item.can_equip(self.char_class):
            return False
        if item in self.inventory:
            self.inventory.remove(item)
        old = self.equipped(item.type)
        if old:
            self.inventory.append(old)
        setattr(self, self.slot_attr(item.type), item)
        self.recalculate_stats()
        return True

    def unequip_item(self, item: Item) -> bool:
        """Moves an equipped item back to the inventory. The weapon can only be swapped, not removed,
        because the character's skills come from it."""
        if item.type == "Weapon" or self.equipped(item.type) is not item:
            return False
        setattr(self, self.slot_attr(item.type), None)
        self.inventory.append(item)
        self.recalculate_stats()
        return True

    @property
    def set_active(self) -> bool:
        """The class set works only while its weapon is equipped (not the starting weapon)."""
        return self.equipped_weapon is not None and self.equipped_weapon.set_name is not None

    def item_active(self, item: Item) -> bool:
        """Set pieces are disabled (no stats, no outfit) while the starting weapon is equipped."""
        return item.type == "Weapon" or item.set_name is None or self.set_active

    def recalculate_stats(self):
        """Rebuilds max HP, energy, damage and block from the class base plus all equipped items."""
        base = CLASS_BASE_STATS[self.char_class]
        items = [i for i in self.equipped_items() if self.item_active(i)]
        total = {stat: base[stat] + sum(i.bonus(stat) for i in items) for stat in base}
        hp_gain = total["max_hp"] - self.max_hp
        self.max_hp = total["max_hp"]
        self.current_hp = max(1, min(self.max_hp, self.current_hp + max(0, hp_gain)))
        self.max_energy = total["max_energy"]
        self.damage = total["damage"]
        self.base_block = total["block"]

    # --- Combat --------------------------------------------------------------
    @property
    def weapon(self) -> Item | None:
        return self.equipped_weapon

    @property
    def equipped_skills(self) -> list[Skill]:
        """The weapon's skills. Learning or upgrading a skill changes the weapon's list, so it sticks."""
        return self.equipped_weapon.skills if self.equipped_weapon else []

    @property
    def stat_bonus(self) -> int:
        return self.damage + self.bonus_damage

    @property
    def outfit_stage(self) -> int:
        """Which outfit sprite to show: each floor's reward builds on the one before it
        (great weapon -> armor -> helmet/mask -> shield/aura -> wings or scythe = final form)."""
        weapon = self.equipped_weapon
        final = self.equipped_wings is not None or (weapon is not None and weapon.name == "Astral Scythe")
        stage = 0
        for has_piece in (weapon is not None and weapon.tier > 0,
                          self.equipped_armor is not None,
                          self.equipped_helmet is not None,
                          self.equipped_shield is not None,
                          final):
            if not has_piece:
                break
            stage += 1
        return stage

    def start_turn(self):
        super().start_turn()
        if self.base_block:
            self.gain_block(self.base_block)

    # --- Save / load --------------------------------------------------------
    def to_dict(self) -> dict:
        return {"name": self.name, "gender": self.gender, "char_class": self.char_class,
                "bonus_damage": self.bonus_damage, "cleared_floors": sorted(self.cleared_floors),
                "equipped": {t: i.to_dict() for t in ITEM_TYPES if (i := self.equipped(t))},
                "inventory": [i.to_dict() for i in self.inventory]}

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        gender, char_class = data["gender"], data["char_class"]

        def keep(d):   # items from older versions are renamed, or dropped if they no longer exist
            d["name"] = current_name(d["name"], char_class, gender)
            if d["name"] not in STARTING_WEAPONS.values():
                d["set_name"] = SET_NAMES.get(char_class)
                d["char_class"] = char_class
            return is_known_item(d["name"], char_class, gender)
        equipped = {t: Item.from_dict(d) for t, d in data.get("equipped", {}).items() if keep(d)}
        weapon = equipped.pop("Weapon", None) or get_weapon(STARTING_WEAPONS[char_class], gender)
        p = cls(data["name"], gender, char_class, weapon)
        p.bonus_damage = data.get("bonus_damage", 0)
        p.cleared_floors = set(data.get("cleared_floors", []))
        for item in equipped.values():
            p.equip_item(item)
        p.inventory = [Item.from_dict(d) for d in data.get("inventory", []) if keep(d)]
        for item in p.inventory + p.equipped_items():     # pick up item art added since the save
            item.icon_path = icon_for(item.name, p.gender, p.char_class)
        p.current_hp = p.max_hp
        return p
