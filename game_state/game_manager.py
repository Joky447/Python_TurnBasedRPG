import json
import os

import pygame

import assets
from character.player import Player
from inventory_mechanics.weapon_library import floor_gear
from world.floor_map import FloorMap

MAX_FLOOR = 5
MAX_ROSTER = 2
SAVE_FILE = assets.path("save.json")      # roster, items and progress between sessions

# Testing: every floor pin on the world map is unlocked and clicking one jumps there.
# Set to False to play normally (floors unlock one by one after each boss).
UNLOCK_ALL_FLOORS = False


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

        # Characters live at Base Camp between runs and keep what they find, even after dying
        self.roster: list[Player] = []
        self.active_player_index = 0
        self.notice = None                  # (message, time left in ms) shown on the map, e.g. boss drops
        self.load()
        self.new_run()

    # --- Roster -------------------------------------------------------------
    @property
    def player(self) -> Player | None:
        """The active character: the one shown at camp and taken on runs."""
        if 0 <= self.active_player_index < len(self.roster):
            return self.roster[self.active_player_index]
        return None

    def add_character(self, player: Player) -> bool:
        if len(self.roster) >= MAX_ROSTER:
            return False
        self.roster.append(player)
        self.active_player_index = len(self.roster) - 1
        self.save()
        return True

    def select_character(self, index: int):
        if 0 <= index < len(self.roster):
            self.active_player_index = index
            self.save()

    def delete_character(self, index: int) -> bool:
        """Removes a character for good. The active character can't be deleted."""
        if index == self.active_player_index or not 0 <= index < len(self.roster):
            return False
        del self.roster[index]
        if index < self.active_player_index:
            self.active_player_index -= 1
        self.save()
        return True

    def save(self):
        data = {"active": self.active_player_index, "roster": [p.to_dict() for p in self.roster]}
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=1)
        except OSError as e:
            print("Could not save:", e)

    def load(self):
        if not os.path.exists(SAVE_FILE):
            return
        try:
            with open(SAVE_FILE, encoding="utf-8") as f:
                data = json.load(f)
            self.roster = [Player.from_dict(d) for d in data.get("roster", [])][:MAX_ROSTER]
            self.active_player_index = min(data.get("active", 0), max(0, len(self.roster) - 1))
        except (OSError, ValueError, KeyError) as e:
            print("Could not load save, starting fresh:", e)
            self.roster, self.active_player_index = [], 0

    # --- Run data -----------------------------------------------------------
    def resume_floor(self) -> int:
        """Where this character's adventure picks up: the first floor whose boss they haven't
        beaten (floors are cleared in order). Once all five are cleared it's free play (see all_cleared)."""
        p = self.player
        floor = 1
        while p and floor in p.cleared_floors and floor < MAX_FLOOR:
            floor += 1
        return floor

    @property
    def all_cleared(self) -> bool:
        """Every floor's boss beaten: free play, where any enemy of any floor can be fought."""
        p = self.player
        return p is not None and all(f in p.cleared_floors for f in range(1, MAX_FLOOR + 1))

    def new_run(self):
        """Starts the adventure at the character's first uncleared floor, from that floor's first
        fight. Cleared floors stay cleared; only the unfinished floor's progress is reset.
        The roster and everyone's items stay."""
        self.current_floor = self.resume_floor()
        self.floor_map = FloorMap(self.current_floor)
        self.rematch = None
        self.stats = {"enemies": 0, "elites": 0, "bosses": 0, "damage": 0}
        self.notice = None
        if self.player:
            self.player.reset_combat()
            self.player.heal(self.player.max_hp)
            self.player.events.clear()

    def return_to_camp(self):
        """End of a run (death or victory): back to Base Camp with everything found."""
        self.new_run()
        self.save()
        self.change_state("LobbyState")

    def give_pre_boss_rewards(self) -> dict:
        """Before every boss: this floor's prepared item (equipped right away) and a skill
        upgrade that brings all 4 skills up to this floor's strength. Nothing to choose."""
        p = self.player
        item = self.give_floor_gear(self.current_floor, "You received")
        before = [(s.name, s.summary(p)) for s in p.equipped_skills]
        for skill in p.equipped_skills:
            skill.empower(self.current_floor)
        after = [(s.name, s.summary(p)) for s in p.equipped_skills]
        self.save()
        return {"item": item, "skills": list(zip(before, after))}

    def give_floor_gear(self, floor: int, source: str):
        """This floor's gear item goes to the active character and is equipped right away
        (the old item moves to the inventory). Items the character already owns aren't given again."""
        p = self.player
        item = floor_gear(floor, p.char_class, p.gender) if p else None
        if not item:
            return None
        owned = {i.name for i in p.inventory + p.equipped_items()}
        if item.name in owned:
            return None
        p.equip_item(item)
        self.save()
        return item

    @property
    def current_encounter(self) -> int:
        """Number of the fight being taken on (1 = first fight of the floor)."""
        enc = self.floor_map.current
        return enc.number if enc else self.floor_map.total

    def jump_to_floor(self, floor: int):
        """Test mode: start any floor from its first fight."""
        self.current_floor = max(1, min(MAX_FLOOR, floor))
        self.floor_map = FloorMap(self.current_floor)

    # --- Rematches: any enemy of a cleared floor, outside the run --------------
    def start_rematch(self, floor: int, number: int):
        """Fights one enemy of a floor this character has cleared. It doesn't count for the
        run: no items, no progress, and HP is back to what it was afterwards. Beating a boss
        again offers its Learn a Skill choice again (a new set of skills to pick from)."""
        self.rematch = (floor, FloorMap(floor).encounters[number - 1], self.player.current_hp)
        self.change_state("CombatState")

    def end_rematch(self, won: bool):
        floor, enc, hp = self.rematch
        self.rematch = None
        self.player.reset_combat()
        self.player.current_hp = min(hp, self.player.max_hp)
        self.player.events.clear()
        self.notice = (f"Rematch {'won' if won else 'lost'}: {enc.enemy}", 2500)
        if won and enc.rank == "boss":
            # skills at the strength of the character's furthest cleared floor, so they stay useful
            level = max(self.player.cleared_floors | {floor})
            self.change_state("RewardState", mode="boss", level=level)
        else:
            self.change_state("MapState")

    def start_next_fight(self):
        if self.floor_map.current:
            self.change_state("CombatState")

    def encounter_won(self):
        """After a victory: the reward comes right before the boss, and a boss win opens the next floor."""
        beat_boss = self.floor_map.current and self.floor_map.current.rank == "boss"
        self.floor_map.complete_current()
        if beat_boss and self.player:
            self.player.cleared_floors.add(self.current_floor)
            self.save()
        if beat_boss:
            if self.current_floor >= MAX_FLOOR:
                self.change_state("GameOverState", victory=True)
                return
            self.current_floor += 1
            self.floor_map = FloorMap(self.current_floor)
            if self.player:
                self.player.heal(self.player.max_hp)   # Fully rested between floors
                self.player.events.clear()
            self.change_state("RewardState", mode="boss", level=self.current_floor - 1)
        elif self.floor_map.next_is_boss():
            self.change_state("RewardState", mode="pre_boss", **self.give_pre_boss_rewards())
        else:
            self.change_state("MapState")

    def reward_claimed(self, mode="pre_boss"):
        """Pre-boss reward: straight into the boss fight. Post-boss skill reward: on to the next floor's map."""
        if mode == "boss":
            self.change_state("MapState")
        else:
            self.start_next_fight()

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
