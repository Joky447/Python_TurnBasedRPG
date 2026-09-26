import math

import pygame

import assets
import ui
from game_state.game_manager import UNLOCK_ALL_FLOORS
from game_state.state import GameState
from world.floor_map import ROWS

NODE_STYLE = {
    "fight":    {"color": (170, 70, 60),  "label": "Battle",   "desc": "Fight a monster of this floor."},
    "elite":    {"color": (200, 60, 170), "label": "Elite",    "desc": "A dangerous foe. Better rewards."},
    "rest":     {"color": (230, 140, 50), "label": "Campfire", "desc": "Rest to heal, or train a skill."},
    "treasure": {"color": (220, 190, 70), "label": "Treasure", "desc": "Find a new weapon or skill."},
    "boss":     {"color": (220, 40, 40),  "label": "Boss",     "desc": "The guardian of this floor."},
}


class MapState(GameState):
    def __init__(self, game_manager):
        super().__init__(game_manager)
        w, h = game_manager.screen.get_size()
        self.bg_image = assets.load_background("map/RPGMAP.png", (w, h))

        # Centers of the round floor pins painted on the world map (at 1280x720)
        self.floor_pins = {1: (190, 565), 2: (420, 436), 3: (649, 320), 4: (874, 212), 5: (1110, 80)}
        self.pin_radius = 27

        # Pop-up window with the branching rooms of the current floor. It stays
        # closed so the world map art is visible, and opens from the floor pin.
        self.path_panel = pygame.Rect(w // 2 - 230, h // 2 - 215, 460, 430)
        self.node_radius = 24
        self.node_positions = {}   # MapNode -> (x, y)
        self.focus = 0
        self.panel_open = False
        self.open_btn = pygame.Rect(w - 250, h - 76, 230, 56)

    def enter(self, **kwargs):
        self.layout_nodes()
        self.focus = 0
        self.panel_open = False

    def pin_at(self, pos):
        """Floor number of the pin under pos, or None."""
        for level, (x, y) in self.floor_pins.items():
            if math.hypot(pos[0] - x, pos[1] - y) <= self.pin_radius + 12:
                return level
        return None

    def on_current_pin(self, pos):
        return self.pin_at(pos) == self.game_manager.current_floor

    def jump_to(self, level):
        self.game_manager.jump_to_floor(level)
        self.layout_nodes()
        self.focus = 0

    def layout_nodes(self):
        fmap = self.game_manager.floor_map
        p = self.path_panel
        top, bottom = p.y + 110, p.bottom - 64
        self.node_positions = {}
        for r, row in enumerate(fmap.rows):
            y = bottom - (bottom - top) * r / (ROWS - 1)
            for c, node in enumerate(row):
                x = p.centerx + (c - (len(row) - 1) / 2) * 115
                self.node_positions[node] = (int(x), int(y))

    def choose(self, node):
        gm = self.game_manager
        gm.floor_map.move_to(node)
        if node.type in ("fight", "elite", "boss"):
            gm.change_state("CombatState", rank={"fight": "normal"}.get(node.type, node.type))
        elif node.type == "rest":
            gm.change_state("RewardState", mode="rest")
        else:
            gm.change_state("RewardState", mode="treasure")

    def node_at(self, pos):
        for node in self.game_manager.floor_map.available():
            x, y = self.node_positions[node]
            if math.hypot(pos[0] - x, pos[1] - y) <= self.node_radius + 6:
                return node
        return None

    def handle_events(self, events):
        available = self.game_manager.floor_map.available()
        for event in events:
            if not self.panel_open:
                if UNLOCK_ALL_FLOORS and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    level = self.pin_at(event.pos)
                    if level and level != self.game_manager.current_floor:
                        self.jump_to(level)
                        continue
                if UNLOCK_ALL_FLOORS and event.type == pygame.KEYDOWN and pygame.K_1 <= event.key <= pygame.K_5:
                    self.jump_to(event.key - pygame.K_0)
                    continue
                opens = (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                         and (self.on_current_pin(event.pos) or self.open_btn.collidepoint(event.pos)))                     or (event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE))
                if opens:
                    self.panel_open = True
                continue
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                node = self.node_at(event.pos)
                if node:
                    self.choose(node)
                    return
                if not self.path_panel.collidepoint(event.pos):
                    self.panel_open = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.panel_open = False
            elif event.type == pygame.KEYDOWN and available:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self.focus = (self.focus - 1) % len(available)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.focus = (self.focus + 1) % len(available)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.choose(available[self.focus % len(available)])
                    return
                elif pygame.K_1 <= event.key <= pygame.K_3 and event.key - pygame.K_1 < len(available):
                    self.choose(available[event.key - pygame.K_1])
                    return

    def draw(self, screen):
        gm = self.game_manager
        if self.bg_image:
            screen.blit(self.bg_image, (0, 0))
        else:
            screen.fill((20, 30, 20))
        mouse = pygame.mouse.get_pos()
        pulse = (math.sin(pygame.time.get_ticks() / 250) + 1) / 2

        # --- World map floor pins (decorate the pins painted on the map) ---
        for level, (x, y) in self.floor_pins.items():
            r = self.pin_radius
            if level > gm.current_floor and not UNLOCK_ALL_FLOORS:   # locked: darken the pin
                shade = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(shade, (0, 0, 0, 140), (r, r), r)
                screen.blit(shade, (x - r, y - r))
            elif level < gm.current_floor and not UNLOCK_ALL_FLOORS:   # cleared: green check badge
                pygame.draw.circle(screen, (25, 60, 30), (x + r - 4, y - r + 4), 12)
                pygame.draw.circle(screen, (140, 230, 140), (x + r - 4, y - r + 4), 12, 2)
                ui.check_icon(screen, (x + r - 4, y - r + 5), 6)
            elif level == gm.current_floor:  # current: pulsing ring + bouncing marker
                pygame.draw.circle(screen, ui.GOLD, (x, y), int(r + 5 + 5 * pulse), 3)
                my = y - r - 22 - 6 * pulse
                pygame.draw.polygon(screen, (0, 0, 0), [(x - 12, my - 3), (x + 12, my - 3), (x, my + 15)])
                pygame.draw.polygon(screen, ui.GOLD, [(x - 9, my - 1), (x + 9, my - 1), (x, my + 11)])
                ui.text_shadow(screen, "You are here", 15, ui.GOLD, midbottom=(x, my - 6))

        # --- HUD ---
        player = gm.player
        hud = pygame.Rect(20, 16, 420, 70)
        ui.panel(screen, hud)
        ui.text(screen, f"Floor {gm.current_floor}/5", 26, ui.GOLD, True, topleft=(hud.x + 16, hud.y + 8))
        ui.text(screen, f"{player.weapon.name}  (+{player.stat_bonus} dmg)", 16, ui.TEXT_DIM, topleft=(hud.x + 16, hud.y + 42))
        ui.health_bar(screen, hud.x + 190, hud.y + 14, player, width=210)

        if not self.panel_open:
            hovered_pin = self.on_current_pin(mouse)
            ui.button(screen, self.open_btn, "Choose Path  [Enter]", self.open_btn.collidepoint(mouse) or hovered_pin,
                      color=(50, 90, 60), hover_color=(70, 130, 80), size=20)
            if hovered_pin:
                ui.tooltip(screen, [(f"Floor {gm.current_floor}", ui.GOLD), ("Click to choose your path.", ui.TEXT)], mouse, 220)
            elif UNLOCK_ALL_FLOORS and self.pin_at(mouse):
                ui.tooltip(screen, [(f"Floor {self.pin_at(mouse)}", ui.GOLD), ("Click to jump here (test mode).", ui.TEXT)], mouse, 240)
            if UNLOCK_ALL_FLOORS:
                banner = pygame.Rect(20, screen.get_height() - 62, 470, 42)
                ui.panel(screen, banner, (60, 20, 20), (230, 120, 90), 220, 8)
                ui.text(screen, "TEST MODE: all floors open. Click a floor or press 1-5.", 16, (255, 210, 190), True,
                        center=banner.center)
            return

        # --- Floor path pop-up ---
        ui.dim(screen, 120)
        ui.panel(screen, self.path_panel, alpha=255)
        ui.text(screen, f"Floor {gm.current_floor}: choose your path", 24, ui.GOLD, True,
                center=(self.path_panel.centerx, self.path_panel.y + 30))
        ui.text(screen, "Click a glowing room (Arrows + Enter)   ·   Esc to close", 15, ui.TEXT_DIM,
                center=(self.path_panel.centerx, self.path_panel.y + 58))

        fmap = gm.floor_map
        available = fmap.available()
        # Connections
        for row in fmap.rows[:-1]:
            for node in row:
                for c in node.children:
                    child = fmap.rows[node.row + 1][c]
                    walked = node.visited and child.visited
                    color = ui.GOLD if walked else (110, 110, 120)
                    pygame.draw.line(screen, color, self.node_positions[node], self.node_positions[child], 4 if walked else 2)

        hovered = None
        for node, pos in self.node_positions.items():
            style = NODE_STYLE[node.type]
            r = self.node_radius + (8 if node.type == "boss" else 0)
            is_available = node in available
            is_focus = is_available and available.index(node) == self.focus % len(available)
            if is_available and (math.hypot(mouse[0] - pos[0], mouse[1] - pos[1]) <= r + 6):
                hovered, is_focus = node, True
            if is_available:
                pygame.draw.circle(screen, ui.GOLD, pos, int(r + 5 + 4 * pulse), 3 if is_focus else 2)
            fill = style["color"] if (is_available or node.visited) else tuple(c // 3 for c in style["color"])
            pygame.draw.circle(screen, fill, pos, r)
            pygame.draw.circle(screen, (240, 240, 240) if node is fmap.current else (30, 30, 30), pos, r, 3)
            self.draw_node_icon(screen, node.type, pos)
            if node.visited and node is not fmap.current:
                ui.check_icon(screen, (pos[0] + r - 4, pos[1] - r + 4), 7)

        if fmap.current:
            cx, cy = self.node_positions[fmap.current]
            pygame.draw.circle(screen, (240, 240, 240), (cx, cy), self.node_radius + 4, 3)

        # Legend
        x = self.path_panel.x + 24
        for t in ("fight", "elite", "rest", "treasure"):
            pygame.draw.circle(screen, NODE_STYLE[t]["color"], (x + 8, self.path_panel.bottom - 20), 8)
            x = ui.text(screen, NODE_STYLE[t]["label"], 15, ui.TEXT, midleft=(x + 20, self.path_panel.bottom - 20)).right + 22

        if hovered:
            style = NODE_STYLE[hovered.type]
            ui.tooltip(screen, [(style["label"], style["color"]), (style["desc"], ui.TEXT)], mouse, 240)

    @staticmethod
    def draw_node_icon(screen, node_type, pos):
        x, y = pos
        if node_type == "fight":
            ui.sword_icon(screen, pos, 11)
        elif node_type == "elite":
            ui.sword_icon(screen, (x - 5, y), 10)
            ui.sword_icon(screen, (x + 5, y), 10)
        elif node_type == "rest":
            pygame.draw.polygon(screen, (255, 220, 120), [(x, y - 13), (x + 9, y + 7), (x - 9, y + 7)])
            pygame.draw.line(screen, (110, 70, 40), (x - 11, y + 10), (x + 11, y + 10), 4)
        elif node_type == "treasure":
            pygame.draw.rect(screen, (120, 80, 40), (x - 12, y - 7, 24, 17), border_radius=3)
            pygame.draw.rect(screen, (250, 220, 90), (x - 12, y - 7, 24, 17), 2, border_radius=3)
            pygame.draw.rect(screen, (250, 220, 90), (x - 3, y - 2, 6, 6))
        elif node_type == "boss":
            pygame.draw.polygon(screen, ui.GOLD, [(x - 16, y + 8), (x - 16, y - 8), (x - 8, y), (x, y - 14),
                                                  (x + 8, y), (x + 16, y - 8), (x + 16, y + 8)])
