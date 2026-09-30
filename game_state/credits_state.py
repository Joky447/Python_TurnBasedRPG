import pygame

import assets
import ui
from game_state.state import GameState

TEAM = [
    ("Project Lead", "Bernce Joseph E. Borabo"),
    ("DevOps Engineer", "Demel M. Vivares Jr."),
    ("Character Design and Development", "Claude Emil A. Lorejo and AJ Nathaniel Manisan"),
    ("Menu and UI", "Stephanie E. Marapao and Aloha Jean C. Lapiz"),
    ("Map Design", "Steven Jey G. Decenan and Cedrick Samonte"),
    ("Mobs and Boss", "Belle Brainner B. Villagonzalo and Neil Bryan C. Cagadas"),
    ("QA, Game Tester & Sound Effects", "Cliff Harry E. Paran and Levon Jenu V. Lacia"),
    ("Inventory & Mechanics", "Rynz Karl J. Cebua and Lyster Loyd C. Cabillas"),
    ("Skills", "Mhike Clifford D. Boniao"),
]

MUSIC_BY = "Kevin MacLeod (incompetech.com)"
MUSIC_TRACKS = ["Teller of the Tales", "Darkling", "Burnt Spirit", "That Zen Moment"]
MUSIC_LICENSE = ["Licensed under Creative Commons: By Attribution 4.0 License",
                 "http://creativecommons.org/licenses/by/4.0/"]

COLS, CARD_W, CARD_H, GAP = 3, 340, 104, 18


class CreditsState(GameState):
    """The development team, opened from the main menu: a grid of role cards, then the music credit."""
    def __init__(self, game_manager):
        super().__init__(game_manager)
        w, h = game_manager.screen.get_size()
        self.w = w
        self.bg = assets.load_background("map/bcgpc.png", (w, h))
        self.panel = pygame.Rect(0, 0, 1160, h - 24)
        self.panel.center = (w // 2, h // 2)
        grid_w = COLS * CARD_W + (COLS - 1) * GAP
        x0, y0 = w // 2 - grid_w // 2, self.panel.y + 96
        self.cards = [pygame.Rect(x0 + (i % COLS) * (CARD_W + GAP), y0 + (i // COLS) * (CARD_H + GAP), CARD_W, CARD_H)
                      for i in range(len(TEAM))]
        self.music_rect = pygame.Rect(x0, self.cards[-1].bottom + GAP + 6, grid_w, 138)
        self.back_rect = pygame.Rect(0, 0, 200, 50)
        self.back_rect.midbottom = (self.panel.centerx, self.panel.bottom - 14)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.back_rect.collidepoint(event.pos) or                     event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                self.game_manager.change_state("MainMenuState")
                return

    def draw_card(self, screen, rect, role, names):
        ui.panel(screen, rect, (14, 28, 62), (150, 112, 56), 215, 10)
        pygame.draw.rect(screen, ui.GOLD, (rect.x + 14, rect.y + 1, rect.width - 28, 3), border_radius=2)
        ui.text(screen, role.upper(), 14, ui.GOLD, True, center=(rect.centerx, rect.y + 26))
        lines = names.split(" and ")
        step = 26
        y = rect.y + 62 + (2 - len(lines)) * step // 2 - (0 if len(lines) > 1 else 6)
        for line in lines:
            ui.text(screen, line, 21, ui.TEXT, center=(rect.centerx, y))
            y += step

    def draw(self, screen):
        if self.bg:
            screen.blit(self.bg, (0, 0))
        else:
            screen.fill(ui.BG)
        ui.dim(screen, 120)
        p = self.panel
        ui.panel(screen, p, alpha=235)
        ui.text_shadow(screen, "Development Team", 42, ui.GOLD, center=(p.centerx, p.y + 44))
        # ornamental divider under the title
        cy = p.y + 76
        for sign in (-1, 1):
            pygame.draw.line(screen, ui.PANEL_BORDER, (p.centerx + sign * 20, cy), (p.centerx + sign * 220, cy), 2)
        pygame.draw.polygon(screen, ui.GOLD, [(p.centerx, cy - 6), (p.centerx + 6, cy), (p.centerx, cy + 6), (p.centerx - 6, cy)])

        for rect, (role, names) in zip(self.cards, TEAM):
            self.draw_card(screen, rect, role, names)

        m = self.music_rect
        ui.panel(screen, m, (14, 28, 62), (150, 112, 56), 215, 10)
        ui.text(screen, "MUSIC", 14, ui.GOLD, True, center=(m.centerx, m.y + 20))
        ui.text(screen, MUSIC_BY, 22, ui.TEXT, True, center=(m.centerx, m.y + 46))
        tracks = "   ·   ".join(f"“{t}”" for t in MUSIC_TRACKS)
        ui.text(screen, tracks, 18, ui.GOLD_LIGHT, center=(m.centerx, m.y + 74))
        for i, line in enumerate(MUSIC_LICENSE):
            ui.text(screen, line, 14, ui.TEXT_DIM, center=(m.centerx, m.y + 98 + i * 17))

        ui.button(screen, self.back_rect, "Back", self.back_rect.collidepoint(pygame.mouse.get_pos()), True, size=20)
