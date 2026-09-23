import pygame
import os
from game_state.state import GameState
from mobs_boss.enemy import Enemy

class CombatState(GameState):
    def __init__(self, game_manager):
        super().__init__(game_manager)
        
        self.font_large = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 16)
        
        # Colors
        self.BACKGROUND_COLOR = (30, 30, 40)
        self.UI_PANEL_COLOR = (20, 20, 25)
        self.BUTTON_COLOR = (70, 70, 90)
        self.BUTTON_HOVER_COLOR = (100, 100, 120)
        self.END_TURN_COLOR = (150, 40, 40)
        self.END_TURN_HOVER = (200, 50, 50)
        self.TEXT_COLOR = (255, 255, 255)
        self.INTENT_TEXT_COLOR = (255, 200, 100)
        
        self.bg_image = None
        self.hero_sprite = None
        self.enemy = None
        
        # Dimensions setup
        w = self.game_manager.screen.get_width()
        h = self.game_manager.screen.get_height()
        
        self.ui_panel_height = 200
        self.ui_panel_rect = pygame.Rect(0, h - self.ui_panel_height, w, self.ui_panel_height)
        
        button_width, button_height = 200, 120
        button_spacing = 40
        self.start_x = (w - (4 * button_width + 3 * button_spacing)) // 2 
        self.button_y = h - self.ui_panel_height + 40
        self.button_width = button_width
        self.button_height = button_height
        self.button_spacing = button_spacing
        
        self.end_turn_rect = pygame.Rect(w - 220, h - self.ui_panel_height - 70, 180, 50)
        
        self.hero_rect = pygame.Rect(200, 250, 120, 200)
        self.goblin_rect = pygame.Rect(w - 320, 250, 140, 200)
        
        self.buttons = []
        
        self.load_assets()

    def load_assets(self):
        w = self.game_manager.screen.get_width()
        h = self.game_manager.screen.get_height()
        
        # Load all 5 floor backgrounds
        self.floor_bgs = {}
        floor_files = {
            1: "map/1stfloor.png",
            2: "map/2ndfloor.png",
            3: "map/3rdfloor.png",
            4: "map/4thfloor.png",
            5: "map/5thfloor.png"
        }
        for floor_num, file_path in floor_files.items():
            if os.path.exists(file_path):
                img = pygame.image.load(file_path).convert()
                self.floor_bgs[floor_num] = pygame.transform.scale(img, (w, h))

    def enter(self, **kwargs):
        # Set background for the current floor
        floor = self.game_manager.current_floor
        self.bg_image = self.floor_bgs.get(floor, None)
        
        # Load player sprite based on gender
        player = self.game_manager.player
        if player:
            hero_img_path = "character/maleSword.png" if player.gender == "Boy" else "character/girlstance.png"
            if os.path.exists(hero_img_path):
                self.hero_sprite = pygame.image.load(hero_img_path).convert_alpha()
                self.hero_sprite = pygame.transform.scale(self.hero_sprite, (120, 200))
        
        # Generate an enemy when entering combat
        floor = self.game_manager.current_floor
        encounter = self.game_manager.current_encounter
        
        if encounter == 5:
            # Boss encounter
            self.enemy = Enemy(name=f"Floor {floor} Boss", max_hp=50 + (floor * 20))
        else:
            # Regular encounter
            self.enemy = Enemy(name=f"Goblin Grunt (Flr {floor}-{encounter})", max_hp=20 + (floor * 10) + (encounter * 2))
            
        self.enemy.decide_intent()
        
        self.game_manager.player.reset_turn()
        self.setup_buttons()

    def setup_buttons(self):
        self.buttons = []
        player = self.game_manager.player
        for i, skill in enumerate(player.equipped_skills):
            rect = pygame.Rect(self.start_x + i * (self.button_width + self.button_spacing), self.button_y, self.button_width, self.button_height)
            self.buttons.append({"rect": rect, "skill": skill})

    def draw_text(self, text, font, text_col, x, y):
        img = font.render(text, True, text_col)
        self.game_manager.screen.blit(img, (x, y))

    def draw_health_bar(self, surface, x, y, current_hp, max_hp, width=150, height=20):
        ratio = max(0, current_hp / max_hp)
        pygame.draw.rect(surface, (100, 30, 30), (x, y, width, height))           
        pygame.draw.rect(surface, (40, 180, 40), (x, y, width * ratio, height))   
        pygame.draw.rect(surface, (255, 255, 255), (x, y, width, height), 2)      

    def handle_events(self, events):
        player = self.game_manager.player
        
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: 
                mouse_pos = pygame.mouse.get_pos()
                
                if player.current_hp > 0 and self.enemy.current_hp > 0:
                    for btn in self.buttons:
                        if btn["rect"].collidepoint(mouse_pos) and player.energy >= btn["skill"].energy_cost:
                            btn["skill"].execute(player, self.enemy)
                            if self.enemy.current_hp <= 0:
                                self.check_win()
                
                # End Turn Button
                if self.end_turn_rect.collidepoint(mouse_pos) and self.enemy.current_hp > 0 and player.current_hp > 0:
                    self.enemy.execute_intent(player)
                    player.reset_turn()
                    if player.current_hp > 0:
                        self.enemy.decide_intent()
                    else:
                        print("Game Over")

    def check_win(self):
        # Enemy defeated
        if self.enemy.current_hp <= 0:
            self.game_manager.change_state("RewardState")

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        player = self.game_manager.player

        # 1. Draw Background
        if self.bg_image:
            screen.blit(self.bg_image, (0, 0))
        else:
            screen.fill(self.BACKGROUND_COLOR)
        
        # 2. Draw Player & Health Bar
        if player.current_hp > 0:
            if self.hero_sprite:
                screen.blit(self.hero_sprite, (self.hero_rect.x, self.hero_rect.y))
            else:
                pygame.draw.rect(screen, (50, 150, 255), self.hero_rect, border_radius=15)
            
            self.draw_text(f"{player.name}", self.font_large, self.TEXT_COLOR, self.hero_rect.x, self.hero_rect.y - 70)
            self.draw_health_bar(screen, self.hero_rect.x, self.hero_rect.y - 35, player.current_hp, player.max_hp, width=150)
            self.draw_text(f"{player.current_hp}/{player.max_hp} HP", self.font_small, self.TEXT_COLOR, self.hero_rect.x + 45, self.hero_rect.y - 32)
            self.draw_text(f"Energy: {player.energy}/{player.max_energy}  |  Block: {player.block}", self.font_medium, self.TEXT_COLOR, self.hero_rect.x, self.hero_rect.bottom + 15)
        else:
            self.draw_text("GAME OVER", self.font_large, (255, 100, 100), self.hero_rect.x, self.hero_rect.y)

        # 3. Draw Enemy & Health Bar
        if self.enemy.current_hp > 0:
            pygame.draw.rect(screen, (50, 200, 50), self.goblin_rect, border_radius=15)
            self.draw_text(f"{self.enemy.name}", self.font_large, self.TEXT_COLOR, self.goblin_rect.x, self.goblin_rect.y - 70)
            self.draw_health_bar(screen, self.goblin_rect.x, self.goblin_rect.y - 35, self.enemy.current_hp, self.enemy.max_hp, width=150)
            self.draw_text(f"{self.enemy.current_hp}/{self.enemy.max_hp} HP", self.font_small, self.TEXT_COLOR, self.goblin_rect.x + 45, self.goblin_rect.y - 32)
            self.draw_text(f"Block: {self.enemy.block}", self.font_medium, self.TEXT_COLOR, self.goblin_rect.x, self.goblin_rect.bottom + 15)
            if self.enemy.intent:
                self.draw_text(f"Intent: {self.enemy.intent['desc']} ({self.enemy.intent['val']})", self.font_medium, self.INTENT_TEXT_COLOR, self.goblin_rect.x, self.goblin_rect.y - 110)

        # 4. Draw UI Panel
        pygame.draw.rect(screen, self.UI_PANEL_COLOR, self.ui_panel_rect)
        
        # 5. Draw Skill Buttons
        for btn in self.buttons:
            skill = btn["skill"]
            
            if btn["rect"].collidepoint(mouse_pos) and player.energy >= skill.energy_cost and player.current_hp > 0 and self.enemy.current_hp > 0:
                pygame.draw.rect(screen, self.BUTTON_HOVER_COLOR, btn["rect"], border_radius=10)
            else:
                color = self.BUTTON_COLOR if (player.energy >= skill.energy_cost and player.current_hp > 0 and self.enemy.current_hp > 0) else (40, 40, 50)
                pygame.draw.rect(screen, color, btn["rect"], border_radius=10)
            
            pygame.draw.rect(screen, self.TEXT_COLOR, btn["rect"], 2, border_radius=10)
            
            name_surf = self.font_medium.render(skill.name, True, self.TEXT_COLOR)
            cost_surf = self.font_small.render(f"Cost: {skill.energy_cost} EN", True, (150, 200, 255))
            
            screen.blit(name_surf, (btn["rect"].x + 15, btn["rect"].y + 15))
            screen.blit(cost_surf, (btn["rect"].x + 15, btn["rect"].y + 45))

        # 6. Draw End Turn Button
        if self.enemy.current_hp > 0 and player.current_hp > 0:
            if self.end_turn_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, self.END_TURN_HOVER, self.end_turn_rect, border_radius=8)
            else:
                pygame.draw.rect(screen, self.END_TURN_COLOR, self.end_turn_rect, border_radius=8)
            
            pygame.draw.rect(screen, self.TEXT_COLOR, self.end_turn_rect, 2, border_radius=8)
            
            end_text = self.font_medium.render("End Turn", True, self.TEXT_COLOR)
            end_text_rect = end_text.get_rect(center=self.end_turn_rect.center)
            screen.blit(end_text, end_text_rect)
