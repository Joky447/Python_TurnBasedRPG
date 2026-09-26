import pygame

import assets
import ui
from game_state.state import GameState


class MainMenuState(GameState):
    def __init__(self, game_manager):
        super().__init__(game_manager)
        w, h = game_manager.screen.get_size()
        self.bg = assets.load_background("map/bcgpc.png", (w, h))
        self.options = [("Start Game", self.start), ("Quit", self.quit)]
        self.rects = [pygame.Rect(w // 2 - 130, 340 + i * 90, 260, 64) for i in range(len(self.options))]
        self.focus = 0

    def enter(self, **kwargs):
        self.focus = 0
        assets.play_music("title")

    def start(self):
        self.game_manager.new_run()
        self.game_manager.change_state("CharacterCreationState")

    def quit(self):
        self.game_manager.running = False

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEMOTION:
                for i, rect in enumerate(self.rects):
                    if rect.collidepoint(event.pos):
                        self.focus = i
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
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
                elif event.key == pygame.K_ESCAPE:
                    self.quit()

    def draw(self, screen):
        if self.bg:
            screen.blit(self.bg, (0, 0))
            ui.dim(screen, 110)
        else:
            screen.fill(ui.BG)

        cx = screen.get_width() // 2
        ui.text_shadow(screen, "Turn-Based RPG", 72, ui.GOLD, center=(cx, 170))
        ui.text_shadow(screen, "Climb five floors. Read your enemy. Survive.", 24, ui.TEXT, False, center=(cx, 240))

        for i, (label, _) in enumerate(self.options):
            is_quit = label == "Quit"
            ui.button(screen, self.rects[i], label, hovered=self.focus == i,
                      color=(100, 30, 30) if is_quit else None,
                      hover_color=(150, 40, 40) if is_quit else None, size=28)

        ui.text(screen, "Mouse or Arrow keys + Enter", 16, ui.TEXT_DIM, center=(cx, screen.get_height() - 30))
