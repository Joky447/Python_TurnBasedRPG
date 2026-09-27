import math
import os

import pygame

import assets
import ui
from game_state.game_manager import UNLOCK_ALL_FLOORS
from game_state.state import GameState
from world.floor_map import FloorMap

GLASS = 160   # how solid the map's panels and buttons are (255 = not see-through)

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
        self.rematch_floor = None
        self.open_btn = pygame.Rect(w - 250, h - 76, 230, 56)
        self.fight_btn = pygame.Rect(0, 0, 260, 54)
        self.camp_btn = pygame.Rect(w - 450, h - 76, 190, 56)
        self.confirm_camp = False       # waiting for a second click when leaving would lose progress

    def enter(self, **kwargs):
        self.panel_open = False
        self.rematch_floor = None       # a cleared floor whose enemy list is open
        self.confirm_camp = False
        assets.play_music("map")

    def update(self):
        gm = self.game_manager
        if gm.notice:
            gm.notice = (gm.notice[0], gm.notice[1] - gm.dt)
            if gm.notice[1] <= 0:
                gm.notice = None

    def pin_at(self, pos):
        """Floor number of the pin under pos, or None."""
        for level, (x, y) in self.floor_pins.items():
            if math.hypot(pos[0] - x, pos[1] - y) <= self.pin_radius + 12:
                return level
        return None

    def on_current_pin(self, pos):
        return self.pin_at(pos) == self.game_manager.current_floor

    @staticmethod
    def enemies_art(level):
        """The floor's enemy line-up picture (mobs_boss/floor<N>/floor <N> enemies.png), trimmed to
        its art; a "(transparent)" copy is used when the original has a baked-in background."""
        folder = assets.path(f"mobs_boss/floor{level}")
        for name in (f"floor {level} enemies (transparent).png", f"floor {level} enemies.png"):
            if os.path.exists(os.path.join(folder, name)):
                return f"mobs_boss/floor{level}/{name}"
        return None

    def draw_enemy_preview(self, screen, level, hint, mouse):
        """Card next to the hovered floor pin showing that floor's enemies."""
        art = self.enemies_art(level)
        cache = self.__dict__.setdefault("_previews", {})
        if art not in cache:
            img = None
            if art:
                raw = pygame.image.load(assets.path(art)).convert_alpha()
                raw = raw.subsurface(raw.get_bounding_rect(20))
                k = min(560 / raw.get_width(), 280 / raw.get_height())
                img = pygame.transform.smoothscale_by(raw, k)
            cache[art] = img
        img = cache[art]
        w = (img.get_width() if img else 300) + 24
        h = (img.get_height() if img else 0) + 50
        box = pygame.Rect(0, 0, w, h)
        box.midbottom = (mouse[0], mouse[1] - 24)
        if box.top < 8:                       # no room above the pin: show it below
            box.midtop = (mouse[0], mouse[1] + 24)
        box.clamp_ip(screen.get_rect().inflate(-16, -16))
        ui.panel(screen, box, alpha=225)
        if img:
            screen.blit(img, (box.x + 12, box.y + 10))
        ui.text(screen, hint, 16, ui.GOLD_LIGHT if hint.startswith("Click") else ui.TEXT_DIM,
                midbottom=(box.centerx, box.bottom - 10))

    def cleared(self, level) -> bool:
        p = self.game_manager.player
        return p is not None and level in p.cleared_floors

    def row_rects(self, fmap):
        p = self.panel
        row_h = min(58, (p.height - 180) // fmap.total)
        return [pygame.Rect(p.x + 24, p.y + 86 + i * row_h, p.width - 48, row_h - 8) for i in range(fmap.total)]

    def draw_rematch_panel(self, screen, mouse):
        """A cleared floor's enemies: pick any one to fight again."""
        ui.dim(screen, 50)
        p = self.panel
        ui.panel(screen, p, alpha=GLASS)
        fmap = FloorMap(self.rematch_floor)
        ui.text(screen, f"Floor {self.rematch_floor} cleared: rematch", 26, ui.GOLD, True, center=(p.centerx, p.y + 32))
        ui.text(screen, "Pick any enemy. No rewards or progress; your HP comes back after.", 15, ui.TEXT_DIM,
                center=(p.centerx, p.y + 60))
        for enc, row in zip(fmap.encounters, self.row_rects(fmap)):
            hovered = row.collidepoint(mouse)
            ui.panel(screen, row, (55, 55, 75) if hovered else (26, 26, 36), ui.GOLD_LIGHT if hovered else ui.GOLD,
                     230 if hovered else GLASS, 8)
            color = RANK_COLOR[enc.rank]
            badge = (row.x + 26, row.centery)
            pygame.draw.circle(screen, color, badge, 16)
            ui.text(screen, enc.number, 18, ui.TEXT, True, center=badge)
            ui.text(screen, enc.title, 18, color, True, midleft=(row.x + 56, row.centery - 9))
            ui.text(screen, enc.enemy, 15, ui.TEXT, midleft=(row.x + 56, row.centery + 11))
            ui.text(screen, "FIGHT" if hovered else f"[{enc.number}]", 15, ui.GOLD_LIGHT if hovered else ui.TEXT_DIM,
                    True, midright=(row.right - 16, row.centery))
        ui.text(screen, "Click an enemy or press its number  ·  Esc to close", 13, ui.TEXT_DIM,
                midtop=(p.centerx, p.bottom - 24))

    def run_in_progress(self) -> bool:
        """True once a fight of the unfinished floor has been won (leaving camp would reset it)."""
        return self.game_manager.floor_map.index > 0

    def go_to_camp(self):
        """Back to Base Camp. Items are kept; floor progress is lost, so that asks for a second click."""
        if self.run_in_progress() and not self.confirm_camp:
            self.confirm_camp = True
            return
        self.game_manager.return_to_camp()

    def jump_to(self, level):
        self.game_manager.jump_to_floor(level)

    def handle_events(self, events):
        gm = self.game_manager
        for event in events:
            click = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
            confirm = event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE)
            if self.rematch_floor:
                fmap = FloorMap(self.rematch_floor)
                if click:
                    for enc, row in zip(fmap.encounters, self.row_rects(fmap)):
                        if row.collidepoint(event.pos):
                            gm.start_rematch(self.rematch_floor, enc.number)
                            return
                    if not self.panel.collidepoint(event.pos):
                        self.rematch_floor = None
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.rematch_floor = None
                elif event.type == pygame.KEYDOWN and pygame.K_1 <= event.key <= pygame.K_9:
                    n = event.key - pygame.K_0
                    if n <= fmap.total:
                        gm.start_rematch(self.rematch_floor, n)
                        return
                continue
            if not self.panel_open:
                if (click and self.camp_btn.collidepoint(event.pos)) or                         (event.type == pygame.KEYDOWN and event.key == pygame.K_b):
                    self.go_to_camp()
                    return
                if click or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    self.confirm_camp = False       # any other action cancels leaving
                if click:
                    level = self.pin_at(event.pos)
                    if level and self.cleared(level) and (level != gm.current_floor or gm.all_cleared):
                        self.rematch_floor = level
                        continue
                if UNLOCK_ALL_FLOORS and click:
                    level = self.pin_at(event.pos)
                    if level and level != gm.current_floor:
                        self.jump_to(level)
                        continue
                if UNLOCK_ALL_FLOORS and event.type == pygame.KEYDOWN and pygame.K_1 <= event.key <= pygame.K_5:
                    self.jump_to(event.key - pygame.K_0)
                    continue
                if gm.all_cleared:          # free play: no run to continue, floors are picked on the map
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
            if level > gm.current_floor and not UNLOCK_ALL_FLOORS and not self.cleared(level):   # locked: darken
                shade = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(shade, (0, 0, 0, 140), (r, r), r)
                screen.blit(shade, (x - r, y - r))
            elif self.cleared(level) and (level != gm.current_floor or gm.all_cleared):   # cleared: green check
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
        ui.panel(screen, hud, alpha=GLASS)
        ui.text(screen, "Free Play" if gm.all_cleared else f"Floor {gm.current_floor}/5", 26, ui.GOLD, True,
                topleft=(hud.x + 16, hud.y + 8))
        ui.text(screen, f"{player.weapon.name}  (+{player.stat_bonus} dmg)", 16, ui.TEXT_DIM, topleft=(hud.x + 16, hud.y + 42))
        ui.health_bar(screen, hud.x + 190, hud.y + 14, player, width=210)

        if gm.notice:
            box = pygame.Rect(0, 0, 560, 50)
            box.midtop = (screen.get_width() // 2, 100)
            ui.panel(screen, box, (40, 30, 12), ui.GOLD, 235, 10)
            ui.text(screen, gm.notice[0], 19, (255, 225, 150), True, center=box.center)

        if self.rematch_floor:
            self.draw_rematch_panel(screen, mouse)
            return
        if not self.panel_open:
            hovered_pin = self.on_current_pin(mouse)
            enc = gm.floor_map.current
            if gm.all_cleared:
                hovered_pin = False
                label = "All floors cleared! Pick any floor"
            else:
                label = f"Next: {enc.title}  [Enter]" if enc else "Floor cleared"
            ui.button(screen, self.open_btn, label, self.open_btn.collidepoint(mouse) or hovered_pin,
                      color=(50, 90, 60), hover_color=(70, 130, 80), size=19, alpha=GLASS)
            camp_label = "Leave run?  [B]" if self.confirm_camp else "Base Camp  [B]"
            ui.button(screen, self.camp_btn, camp_label, self.camp_btn.collidepoint(mouse),
                      color=(110, 40, 40) if self.confirm_camp else None, hover_color=(150, 50, 50) if self.confirm_camp else None,
                      size=18, alpha=GLASS)
            if self.confirm_camp:
                # on a dark plate so it stays crisp over the bright sky
                msg = (f"Floor {gm.current_floor}'s fights will start over. Cleared floors and items are kept. "
                       "Click again to leave.")
                w = assets.font(17).size(msg)[0] + 32
                box = pygame.Rect(0, 0, w, 34)
                box.bottomright = (self.open_btn.right, self.camp_btn.top - 10)
                ui.panel(screen, box, (40, 20, 16), ui.GOLD, 235, 8)
                ui.text(screen, msg, 17, (255, 215, 160), center=box.center)
            level = self.pin_at(mouse)
            if level:
                if hovered_pin:
                    hint = "Click to see this floor's fights."
                elif self.cleared(level):
                    hint = "Cleared! Click to pick an enemy to fight again."
                elif UNLOCK_ALL_FLOORS:
                    hint = "Click to jump here (test mode)."
                else:
                    hint = "Not reached yet."
                self.draw_enemy_preview(screen, level, hint, mouse)
            if UNLOCK_ALL_FLOORS:
                banner = pygame.Rect(20, screen.get_height() - 62, 470, 42)
                ui.panel(screen, banner, (60, 20, 20), (230, 120, 90), 220, 8)
                ui.text(screen, "TEST MODE: all floors open. Click a floor or press 1-5.", 16, (255, 210, 190), True,
                        center=banner.center)
            return

        # --- This floor's fights, in order ---
        ui.dim(screen, 50)
        p = self.panel
        ui.panel(screen, p, alpha=GLASS)
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
            ui.panel(screen, row, fill, ui.GOLD if is_next else (80, 80, 95), GLASS, 8)
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
                      color=(120, 40, 40), hover_color=(170, 55, 55), size=19, alpha=GLASS)
        ui.text(screen, "Esc to close", 13, ui.TEXT_DIM, midtop=(p.centerx, p.bottom - 18))
