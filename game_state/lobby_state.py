import pygame

import animation
import assets
import ui
from game_state.game_manager import MAX_ROSTER
from game_state.state import GameState
from game_state.ui_layouts import CAMP, ArtLayout
from inventory_mechanics.item import ITEM_TYPES

GEN = "menu_ui/generated/"

INVENTORY_COLS = 7


_BODY_X = {}


# Where each outfit's face is in its resting pose, as (x, y) in units of the frame's height
# (measured on the art; wings, staffs and long hair make it hard to find automatically)
FACES = {
    ("Boy", "Swordsman"): [(120, 30), (125, 35), (155, 30), (145, 40), (145, 35), (146, 103)],
    ("Girl", "Swordsman"): [(140, 25), (163, 34), (137, 36), (232, 26), (210, 30), (178, 84)],
    ("Boy", "Sorcerist"): [(110, 55), (115, 70), (105, 65), (100, 90), (110, 80), (116, 140)],
    ("Girl", "Sorcerist"): [(120, 50), (118, 82), (100, 80), (100, 110), (100, 105), (108, 120)],
}


def face_center(surf, gender, char_class, stage) -> tuple[int, int]:
    x, y = FACES[(gender, char_class)][stage]
    k = surf.get_height() / 360
    return int(x * k), int(y * k)


def body_center_x(surf, rows=None) -> int:
    """x that splits a sprite's solid pixels in half (optionally only within `rows`).
    Thin things like a staff or sword barely move it, so it finds the body, not the weapon.
    Cached, since sprite frames are shared and never change."""
    key = (id(surf), None if rows is None else (rows.start, rows.stop))
    if key not in _BODY_X:
        _BODY_X[key] = _body_center_x(surf, rows)
    return _BODY_X[key]


def _body_center_x(surf, rows=None) -> int:
    mask = pygame.mask.from_surface(surf, 100)
    w, h = surf.get_size()
    rows = rows if rows is not None else range(0, h, 2)
    cols = [sum(mask.get_at((x, y)) for y in rows) for x in range(w)]
    total, run = sum(cols), 0
    for x, c in enumerate(cols):
        run += c
        if run * 2 >= total:
            return x
    return w // 2


