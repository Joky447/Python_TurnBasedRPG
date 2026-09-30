import os

import pygame

import assets

from game_state.game_manager import GameManager
from game_state.main_menu import MainMenuState
from game_state.character_creation_state import CharacterCreationState
from game_state.lobby_state import LobbyState
from game_state.combat_state import CombatState
from game_state.map_state import MapState
from game_state.reward_state import RewardState
from game_state.game_over_state import GameOverState
from game_state.settings_state import SettingsState
from game_state.credits_state import CreditsState


def main():
    # Run relative to this file so assets load no matter where the game is started from
    os.chdir(assets.BASE_DIR)

    pygame.init()
    assets.load_settings()
    
    try:
        pygame.mixer.init()
    except pygame.error:
        pass  # No audio device: the game runs silently

    try:
        pygame.display.set_icon(pygame.image.load(assets.path("menu_ui/game_icon.png")))   # window / taskbar icon
    except (pygame.error, FileNotFoundError):
        pass

    WIDTH, HEIGHT = 1280, 720
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE |
                                     (pygame.FULLSCREEN if assets.settings["fullscreen"] else 0))   # scales to any window size
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
    game_manager.add_state("SettingsState", SettingsState(game_manager))
    game_manager.add_state("CreditsState", CreditsState(game_manager))

    # Start Game
    game_manager.change_state("MainMenuState")
    game_manager.run()


if __name__ == "__main__":
    main()
