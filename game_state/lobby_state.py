import pygame

import animation
import assets
import ui
from game_state.state import GameState


class LobbyState(GameState):
    def __init__(self, game_manager):
        super().__init__(game_manager)
        w, h = game_manager.screen.get_size()
        self.bg = assets.load_background("map/bcgpc.png", (w, h))
        self.btn_start = pygame.Rect(w // 2 - 160, h - 100, 320, 64)
        self.hero = None

    def enter(self, **kwargs):
        p = self.game_manager.player
        self.hero = animation.hero_sprite(p.gender, p.char_class, p.weapon.tier, height=300)

    def handle_events(self, events):
        for event in events:
            if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.btn_start.collidepoint(event.pos)) \
                    or (event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE)):
                self.game_manager.change_state("MapState")
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game_manager.change_state("CharacterCreationState")
                return

    def update(self):
        self.hero.update(self.game_manager.dt)

    def draw(self, screen):
        if self.bg:
            screen.blit(self.bg, (0, 0))
            ui.dim(screen, 150)
        else:
            screen.fill(ui.BG)

        player = self.game_manager.player
        if not player:
            return

        ui.text_shadow(screen, "Game Lobby", 48, ui.GOLD, center=(screen.get_width() // 2, 60))

        # Character Info Box
        info_rect = pygame.Rect(80, 120, 440, 470)
        ui.panel(screen, info_rect)
        pygame.draw.ellipse(screen, (0, 0, 0), (info_rect.x + 40, info_rect.bottom - 42, 160, 24))
        self.hero.draw(screen, (info_rect.x + 120, info_rect.bottom - 30))

        x, y = info_rect.x + 240, info_rect.y + 30
        for label, value in [("Name", player.name), ("Gender", player.gender), ("Class", player.char_class),
                             ("Weapon", player.weapon.name), ("HP", player.max_hp),
                             ("Energy", player.max_energy), ("Damage", f"+{player.stat_bonus}")]:
            ui.text(screen, label, 16, ui.TEXT_DIM, topleft=(x, y))
            ui.text(screen, value, 22, ui.TEXT, True, topleft=(x, y + 18))
            y += 54

        # Skills Box
        skills_rect = pygame.Rect(560, 120, 640, 470)
        ui.panel(screen, skills_rect)
        ui.text(screen, "Equipped Skills", 26, ui.GOLD, True, topleft=(skills_rect.x + 30, skills_rect.y + 24))

        y = skills_rect.y + 80
        for i, skill in enumerate(player.equipped_skills):
            ui.text(screen, f"[{i + 1}] {skill.name}", 22, skill.color, True, topleft=(skills_rect.x + 30, y))
            ui.text(screen, f"{skill.energy_cost} Energy", 18, ui.ENERGY, True, topright=(skills_rect.right - 30, y + 2))
            ui.text(screen, skill.summary(), 18, ui.TEXT, topleft=(skills_rect.x + 30, y + 30))
            ui.text(screen, skill.description, 16, ui.TEXT_DIM, topleft=(skills_rect.x + 30, y + 54))
            y += 92

        mouse = pygame.mouse.get_pos()
        ui.button(screen, self.btn_start, "Begin Adventure", self.btn_start.collidepoint(mouse), size=28,
                  color=(50, 90, 60), hover_color=(70, 130, 80))
