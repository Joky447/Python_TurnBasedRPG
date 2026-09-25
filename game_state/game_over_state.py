import pygame

import assets
import ui
from game_state.state import GameState


class GameOverState(GameState):
    """End of a run, either by defeat or by clearing all 5 floors."""
    def __init__(self, game_manager):
        super().__init__(game_manager)
        w, h = game_manager.screen.get_size()
        self.w, self.h = w, h
        self.bg = assets.load_background("map/bcgpc.png", (w, h))
        self.btn_retry = pygame.Rect(w // 2 - 250, h - 150, 230, 64)
        self.btn_menu = pygame.Rect(w // 2 + 20, h - 150, 230, 64)
        self.victory = False

    def enter(self, victory=False, **kwargs):
        self.victory = victory
        self.last_class = None
        p = self.game_manager.player
        if p:
            self.last_class = (p.gender, p.char_class)

    def retry(self):
        gm = self.game_manager
        gm.new_run()
        creation = gm.states["CharacterCreationState"]
        if self.last_class:
            creation.selected_gender, creation.selected_class = self.last_class
        gm.change_state("CharacterCreationState")

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.btn_retry.collidepoint(event.pos):
                    self.retry()
                    return
                if self.btn_menu.collidepoint(event.pos):
                    self.game_manager.change_state("MainMenuState")
                    return
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_r):
                    self.retry()
                    return
                if event.key == pygame.K_ESCAPE:
                    self.game_manager.change_state("MainMenuState")
                    return

    def draw(self, screen):
        if self.bg:
            screen.blit(self.bg, (0, 0))
            ui.dim(screen, 180)
        else:
            screen.fill(ui.BG)
        gm = self.game_manager
        cx = self.w // 2

        if self.victory:
            ui.text_shadow(screen, "VICTORY", 84, ui.GOLD, center=(cx, 140))
            ui.text_shadow(screen, "You conquered all five floors!", 28, ui.TEXT, False, center=(cx, 215))
        else:
            ui.text_shadow(screen, "GAME OVER", 84, ui.RED, center=(cx, 140))
            ui.text_shadow(screen, f"You fell on floor {gm.current_floor}, room {gm.current_encounter}.", 28, ui.TEXT,
                           False, center=(cx, 215))

        box = pygame.Rect(cx - 220, 270, 440, 230)
        ui.panel(screen, box)
        rows = [("Floor reached", gm.current_floor), ("Enemies defeated", gm.stats["enemies"]),
                ("Elites defeated", gm.stats["elites"]), ("Bosses defeated", gm.stats["bosses"]),
                ("Damage dealt", gm.stats["damage"])]
        y = box.y + 24
        for label, value in rows:
            ui.text(screen, label, 22, ui.TEXT_DIM, topleft=(box.x + 30, y))
            ui.text(screen, value, 22, ui.TEXT, True, topright=(box.right - 30, y))
            y += 38

        mouse = pygame.mouse.get_pos()
        ui.button(screen, self.btn_retry, "Play Again  [R]", self.btn_retry.collidepoint(mouse), size=22,
                  color=(50, 90, 60), hover_color=(70, 130, 80))
        ui.button(screen, self.btn_menu, "Main Menu  [Esc]", self.btn_menu.collidepoint(mouse), size=22)
