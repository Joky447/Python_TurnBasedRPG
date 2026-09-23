import pygame

class GameState:
    """Base class for all game states."""
    def __init__(self, game_manager):
        self.game_manager = game_manager
        
    def enter(self, **kwargs):
        """Called when the state is transitioned to."""
        pass
        
    def exit(self):
        """Called when the state is transitioned away from."""
        pass
        
    def handle_events(self, events):
        """Process Pygame events."""
        pass
        
    def update(self):
        """Update game logic."""
        pass
        
    def draw(self, screen):
        """Render to the screen."""
        pass
