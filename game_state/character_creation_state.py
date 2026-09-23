import pygame
from game_state.state import GameState
from character.player import Player
from skills.skill import Skill
from inventory_mechanics.weapon import Weapon

class CharacterCreationState(GameState):
    def __init__(self, game_manager):
        super().__init__(game_manager)
        self.font_large = pygame.font.SysFont("Arial", 48, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 28, bold=True)
        
        w = game_manager.screen.get_width()
        h = game_manager.screen.get_height()
        
        # Selection state
        self.selected_gender = "Boy"
        self.selected_class = "Swordsman"
        
        # Buttons
        # Gender Buttons
        self.btn_boy = pygame.Rect(w // 2 - 250, 250, 200, 60)
        self.btn_girl = pygame.Rect(w // 2 + 50, 250, 200, 60)
        
        # Class Buttons
        self.btn_swordsman = pygame.Rect(w // 2 - 250, 400, 200, 60)
        self.btn_sorcerist = pygame.Rect(w // 2 + 50, 400, 200, 60)
        
        # Confirm
        self.btn_confirm = pygame.Rect(w // 2 - 100, 550, 200, 60)
        
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                
                if self.btn_boy.collidepoint(mouse_pos):
                    self.selected_gender = "Boy"
                elif self.btn_girl.collidepoint(mouse_pos):
                    self.selected_gender = "Girl"
                    
                if self.btn_swordsman.collidepoint(mouse_pos):
                    self.selected_class = "Swordsman"
                elif self.btn_sorcerist.collidepoint(mouse_pos):
                    self.selected_class = "Sorcerist"
                    
                if self.btn_confirm.collidepoint(mouse_pos):
                    self.create_character()
                    self.game_manager.change_state("LobbyState")

    def create_character(self):
        if self.selected_class == "Swordsman":
            slash = Skill(name="Slash", energy_cost=1, damage=8, description="A basic blade attack.")
            parry = Skill(name="Parry", energy_cost=1, block=6, description="Raise guard to gain Block.")
            heavy_strike = Skill(name="Heavy Strike", energy_cost=2, damage=14, description="Powerful blow.")
            second_wind = Skill(name="Second Wind", energy_cost=1, heal=5, block=3, description="Recover HP & Block.")
            weapon = Weapon(name="Iron Sword", stat_bonus=2, skills=[slash, parry, heavy_strike, second_wind])
        else: # Sorcerist
            fireball = Skill(name="Fireball", energy_cost=2, damage=16, description="High damage fire spell.")
            mana_shield = Skill(name="Mana Shield", energy_cost=1, block=8, description="Block with mana.")
            magic_missile = Skill(name="Magic Missile", energy_cost=1, damage=6, description="Quick magic attack.")
            heal_spell = Skill(name="Heal", energy_cost=2, heal=15, description="Restore health.")
            weapon = Weapon(name="Novice Staff", stat_bonus=1, skills=[fireball, mana_shield, magic_missile, heal_spell])
            
        self.game_manager.player = Player(
            name="Hero", 
            gender=self.selected_gender, 
            char_class=self.selected_class, 
            weapon=weapon
        )

    def draw_button(self, screen, rect, text, is_selected):
        color = (100, 150, 100) if is_selected else (70, 70, 90)
        pygame.draw.rect(screen, color, rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=10)
        text_surf = self.font_medium.render(text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)

    def draw(self, screen):
        screen.fill((30, 30, 40))
        
        # Title
        title_surf = self.font_large.render("Create Your Character", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(screen.get_width() // 2, 100))
        screen.blit(title_surf, title_rect)
        
        # Gender Selection
        gender_title = self.font_medium.render("Select Gender:", True, (200, 200, 200))
        screen.blit(gender_title, (screen.get_width() // 2 - 250, 200))
        self.draw_button(screen, self.btn_boy, "Boy", self.selected_gender == "Boy")
        self.draw_button(screen, self.btn_girl, "Girl", self.selected_gender == "Girl")
        
        # Class Selection
        class_title = self.font_medium.render("Select Class:", True, (200, 200, 200))
        screen.blit(class_title, (screen.get_width() // 2 - 250, 350))
        self.draw_button(screen, self.btn_swordsman, "Swordsman", self.selected_class == "Swordsman")
        self.draw_button(screen, self.btn_sorcerist, "Sorcerist", self.selected_class == "Sorcerist")
        
        # Confirm Button
        mouse_pos = pygame.mouse.get_pos()
        confirm_color = (100, 100, 150) if self.btn_confirm.collidepoint(mouse_pos) else (60, 60, 100)
        pygame.draw.rect(screen, confirm_color, self.btn_confirm, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), self.btn_confirm, 2, border_radius=10)
        conf_text = self.font_medium.render("Confirm", True, (255, 255, 255))
        conf_text_rect = conf_text.get_rect(center=self.btn_confirm.center)
        screen.blit(conf_text, conf_text_rect)
