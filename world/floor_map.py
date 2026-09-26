"""The fixed sequence of fights on one floor.

Every enemy of the floor is fought once, in order: regular enemies from weakest
to strongest, then the elite, then the boss. The reward screen appears only
after the fight right before the boss.
"""
from mobs_boss.enemy_library import FLOOR_POOLS, TEMPLATES

# Title shown for each regular fight, in order. Elite and boss have fixed titles.
REGULAR_TITLES = ["Scout", "Fighter", "Warrior", "Veteran", "Champion"]


class Encounter:
    def __init__(self, number: int, enemy: str, rank: str, title: str):
        self.number = number        # 1-based position on the floor
        self.enemy = enemy          # template name in enemy_library.TEMPLATES
        self.rank = rank            # "normal", "elite" or "boss"
        self.title = title
        self.done = False


class FloorMap:
    def __init__(self, floor: int):
        self.floor = floor
        pool = FLOOR_POOLS[min(max(floor, 1), max(FLOOR_POOLS))]
        regulars = sorted(pool["normal"], key=lambda name: TEMPLATES[name]["hp"])
        order = [(n, "normal") for n in regulars] + [(n, "elite") for n in pool["elite"]] + \
                [(n, "boss") for n in pool["boss"]]
        self.encounters = []
        for i, (name, rank) in enumerate(order):
            if rank == "normal":
                title = REGULAR_TITLES[min(i, len(REGULAR_TITLES) - 1)]
            else:
                title = "Elite" if rank == "elite" else "Floor Boss"
            self.encounters.append(Encounter(i + 1, name, rank, title))
        self.index = 0              # the next fight to take on

    @property
    def current(self) -> Encounter | None:
        return self.encounters[self.index] if self.index < len(self.encounters) else None

    @property
    def total(self) -> int:
        return len(self.encounters)

    def complete_current(self):
        if self.current:
            self.current.done = True
            self.index += 1

    def next_is_boss(self) -> bool:
        return self.current is not None and self.current.rank == "boss"
