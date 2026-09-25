import pygame

from world.floor_map import FloorMap

MAX_FLOOR = 5


class GameManager:
    """Manages the main game loop, state transitions and the data of the current run."""
    def __init__(self, screen, clock, fps):
        self.screen = screen
        self.clock = clock
        self.fps = fps
        self.states = {}
        self.current_state = None
        self.running = True
        self.dt = 0
        self.fade_alpha = 0

        # Shared game data (player, floor, etc.)
        self.new_run()

    # --- Run data -----------------------------------------------------------
    def new_run(self):
        self.player = None
        self.current_floor = 1
        self.floor_map = FloorMap(1)
        self.stats = {"enemies": 0, "elites": 0, "bosses": 0, "damage": 0}

    @property
    def current_encounter(self) -> int:
        """Room number on this floor (1-5)."""
        node = self.floor_map.current
        return node.row + 1 if node else 1

    def complete_node(self):
        """Called when the current map room is finished. Advances floors after a boss."""
        node = self.floor_map.current
        if node and node.type == "boss":
            if self.current_floor >= MAX_FLOOR:
                self.change_state("GameOverState", victory=True)
                return
            self.current_floor += 1
            self.floor_map = FloorMap(self.current_floor)
            if self.player:
                self.player.heal(self.player.max_hp)   # Fully rested between floors
                self.player.events.clear()
        self.change_state("MapState")

    # --- States -------------------------------------------------------------
    def add_state(self, state_name, state_obj):
        self.states[state_name] = state_obj

    def change_state(self, state_name, **kwargs):
        if state_name not in self.states:
            print(f"Error: State '{state_name}' not found!")
            return
        if self.current_state:
            self.current_state.exit()
        self.current_state = self.states[state_name]
        self.current_state.enter(**kwargs)
        self.fade_alpha = 255

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

            # Fade in after every screen change
            if self.fade_alpha > 0:
                overlay = pygame.Surface(self.screen.get_size())
                overlay.set_alpha(self.fade_alpha)
                self.screen.blit(overlay, (0, 0))
                self.fade_alpha = max(0, self.fade_alpha - self.dt * 0.9)

            pygame.display.flip()
            self.dt = self.clock.tick(self.fps)

        pygame.quit()
