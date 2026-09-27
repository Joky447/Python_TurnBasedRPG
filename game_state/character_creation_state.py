import pygame

import animation
import assets
import ui
from character.player import Player
from game_state.lobby_state import body_center_x
from game_state.state import GameState
from game_state.ui_layouts import CAMP, CREATE, ArtLayout
from inventory_mechanics.weapon_library import STARTING_WEAPONS, get_weapon

GEN = "menu_ui/generated/"

MAX_NAME_LENGTH = 14

# Suggested names, used when the name box is left empty
DEFAULT_NAMES = {("Boy", "Swordsman"): "Aldric", ("Girl", "Swordsman"): "Seraphine",
                 ("Boy", "Sorcerist"): "Kael", ("Girl", "Sorcerist"): "Lyra"}

CLASS_BLURBS = {
    "Swordsman": "Sturdy melee fighter. Strong blocks and heavy hits.",
    "Sorcerist": "Fragile spellcaster. Burns, curses and big spells.",
}


class CharacterCreationState(GameState):
    def __init__(self, game_manager):
        super().__init__(game_manager)
        w, h = game_manager.screen.get_size()
        self.bg = assets.load_background("map/bcgpc.png", (w, h))

        # Selection state
        self.selected_gender = "Boy"
        self.selected_class = "Swordsman"

        self.name = ""

        # The Create Character mockup (menu_ui/character selection ui.png) with its sample
        # content erased by tools/make_ui_templates.py; live content goes in the same spots.
        L = self.L = ArtLayout(CREATE, (w, h))
        self.art = assets.load_part(GEN + "create.png", (w, h))
        self.name_box = L.rect((300, 618, 700, 670))
        self.btn_boy = L.rect(CREATE["btn_boy"])
        self.btn_girl = L.rect(CREATE["btn_girl"])
        self.btn_swordsman = L.rect(CREATE["btn_sword"])
        self.btn_sorcerist = L.rect(CREATE["btn_sorc"])
        self.btn_confirm = L.rect(CREATE["confirm"])
        self.preview_panel = L.rect(CREATE["preview_stage"])
        # Back button, in the Base Camp's "Main Menu" button style and spot
        self.btn_back = ArtLayout(CAMP, (w, h)).rect(CAMP["menu_btn"])
        self.preview = None

    def enter(self, **kwargs):
        assets.play_music("title")
        self.name = ""
        pygame.key.start_text_input()
        self.refresh_preview()

    def exit(self):
        pygame.key.stop_text_input()

    @property
    def suggested_name(self) -> str:
        return DEFAULT_NAMES[(self.selected_gender, self.selected_class)]

    def refresh_preview(self):
        self.preview = animation.hero_sprite(self.selected_gender, self.selected_class, 0, height=self.L.size(330))
        self.preview_timer = 0
        # stand the body (not the weapon) on the middle of the pedestal
        rest = self.preview.clips.get("idle", [None])[0]
        self.preview_shift = rest[1][0] + body_center_x(rest[0]) if rest else 0

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if self.btn_boy.collidepoint(pos):
                    self.select(gender="Boy")
                elif self.btn_girl.collidepoint(pos):
                    self.select(gender="Girl")
                elif self.btn_swordsman.collidepoint(pos):
                    self.select(char_class="Swordsman")
                elif self.btn_sorcerist.collidepoint(pos):
                    self.select(char_class="Sorcerist")
                elif self.btn_confirm.collidepoint(pos):
                    self.confirm()
                    return
                elif self.btn_back.collidepoint(pos):
                    self.go_back()
                    return
            elif event.type == pygame.TEXTINPUT:
                # Letters, digits, spaces and a few name characters
                for ch in event.text:
                    if (ch.isalnum() or ch in " '-") and len(self.name) < MAX_NAME_LENGTH:
                        if not (ch == " " and (not self.name or self.name.endswith(" "))):
                            self.name += ch
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.name = self.name[:-1]
                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    self.select(gender="Girl" if self.selected_gender == "Boy" else "Boy")
                elif event.key in (pygame.K_UP, pygame.K_DOWN):
                    self.select(char_class="Sorcerist" if self.selected_class == "Swordsman" else "Swordsman")
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.confirm()
                    return
                elif event.key == pygame.K_ESCAPE:
                    self.go_back()
                    return

    def go_back(self):
        """Leaves without making a character: back to Base Camp, or the main menu if the roster is empty."""
        self.game_manager.change_state("LobbyState" if self.game_manager.roster else "MainMenuState")

    def select(self, gender=None, char_class=None):
        self.selected_gender = gender or self.selected_gender
        self.selected_class = char_class or self.selected_class
        self.refresh_preview()

    def confirm(self):
        self.create_character()
        self.game_manager.change_state("LobbyState")

    def create_character(self):
        """Adds the new character to the Base Camp roster and makes them the active one."""
        gm = self.game_manager
        name = self.name.strip() or self.suggested_name
        if any(p.name == name for p in gm.roster):
            name += " II"
        weapon = get_weapon(STARTING_WEAPONS[self.selected_class], self.selected_gender)
        gm.add_character(Player(name=name, gender=self.selected_gender, char_class=self.selected_class, weapon=weapon))
        gm.new_run()

    @staticmethod
    def edge_fade(size, width=70):
        """Alpha mask that fades the right edge of the preview area, so big attack effects
        trail off softly before the text instead of being cut straight."""
        mask = pygame.Surface(size, pygame.SRCALPHA)
        mask.fill((255, 255, 255, 255))
        for i in range(width):
            x = size[0] - width + i
            pygame.draw.line(mask, (255, 255, 255, int(255 * (1 - i / width))), (x, 0), (x, size[1]))
        return mask

    def update(self):
        # Show off the attack animation every few seconds
        self.preview.update(self.game_manager.dt)
        self.preview_timer += self.game_manager.dt
        if self.preview_timer > 2500 and not self.preview.busy:
            self.preview_timer = 0
            self.preview.play("attack")

    def part(self, screen, name, rect):
        img = assets.load_part(GEN + name, rect.size)
        if img:
            screen.blit(img, rect.topleft)

    def hover_glow(self, screen, rect):
        glow = pygame.Surface(rect.size)
        pygame.draw.rect(glow, (24, 24, 16), glow.get_rect().inflate(-14, -14), border_radius=10)
        screen.blit(glow, rect.topleft, special_flags=pygame.BLEND_RGB_ADD)

    def choice(self, screen, rect, on, template_on, template_off, icon, icon_rect, label, mouse):
        """A Boy/Girl/Swordsman/Sorcerist button: lit blue when chosen, dark otherwise."""
        self.part(screen, template_on if on else template_off, rect)
        if not on and rect.collidepoint(mouse):
            self.hover_glow(screen, rect)
        img = assets.load_icon(GEN + icon, icon_rect.size)
        if img:
            if not on:
                img = img.copy()
                img.fill((170, 180, 210), special_flags=pygame.BLEND_RGB_MULT)
            screen.blit(img, img.get_rect(center=icon_rect.center))
        area = pygame.Rect(icon_rect.right, rect.y, rect.right - icon_rect.right - self.L.size(30), rect.height)
        ui.text_shadow(screen, label, self.L.size(28), ui.TEXT if on else (200, 205, 225), bold=on, center=area.center)

    def draw(self, screen):
        if not self.art:
            screen.fill(ui.BG)
            return
        L = self.L
        mouse = pygame.mouse.get_pos()
        if not getattr(self, "_backdrop", None):
            # the art over the night background (it shows through the see-through panels),
            # combined once into one opaque image so each frame is a single fast copy
            self._backdrop = pygame.Surface(self.art.get_size()).convert()
            if self.bg:
                self._backdrop.blit(self.bg, (0, 0))
            self._backdrop.blit(self.art, (0, 0))
        screen.blit(self._backdrop, (0, 0))

        boy, sword = self.selected_gender == "Boy", self.selected_class == "Swordsman"
        self.choice(screen, self.btn_boy, boy, "create_btn_on.png", "create_btn_off.png", "icon_male.png",
                    L.rect(CREATE["icon_male"]).move(self.btn_boy.x - L.rect(CREATE["btn_boy"]).x, 0), "Boy", mouse)
        self.choice(screen, self.btn_girl, not boy, "create_btn_on.png", "create_btn_off.png", "icon_female.png",
                    L.rect(CREATE["icon_female"]), "Girl", mouse)
        self.choice(screen, self.btn_swordsman, sword, "create_btn_on_2.png", "create_btn_off_2.png", "icon_sword.png",
                    L.rect(CREATE["icon_sword"]), "Swordsman", mouse)
        self.choice(screen, self.btn_sorcerist, not sword, "create_btn_on_2.png", "create_btn_off_2.png",
                    "icon_staff.png", L.rect(CREATE["icon_staff"]), "Sorcerist", mouse)

        # Name box, where the class description sat in the mockup
        ui.text_shadow(screen, "Name", L.size(28), ui.GOLD, midleft=(L.point((196, 0))[0], self.name_box.centery))
        box = pygame.Surface(self.name_box.size, pygame.SRCALPHA)
        box.fill((4, 10, 30, 200))
        screen.blit(box, self.name_box.topleft)
        pygame.draw.rect(screen, ui.GOLD, self.name_box, 1)
        tx = self.name_box.x + L.size(16)
        if self.name:
            r = ui.text(screen, self.name, L.size(28), ui.TEXT, True, midleft=(tx, self.name_box.centery))
            cursor_x = r.right + 2
        else:
            ui.text(screen, self.suggested_name, L.size(28), (110, 120, 150), True, midleft=(tx, self.name_box.centery))
            cursor_x = tx
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            pygame.draw.line(screen, ui.GOLD_LIGHT, (cursor_x, self.name_box.y + 8), (cursor_x, self.name_box.bottom - 8), 2)
        ui.text(screen, f"Type a name  ·  {len(self.name)}/{MAX_NAME_LENGTH}", L.size(17), ui.TEXT_DIM,
                topright=(self.name_box.right, self.name_box.bottom + 3))

        # Character on the pedestal (the attack fades out before the weapon panel)
        stage = self.preview_panel
        fx, fy = L.point(CREATE["preview_feet"])
        fx -= self.preview_shift
        layer = pygame.Surface(stage.size, pygame.SRCALPHA)
        self.preview.draw(layer, (fx - stage.x, fy - stage.y))
        layer.blit(self.edge_fade(stage.size), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(layer, stage.topleft)

        # Starting weapon and its skills
        weapon = get_weapon(STARTING_WEAPONS[self.selected_class], self.selected_gender)
        ui.item_icon(screen, weapon, L.rect(CREATE["weapon_icon"]))
        wx, wy = L.point(CREATE["weapon_text"])
        ui.text_shadow(screen, weapon.name, L.size(38), ui.GOLD, topleft=(wx, wy))
        ui.text(screen, ", ".join(weapon.stat_lines()), L.size(23), ui.TEXT, topleft=(wx, wy + L.size(48)))
        for skill, gem, pos in zip(weapon.skills, CREATE["skill_gems"], CREATE["skill_text"]):
            gx, gy = L.point(gem)
            r = L.size(9)
            pygame.draw.polygon(screen, skill.color, [(gx, gy - r), (gx + r, gy), (gx, gy + r), (gx - r, gy)])
            pygame.draw.polygon(screen, ui.GOLD_LIGHT, [(gx, gy - r), (gx + r, gy), (gx, gy + r), (gx - r, gy)], 1)
            sx, sy = L.point(pos)
            ui.text_shadow(screen, f"{skill.name} ({skill.energy_cost})", L.size(27), ui.GOLD_LIGHT, topleft=(sx, sy))
            summary, size = skill.summary(), L.size(21)
            max_w = L.point((1578, 0))[0] - sx
            while assets.font(size).size(summary)[0] > max_w and size > 11:
                size -= 1
            ui.text(screen, summary, size, ui.TEXT, topleft=(sx, sy + L.size(36)))

        if self.btn_confirm.collidepoint(mouse):
            self.hover_glow(screen, self.btn_confirm)

        self.part(screen, "camp_back_btn.png", self.btn_back)
        if self.btn_back.collidepoint(mouse):
            self.hover_glow(screen, self.btn_back)
        back = "< Base Camp  [Esc]" if self.game_manager.roster else "< Main Menu  [Esc]"
        ui.text_shadow(screen, back, L.size(24), ui.TEXT, center=self.btn_back.center)
