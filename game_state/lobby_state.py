import pygame
from game_state.state import GameState

class LobbyState(GameState):
    def __init__(self, game_manager):
        super().__init__(game_manager)
        self.font_large = pygame.font.SysFont("Arial", 48, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 20)
        
        w = game_manager.screen.get_width()
        h = game_manager.screen.get_height()
        
        self.btn_start = pygame.Rect(w // 2 - 150, h - 100, 300, 60)
        
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                if self.btn_start.collidepoint(mouse_pos):
                    self.game_manager.change_state("MapState")

    def draw(self, screen):
        screen.fill((40, 40, 50))
        
        player = self.game_manager.player
        if not player:
            return
            
        # Title
        title_surf = self.font_large.render("Game Lobby", True, (255, 255, 200))
        title_rect = title_surf.get_rect(center=(screen.get_width() // 2, 80))
        screen.blit(title_surf, title_rect)
        
        # Character Info Box
        info_rect = pygame.Rect(100, 150, 400, 400)
        pygame.draw.rect(screen, (30, 30, 40), info_rect, border_radius=15)
        pygame.draw.rect(screen, (200, 200, 200), info_rect, 2, border_radius=15)
        
        y_offset = 180
        info_lines = [
            f"Name: {player.name}",
            f"Gender: {player.gender}",
            f"Class: {player.char_class}",
            f"Weapon: {player.weapon.name}",
            f"HP: {player.max_hp}",
            f"Energy: {player.max_energy}"
        ]
        
        for line in info_lines:
            text_surf = self.font_medium.render(line, True, (255, 255, 255))
            screen.blit(text_surf, (130, y_offset))
            y_offset += 40
            
        # Skills Box
        skills_rect = pygame.Rect(550, 150, 600, 400)
        pygame.draw.rect(screen, (30, 30, 40), skills_rect, border_radius=15)
        pygame.draw.rect(screen, (200, 200, 200), skills_rect, 2, border_radius=15)
        
        skills_title = self.font_medium.render("Equipped Skills:", True, (255, 200, 100))
        screen.blit(skills_title, (580, 180))
        
        y_offset = 240
        for skill in player.equipped_skills:
            skill_text = f"- {skill.name} (Cost: {skill.energy_cost}): {skill.description}"
            text_surf = self.font_small.render(skill_text, True, (220, 220, 220))
            screen.blit(text_surf, (580, y_offset))
            y_offset += 35
            
        # Start Button
        mouse_pos = pygame.mouse.get_pos()
        btn_color = (100, 150, 100) if self.btn_start.collidepoint(mouse_pos) else (60, 100, 60)
        pygame.draw.rect(screen, btn_color, self.btn_start, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), self.btn_start, 2, border_radius=10)
        
        btn_text = self.font_medium.render("Begin Adventure", True, (255, 255, 255))
        btn_text_rect = btn_text.get_rect(center=self.btn_start.center)
        screen.blit(btn_text, btn_text_rect)
