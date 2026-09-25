import math
import random

import pygame

import animation
import assets
import ui
from character.entity import STATUS_INFO
from game_state.state import GameState
from mobs_boss.enemy_library import create_enemy

ENEMY_TURN_DELAY = 550      # ms pause before the enemy acts, so the player can follow along
END_SCREEN_DELAY = 1400     # ms before leaving combat after a win/loss


class FloatingText:
    def __init__(self, msg, pos, color, size=30):
        self.msg, self.x, self.y, self.color, self.size = msg, pos[0], pos[1], color, size
        self.life = 1000

    def update(self, dt):
        self.life -= dt
        self.y -= dt * 0.06

    def draw(self, screen):
        ui.text_shadow(screen, self.msg, self.size, self.color, center=(int(self.x), int(self.y)))


class CombatState(GameState):
    """Turn loop: player uses skills -> End Turn -> enemy performs its shown intent -> repeat."""
    def __init__(self, game_manager):
        super().__init__(game_manager)
        w, h = game_manager.screen.get_size()
        self.w, self.h = w, h

        # Layout
        self.ui_panel_rect = pygame.Rect(0, h - 190, w, 190)
        self.ground_y = self.ui_panel_rect.top - 12
        self.hero_x = 310
        self.enemy_x = w - 330
        card_w, card_h, gap = 210, 150, 18
        start_x = (w - (4 * card_w + 3 * gap)) // 2
        self.skill_rects = [pygame.Rect(start_x + i * (card_w + gap), self.ui_panel_rect.y + 22, card_w, card_h)
                            for i in range(4)]
        self.end_turn_rect = pygame.Rect(w - 170, self.ui_panel_rect.y + 60, 150, 70)
        self.energy_center = (85, self.ui_panel_rect.centery)

        self.enemy = None
        self.buttons = []

    # ------------------------------------------------------------------ setup
    def enter(self, rank="normal", **kwargs):
        gm = self.game_manager
        player = gm.player
        floor = gm.current_floor

        self.bg_image = assets.load_background(f"map/{['1st', '2nd', '3rd', '4th', '5th'][min(floor, 5) - 1]}floor.png",
                                               (self.w, self.h))
        self.enemy = create_enemy(floor, rank, gm.current_encounter)
        self.hero_anim = animation.hero_sprite(player.gender, player.char_class, player.weapon.tier, height=250)
        self.enemy_anim = animation.enemy_sprite(self.enemy.anim, self.enemy.height, self.enemy.tint)

        player.reset_combat()
        player.start_turn()
        self.enemy.decide_intent()

        self.phase = "player"         # player | enemy | victory | defeat
        self.phase_timer = 0
        self.pending_skill = None     # skill waiting for the attack animation to connect
        self.enemy_acted = False
        self.floaters: list[FloatingText] = []
        self.log: list[tuple[str, tuple]] = [(f"{self.enemy.name} appears!", ui.GOLD)]
        self.shake = 0
        self.flash = {"hero": 0, "enemy": 0}
        self.shown_hp = {"hero": player.current_hp, "enemy": self.enemy.current_hp}
        self.enemy_alpha = 255
        self.status_hitboxes = []
        self.setup_buttons()
        assets.play_sound("battle_start")

    def setup_buttons(self):
        player = self.game_manager.player
        self.buttons = [{"rect": self.skill_rects[i], "skill": s} for i, s in enumerate(player.equipped_skills[:4])]

    # ------------------------------------------------------------------ input
    @property
    def input_locked(self):
        return self.phase != "player" or self.pending_skill is not None or self.hero_anim.busy

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, btn in enumerate(self.buttons):
                    if btn["rect"].collidepoint(event.pos):
                        self.use_skill(i)
                if self.end_turn_rect.collidepoint(event.pos):
                    self.end_player_turn()
            elif event.type == pygame.KEYDOWN:
                if pygame.K_1 <= event.key <= pygame.K_4:
                    self.use_skill(event.key - pygame.K_1)
                elif event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
                    self.end_player_turn()

    def use_skill(self, index):
        if self.input_locked or index >= len(self.buttons):
            return
        player = self.game_manager.player
        skill = self.buttons[index]["skill"]
        if not skill.can_use(player):
            self.add_float("Not enough energy", (self.hero_x, self.ground_y - 290), (140, 190, 255), 22)
            return

        self.add_log(f"{player.name} uses {skill.name}", skill.color)
        targets_enemy = skill.damage or skill.effects
        if targets_enemy and self.hero_anim.available:
            # Resolve the hit when the swing connects (see update)
            self.pending_skill = skill
            self.hero_anim.play("attack", on_done=self.resolve_pending)
            assets.play_sound("swing")
        else:
            skill.execute(player, self.enemy)
            assets.play_sound("buff")
            self.check_end()

    def resolve_pending(self):
        if self.pending_skill:
            self.pending_skill.execute(self.game_manager.player, self.enemy)
            self.pending_skill = None
            self.check_end()

    def end_player_turn(self):
        if self.input_locked:
            return
        self.game_manager.player.end_turn()
        self.phase = "enemy"
        self.phase_timer = 0
        self.enemy_acted = False

    # ------------------------------------------------------------------ turn flow
    def enemy_turn(self):
        """Runs once the delay has passed: DoTs tick, then the enemy performs its intent."""
        enemy = self.enemy
        enemy.start_turn()
        if not enemy.is_alive:
            self.add_log(f"{enemy.name} succumbs!", ui.GOLD)
            self.check_end()
            return
        move = enemy.intent
        self.add_log(f"{enemy.name} uses {move.name}", (255, 190, 120))
        if (move.damage or move.effects) and "attack" in self.enemy_anim.clips:
            self.enemy_anim.play("attack", on_done=lambda: self.finish_enemy_turn(move))
        else:
            self.finish_enemy_turn(move)

    def finish_enemy_turn(self, move):
        player = self.game_manager.player
        if self.phase != "enemy":
            return
        move.execute(self.enemy, player)
        self.enemy.intent = None
        if self.check_end():
            return
        self.enemy.end_turn()
        self.enemy.decide_intent()
        player.start_turn()      # new player turn: energy refills, Block expires, DoTs tick
        if not self.check_end():
            self.phase = "player"

    def check_end(self):
        player = self.game_manager.player
        if not self.enemy.is_alive and self.phase not in ("victory", "defeat"):
            self.phase, self.phase_timer = "victory", 0
            self.add_log(f"{self.enemy.name} is defeated!", ui.GOLD)
            assets.play_sound("victory")
            return True
        if not player.is_alive and self.phase not in ("victory", "defeat"):
            self.phase, self.phase_timer = "defeat", 0
            self.add_log(f"{player.name} has fallen...", ui.RED)
            assets.play_sound("defeat")
            return True
        return self.phase in ("victory", "defeat")

    def update(self):
        dt = self.game_manager.dt
        self.hero_anim.update(dt)
        self.enemy_anim.update(dt)

        # The player's swing lands a little past half-way through the animation
        if self.pending_skill and self.hero_anim.progress() >= 0.6:
            self.resolve_pending()

        if self.phase == "enemy" and not self.enemy_acted:
            self.phase_timer += dt
            if self.phase_timer >= ENEMY_TURN_DELAY:
                self.enemy_acted = True
                self.enemy_turn()
        elif self.phase in ("victory", "defeat"):
            self.phase_timer += dt
            if self.phase == "victory":
                self.enemy_alpha = max(0, 255 - self.phase_timer * 0.4)
            if self.phase_timer >= END_SCREEN_DELAY and not self.hero_anim.busy:
                self.leave_combat()
                return

        self.process_events()
        for f in self.floaters:
            f.update(dt)
        self.floaters = [f for f in self.floaters if f.life > 0]
        self.shake = max(0, self.shake - dt * 0.05)
        for k in self.flash:
            self.flash[k] = max(0, self.flash[k] - dt)
        # Health bars drain smoothly
        for key, ent in (("hero", self.game_manager.player), ("enemy", self.enemy)):
            if self.shown_hp[key] > ent.current_hp:
                self.shown_hp[key] = max(ent.current_hp, self.shown_hp[key] - dt * 0.04)
            else:
                self.shown_hp[key] = ent.current_hp

    def leave_combat(self):
        gm = self.game_manager
        if self.phase == "victory":
            gm.stats[{"normal": "enemies", "elite": "elites", "boss": "bosses"}[self.enemy.rank]] += 1
            gm.change_state("RewardState", mode=self.enemy.rank)
        else:
            gm.change_state("GameOverState", victory=False)

    def process_events(self):
        """Turns entity events into floating numbers, hit reactions and log lines."""
        player = self.game_manager.player
        for ent, who in ((player, "hero"), (self.enemy, "enemy")):
            x = self.hero_x if who == "hero" else self.enemy_x
            height = 250 if who == "hero" else self.enemy.height
            y = self.ground_y - height * 0.6
            for ev in ent.events:
                kind = ev[0]
                jitter = (x + random.randint(-20, 20), y)
                if kind == "damage":
                    self.add_float(f"-{ev[1]}", jitter, (255, 80, 70), 38)
                    if ev[1] > 0:
                        self.flash[who] = 160
                        if who == "hero":
                            self.shake = 12
                        else:
                            self.game_manager.stats["damage"] += ev[1]
                            if not self.enemy_anim.busy and self.enemy.is_alive:
                                self.enemy_anim.play("hurt")
                        assets.play_sound("hit")
                elif kind == "blocked":
                    self.add_float(f"Blocked {ev[1]}", jitter, ui.BLOCK_BLUE, 24)
                    assets.play_sound("block")
                elif kind == "heal":
                    self.add_float(f"+{ev[1]}", jitter, (90, 230, 100), 34)
                elif kind == "block":
                    self.add_float(f"+{ev[1]} Block", jitter, ui.BLOCK_BLUE, 26)
                elif kind == "status":
                    color = STATUS_INFO.get(ev[1], {}).get("color", ui.TEXT)
                    self.add_float(f"{ev[1].title()} +{ev[2]}", jitter, color, 24)
                elif kind == "dot":
                    self.add_log(f"{ent.name} suffers from {ev[1]}", STATUS_INFO[ev[1]]["color"])
            ent.events.clear()

    def add_float(self, msg, pos, color, size=30):
        # Stack new numbers above recent ones near the same spot so they don't overlap
        recent = [f for f in self.floaters if f.life > 650 and abs(f.x - pos[0]) < 120]
        self.floaters.append(FloatingText(msg, (pos[0], pos[1] - 34 * len(recent)), color, size))

    def add_log(self, msg, color=ui.TEXT):
        self.log.append((msg, color))
        self.log = self.log[-6:]

    # ------------------------------------------------------------------ drawing
    def draw(self, screen):
        player = self.game_manager.player
        mouse = pygame.mouse.get_pos()
        self.status_hitboxes = []

        world = screen
        if self.shake > 0.5:
            world = pygame.Surface(screen.get_size())
        if self.bg_image:
            world.blit(self.bg_image, (0, 0))
        else:
            world.fill(ui.BG)

        self.draw_hero(world, player)
        self.draw_enemy(world)
        for f in self.floaters:
            f.draw(world)

        if world is not screen:
            screen.fill((0, 0, 0))
            screen.blit(world, (random.uniform(-self.shake, self.shake), random.uniform(-self.shake, self.shake)))

        self.draw_bottom_panel(screen, player, mouse)
        self.draw_log(screen)
        self.draw_turn_banner(screen)
        self.draw_tooltips(screen, player, mouse)

        if self.phase in ("victory", "defeat") and self.phase_timer > 400:
            ui.dim(screen, min(140, int((self.phase_timer - 400) * 0.3)))
            msg, color = ("VICTORY!", ui.GOLD) if self.phase == "victory" else ("DEFEATED", ui.RED)
            ui.text_shadow(screen, msg, 80, color, center=(self.w // 2, self.h // 2 - 120))

    def draw_hero(self, screen, player):
        x = self.hero_x
        if self.hero_anim.busy and player.char_class == "Swordsman" and self.hero_anim.current == "attack":
            # Swordsman dashes toward the enemy and back during the swing
            x += math.sin(self.hero_anim.progress() * math.pi) * (self.enemy_x - self.hero_x - 260)
        pygame.draw.ellipse(screen, (0, 0, 0), (x - 70, self.ground_y - 10, 140, 22))
        if player.is_alive or self.phase != "defeat":
            if self.hero_anim.available:
                self.hero_anim.draw(screen, (int(x), self.ground_y), flash=self.flash["hero"] > 0)
            else:
                pygame.draw.rect(screen, (50, 150, 255), (x - 60, self.ground_y - 220, 120, 220), border_radius=15)

        top = self.ground_y - 300
        ui.text_shadow(screen, f"{player.name}  ·  {player.char_class}", 22, ui.TEXT, midbottom=(self.hero_x, top - 30))
        ui.health_bar(screen, self.hero_x - 110, top - 24, player, 220, shown_hp=self.shown_hp["hero"])
        self.status_hitboxes += [(r, n, player) for r, n in ui.status_row(screen, player, self.hero_x - 110, top + 4)]

    def draw_enemy(self, screen):
        enemy = self.enemy
        pygame.draw.ellipse(screen, (0, 0, 0), (self.enemy_x - 90, self.ground_y - 10, 180, 24))
        if self.enemy_anim.available:
            if self.enemy_alpha < 255:
                layer = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
                self.enemy_anim.draw(layer, (self.enemy_x, self.ground_y))
                layer.set_alpha(int(self.enemy_alpha))
                screen.blit(layer, (0, 0))
            else:
                self.enemy_anim.draw(screen, (self.enemy_x, self.ground_y), flash=self.flash["enemy"] > 0)
        elif enemy.is_alive:
            pygame.draw.rect(screen, (50, 200, 50), (self.enemy_x - 70, self.ground_y - 220, 140, 220), border_radius=15)

        top = self.ground_y - enemy.height - 20
        name_color = {"elite": (240, 120, 220), "boss": (255, 90, 80)}.get(enemy.rank, ui.TEXT)
        ui.text_shadow(screen, enemy.name, 24, name_color, midbottom=(self.enemy_x, top - 30))
        ui.health_bar(screen, self.enemy_x - 120, top - 24, enemy, 240, shown_hp=self.shown_hp["enemy"])
        self.status_hitboxes += [(r, n, enemy) for r, n in ui.status_row(screen, enemy, self.enemy_x - 120, top + 4)]

        # Intent: what the enemy will do next turn
        self.intent_rect = None
        if enemy.intent and enemy.is_alive:
            kinds = enemy.intent_kinds()
            bob = math.sin(pygame.time.get_ticks() / 300) * 4
            cy = top - 90 + bob
            label = ""
            if enemy.intent.damage:
                per_hit = enemy.calculate_damage(enemy.intent.damage, self.game_manager.player)
                label = f"{per_hit}" + (f"x{enemy.intent.hits}" if enemy.intent.hits > 1 else "")
            width = len(kinds) * 38 + (assets.font(24, True).size(label)[0] + 10 if label else 0)
            self.intent_rect = pygame.Rect(0, 0, width + 16, 46)
            self.intent_rect.center = (self.enemy_x, int(cy))
            ui.panel(screen, self.intent_rect, (15, 15, 22), (255, 200, 100), 200, 10)
            x = self.intent_rect.x + 26
            for kind in kinds:
                ui.intent_icon(screen, kind, (x, int(cy)), 14)
                x += 38
            if label:
                ui.text_shadow(screen, label, 24, (255, 120, 100), midleft=(x - 12, int(cy)))

    def draw_bottom_panel(self, screen, player, mouse):
        ui.panel(screen, self.ui_panel_rect, ui.PANEL, ui.PANEL_BORDER, 235, 0)
        ui.energy_orb(screen, self.energy_center, player.energy, player.max_energy)
        ui.text(screen, "ENERGY", 14, ui.TEXT_DIM, True, center=(self.energy_center[0], self.energy_center[1] + 50))

        for i, btn in enumerate(self.buttons):
            skill = btn["skill"]
            usable = skill.can_use(player) and not self.input_locked
            rect = btn["rect"].copy()
            hovered = rect.collidepoint(mouse)
            if hovered and usable:
                rect.y -= 8
            fill = ui.BUTTON_HOVER if hovered and usable else (ui.BUTTON if usable else ui.BUTTON_DISABLED)
            pygame.draw.rect(screen, fill, rect, border_radius=10)
            pygame.draw.rect(screen, skill.color, (rect.x, rect.y, rect.width, 6), border_top_left_radius=10,
                             border_top_right_radius=10)
            pygame.draw.rect(screen, ui.GOLD if hovered and usable else (200, 200, 210), rect, 2, border_radius=10)

            text_color = ui.TEXT if usable else ui.TEXT_DIM
            ui.text(screen, f"[{i + 1}]", 14, ui.TEXT_DIM, True, topleft=(rect.x + 10, rect.y + 14))
            ui.text(screen, skill.name, 20, text_color, True, topleft=(rect.x + 40, rect.y + 12))
            for p in range(skill.energy_cost):
                pygame.draw.circle(screen, ui.ENERGY if usable else (70, 80, 100), (rect.right - 16 - p * 16, rect.y + 24), 6)
            ui.text_wrapped(screen, skill.summary(player, self.enemy), 16,
                            pygame.Rect(rect.x + 10, rect.y + 46, rect.width - 20, 90), text_color)

        can_end = not self.input_locked
        hovered = self.end_turn_rect.collidepoint(mouse)
        ui.button(screen, self.end_turn_rect, "End Turn", hovered, can_end, (150, 40, 40), (200, 50, 50), 24)
        ui.text(screen, "[E / Space]", 13, ui.TEXT_DIM, center=(self.end_turn_rect.centerx, self.end_turn_rect.bottom + 14))

    def draw_log(self, screen):
        rect = pygame.Rect(16, 16, 360, 26 + 22 * len(self.log))
        ui.panel(screen, rect, (10, 10, 16), None, 150, 8)
        y = rect.y + 12
        for i, (msg, color) in enumerate(self.log):
            faded = tuple(int(c * (0.5 + 0.5 * (i + 1) / len(self.log))) for c in color)
            ui.text(screen, msg, 16, faded, topleft=(rect.x + 12, y))
            y += 22
        gm = self.game_manager
        ui.text_shadow(screen, f"Floor {gm.current_floor}  ·  Room {gm.current_encounter}/5", 20, ui.GOLD,
                       topright=(self.w - 20, 16))

    def draw_turn_banner(self, screen):
        if self.phase == "enemy":
            ui.text_shadow(screen, "Enemy Turn", 32, (255, 140, 120), center=(self.w // 2, 60))
        elif self.phase == "player" and not self.input_locked:
            ui.text_shadow(screen, "Your Turn", 28, (160, 220, 255), center=(self.w // 2, 60))

    def draw_tooltips(self, screen, player, mouse):
        for i, btn in enumerate(self.buttons):
            if btn["rect"].collidepoint(mouse):
                s = btn["skill"]
                lines = [(f"{s.name}  ·  {s.energy_cost} Energy", s.color), (s.summary(player, self.enemy), ui.TEXT)]
                if s.description:
                    lines.append((s.description, ui.TEXT_DIM))
                ui.tooltip(screen, lines, (btn["rect"].x, btn["rect"].y - 10))
                return
        if self.intent_rect and self.intent_rect.collidepoint(mouse) and self.enemy.intent:
            m = self.enemy.intent
            ui.tooltip(screen, [(f"Intent: {m.name}", (255, 200, 100)), (m.summary(self.enemy, player), ui.TEXT)], mouse)
            return
        for rect, name, ent in self.status_hitboxes:
            if rect.collidepoint(mouse):
                info = STATUS_INFO.get(name, {"color": ui.TEXT, "desc": ""})
                ui.tooltip(screen, [(f"{name.title()} ({ent.status(name)})", info["color"]), (info["desc"], ui.TEXT)], mouse)
                return
