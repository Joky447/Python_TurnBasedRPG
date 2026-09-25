"""Procedural branching path for one floor (5 rooms deep, boss at the top)."""
import random

ROWS = 5
NODE_TYPES = ("fight", "elite", "rest", "treasure", "boss")


class MapNode:
    def __init__(self, row: int, col: int, node_type: str):
        self.row = row
        self.col = col
        self.type = node_type
        self.children: list[int] = []   # column indices in the next row
        self.visited = False


class FloorMap:
    def __init__(self, floor: int):
        self.floor = floor
        self.rows: list[list[MapNode]] = []
        self.current: MapNode | None = None
        self._generate()

    def _generate(self):
        widths = [random.randint(2, 3) for _ in range(ROWS - 1)] + [1]
        for r, width in enumerate(widths):
            row = []
            for c in range(width):
                row.append(MapNode(r, c, self._roll_type(r)))
            self.rows.append(row)

        # Guarantee a campfire right before the boss
        pre_boss = self.rows[ROWS - 2]
        if not any(n.type == "rest" for n in pre_boss):
            random.choice(pre_boss).type = "rest"

        # Connect each row to the next. Walking both rows left-to-right together
        # means paths never cross, and every node gets at least one link in and out.
        for r in range(ROWS - 1):
            here, nxt = self.rows[r], self.rows[r + 1]
            i = j = 0
            here[0].children.append(0)
            while i < len(here) - 1 or j < len(nxt) - 1:
                if i == len(here) - 1:
                    j += 1
                elif j == len(nxt) - 1:
                    i += 1
                else:
                    step = random.choice(("left", "right", "both"))
                    if step in ("left", "both"):
                        i += 1
                    if step in ("right", "both"):
                        j += 1
                here[i].children.append(j)
            for node in here:
                node.children = sorted(set(node.children))

    @staticmethod
    def _roll_type(row: int) -> str:
        if row == ROWS - 1:
            return "boss"
        if row == 0:
            return "fight"
        return random.choices(("fight", "elite", "rest", "treasure"), weights=(55, 15, 15, 15))[0]

    def available(self) -> list[MapNode]:
        """Nodes the player may move to next."""
        if self.current is None:
            return list(self.rows[0])
        if self.current.row == ROWS - 1:
            return []
        return [self.rows[self.current.row + 1][c] for c in self.current.children]

    def move_to(self, node: MapNode):
        self.current = node
        node.visited = True
