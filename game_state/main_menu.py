import math

import pygame

import assets
import ui
from game_state.state import GameState


class MainMenuState(GameState):
    """Start screen. The title art (menu_ui/start screen ui.png) has the buttons painted in;
    this screen maps clicks to them and highlights the one under the mouse or keyboard focus."""
    ART = "menu_ui/start screen ui.png"
    ART_SIZE = (1675, 939)
    # Where the painted buttons are in the original art: (left, top, right, bottom)
    BUTTONS_IN_ART = [(603, 447, 1072, 543), (617, 571, 1045, 655)]

    def __init__(self, game_manager):
        super().__init__(game_manager)
        w, h = game_manager.screen.get_size()
        self.art = assets.load_background(self.ART, (w, h))
        self.bg = assets.load_background("map/bcgpc.png", (w, h))
        self.options = [("Start Game", self.start), ("Quit", self.quit)]
        sx, sy = w / self.ART_SIZE[0], h / self.ART_SIZE[1]
        self.rects = [pygame.Rect(round(l * sx), round(t * sy), round((r - l) * sx), round((b - t) * sy))
                      for l, t, r, b in self.BUTTONS_IN_ART]
        self.focus = 0
        self.settings_rect = pygame.Rect(w - 170, h - 66, 150, 46)
        self.credits_rect = pygame.Rect(20, h - 66, 150, 46)

    def enter(self, **kwargs):
        self.focus = 0
        assets.play_music("title")

    def start(self):
        gm = self.game_manager
        gm.new_run()
        # Returning players go to Base Camp; the first time, make a character
        gm.change_state("LobbyState" if gm.roster else "CharacterCreationState")

    def open_settings(self):
        self.game_manager.change_state("SettingsState", back="MainMenuState")

    def quit(self):
        self.game_manager.running = False

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEMOTION:
                for i, rect in enumerate(self.rects):
                    if rect.collidepoint(event.pos):
                        self.focus = i
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.settings_rect.collidepoint(event.pos):
                    self.open_settings()
                    return
                if self.credits_rect.collidepoint(event.pos):
                    self.game_manager.change_state("CreditsState")
                    return
                for i, rect in enumerate(self.rects):
                    if rect.collidepoint(event.pos):
                        self.options[i][1]()
                        return
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.focus = (self.focus - 1) % len(self.options)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.focus = (self.focus + 1) % len(self.options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.options[self.focus][1]()
                    return
                elif event.key == pygame.K_c:
                    self.game_manager.change_state("CreditsState")
                    return
                elif event.key == pygame.K_o:
                    self.open_settings()
                    return
                elif event.key == pygame.K_ESCAPE:
                    self.quit()

    def draw(self, screen):
        if not self.art:
            self.draw_fallback(screen)
            return
        screen.blit(self.art, (0, 0))

        # Highlight the focused painted button: a soft light over it plus a pulsing gold frame
        rect = self.rects[self.focus]
        pulse = (math.sin(pygame.time.get_ticks() / 250) + 1) / 2
        k = int(22 + 18 * pulse)
        glow = pygame.Surface(rect.size)
        pygame.draw.rect(glow, (k, k, int(k * 0.7)), glow.get_rect().inflate(-8, -8), border_radius=14)
        screen.blit(glow, rect.topleft, special_flags=pygame.BLEND_RGB_ADD)
        frame = rect.inflate(10 + 4 * pulse, 10 + 4 * pulse)
        pygame.draw.rect(screen, (255, 215, 120), frame, 3, border_radius=16)

        ui.pill_button(screen, self.credits_rect, "Credits", self.credits_rect.collidepoint(pygame.mouse.get_pos()),
                       "star")
        ui.gear_button(screen, self.settings_rect, hovered=self.settings_rect.collidepoint(pygame.mouse.get_pos()))
        ui.text_shadow(screen, "Mouse or Arrow keys + Enter  ·  F11 Fullscreen", 15, ui.TEXT_DIM, False,
                       center=(screen.get_width() // 2, screen.get_height() - 24))

    def draw_fallback(self, screen):
        """Plain menu used if the title art is missing."""
        if self.bg:
            screen.blit(self.bg, (0, 0))
            ui.dim(screen, 110)
        else:
            screen.fill(ui.BG)
        cx = screen.get_width() // 2
        ui.text_shadow(screen, "Spells x Blades", 72, ui.GOLD, center=(cx, 170))
        for i, (label, _) in enumerate(self.options):
            is_quit = label == "Quit"
            ui.button(screen, self.rects[i], label, hovered=self.focus == i,
                      color=(100, 30, 30) if is_quit else None,
                      hover_color=(150, 40, 40) if is_quit else None, size=28)
