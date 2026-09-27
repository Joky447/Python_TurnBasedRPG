import os

import pygame

from game_state.game_manager import GameManager
from game_state.main_menu import MainMenuState
from game_state.character_creation_state import CharacterCreationState
from game_state.lobby_state import LobbyState
from game_state.combat_state import CombatState
from game_state.map_state import MapState
from game_state.reward_state import RewardState
from game_state.game_over_state import GameOverState


def main():
    # Run relative to this file so assets load no matter where the game is started from
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    pygame.init()
    try:
        pygame.mixer.init()
    except pygame.error:
        pass  # No audio device: the game runs silently

    WIDTH, HEIGHT = 1280, 720
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Spells x Blades")
    clock = pygame.time.Clock()
    FPS = 60

    game_manager = GameManager(screen, clock, FPS)

    # Add States
    game_manager.add_state("MainMenuState", MainMenuState(game_manager))
    game_manager.add_state("CharacterCreationState", CharacterCreationState(game_manager))
    game_manager.add_state("LobbyState", LobbyState(game_manager))
    game_manager.add_state("CombatState", CombatState(game_manager))
    game_manager.add_state("MapState", MapState(game_manager))
    game_manager.add_state("RewardState", RewardState(game_manager))
    game_manager.add_state("GameOverState", GameOverState(game_manager))

    # Start Game
    game_manager.change_state("MainMenuState")
    game_manager.run()


if __name__ == "__main__":
    main()
