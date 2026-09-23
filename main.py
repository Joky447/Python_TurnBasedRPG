import pygame
import sys
import os

from game_state.game_manager import GameManager
from game_state.main_menu import MainMenuState
from game_state.character_creation_state import CharacterCreationState
from game_state.lobby_state import LobbyState
from game_state.combat_state import CombatState
from game_state.map_state import MapState
from game_state.reward_state import RewardState

def main():
    pygame.init()
    WIDTH, HEIGHT = 1280, 720
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Turn-Based RPG")
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

    # Start Game
    game_manager.change_state("MainMenuState")
    game_manager.run()

if __name__ == "__main__":
    main()