import pygame
from game_state.state import GameState

class MainMenuState(GameState):
    def __init__(self, game_manager):
        super().__init__(game_manager)
        self.font_large = pygame.font.SysFont("Arial", 48, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 28, bold=True)
        
        self.start_btn = pygame.Rect(game_manager.screen.get_width() // 2 - 100, 300, 200, 60)
        self.quit_btn = pygame.Rect(game_manager.screen.get_width() // 2 - 100, 400, 200, 60)
        
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                if self.start_btn.collidepoint(mouse_pos):
                    self.game_manager.change_state("CharacterCreationState")
                elif self.quit_btn.collidepoint(mouse_pos):
                    self.game_manager.running = False

    def draw(self, screen):
        screen.fill((30, 30, 40)) # Background
        
        # Title
        title_surf = self.font_large.render("Turn-Based RPG", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(screen.get_width() // 2, 150))
        screen.blit(title_surf, title_rect)
        
        # Start Button
        mouse_pos = pygame.mouse.get_pos()
        start_color = (100, 100, 120) if self.start_btn.collidepoint(mouse_pos) else (70, 70, 90)
        pygame.draw.rect(screen, start_color, self.start_btn, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), self.start_btn, 2, border_radius=10)
        start_text = self.font_medium.render("Start Game", True, (255, 255, 255))
        start_text_rect = start_text.get_rect(center=self.start_btn.center)
        screen.blit(start_text, start_text_rect)
        
        # Quit Button
        quit_color = (150, 40, 40) if self.quit_btn.collidepoint(mouse_pos) else (100, 30, 30)
        pygame.draw.rect(screen, quit_color, self.quit_btn, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), self.quit_btn, 2, border_radius=10)
        quit_text = self.font_medium.render("Quit", True, (255, 255, 255))
        quit_text_rect = quit_text.get_rect(center=self.quit_btn.center)
        screen.blit(quit_text, quit_text_rect)
