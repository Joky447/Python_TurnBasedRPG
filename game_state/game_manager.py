import pygame

class GameManager:
    """Manages the main game loop and state transitions."""
    def __init__(self, screen, clock, fps):
        self.screen = screen
        self.clock = clock
        self.fps = fps
        self.states = {}
        self.current_state = None
        self.running = True
        
        # Shared game data (player, floor, etc.)
        self.player = None
        self.current_floor = 1
        self.current_encounter = 1

    def add_state(self, state_name, state_obj):
        self.states[state_name] = state_obj

    def change_state(self, state_name, **kwargs):
        if self.current_state:
            self.current_state.exit()
            
        if state_name in self.states:
            self.current_state = self.states[state_name]
            self.current_state.enter(**kwargs)
        else:
            print(f"Error: State '{state_name}' not found!")

    def run(self):
        while self.running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

            if self.current_state:
                self.current_state.handle_events(events)
                self.current_state.update()
                self.current_state.draw(self.screen)

            pygame.display.flip()
            self.clock.tick(self.fps)
            
        pygame.quit()
