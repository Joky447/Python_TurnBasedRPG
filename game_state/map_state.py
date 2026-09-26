import math

import pygame

import assets
import ui
from game_state.game_manager import UNLOCK_ALL_FLOORS
from game_state.state import GameState

RANK_COLOR = {"normal": (170, 70, 60), "elite": (200, 60, 170), "boss": (220, 40, 40)}


class MapState(GameState):
    def __init__(self, game_manager):
        super().__init__(game_manager)
        w, h = game_manager.screen.get_size()
        self.bg_image = assets.load_background("map/RPGMAP.png", (w, h))

        # Centers of the round floor pins painted on the world map (at 1280x720)
        self.floor_pins = {1: (190, 565), 2: (420, 436), 3: (649, 320), 4: (874, 212), 5: (1110, 80)}
        self.pin_radius = 27

        # Pop-up listing this floor's fights in order. It stays closed so the
        # world map art is visible, and opens from the floor pin or Enter.
        self.panel = pygame.Rect(w // 2 - 260, 60, 520, h - 120)
        self.panel_open = False
        self.open_btn = pygame.Rect(w - 250, h - 76, 230, 56)
        self.fight_btn = pygame.Rect(0, 0, 260, 54)

    def enter(self, **kwargs):
        self.panel_open = False
        assets.stop_music()     # the title music ends once the adventure starts

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

    def handle_events(self, events):
        gm = self.game_manager
        for event in events:
            click = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
            confirm = event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE)
            if not self.panel_open:
                if UNLOCK_ALL_FLOORS and click:
                    level = self.pin_at(event.pos)
                    if level and level != gm.current_floor:
                        self.jump_to(level)
                        continue
                if UNLOCK_ALL_FLOORS and event.type == pygame.KEYDOWN and pygame.K_1 <= event.key <= pygame.K_5:
                    self.jump_to(event.key - pygame.K_0)
                    continue
                if confirm or (click and (self.on_current_pin(event.pos) or self.open_btn.collidepoint(event.pos))):
                    self.panel_open = True
                continue
            if confirm or (click and self.fight_btn.collidepoint(event.pos)):
                gm.start_next_fight()
                return
            if (click and not self.panel.collidepoint(event.pos)) or                     (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.panel_open = False

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
            enc = gm.floor_map.current
            label = f"Next: {enc.title}  [Enter]" if enc else "Floor cleared"
            ui.button(screen, self.open_btn, label, self.open_btn.collidepoint(mouse) or hovered_pin,
                      color=(50, 90, 60), hover_color=(70, 130, 80), size=19)
            if hovered_pin:
                ui.tooltip(screen, [(f"Floor {gm.current_floor}", ui.GOLD), ("Click to see this floor's fights.", ui.TEXT)],
                           mouse, 240)
            elif UNLOCK_ALL_FLOORS and self.pin_at(mouse):
                ui.tooltip(screen, [(f"Floor {self.pin_at(mouse)}", ui.GOLD), ("Click to jump here (test mode).", ui.TEXT)], mouse, 240)
            if UNLOCK_ALL_FLOORS:
                banner = pygame.Rect(20, screen.get_height() - 62, 470, 42)
                ui.panel(screen, banner, (60, 20, 20), (230, 120, 90), 220, 8)
                ui.text(screen, "TEST MODE: all floors open. Click a floor or press 1-5.", 16, (255, 210, 190), True,
                        center=banner.center)
            return

        # --- This floor's fights, in order ---
        ui.dim(screen, 120)
        p = self.panel
        ui.panel(screen, p, alpha=255)
        fmap = gm.floor_map
        ui.text(screen, f"Floor {gm.current_floor}: {fmap.total} fights", 26, ui.GOLD, True, center=(p.centerx, p.y + 32))
        ui.text(screen, "Defeat them in order. A reward awaits before the boss.", 15, ui.TEXT_DIM,
                center=(p.centerx, p.y + 60))

        row_h = min(58, (p.height - 180) // fmap.total)
        y = p.y + 86
        for enc in fmap.encounters:
            is_next = enc is fmap.current
            row = pygame.Rect(p.x + 24, y, p.width - 48, row_h - 8)
            fill = (45, 45, 62) if is_next else (26, 26, 36)
            ui.panel(screen, row, fill, ui.GOLD if is_next else (80, 80, 95), 255, 8)
            color = RANK_COLOR[enc.rank]
            badge = (row.x + 26, row.centery)
            pygame.draw.circle(screen, color if (is_next or enc.done) else tuple(c // 2 for c in color), badge, 16)
            ui.text(screen, enc.number, 18, ui.TEXT, True, center=badge)
            text_col = ui.TEXT if not enc.done else ui.TEXT_DIM
            ui.text(screen, enc.title, 18, color if not enc.done else ui.TEXT_DIM, True, midleft=(row.x + 56, row.centery - 9))
            ui.text(screen, enc.enemy, 15, text_col, midleft=(row.x + 56, row.centery + 11))
            if enc.done:
                ui.check_icon(screen, (row.right - 26, row.centery), 9)
            elif is_next:
                ui.text(screen, "NEXT", 15, ui.GOLD, True, midright=(row.right - 16, row.centery))
            if enc.rank != "boss" and fmap.encounters[enc.number].rank == "boss" and not enc.done:
                ui.text(screen, "+ Reward after", 14, ui.GOLD, True, midright=(row.right - (80 if is_next else 16), row.centery))
            y += row_h

        self.fight_btn.midbottom = (p.centerx, p.bottom - 34)
        if fmap.current:
            ui.button(screen, self.fight_btn, f"Fight {fmap.current.title}  [Enter]", self.fight_btn.collidepoint(mouse),
                      color=(120, 40, 40), hover_color=(170, 55, 55), size=19)
        ui.text(screen, "Esc to close", 13, ui.TEXT_DIM, midtop=(p.centerx, p.bottom - 18))
