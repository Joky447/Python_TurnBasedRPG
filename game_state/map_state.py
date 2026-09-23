import pygame
import os
from game_state.state import GameState

class MapState(GameState):
    def __init__(self, game_manager):
        super().__init__(game_manager)
        self.font_large = pygame.font.SysFont("Arial", 48, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 18, bold=True)
        
        # Load map background
        w = game_manager.screen.get_width()
        h = game_manager.screen.get_height()
        
        self.bg_image = None
        map_path = "map/RPGMAP.png"
        if os.path.exists(map_path):
            self.bg_image = pygame.image.load(map_path).convert()
            self.bg_image = pygame.transform.scale(self.bg_image, (w, h))

        # Define 5 node locations perfectly aligned with the circular pins in the map layout
        self.nodes = [
            {"level": 1, "pos": (210, 580)},
            {"level": 2, "pos": (410, 430)},
            {"level": 3, "pos": (640, 310)},
            {"level": 4, "pos": (820, 190)},
            {"level": 5, "pos": (1110, 60)},
        ]
        
        # Dimensions for the clickable circular area
        self.hitbox_radius = 60
        
    def get_current_node_rect(self):
        floor = self.game_manager.current_floor
        for node in self.nodes:
            if node["level"] == floor:
                pos = node["pos"]
                # Return a rectangular rect centered on the button for collision
                return pygame.Rect(pos[0] - self.hitbox_radius, pos[1] - self.hitbox_radius, self.hitbox_radius * 2, self.hitbox_radius * 2)
        return None

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                current_rect = self.get_current_node_rect()
                
                if current_rect and current_rect.collidepoint(mouse_pos):
                    # Enter combat when clicking the next node
                    self.game_manager.change_state("CombatState")

    def draw(self, screen):
        # Draw Background Map
        if self.bg_image:
            screen.blit(self.bg_image, (0, 0))
        else:
            screen.fill((20, 30, 20)) # Fallback
            
        mouse_pos = pygame.mouse.get_pos()
        current_floor = self.game_manager.current_floor
            
        # Draw nodes (Highlight only the active one)
        for node in self.nodes:
            pos = node["pos"]
            level = node["level"]
            
            if level == current_floor:
                # Removed the yellow ring.
                
                # Draw the progress pill above the button center
                encounter = self.game_manager.current_encounter
                prog_surf = self.font_small.render(f"Battle {encounter}/5", True, (255, 255, 100))
                prog_rect = prog_surf.get_rect(center=(pos[0], pos[1] - self.hitbox_radius - 20))
                
                # Add background pill for readability
                bg_rect = prog_rect.inflate(10, 6)
                pygame.draw.rect(screen, (0, 0, 0, 150), bg_rect, border_radius=5)
                screen.blit(prog_surf, prog_rect)

            # Draw level number perfectly in the circle
            num_surf = self.font_medium.render(str(level), True, (255, 255, 255))
            
            # Draw a subtle dark background so the white text pops against the map's icons
            pygame.draw.circle(screen, (0, 0, 0), pos, 18)
            pygame.draw.circle(screen, (200, 150, 50), pos, 18, 2) # Gold border
            
            num_rect = num_surf.get_rect(center=pos)
            screen.blit(num_surf, num_rect)

