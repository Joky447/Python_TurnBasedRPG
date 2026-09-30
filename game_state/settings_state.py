import pygame

import assets
import ui
from game_state.state import GameState

STEP = 0.1      # arrow keys change a slider by this much


class SettingsState(GameState):
    """Options screen: music and sound volume, fullscreen. Saved to settings.json."""
    def __init__(self, game_manager):
        super().__init__(game_manager)
        w, h = game_manager.screen.get_size()
        self.w, self.h = w, h
        self.bg = assets.load_background("map/bcgpc.png", (w, h))
        self.panel = pygame.Rect(0, 0, 640, 420)
        self.panel.center = (w // 2, h // 2)
        x, top = self.panel.x + 60, self.panel.y + 140
        self.sliders = [("music", "Music", pygame.Rect(x + 180, top, 270, 14)),
                        ("sfx", "Sound Effects", pygame.Rect(x + 180, top + 66, 270, 14))]
        self.full_rect = pygame.Rect(x, top + 112, 520, 50)
        self.back_rect = pygame.Rect(0, 0, 220, 54)
        self.back_rect.midbottom = (self.panel.centerx, self.panel.bottom - 30)
        self.back = "MainMenuState"
        self.focus = 0                  # keyboard row: 0 music, 1 sound effects, 2 fullscreen, 3 back
        self.dragging = None

    def enter(self, back="MainMenuState", **kwargs):
        self.back = back
        self.focus = 0
        self.dragging = None

    def leave(self):
        assets.save_settings()
        self.game_manager.change_state(self.back)

    def set_value(self, key, value):
        assets.settings[key] = min(1.0, max(0.0, value))
        if key == "music":
            assets.apply_music_volume()

    def handle_events(self, events):
        gm = self.game_manager
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, (key, _, rect) in enumerate(self.sliders):
                    if rect.inflate(20, 30).collidepoint(event.pos):
                        self.focus, self.dragging = i, (key, rect)
                        self.set_value(key, (event.pos[0] - rect.x) / rect.width)
                if self.full_rect.collidepoint(event.pos):
                    gm.toggle_fullscreen()
                elif self.back_rect.collidepoint(event.pos):
                    self.leave()
                    return
            elif event.type == pygame.MOUSEMOTION and self.dragging:
                key, rect = self.dragging
                self.set_value(key, (event.pos[0] - rect.x) / rect.width)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.dragging:
                    assets.save_settings()
                    if self.dragging[0] == "sfx":
                        assets.play_sound("sword_basic")    # so the new volume can be heard
                self.dragging = None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.leave()
                    return
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self.focus = (self.focus - 1) % 4
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.focus = (self.focus + 1) % 4
                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d) and self.focus < 2:
                    key = self.sliders[self.focus][0]
                    sign = 1 if event.key in (pygame.K_RIGHT, pygame.K_d) else -1
                    self.set_value(key, round(assets.settings[key] + sign * STEP, 2))
                    assets.save_settings()
                    if key == "sfx":
                        assets.play_sound("sword_basic")
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self.focus == 2:
                        gm.toggle_fullscreen()
                    elif self.focus == 3:
                        self.leave()
                        return

    def draw(self, screen):
        if self.bg:
            screen.blit(self.bg, (0, 0))
        else:
            screen.fill(ui.BG)
        ui.dim(screen, 120)
        p = self.panel
        ui.panel(screen, p, alpha=235)
        ui.text_shadow(screen, "Settings", 44, ui.GOLD, center=(p.centerx, p.y + 55))
        ui.text(screen, "Mouse, or Up/Down + Left/Right  ·  Esc to go back", 15, ui.TEXT_DIM,
                center=(p.centerx, p.y + 95))
        mouse = pygame.mouse.get_pos()

        for i, (key, label, rect) in enumerate(self.sliders):
            focused = self.focus == i
            color = ui.GOLD_LIGHT if focused else ui.TEXT
            ui.text(screen, label, 22, color, True, midleft=(p.x + 60, rect.centery))
            value = assets.settings[key]
            pygame.draw.rect(screen, (4, 8, 20), rect.inflate(4, 4), border_radius=9)
            pygame.draw.rect(screen, ui.PANEL_BORDER, rect, border_radius=7)
            fill = rect.copy()
            fill.width = int(rect.width * value)
            pygame.draw.rect(screen, ui.ENERGY, fill, border_radius=7)
            knob = (rect.x + int(rect.width * value), rect.centery)
            pygame.draw.circle(screen, (4, 8, 20), knob, 14)
            pygame.draw.circle(screen, ui.GOLD_LIGHT if focused else ui.GOLD, knob, 11)
            ui.text(screen, f"{round(value * 100)}%", 18, color, True, midleft=(rect.right + 18, rect.centery))

        on = assets.settings["fullscreen"]
        ui.button(screen, self.full_rect, f"Fullscreen: {'ON' if on else 'OFF'}  [F11]",
                  self.full_rect.collidepoint(mouse) or self.focus == 2, True,
                  (50, 90, 60) if on else None, (70, 130, 80) if on else None, 20, selected=self.focus == 2)
        ui.button(screen, self.back_rect, "Back", self.back_rect.collidepoint(mouse) or self.focus == 3, True,
                  size=22, selected=self.focus == 3)
