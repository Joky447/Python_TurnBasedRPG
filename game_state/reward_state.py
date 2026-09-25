import random

import pygame

import assets
import ui
from game_state.state import GameState
from inventory_mechanics.weapon_library import random_weapons
from skills.skill_library import random_skills

TITLES = {
    "normal": "Victory! Choose a Reward",
    "elite": "Elite Defeated! Choose a Reward",
    "boss": "Boss Defeated! Claim a Weapon",
    "treasure": "Treasure! Choose One",
    "rest": "Campfire: Rest or Train",
}


class RewardState(GameState):
    """Loot after combat, treasure rooms and campfires.

    Some rewards need a second step: learning a skill asks which slot to replace,
    and training asks which skill to upgrade.
    """
    def __init__(self, game_manager):
        super().__init__(game_manager)
        w, h = game_manager.screen.get_size()
        self.w, self.h = w, h
        self.bg = assets.load_background("map/bcgpc.png", (w, h))
        self.skip_rect = pygame.Rect(w // 2 - 90, h - 80, 180, 52)
        self.options = []
        self.option_rects = []
        self.pending = None       # {"kind": "skill"/"upgrade", "skill": Skill or None}
        self.slot_rects = [pygame.Rect(w // 2 - 2 * 260 + i * 260 + 10, 330, 240, 200) for i in range(4)]

    # ------------------------------------------------------------------ setup
    def enter(self, mode="normal", **kwargs):
        self.mode = mode
        self.pending = None
        self.options = self.generate_options(mode)
        n = len(self.options)
        card_w, gap = 290, 30
        start = (self.w - (n * card_w + (n - 1) * gap)) // 2
        self.option_rects = [pygame.Rect(start + i * (card_w + gap), 170, card_w, 360) for i in range(n)]

    def generate_options(self, mode):
        p = self.game_manager.player
        owned = [s.name for s in p.equipped_skills]
        can_upgrade = any(not s.upgraded for s in p.equipped_skills)
        opts = []

        def skill_opt():
            skills = random_skills(p.char_class, 1, owned)
            return [{"kind": "skill", "skill": skills[0]}] if skills else []

        def weapon_opts(n):
            return [{"kind": "weapon", "weapon": w} for w in random_weapons(p.char_class, n, p.weapon.name)]

        upgrade = [{"kind": "upgrade"}] if can_upgrade else []

        if mode == "normal":
            opts += skill_opt()
            extras = [{"kind": "heal", "amount": 20}, {"kind": "maxhp", "amount": 8},
                      {"kind": "damage", "amount": 1}] + upgrade
            opts += random.sample(extras, 3 - len(opts))
        elif mode == "elite":
            opts += skill_opt() + weapon_opts(1)
            opts.append(random.choice(upgrade + [{"kind": "damage", "amount": 2}]))
        elif mode == "boss":
            opts += weapon_opts(3)
            while len(opts) < 3:
                opts.append({"kind": "damage", "amount": 2})
        elif mode == "treasure":
            opts += weapon_opts(2) + skill_opt()
        elif mode == "rest":
            opts.append({"kind": "heal", "amount": int(p.max_hp * 0.3)})
            opts += upgrade or [{"kind": "maxhp", "amount": 6}]
        return opts

    # ------------------------------------------------------------------ input
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.pending:
                    for i, rect in enumerate(self.slot_rects):
                        if rect.collidepoint(event.pos):
                            self.pick_slot(i)
                            return
                    if self.skip_rect.collidepoint(event.pos):
                        self.pending = None
                else:
                    for i, rect in enumerate(self.option_rects):
                        if rect.collidepoint(event.pos):
                            self.pick(i)
                            return
                    if self.skip_rect.collidepoint(event.pos):
                        self.finish()
                        return
            elif event.type == pygame.KEYDOWN:
                idx = event.key - pygame.K_1
                if self.pending:
                    if 0 <= idx < 4:
                        self.pick_slot(idx)
                        return
                    if event.key == pygame.K_ESCAPE:
                        self.pending = None
                else:
                    if 0 <= idx < len(self.options):
                        self.pick(idx)
                        return
                    if event.key in (pygame.K_s, pygame.K_ESCAPE):
                        self.finish()
                        return

    def pick(self, index):
        opt = self.options[index]
        p = self.game_manager.player
        kind = opt["kind"]
        if kind in ("skill", "upgrade"):
            self.pending = opt
            return
        if kind == "weapon":
            p.equip_weapon(opt["weapon"])
        elif kind == "heal":
            p.heal(opt["amount"])
        elif kind == "maxhp":
            p.max_hp += opt["amount"]
            p.heal(opt["amount"])
        elif kind == "damage":
            p.bonus_damage += opt["amount"]
        assets.play_sound("reward")
        self.finish()

    def pick_slot(self, slot):
        p = self.game_manager.player
        if slot >= len(p.equipped_skills):
            return
        if self.pending["kind"] == "skill":
            p.equipped_skills[slot] = self.pending["skill"]
        else:
            if p.equipped_skills[slot].upgraded:
                return
            p.equipped_skills[slot].upgrade()
        assets.play_sound("reward")
        self.pending = None
        self.finish()

    def finish(self):
        self.game_manager.player.events.clear()
        self.game_manager.complete_node()

    # ------------------------------------------------------------------ drawing
    def describe(self, opt):
        """Returns (title, color, body lines) for a reward card."""
        kind = opt["kind"]
        if kind == "skill":
            s = opt["skill"]
            return "New Skill", s.color, [(s.name, s.color, 24), (f"{s.energy_cost} Energy", ui.ENERGY, 18),
                                          (s.summary(), ui.TEXT, 18), (s.description, ui.TEXT_DIM, 16),
                                          ("Replaces one of your skills.", ui.TEXT_DIM, 16)]
        if kind == "weapon":
            w = opt["weapon"]
            lines = [(w.name, ui.GOLD, 24), (f"+{w.stat_bonus} damage" + (f", +{w.max_hp_bonus} Max HP" if w.max_hp_bonus else ""),
                                              ui.TEXT, 18), (w.description, ui.TEXT_DIM, 16)]
            lines += [(f"• {s.name}", s.color, 17) for s in w.skills]
            lines.append(("Replaces all 4 skills.", (255, 160, 120), 15))
            return "Weapon", ui.GOLD, lines
        if kind == "upgrade":
            return "Train", (120, 220, 255), [("Upgrade a skill", ui.TEXT, 22),
                                               ("Its numbers improve by about a third, and it gains a +.", ui.TEXT_DIM, 17)]
        if kind == "heal":
            return "Heal", (90, 230, 100), [(f"Restore {opt['amount']} HP", ui.TEXT, 22)]
        if kind == "maxhp":
            return "Vitality", (240, 90, 90), [(f"+{opt['amount']} Max HP", ui.TEXT, 22), ("And heal that much.", ui.TEXT_DIM, 17)]
        if kind == "damage":
            return "Power", (255, 150, 60), [(f"+{opt['amount']} damage", ui.TEXT, 22), ("On every hit, permanently.", ui.TEXT_DIM, 17)]
        return kind.title(), ui.TEXT, []

    def draw(self, screen):
        if self.bg:
            screen.blit(self.bg, (0, 0))
            ui.dim(screen, 170)
        else:
            screen.fill((40, 30, 40))
        mouse = pygame.mouse.get_pos()
        p = self.game_manager.player

        ui.text_shadow(screen, TITLES.get(self.mode, "Choose a Reward"), 44, ui.GOLD, center=(self.w // 2, 70))
        ui.text(screen, f"HP {p.current_hp}/{p.max_hp}   ·   {p.weapon.name} (+{p.stat_bonus} dmg)", 20, ui.TEXT_DIM,
                center=(self.w // 2, 118))

        if self.pending:
            self.draw_slot_picker(screen, mouse)
            return

        for i, (opt, rect) in enumerate(zip(self.options, self.option_rects)):
            title, color, lines = self.describe(opt)
            hovered = rect.collidepoint(mouse)
            r = rect.move(0, -8) if hovered else rect
            ui.panel(screen, r, (40, 40, 58) if hovered else (28, 28, 40), ui.GOLD if hovered else (150, 150, 165), 240, 14)
            pygame.draw.rect(screen, color, (r.x, r.y, r.width, 8), border_top_left_radius=14, border_top_right_radius=14)
            ui.text(screen, f"[{i + 1}]", 16, ui.TEXT_DIM, True, topleft=(r.x + 14, r.y + 20))
            ui.text(screen, title, 28, color, True, midtop=(r.centerx, r.y + 18))
            y = r.y + 70
            for msg, c, size in lines:
                y = ui.text_wrapped(screen, msg, size, pygame.Rect(r.x + 20, y, r.width - 40, 200), c) + 8

        ui.button(screen, self.skip_rect, "Skip  [S]", self.skip_rect.collidepoint(mouse), size=20)

    def draw_slot_picker(self, screen, mouse):
        p = self.game_manager.player
        upgrading = self.pending["kind"] == "upgrade"
        if upgrading:
            prompt = "Choose a skill to upgrade"
        else:
            s = self.pending["skill"]
            prompt = f"Learn {s.name}: {s.summary()}  —  choose a skill to replace"
        ui.text_shadow(screen, prompt, 24, ui.TEXT, center=(self.w // 2, 250))

        for i, (skill, rect) in enumerate(zip(p.equipped_skills, self.slot_rects)):
            allowed = not (upgrading and skill.upgraded)
            hovered = rect.collidepoint(mouse) and allowed
            ui.panel(screen, rect, (40, 40, 58) if hovered else (28, 28, 40), ui.GOLD if hovered else (150, 150, 165), 240, 12)
            pygame.draw.rect(screen, skill.color, (rect.x, rect.y, rect.width, 6), border_top_left_radius=12,
                             border_top_right_radius=12)
            ui.text(screen, f"[{i + 1}] {skill.name}", 20, skill.color if allowed else ui.TEXT_DIM, True,
                    topleft=(rect.x + 14, rect.y + 18))
            ui.text(screen, f"{skill.energy_cost} Energy", 16, ui.ENERGY, topleft=(rect.x + 14, rect.y + 48))
            ui.text_wrapped(screen, skill.summary(), 17, pygame.Rect(rect.x + 14, rect.y + 76, rect.width - 28, 80),
                            ui.TEXT if allowed else ui.TEXT_DIM)
            if hovered and upgrading:
                preview = skill.copy()
                preview.upgrade()
                ui.text_wrapped(screen, "→ " + preview.summary(), 16,
                                pygame.Rect(rect.x + 14, rect.y + 140, rect.width - 28, 60), (140, 230, 140))
            elif upgrading and not allowed:
                ui.text(screen, "Already upgraded", 15, ui.TEXT_DIM, topleft=(rect.x + 14, rect.bottom - 30))

        ui.button(screen, self.skip_rect, "Back  [Esc]", self.skip_rect.collidepoint(mouse), size=20)