class LobbyState(GameState):
    """Base Camp: the active character's stats, the 2-character roster, and a
    Skills / Equipment panel where items are equipped and unequipped."""

    def __init__(self, game_manager):
        super().__init__(game_manager)
        w, h = game_manager.screen.get_size()
        self.w, self.h = w, h
        self.bg = assets.load_background("map/bcgpc.png", (w, h))
        # The Base Camp mockup (menu_ui/base camp ui.png) with its sample content erased,
        # made by tools/make_ui_templates.py. Live content is drawn in the mockup's spots.
        L = self.L = ArtLayout(CAMP, (w, h))
        self.art = assets.load_part(GEN + "camp.png", (w, h))
        self.art_skills = assets.load_part(GEN + "camp_skills.png", (w, h))

        self.left = L.rect((36, 140, 652, 872))
        self.right = L.rect((688, 152, 1608, 772))
        self.sprite_stage = L.rect(CAMP["sprite_stage"])
        self.roster_rows = [L.rect(r) for r in CAMP["roster_rows"]]
        self.tabs = {"Skills": L.rect(CAMP["tab_skills"]), "Equipment": L.rect(CAMP["tab_equipment"])}
        self.slot_rects = {t: L.rect(r) for t, r in zip(ITEM_TYPES, CAMP["slot_boxes"])}
        area = L.rect(CAMP["inventory_area"])
        cell, cgap = L.size(96), L.size(12)
        gx = area.x + (area.width - (INVENTORY_COLS * cell + (INVENTORY_COLS - 1) * cgap)) // 2
        self.grid_origin, self.cell, self.cgap = (gx, area.y + L.size(8)), cell, cgap
        self.inventory_area = area
        self.btn_start = L.rect(CAMP["begin_btn"])
        self.btn_menu = L.rect(CAMP["menu_btn"])
        self.tab = "Equipment"
        self.hero = None
        self.hero_key = None
        self.confirm_delete = None      # roster index waiting for a second Delete click
        self.message = None             # (text, time left in ms)

    # ------------------------------------------------------------------ setup
    def enter(self, **kwargs):
        assets.play_music("title")
        self.confirm_delete = None
        self.refresh_hero()

    def refresh_hero(self):
        """Rebuilds the sprite when the active character or their outfit changes."""
        p = self.game_manager.player
        key = (id(p), p.outfit_stage) if p else None
        if key != self.hero_key:
            self.hero_key = key
            self.hero = animation.hero_sprite(p.gender, p.char_class, p.outfit_stage, height=260) if p else None

    # ------------------------------------------------------------------ layout helpers
    def roster_buttons(self, i):
        dy = self.roster_rows[i].y - self.roster_rows[0].y
        select = self.L.rect(CAMP["btn_selected"]).move(0, dy)
        delete = self.L.rect(CAMP["btn_delete"]).move(0, dy)
        return select, delete

    def create_button(self, i):
        dy = self.roster_rows[i].y - self.roster_rows[1].y
        return self.L.rect(CAMP["create_btn"]).move(0, dy)

    def inventory_rects(self):
        p = self.game_manager.player
        gx, gy = self.grid_origin
        return [(item, pygame.Rect(gx + (n % INVENTORY_COLS) * (self.cell + self.cgap),
                                   gy + (n // INVENTORY_COLS) * (self.cell + self.cgap), self.cell, self.cell))
                for n, item in enumerate(p.inventory if p else [])]

    def say(self, text):
        self.message = (text, 2500)

    # ------------------------------------------------------------------ input
    def handle_events(self, events):
        gm = self.game_manager
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.begin()
                    return
                if event.key == pygame.K_ESCAPE:
                    gm.save()
                    gm.change_state("MainMenuState")
                    return
                if event.key == pygame.K_TAB:
                    self.tab = "Skills" if self.tab == "Equipment" else "Equipment"
            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                continue
            pos = event.pos
            if self.btn_menu.collidepoint(pos):
                gm.save()
                gm.change_state("MainMenuState")
                return
            if self.btn_start.collidepoint(pos):
                self.begin()
                return
            for name, rect in self.tabs.items():
                if rect.collidepoint(pos):
                    self.tab = name
            if self.click_roster(pos):
                return
            if self.tab == "Equipment":
                self.click_equipment(pos)

    def click_roster(self, pos) -> bool:
        gm = self.game_manager
        for i in range(MAX_ROSTER):
            if i >= len(gm.roster):
                if self.create_button(i).collidepoint(pos):
                    gm.change_state("CharacterCreationState")
                    return True
                continue
            select, delete = self.roster_buttons(i)
            if select.collidepoint(pos) and i != gm.active_player_index:
                gm.select_character(i)
                gm.new_run()
                self.confirm_delete = None
                self.refresh_hero()
            elif delete.collidepoint(pos) and i != gm.active_player_index:
                if self.confirm_delete == i:
                    name = gm.roster[i].name
                    gm.delete_character(i)
                    self.confirm_delete = None
                    self.say(f"{name} has left the camp.")
                else:
                    self.confirm_delete = i
            else:
                continue
            return True
        return False

    def click_equipment(self, pos):
        p = self.game_manager.player
        for item_type, rect in self.slot_rects.items():
            item = p.equipped(item_type)
            if rect.collidepoint(pos) and item:
                if p.unequip_item(item):
                    self.after_gear_change()
                elif item.type == "Weapon":
                    self.say("Your skills come from your weapon: equip another weapon to swap it.")
                return
        for item, rect in self.inventory_rects():
            if rect.collidepoint(pos):
                if p.equip_item(item):
                    self.after_gear_change()
                else:
                    self.say(f"{item.name} can't be used by a {p.char_class}.")
                return

    def after_gear_change(self):
        p = self.game_manager.player
        p.current_hp = p.max_hp          # resting at camp
        self.game_manager.save()
        self.refresh_hero()

    def begin(self):
        gm = self.game_manager
        if gm.player:
            gm.new_run()
            gm.change_state("MapState")

    def update(self):
        dt = self.game_manager.dt
        if self.hero:
            self.hero.update(dt)
        if self.message:
            self.message = (self.message[0], self.message[1] - dt)
            if self.message[1] <= 0:
                self.message = None

    # ------------------------------------------------------------------ drawing
    def part(self, screen, name, rect, add=None, mult=None):
        """Draws a UI part; `add` brightens it by a color and `mult` scales its colors
        (only where the part is drawn, so pointed buttons keep their shape)."""
        img = assets.load_part(GEN + name, rect.size)
        if not img:
            return
        if add or mult:
            key = (name, rect.size, add, mult)
            cache = self.__dict__.setdefault("_tinted", {})
            if key not in cache:
                tinted = img.copy()
                if mult:
                    tinted.fill([int(255 * m) for m in mult], special_flags=pygame.BLEND_RGB_MULT)
                if add:
                    tinted.fill(add, special_flags=pygame.BLEND_RGB_ADD)
                # only the solid button is tinted; its faint outer glow keeps its color
                w, h = img.get_size()
                for y in range(h):
                    for x in range(w):
                        if img.get_at((x, y)).a < 200:
                            tinted.set_at((x, y), img.get_at((x, y)))
                cache[key] = tinted
            img = cache[key]
        screen.blit(img, rect.topleft)

    def portrait(self, member, size):
        """Head-and-shoulders crop of the character's resting pose, framed on the face (cached)."""
        key = (member.gender, member.char_class, member.outfit_stage, size)
        cache = self.__dict__.setdefault("_portraits", {})
        if key not in cache:
            sprite = animation.hero_sprite(member.gender, member.char_class, member.outfit_stage, height=size[1] * 4)
            frame = sprite.current_frame()
            cache[key] = None
            if frame:
                surf = frame[0]
                cx, cy = face_center(surf, member.gender, member.char_class, member.outfit_stage)
                crop = pygame.Rect(cx - size[0] // 2, cy - size[1] * 2 // 5, size[0], size[1])
                out = pygame.Surface(size, pygame.SRCALPHA)
                out.blit(surf, (0, 0), crop)
                cache[key] = out
        return cache[key]

    def hover_glow(self, screen, rect):
        glow = pygame.Surface(rect.size)
        pygame.draw.rect(glow, (26, 26, 18), glow.get_rect().inflate(-10, -10), border_radius=10)
        screen.blit(glow, rect.topleft, special_flags=pygame.BLEND_RGB_ADD)

    def label(self, screen, text, rect, size, color=ui.TEXT):
        f_size = self.L.size(size)
        while assets.font(f_size, True).size(text)[0] > rect.width - self.L.size(40) and f_size > 11:
            f_size -= 1
        ui.text_shadow(screen, text, f_size, color, center=rect.center)

    def backdrop(self, art):
        """The screen art over the night background (it shows through the see-through panels),
        combined once into one opaque image so each frame is a single fast copy."""
        cache = self.__dict__.setdefault("_backdrops", {})
        if id(art) not in cache:
            out = pygame.Surface(art.get_size()).convert()
            if self.bg:
                out.blit(self.bg, (0, 0))
            out.blit(art, (0, 0))
            cache[id(art)] = out
        return cache[id(art)]

    def draw(self, screen):
        gm = self.game_manager
        p = gm.player
        mouse = pygame.mouse.get_pos()
        art = self.art_skills if self.tab == "Skills" else self.art
        if not art or not p:
            screen.fill(ui.BG)
            return
        screen.blit(self.backdrop(art), (0, 0))
        # Title, straightened and a little smaller than in the mockup
        title = self.L.rect(CAMP["title"])
        img = assets.load_part(GEN + "camp_title.png", (int(title.width * 0.82), int(title.height * 0.82)))
        if img:
            screen.blit(img, img.get_rect(center=(title.centerx, title.centery - self.L.size(4))))
        if self.btn_menu.collidepoint(mouse):
            self.hover_glow(screen, self.btn_menu)

        self.draw_character(screen, p)
        self.draw_roster(screen, mouse)
        self.draw_tabs(screen, mouse)
        tooltip = self.draw_equipment(screen, p, mouse) if self.tab == "Equipment" else self.draw_skills(screen, p)

        # Begin Adventure: the blue banner and its compass icon are part of the art
        if self.btn_start.collidepoint(mouse):
            self.hover_glow(screen, self.btn_start)
        text_rect = pygame.Rect(self.L.point((CAMP["begin_text_x"], 0))[0], self.btn_start.y,
                                self.btn_start.right - self.L.point((CAMP["begin_text_x"], 0))[0] - self.L.size(40),
                                self.btn_start.height)
        start = gm.resume_floor()
        if gm.all_cleared:
            label = f"Free Play: any floor as {p.name}"
        else:
            label = f"Begin Adventure as {p.name}" if start == 1 else f"Continue {p.name}: Floor {start}"
        self.label(screen, label, text_rect, 30, ui.GOLD_LIGHT if
                   self.btn_start.collidepoint(mouse) else ui.TEXT)

        if self.message:
            ui.text_shadow(screen, self.message[0], 17, (255, 210, 150), False,
                           center=(self.right.centerx, self.right.bottom - 22))
        if tooltip:
            tooltip(screen, mouse)

    def draw_character(self, screen, p):
        L = self.L
        stage = self.sprite_stage
        # Center the character in its area: shift by where its resting pose sits, so poses
        # that lean one way (or hold a long weapon) still end up in the middle
        fx, fy = L.point(CAMP["sprite_feet"])
        rest = self.hero.clips.get("idle", [None])[0] if self.hero else None
        if rest:
            surf, (ox, _) = rest
            fx = stage.centerx - (ox + body_center_x(surf))
        # Glowing platform under the character, in the style of the Create screen's pedestal
        rx, ry = L.size(120), L.size(22)
        glow = pygame.Surface((rx * 2 + 40, ry * 2 + 40), pygame.SRCALPHA)
        for k in range(10, 0, -1):
            pygame.draw.ellipse(glow, (60, 120, 230, 10), glow.get_rect().inflate(-k * 4, -k * 2))
        screen.blit(glow, glow.get_rect(center=(stage.centerx, fy + L.size(6))))
        plat = pygame.Rect(0, 0, rx * 2, ry * 2)
        plat.center = (stage.centerx, fy + L.size(6))
        pygame.draw.ellipse(screen, (12, 22, 48), plat)
        pygame.draw.ellipse(screen, ui.GOLD_DARK, plat, 2)
        pygame.draw.ellipse(screen, (70, 130, 220), plat.inflate(-L.size(26), -L.size(10)), 1)
        if self.hero:
            layer = pygame.Surface(stage.size, pygame.SRCALPHA)
            self.hero.draw(layer, (fx - stage.x, fy - stage.y))
            screen.blit(layer, stage.topleft)
        ui.text_shadow(screen, p.name, L.size(44), ui.GOLD, topleft=L.point(CAMP["name"]))
        ui.text(screen, f"{p.gender} {p.char_class}", L.size(22), ui.TEXT, topleft=L.point(CAMP["class"]))
        x0, x1, dy = CAMP["divider"]
        a, b = L.point((x0, dy)), L.point((x1, dy))
        pygame.draw.line(screen, ui.GOLD_DARK, a, b, 1)
        mid = ((a[0] + b[0]) // 2, a[1])
        pygame.draw.polygon(screen, ui.GOLD, [(mid[0], mid[1] - 4), (mid[0] + 4, mid[1]), (mid[0], mid[1] + 4),
                                              (mid[0] - 4, mid[1])])
        labels = ["HP", "Energy", "Damage", "Block per turn", "Weapon"]
        values = [p.max_hp, p.max_energy, f"+{p.stat_bonus}", p.base_block, p.weapon.name if p.weapon else "-"]
        for n, (label, value) in enumerate(zip(labels, values)):
            icon = assets.load_icon(f"{GEN}camp_stat_{n}.png", (L.size(40), L.size(40)))
            if icon:
                screen.blit(icon, icon.get_rect(center=L.point(CAMP["stat_icons"][n])))
            ui.text(screen, label, L.size(22), ui.TEXT, topleft=L.point(CAMP["stat_labels"][n]))
            # shrink long values (weapon names) so they stay inside the panel's frame
            pos, size = L.point(CAMP["stat_values"][n]), L.size(28)
            max_w = L.point((CAMP["stat_right"], 0))[0] - pos[0]
            while assets.font(size, True).size(str(value))[0] > max_w and size > 12:
                size -= 1
            ui.text_shadow(screen, value, size, ui.GOLD_LIGHT, topleft=(pos[0], pos[1] + (L.size(28) - size) // 2))

    def draw_roster(self, screen, mouse):
        gm = self.game_manager
        L = self.L
        ui.text_shadow(screen, f"Roster ({len(gm.roster)}/{MAX_ROSTER})", L.size(26), ui.GOLD,
                       midleft=L.point(CAMP["roster_header"]))
        for i, row in enumerate(self.roster_rows):
            if i >= len(gm.roster):
                btn = self.create_button(i)
                self.part(screen, "camp_wide_btn.png", btn)
                if btn.collidepoint(mouse):
                    self.hover_glow(screen, btn)
                self.label(screen, "+  Create New Character", btn, 28)
                continue
            member = gm.roster[i]
            active = i == gm.active_player_index
            self.part(screen, "camp_row.png", row)
            if not active:
                ui.dim_rect(screen, row.inflate(-8, -8), 70)
            face = pygame.Rect(row.x + L.size(10), row.y + L.size(8), L.size(84), row.height - L.size(16))
            pygame.draw.rect(screen, (8, 16, 40), face)
            portrait = self.portrait(member, face.size)
            if portrait:
                screen.blit(portrait, face.topleft)
            pygame.draw.rect(screen, ui.GOLD, face, 1)
            tx = face.right + L.size(14)
            ui.text_shadow(screen, member.name, L.size(26), ui.TEXT, topleft=(tx, row.y + L.size(12)))
            ui.text(screen, f"{member.gender} {member.char_class}", L.size(17), ui.TEXT_DIM,
                    topleft=(tx, row.y + L.size(44)))
            if active:
                badge = pygame.Rect(tx, row.y + L.size(66), L.size(74), L.size(24))
                pygame.draw.rect(screen, (18, 70, 50), badge, border_radius=3)
                pygame.draw.rect(screen, (80, 190, 130), badge, 1, border_radius=3)
                ui.text(screen, "ACTIVE", L.size(15), (150, 230, 180), center=badge.center)
            select, delete = self.roster_buttons(i)
            confirming = self.confirm_delete == i
            # hover and "Sure?" tint the button itself, so no box shows around its pointed ends
            self.part(screen, "camp_btn_on.png" if active else "camp_btn_off.png", select,
                      (26, 26, 18) if not active and select.collidepoint(mouse) else None)
            if confirming:
                self.part(screen, "camp_btn_off.png", delete, (110, 0, 0), (1.0, 0.45, 0.45))
            else:
                self.part(screen, "camp_btn_off.png", delete,
                          (26, 26, 18) if not active and delete.collidepoint(mouse) else None)
            self.label(screen, "Selected" if active else "Select", select, 22)
            self.label(screen, "Sure?" if confirming else "Delete", delete, 22,
                       (120, 120, 132) if active else ui.TEXT)

    def draw_tabs(self, screen, mouse):
        for name, rect in self.tabs.items():
            on = self.tab == name
            self.part(screen, "camp_tab_on.png" if on else "camp_tab_off.png", rect)
            if not on and rect.collidepoint(mouse):
                self.hover_glow(screen, rect)
            self.label(screen, name, rect, 28 if on else 26, ui.TEXT)

    def draw_equipment(self, screen, p, mouse):
        """Draws the 5 slots and the inventory grid. Returns a tooltip drawer for the hovered item, if any."""
        L = self.L
        hovered = None
        for item_type, rect in self.slot_rects.items():
            item = p.equipped(item_type)
            is_hover = rect.collidepoint(mouse)
            self.part(screen, "camp_slot_on.png" if item else "camp_slot.png", rect)
            if is_hover and item:
                self.hover_glow(screen, rect)
            ui.text(screen, item_type, L.size(20), ui.TEXT, midtop=(rect.centerx, rect.y + L.size(20)))
            icon_rect = pygame.Rect(rect.x + L.size(30), rect.y + L.size(50), rect.width - L.size(60), L.size(88))
            if item:
                ui.item_icon(screen, item, icon_rect)
                name = item.name if len(item.name) <= 16 else item.name[:15] + "…"
                size = L.size(19)
                while assets.font(size, True).size(name)[0] > rect.width - L.size(16) and size > 10:
                    size -= 1
                active = p.item_active(item)
                if not active:     # set piece switched off by the starting weapon
                    ui.dim_rect(screen, rect.inflate(-L.size(14), -L.size(14)), 170)
                    ui.text_shadow(screen, "DISABLED", L.size(17), (255, 140, 120), center=icon_rect.center)
                ui.text_shadow(screen, name, size, ui.TEXT if active else ui.TEXT_DIM,
                               midbottom=(rect.centerx, rect.bottom - L.size(18)))
                if is_hover:
                    hovered = (item, True)
            else:
                ui.type_icon(screen, item_type, icon_rect, (70, 80, 110))
                ui.text(screen, "Empty", L.size(18), (140, 150, 180), midbottom=(rect.centerx, rect.bottom - L.size(18)))

        ui.text_shadow(screen, f"Inventory ({len(p.inventory)})", L.size(28), ui.GOLD,
                       topleft=L.point(CAMP["inventory_header"]))
        cells = self.inventory_rects()
        if not cells:
            ui.text(screen, "Empty. Bosses drop gear and swapped weapons land here.", L.size(19), (160, 175, 210),
                    center=self.inventory_area.center)
        for item, rect in cells:
            is_hover = rect.collidepoint(mouse)
            usable = item.can_equip(p.char_class)
            ui.panel(screen, rect, (14, 34, 80), ui.GOLD_LIGHT if is_hover else ui.GOLD, 255, 6)
            ui.item_icon(screen, item, rect.inflate(-14, -14))
            if not usable:
                ui.dim_rect(screen, rect)
            if is_hover:
                hovered = (item, False)

        if not hovered:
            return None
        item, equipped = hovered

        def show(screen, mouse):
            lines = [(item.name, ui.GOLD), (f"{item.set_name} set  ·  {item.type}" if item.set_name else item.type,
                                            ui.TEXT_DIM)]
            active = not equipped or p.item_active(item)
            lines += [(line, (140, 230, 140) if active else (130, 130, 140)) for line in item.stat_lines()]
            if not active:
                lines.append((f"Disabled: equip a {item.set_name} weapon to use this.", (255, 150, 130)))
            elif item.type == "Weapon" and item.set_name is None:
                lines.append(("Starting weapon: set pieces are disabled while it is equipped.", (255, 190, 140)))
            if item.skills:
                lines.append(("Skills: " + ", ".join(s.name for s in item.skills), ui.TEXT))
            if item.description:
                lines.append((item.description, ui.TEXT_DIM))
            if not item.can_equip(p.char_class):
                lines.append((f"Only for {item.char_class}s.", (255, 150, 130)))
            elif equipped and item.type == "Weapon":
                lines.append(("Equip another weapon to swap.", (255, 210, 150)))
            else:
                lines.append(("Click to unequip." if equipped else "Click to equip.", (255, 210, 150)))
            ui.tooltip(screen, lines, mouse, 300)
        return show

    def draw_skills(self, screen, p):
        L = self.L
        x0 = self.right.x + L.size(50)
        ui.text_shadow(screen, f"Skills from {p.weapon.name}", L.size(28), ui.GOLD,
                       topleft=(x0, self.right.y + L.size(112)))
        y = self.right.y + L.size(166)
        for i, skill in enumerate(p.equipped_skills):
            ui.text_shadow(screen, f"[{i + 1}] {skill.name}", L.size(26), skill.color, topleft=(x0, y))
            ui.text(screen, f"{skill.energy_cost} Energy", L.size(21), ui.ENERGY, True,
                    topright=(self.right.right - L.size(50), y + 2))
            ui.text(screen, skill.summary(p), L.size(21), ui.TEXT, topleft=(x0, y + L.size(34)))
            ui.text(screen, skill.description, L.size(18), ui.TEXT_DIM, topleft=(x0, y + L.size(62)))
            y += L.size(112)
        return None
