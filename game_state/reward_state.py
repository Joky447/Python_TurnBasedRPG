import pygame
from game_state.state import GameState

class RewardState(GameState):
    def __init__(self, game_manager):
        super().__init__(game_manager)
        self.font_large = pygame.font.SysFont("Arial", 48, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 28, bold=True)
        
        # 3 reward options
        w = game_manager.screen.get_width()
        h = game_manager.screen.get_height()
        
        self.rewards = [
            {"rect": pygame.Rect(w//2 - 350, 300, 200, 250), "type": "Heal", "desc": "Restore 30 HP"},
            {"rect": pygame.Rect(w//2 - 100, 300, 200, 250), "type": "Max HP", "desc": "+10 Max HP"},
            {"rect": pygame.Rect(w//2 + 150, 300, 200, 250), "type": "Upgrade", "desc": "+2 Damage Stat"}
        ]
        
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                for reward in self.rewards:
                    if reward["rect"].collidepoint(mouse_pos):
                        self.apply_reward(reward["type"])
                        self.game_manager.current_encounter += 1
                        if self.game_manager.current_encounter > 5:
                            self.game_manager.current_encounter = 1
                            self.game_manager.current_floor += 1
                        self.game_manager.change_state("MapState")
                        return

    def apply_reward(self, reward_type):
        player = self.game_manager.player
        if not player:
            return
            
        if reward_type == "Heal":
            player.heal(30)
        elif reward_type == "Max HP":
            player.max_hp += 10
            player.heal(10)
        elif reward_type == "Upgrade":
            player.stat_bonus += 2

    def draw(self, screen):
        screen.fill((40, 30, 40)) # Dark purple background
        
        title_surf = self.font_large.render("Victory! Choose a Reward", True, (255, 255, 150))
        title_rect = title_surf.get_rect(center=(screen.get_width() // 2, 100))
        screen.blit(title_surf, title_rect)
        
        mouse_pos = pygame.mouse.get_pos()
        
        for reward in self.rewards:
            rect = reward["rect"]
            color = (80, 80, 100) if rect.collidepoint(mouse_pos) else (50, 50, 70)
            
            pygame.draw.rect(screen, color, rect, border_radius=15)
            pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=15)
            
            type_surf = self.font_medium.render(reward["type"], True, (255, 200, 100))
            desc_surf = pygame.font.SysFont("Arial", 20).render(reward["desc"], True, (255, 255, 255))
            
            screen.blit(type_surf, (rect.x + 20, rect.y + 20))
            screen.blit(desc_surf, (rect.x + 20, rect.y + 80))
