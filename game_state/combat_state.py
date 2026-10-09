import math
import random

import pygame

import animation
import assets
import ui
from character.entity import STATUS_INFO
from game_state.effects import skill_effects
from game_state.game_manager import MAX_FLOOR
from game_state.state import GameState
from mobs_boss.enemy_library import create_enemy
from world.floor_map import FloorMap

ENEMY_TURN_DELAY = 550      # ms pause before the enemy acts, so the player can follow along
END_SCREEN_DELAY = 1400     # ms before leaving combat after a win/loss


GLASS = 160   # how solid the bottom panel and skill cards are (255 = not see-through)

class FloatingText:
    def __init__(self, msg, pos, color, size=30):
        self.msg, self.x, self.y, self.color, self.size = msg, pos[0], pos[1], color, size
        self.life = 1000

    def update(self, dt):
        self.life -= dt
        self.y -= dt * 0.06

    def draw(self, screen):
        ui.text_shadow(screen, self.msg, self.size, self.color, center=(int(self.x), int(self.y)))


# Sorcerist spells that fly out as a projectile (name -> look). Meteor falls from the sky.
# Chain Lightning, Frost Nova and Hex have no projectile; their effect appears on the target at once.
SPELL_STYLE = {"Fireball": "fireball", "Ignite": "fireball", "Ice Lance": "spear", "Meteor": "meteor",
               "Toxic Cloud": "cloud", "Magic Missile": "missile"}
NO_PROJECTILE = {"Chain Lightning", "Frost Nova", "Hex"}
SCREEN_SHAKE = {"Meteor": 22, "Fireball": 9, "Heavy Strike": 12}


