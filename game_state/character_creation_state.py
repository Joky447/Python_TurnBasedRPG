import pygame

import animation
import assets
import ui
from character.player import Player
from game_state.state import GameState
from inventory_mechanics.weapon_library import STARTING_WEAPONS, get_weapon

CLASS_BLURBS = {
    "Swordsman": "Sturdy melee fighter. Strong blocks and heavy hits.",
    "Sorcerist": "Fragile spellcaster. Burns, curses and big spells.",
}


class CharacterCreationState(GameState):
    def __init__(self, game_manager):
        super().__init__(game_manager)
        w, h = game_manager.screen.get_size()
        self.bg = assets.load_background("map/bcgpc.png", (w, h))

        # Selection state
        self.selected_gender = "Boy"
        self.selected_class = "Swordsman"

        # Buttons
        self.btn_boy = pygame.Rect(90, 230, 200, 60)
        self.btn_girl = pygame.Rect(310, 230, 200, 60)
        self.btn_swordsman = pygame.Rect(90, 390, 200, 60)
        self.btn_sorcerist = pygame.Rect(310, 390, 200, 60)
        self.btn_confirm = pygame.Rect(w // 2 - 120, h - 100, 240, 64)
        self.preview_panel = pygame.Rect(620, 130, 580, 470)
        self.preview = None

    def enter(self, **kwargs):
        self.refresh_preview()

    def refresh_preview(self):
        self.preview = animation.hero_sprite(self.selected_gender, self.selected_class, 0, height=320)
        self.preview_timer = 0

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if self.btn_boy.collidepoint(pos):
                    self.select(gender="Boy")
                elif self.btn_girl.collidepoint(pos):
                    self.select(gender="Girl")
                elif self.btn_swordsman.collidepoint(pos):
                    self.select(char_class="Swordsman")
                elif self.btn_sorcerist.collidepoint(pos):
                    self.select(char_class="Sorcerist")
                elif self.btn_confirm.collidepoint(pos):
                    self.confirm()
                    return
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d):
                    self.select(gender="Girl" if self.selected_gender == "Boy" else "Boy")
                elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_w, pygame.K_s):
                    self.select(char_class="Sorcerist" if self.selected_class == "Swordsman" else "Swordsman")
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.confirm()
                    return
                elif event.key == pygame.K_ESCAPE:
                    self.game_manager.change_state("MainMenuState")
                    return

    def select(self, gender=None, char_class=None):
        self.selected_gender = gender or self.selected_gender
        self.selected_class = char_class or self.selected_class
        self.refresh_preview()

    def confirm(self):
        self.create_character()
        self.game_manager.change_state("LobbyState")

    def create_character(self):
        weapon = get_weapon(STARTING_WEAPONS[self.selected_class])
        player = Player(name="Hero", gender=self.selected_gender, char_class=self.selected_class, weapon=weapon)
        if self.selected_class == "Sorcerist":
            player.max_hp = player.current_hp = 70
        self.game_manager.player = player

    def update(self):
        # Show off the attack animation every few seconds
        self.preview.update(self.game_manager.dt)
        self.preview_timer += self.game_manager.dt
        if self.preview_timer > 2500 and not self.preview.busy:
            self.preview_timer = 0
            self.preview.play("attack")

    def draw(self, screen):
        if self.bg:
            screen.blit(self.bg, (0, 0))
            ui.dim(screen, 150)
        else:
            screen.fill(ui.BG)
        mouse = pygame.mouse.get_pos()

        ui.text_shadow(screen, "Create Your Character", 48, ui.GOLD, center=(screen.get_width() // 2, 70))

        ui.text(screen, "Select Gender  (Left/Right)", 24, ui.TEXT_DIM, True, topleft=(90, 190))
        ui.button(screen, self.btn_boy, "Boy", self.btn_boy.collidepoint(mouse), selected=self.selected_gender == "Boy")
        ui.button(screen, self.btn_girl, "Girl", self.btn_girl.collidepoint(mouse), selected=self.selected_gender == "Girl")

        ui.text(screen, "Select Class  (Up/Down)", 24, ui.TEXT_DIM, True, topleft=(90, 350))
        ui.button(screen, self.btn_swordsman, "Swordsman", self.btn_swordsman.collidepoint(mouse),
                  selected=self.selected_class == "Swordsman")
        ui.button(screen, self.btn_sorcerist, "Sorcerist", self.btn_sorcerist.collidepoint(mouse),
                  selected=self.selected_class == "Sorcerist")
        ui.text_wrapped(screen, CLASS_BLURBS[self.selected_class], 20, pygame.Rect(90, 470, 420, 80), ui.TEXT)

        # Preview + starting kit
        ui.panel(screen, self.preview_panel)
        feet = (self.preview_panel.x + 170, self.preview_panel.bottom - 40)
        pygame.draw.ellipse(screen, (0, 0, 0), (feet[0] - 80, feet[1] - 12, 160, 24))
        self.preview.draw(screen, feet)

        weapon = get_weapon(STARTING_WEAPONS[self.selected_class])
        x = self.preview_panel.x + 330
        ui.text(screen, weapon.name, 24, ui.GOLD, True, topleft=(x, self.preview_panel.y + 30))
        ui.text(screen, f"+{weapon.stat_bonus} damage", 18, ui.TEXT_DIM, topleft=(x, self.preview_panel.y + 62))
        y = self.preview_panel.y + 100
        for skill in weapon.skills:
            ui.text(screen, f"{skill.name}  ({skill.energy_cost})", 19, skill.color, True, topleft=(x, y))
            y = ui.text_wrapped(screen, skill.summary(), 16, pygame.Rect(x, y + 24, 230, 60), ui.TEXT) + 10

        ui.button(screen, self.btn_confirm, "Confirm", self.btn_confirm.collidepoint(mouse), size=28,
                  color=(50, 90, 60), hover_color=(70, 130, 80))