class Projectile:
    """An arrow or a spell flying from one fighter to the other. on_hit runs when it lands.
    style picks the look of a spell: orb, fireball, spear (Ice Lance), meteor, cloud or missile."""
    SPEEDS = {"orb": 1.5, "fireball": 1.2, "spear": 2.0, "meteor": 1.1, "cloud": 0.75, "missile": 1.9, "arrow": 1.5}

    def __init__(self, kind, start, end, color, on_hit, style="orb", delay=0):
        self.kind, self.start, self.end, self.color, self.on_hit = kind, start, end, color, on_hit
        self.style = "arrow" if kind == "arrow" else style
        self.duration = max(220, math.dist(start, end) / self.SPEEDS[self.style])
        self.t = 0.0
        self.delay = delay
        self.trail = []

    @property
    def done(self):
        return self.t >= 1

    def position(self, t):
        x = self.start[0] + (self.end[0] - self.start[0]) * t
        y = self.start[1] + (self.end[1] - self.start[1]) * t
        if self.style == "arrow":
            y -= math.sin(t * math.pi) * 28      # a light arc
        elif self.style == "cloud":
            y -= math.sin(t * math.pi) * 40
        elif self.style == "meteor":
            t2 = t * t                            # speeds up as it falls
            x = self.start[0] + (self.end[0] - self.start[0]) * t2
            y = self.start[1] + (self.end[1] - self.start[1]) * t2
        return x, y

    def update(self, dt):
        if self.delay > 0:
            self.delay -= dt
            return
        self.t = min(1.0, self.t + dt / self.duration)
        keep = 16 if self.style == "meteor" else 9
        self.trail = (self.trail + [self.position(self.t)])[-keep:]

    def draw(self, screen):
        if self.delay > 0:
            return
        x, y = self.position(self.t)
        if self.style == "arrow":
            px, py = self.position(max(0.0, self.t - 0.02))
            angle = math.atan2(y - py, x - px)
            ux, uy = math.cos(angle), math.sin(angle)
            nx, ny = -uy, ux
            tail = (x - ux * 46, y - uy * 46)
            pygame.draw.line(screen, (60, 40, 25), tail, (x, y), 5)
            pygame.draw.line(screen, (215, 180, 120), tail, (x, y), 3)
            head = [(x + ux * 12, y + uy * 12), (x + nx * 6, y + ny * 6), (x - nx * 6, y - ny * 6)]
            pygame.draw.polygon(screen, (40, 40, 48), head)
            pygame.draw.polygon(screen, (200, 205, 215), head, 1)
            for off in (0, 9):      # fletching
                fx, fy = tail[0] + ux * off, tail[1] + uy * off
                pygame.draw.line(screen, (200, 60, 50), (fx, fy), (fx - ux * 8 + nx * 6, fy - uy * 8 + ny * 6), 3)
                pygame.draw.line(screen, (200, 60, 50), (fx, fy), (fx - ux * 8 - nx * 6, fy - uy * 8 - ny * 6), 3)
            return

        n = max(1, len(self.trail))
        if self.style == "meteor":
            # a rock wrapped in flame, dragging a long fiery tail
            for i, (tx, ty) in enumerate(self.trail):
                k = (i + 1) / n
                col = (255, int(60 + 150 * k), int(20 + 40 * k))
                pygame.draw.circle(screen, tuple(int(c * k) for c in col), (int(tx), int(ty)), int(6 + 26 * k))
            layer = pygame.Surface((160, 160), pygame.SRCALPHA)
            pygame.draw.circle(layer, (255, 140, 40, 90), (80, 80), 52)
            pygame.draw.circle(layer, (255, 200, 90, 160), (80, 80), 38)
            pygame.draw.circle(layer, (95, 62, 48, 255), (80, 80), 27)
            pygame.draw.circle(layer, (60, 38, 30, 255), (70, 74), 12)
            pygame.draw.circle(layer, (255, 130, 40, 255), (92, 86), 5)
            pygame.draw.circle(layer, (255, 130, 40, 255), (74, 90), 4)
            screen.blit(layer, (x - 80, y - 80))
            return
        if self.style == "spear":
            px, py = self.position(max(0.0, self.t - 0.02))
            ang = math.atan2(y - py, x - px)
            ux, uy = math.cos(ang), math.sin(ang)
            nx, ny = -uy, ux
            for i, (tx, ty) in enumerate(self.trail):
                k = (i + 1) / n
                pygame.draw.circle(screen, tuple(int(c * k) for c in (150, 215, 255)), (int(tx), int(ty)), int(2 + 5 * k))
            pts = [(x + ux * 40, y + uy * 40), (x + nx * 9, y + ny * 9), (x - ux * 34, y - uy * 34), (x - nx * 9, y - ny * 9)]
            pygame.draw.polygon(screen, (120, 200, 255), pts)
            pygame.draw.polygon(screen, (235, 250, 255), pts, 2)
            pygame.draw.line(screen, (255, 255, 255), (x - ux * 24, y - uy * 24), (x + ux * 32, y + uy * 32), 2)
            return
        if self.style == "cloud":
            layer = pygame.Surface((160, 160), pygame.SRCALPHA)
            for dx, dy, r, a in ((0, 0, 30, 150), (-22, 10, 22, 130), (20, 8, 24, 130), (4, -18, 20, 120)):
                pygame.draw.circle(layer, (100, 200, 70, a), (80 + dx, 80 + dy), r)
                pygame.draw.circle(layer, (170, 245, 120, a // 2), (80 + dx - 4, 80 + dy - 4), r // 2)
            screen.blit(layer, (x - 80, y - 80))
            return

        scale = {"fireball": 1.6, "missile": 0.6}.get(self.style, 1.0)
        for i, (tx, ty) in enumerate(self.trail):
            k = (i + 1) / n
            pygame.draw.circle(screen, tuple(int(c * k) for c in self.color), (int(tx), int(ty)), int((3 + 9 * k) * scale))
        layer = pygame.Surface((120, 120), pygame.SRCALPHA)
        for r, a in ((26, 50), (18, 110), (11, 200)):
            pygame.draw.circle(layer, (*self.color, a), (60, 60), int(r * scale))
        pygame.draw.circle(layer, (255, 255, 255, 255), (60, 60), max(2, int(6 * scale)))
        screen.blit(layer, (x - 60, y - 60))


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
        self.exit_rect = pygame.Rect(w - 170, 52, 150, 38)
        self.dialog_rect = pygame.Rect(0, 0, 520, 230)
        self.dialog_rect.center = (w // 2, h // 2 - 40)
        self.leave_rect = pygame.Rect(0, 0, 200, 50)
        self.leave_rect.bottomleft = (self.dialog_rect.x + 30, self.dialog_rect.bottom - 24)
        self.stay_rect = pygame.Rect(0, 0, 200, 50)
        self.stay_rect.bottomright = (self.dialog_rect.right - 30, self.dialog_rect.bottom - 24)

        self.enemy = None
        self.buttons = []
        self.projectiles: list[Projectile] = []
        self.fx = []                    # skill visual effects (see effects.py)
        self.enemy_release = None       # ranged move waiting for the enemy's attack animation to let go

    # ------------------------------------------------------------------ setup
    def enter(self, **kwargs):
        gm = self.game_manager
        player = gm.player
        self.rematch = gm.rematch is not None
        if self.rematch:
            floor, self.encounter, _ = gm.rematch
            self.floor_total = len(FloorMap(floor).encounters)
        else:
            floor = gm.current_floor
            self.encounter = gm.floor_map.current
            self.floor_total = gm.floor_map.total
        self.floor = floor
        final_boss = self.encounter.rank == "boss" and floor >= MAX_FLOOR

        self.bg_image = assets.load_background(f"map/{['1st', '2nd', '3rd', '4th', '5th'][min(floor, 5) - 1]}floor.png",
                                               (self.w, self.h))
        enc = self.encounter
        self.enemy = create_enemy(floor, enc.enemy, enc.rank, enc.number)
        self.hero_anim = animation.hero_sprite(player.gender, player.char_class, player.outfit_stage, height=250)
        self.enemy_anim = animation.enemy_sprite(self.enemy.anim, self.enemy.height, self.enemy.tint)
        # Music starts once the sprites are loaded, so it lines up with the battle appearing
        assets.play_music("final_boss" if final_boss else "battle")

        player.reset_combat()
        player.start_turn()
        self.enemy.decide_intent()

        self.phase = "player"         # player | enemy | victory | defeat
        self.phase_timer = 0
        self.pending_skill = None     # skill waiting for the attack animation to connect
        self.enemy_acted = False
        self.floaters: list[FloatingText] = []
        self.log: list[tuple[str, tuple]] = [(f"Encounter {enc.number} · {enc.title}", (205, 210, 230)),
                                                 (f"{self.enemy.name} appears!", ui.GOLD)]
        self.shake = 0
        self.flash = {"hero": 0, "enemy": 0}
        self.shown_hp = {"hero": player.current_hp, "enemy": self.enemy.current_hp}
        self.enemy_alpha = 255
        self.enemy_lunge = False
        self.projectiles = []
        self.fx = []
        self.enemy_release = None
        self.confirm_exit = False
        self.status_hitboxes = []
        self.setup_buttons()
        assets.play_sound("battle_start")

    def setup_buttons(self):
        player = self.game_manager.player
        self.buttons = [{"rect": self.skill_rects[i], "skill": s} for i, s in enumerate(player.equipped_skills[:4])]

    # ------------------------------------------------------------------ input
    @property
    def input_locked(self):
        return self.phase != "player" or self.pending_skill is not None or self.hero_anim.busy or bool(self.projectiles)

    def handle_events(self, events):
        for event in events:
            if self.confirm_exit:       # warning dialog is modal
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.leave_rect.collidepoint(event.pos):
                        self.game_manager.exit_fight()
                        return
                    if self.stay_rect.collidepoint(event.pos):
                        self.confirm_exit = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_y):
                        self.game_manager.exit_fight()
                        return
                    if event.key in (pygame.K_ESCAPE, pygame.K_n):
                        self.confirm_exit = False
                continue
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, btn in enumerate(self.buttons):
                    if btn["rect"].collidepoint(event.pos):
                        self.use_skill(i)
                if self.end_turn_rect.collidepoint(event.pos):
                    self.end_player_turn()
                if self.exit_rect.collidepoint(event.pos):
                    self.request_exit()
            elif event.type == pygame.KEYDOWN:
                if pygame.K_1 <= event.key <= pygame.K_4:
                    self.use_skill(event.key - pygame.K_1)
                elif pygame.K_KP1 <= event.key <= pygame.K_KP4:
                    self.use_skill(event.key - pygame.K_KP1)
                elif event.key == pygame.K_ESCAPE:
                    self.request_exit()
                elif event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
                    self.end_player_turn()

    def request_exit(self):
        """Opens the warning dialog; the fight is only left once the player confirms."""
        if self.phase not in ("victory", "defeat"):
            self.confirm_exit = True

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
            assets.play_sound(self.attack_sound())
        else:
            skill.execute(player, self.enemy)
            self.fx += skill_effects(skill, self.hero_body(), self.enemy_body())
            assets.play_sound("buff")
            self.check_end()

    def attack_sound(self):
        """Metal sword / normal wand with the starting weapon; great sword / great wand once upgraded."""
        player = self.game_manager.player
        upgraded = player.weapon.tier > 0
        kind = "sword" if player.char_class == "Swordsman" else "wand"
        return f"{kind}_{'great' if upgraded else 'basic'}"

    def hero_point(self):
        return self.hero_x + 60, self.ground_y - 250 * 0.6

    def enemy_point(self):
        return self.enemy_x - 60, self.ground_y - self.enemy.height * 0.55

    def resolve_pending(self):
        if not self.pending_skill:
            return
        skill, self.pending_skill = self.pending_skill, None
        player = self.game_manager.player
        name = skill.name.rstrip("+")
        if player.char_class == "Sorcerist" and name not in NO_PROJECTILE:
            # the mage's spell flies to the enemy and lands there
            color = skill.color if skill.element != "physical" else (190, 150, 255)
            style = SPELL_STYLE.get(name, "orb")
            end = self.enemy_point()
            if style == "meteor":
                start = (end[0] + 260, -90)        # drops from the sky
            else:
                start = self.hero_point()
            if style == "missile":                  # one small missile per hit, the last one lands the skill
                hits = max(1, skill.hits)
                for i in range(hits):
                    last = i == hits - 1
                    self.projectiles.append(Projectile("magic", start, (end[0], end[1] + (i - hits / 2) * 18), color,
                                                       (lambda: self.land_player_skill(skill)) if last else (lambda: None),
                                                       "missile", delay=i * 130))
            else:
                self.projectiles.append(Projectile("magic", start, end, color,
                                                   lambda: self.land_player_skill(skill), style))
        else:
            self.land_player_skill(skill)

    def hero_body(self):
        return self.hero_x, self.ground_y - 250 * 0.5

    def enemy_body(self):
        return self.enemy_x, self.ground_y - self.enemy.height * 0.5

    def land_player_skill(self, skill):
        player = self.game_manager.player
        skill.execute(player, self.enemy)
        self.fx += skill_effects(skill, self.hero_body(), self.enemy_body(), slash=player.char_class == "Swordsman")
        self.shake = max(self.shake, SCREEN_SHAKE.get(skill.name.rstrip("+"), 0))
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
            # melee enemies dash over to the hero for attacks that deal damage
            self.enemy_lunge = bool(move.damage) and getattr(enemy, "melee", False)
            if not getattr(enemy, "melee", False):
                # archers and casters let go of an arrow or spell partway through the attack
                self.enemy_release = move
                self.enemy_anim.play("attack", on_done=lambda: self.release_enemy_shot(move))
            else:
                self.enemy_anim.play("attack", on_done=lambda: self.finish_enemy_turn(move))
        else:
            self.finish_enemy_turn(move)

    def release_enemy_shot(self, move):
        """Fires the enemy's arrow or spell at the hero once; the move lands when it arrives."""
        if self.enemy_release is not move:
            return
        self.enemy_release = None
        if not (move.damage or move.effects):       # buffs, blocks and heals have nothing to fire
            self.finish_enemy_turn(move)
            return
        if "Archer" in self.enemy.name:
            kind, color = "arrow", (215, 180, 120)
        else:
            kind, color = "magic", move.color if move.element != "physical" else (190, 150, 255)
        self.projectiles.append(Projectile(kind, self.enemy_point(), (self.hero_x, self.ground_y - 250 * 0.55), color,
                                           lambda: self.finish_enemy_turn(move)))

    def finish_enemy_turn(self, move):
        player = self.game_manager.player
        if self.phase != "enemy":
            return
        move.execute(self.enemy, player)
        self.fx += skill_effects(move, self.enemy_body(), self.hero_body(), slash=getattr(self.enemy, "melee", False))
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
        if self.enemy_release and self.enemy_anim.current == "attack" and self.enemy_anim.progress() >= 0.55:
            self.release_enemy_shot(self.enemy_release)
        for e in self.fx:
            e.update(dt)
        self.fx = [e for e in self.fx if e.alive]
        for proj in self.projectiles:
            proj.update(self.game_manager.dt)
        landed = [pr for pr in self.projectiles if pr.done]
        self.projectiles = [pr for pr in self.projectiles if not pr.done]
        for pr in landed:
            pr.on_hit()

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
        if self.rematch:
            gm.end_rematch(self.phase == "victory")
        elif self.phase == "victory":
            gm.stats[{"normal": "enemies", "elite": "elites", "boss": "bosses"}[self.enemy.rank]] += 1
            gm.encounter_won()
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
                            if not self.hero_anim.busy and ent.is_alive:
                                self.hero_anim.play("hurt")
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
        for proj in self.projectiles:
            proj.draw(world)
        for e in self.fx:
            e.draw(world)
        for f in self.floaters:
            f.draw(world)

        if world is not screen:
            screen.fill((0, 0, 0))
            screen.blit(world, (random.uniform(-self.shake, self.shake), random.uniform(-self.shake, self.shake)))

        self.draw_bottom_panel(screen, player, mouse)
        self.draw_log(screen)
        self.draw_turn_banner(screen)
        if self.phase not in ("victory", "defeat"):
            ui.button(screen, self.exit_rect, "Exit Fight [Esc]", self.exit_rect.collidepoint(mouse), True, size=15)
        if self.confirm_exit:
            self.draw_exit_dialog(screen, mouse)
        else:
            self.draw_tooltips(screen, player, mouse)

        if self.phase in ("victory", "defeat") and self.phase_timer > 400:
            ui.dim(screen, min(140, int((self.phase_timer - 400) * 0.3)))
            msg, color = ("VICTORY!", ui.GOLD) if self.phase == "victory" else ("DEFEATED", ui.RED)
            ui.text_shadow(screen, msg, 80, color, center=(self.w // 2, self.h // 2 - 120))

    def draw_exit_dialog(self, screen, mouse):
        ui.dim(screen, 150)
        r = self.dialog_rect
        ui.panel(screen, r, (26, 20, 20), ui.GOLD, 245, 10)
        ui.text_shadow(screen, "Leave the fight?", 32, (255, 140, 120), center=(r.centerx, r.y + 38))
        if self.rematch:
            msg = "This rematch will count as a loss. Nothing else is lost."
        else:
            msg = (f"Floor {self.floor}'s progress will be reset and you'll start again "
                   "from its first fight. Cleared floors and items are kept.")
        ui.text_wrapped(screen, msg, 18, pygame.Rect(r.x + 30, r.y + 70, r.width - 60, 80), ui.TEXT)
        ui.button(screen, self.leave_rect, "Leave [Enter]", self.leave_rect.collidepoint(mouse), True,
                  (150, 40, 40), (200, 50, 50), 19)
        ui.button(screen, self.stay_rect, "Keep Fighting [Esc]", self.stay_rect.collidepoint(mouse), True, size=17)

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
        x = self.enemy_x
        if self.enemy_anim.busy and self.enemy_anim.current == "attack" and getattr(self, "enemy_lunge", False):
            # dashes toward the hero and back during the swing (mirror of the Swordsman's dash)
            x -= math.sin(self.enemy_anim.progress() * math.pi) * (self.enemy_x - self.hero_x - 260)
        x = int(x)
        pygame.draw.ellipse(screen, (0, 0, 0), (x - 90, self.ground_y - 10, 180, 24))
        if self.enemy_anim.available:
            if self.enemy_alpha < 255:
                layer = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
                self.enemy_anim.draw(layer, (x, self.ground_y))
                layer.set_alpha(int(self.enemy_alpha))
                screen.blit(layer, (0, 0))
            else:
                self.enemy_anim.draw(screen, (x, self.ground_y), flash=self.flash["enemy"] > 0)
        elif enemy.is_alive:
            pygame.draw.rect(screen, (50, 200, 50), (self.enemy_x - 70, self.ground_y - 220, 140, 220), border_radius=15)

        top = max(140, self.ground_y - enemy.height - 20)   # keep name, HP and intent on screen for giant bosses
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
        ui.panel(screen, self.ui_panel_rect, ui.PANEL, ui.PANEL_BORDER, GLASS, 0)
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
            ui.panel(screen, rect, fill, ui.GOLD_LIGHT if hovered and usable else (ui.GOLD if usable else (92, 84, 70)),
                     220 if hovered and usable else GLASS, 8)
            pygame.draw.rect(screen, skill.color, (rect.x + 8, rect.y + 5, rect.width - 16, 4), border_radius=2)

            text_color = ui.TEXT if usable else ui.TEXT_DIM
            ui.text(screen, f"[{i + 1}]", 14, ui.TEXT_DIM, True, topleft=(rect.x + 10, rect.y + 14))
            # energy cost badge (top right) -- red when there isn't enough energy
            affordable = player.energy >= skill.energy_cost
            badge = (rect.right - 20, rect.y + 24)
            pygame.draw.circle(screen, (4, 8, 20), badge, 14)
            pygame.draw.circle(screen, ui.ENERGY if affordable else (150, 50, 50), badge, 12)
            pygame.draw.circle(screen, ui.GOLD_LIGHT if affordable else (92, 84, 70), badge, 12, 1)
            ui.text(screen, str(skill.energy_cost), 17, (10, 20, 40) if affordable else ui.TEXT, True, center=badge)
            name_w = rect.width - 40 - 44
            name_size = 20
            while assets.font(name_size, True).size(skill.name)[0] > name_w and name_size > 13:
                name_size -= 1
            ui.text_shadow(screen, skill.name, name_size, text_color, midleft=(rect.x + 40, rect.y + 24))
            ui.text_wrapped(screen, skill.summary(player, self.enemy), 16,
                            pygame.Rect(rect.x + 10, rect.y + 46, rect.width - 20, 60), text_color)
            cost = f"Costs {skill.energy_cost} Energy" if affordable else f"Needs {skill.energy_cost} Energy"
            ui.text_shadow(screen, cost, 14, (150, 200, 255) if affordable else (255, 130, 120), False,
                           bottomleft=(rect.x + 10, rect.bottom - 8))

        can_end = not self.input_locked
        hovered = self.end_turn_rect.collidepoint(mouse)
        ui.button(screen, self.end_turn_rect, "End Turn", hovered, can_end, (150, 40, 40), (200, 50, 50), 24)
        ui.text(screen, "[E / Space]", 13, ui.TEXT_DIM, center=(self.end_turn_rect.centerx, self.end_turn_rect.bottom + 14))

    def draw_log(self, screen):
        # Only show as many lines as fit above the hero's name so they never overlap
        name_top = self.ground_y - 330 - assets.font(22, True).get_linesize() - 8
        max_lines = max(1, (name_top - 16 - 26) // 22)
        log = self.log[-max_lines:]
        rect = pygame.Rect(16, 16, 360, 26 + 22 * len(log))
        ui.panel(screen, rect, (10, 10, 16), None, 185, 8)
        y = rect.y + 12
        for i, (msg, color) in enumerate(log):
            faded = tuple(int(c * (0.5 + 0.5 * (i + 1) / len(log))) for c in color)
            ui.text(screen, msg, 16, faded, topleft=(rect.x + 12, y))
            y += 22
        gm = self.game_manager
        label = "Rematch" if self.rematch else f"Encounter {self.encounter.number}/{self.floor_total}"
        ui.text_shadow(screen, f"Floor {self.floor}  ·  {label}  ·  {self.encounter.title}", 20, ui.GOLD,
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
                lines = [(s.name, s.color), (f"Energy cost: {s.energy_cost}  (you have {player.energy})",
                                              (150, 200, 255) if player.energy >= s.energy_cost else (255, 130, 120)),
                         (s.summary(player, self.enemy), ui.TEXT)]
                if s.description:
                    lines.append((s.description, ui.TEXT_DIM))
                # small and see-through, so it doesn't hide the fighters
                ui.tooltip(screen, lines, (btn["rect"].x - 12, btn["rect"].y - 4), width=230, size=15, alpha=170)
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
