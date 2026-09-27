"""Frame-based sprite animation with idle / attack / hurt clips."""
import pygame

import assets


class AnimatedSprite:
    """Plays named clips (lists of frames from assets.load_frames).

    "idle" loops. Any other clip plays once and then returns to idle.
    Without an idle clip, the first frame of the first clip is shown as a still pose.
    """
    def __init__(self, clips: dict, frame_ms: dict | None = None):
        self.clips = {name: frames for name, frames in clips.items() if frames}
        self.frame_ms = {"idle": 140, "attack": 90, "hurt": 70}
        self.frame_ms.update(frame_ms or {})
        self.current = "idle"
        self.index = 0
        self.timer = 0
        self._on_done = None

    @property
    def available(self) -> bool:
        return bool(self.clips)

    @property
    def busy(self) -> bool:
        return self.current != "idle"

    def play(self, name: str, on_done=None):
        """Starts a one-shot clip. on_done() runs when it finishes (or right away if the clip is missing)."""
        if name not in self.clips:
            if on_done:
                on_done()
            return
        self.current = name
        self.index = 0
        self.timer = 0
        self._on_done = on_done

    def progress(self) -> float:
        """0.0 -> 1.0 through the current one-shot clip."""
        frames = self.clips.get(self.current, [])
        return self.index / max(1, len(frames) - 1)

    def update(self, dt: int):
        frames = self.clips.get(self.current)
        if not frames:
            return
        self.timer += dt
        step = self.frame_ms.get(self.current, 100)
        while self.timer >= step:
            self.timer -= step
            self.index += 1
            if self.index >= len(frames):
                if self.current == "idle":
                    self.index = 0
                else:
                    done, self._on_done = self._on_done, None
                    self.current, self.index = "idle", 0
                    if done:
                        done()
                    return

    def current_frame(self):
        frames = self.clips.get(self.current)
        if frames:
            return frames[self.index % len(frames)]
        if "idle" not in self.clips and self.clips:
            return next(iter(self.clips.values()))[0]
        return None

    def draw(self, screen, feet_pos, flash: bool = False):
        """Draws the current frame with the character's feet at feet_pos. Returns the drawn rect."""
        frame = self.current_frame()
        if not frame:
            return None
        surf, (ox, oy) = frame
        pos = (feet_pos[0] + ox, feet_pos[1] + oy)
        if flash:
            surf = surf.copy()
            surf.fill((120, 120, 120), special_flags=pygame.BLEND_RGB_ADD)
        screen.blit(surf, pos)
        return surf.get_rect(topleft=pos)


# ---------------------------------------------------------------------------
# Hero outfits by progress: stage N is used after clearing N floors (0 = start of the
# run, 4 = after the Floor 4 boss). Each stage lists that outfit's attack sheet
# (frame 0 is the resting pose). Stages repeat an earlier outfit until its art exists.
BS, BM, GS, GM = "character/boysword/", "character/boymage/", "character/girlsword/", "character/girlmage/"
HERO_SHEETS = {
    ("Boy", "Swordsman"): [BS + "boy sword basic all- first floor character.png",
                           BS + "boy sword basic cloth-equipped with great sword received from clear flloor 1.png",
                           BS + "boy sword fully equip-used when recieved the armor from clear floor2.png",
                           BS + "boy sword fuly equipped with helmet.png",
                           BS + "boy sword fully equipped with shield.png",
                           BS + "final form with wings attack.png"],
    ("Boy", "Sorcerist"): [BM + "boy mage basic all.png",
                           BM + "mage boy basic cloth upgraded eapon attack.png",
                           BM + "mageboyattck.png",
                           BM + "boy mage attack mask equipped.png",
                           BM + "fully equipped with aura and mask attack.png",
                           BM + "final form with scythe attack.png"],
    ("Girl", "Swordsman"): [GS + "girl sword basic ala.png",
                            GS + "girl sword greatsword attack.png",
                            GS + "girl sword armor attack (cells).png",
                            GS + "sword girl attack with mask.png",
                            GS + "fully equipped with mask and shield attack.png",
                            GS + "final form with wings attack (cells).png"],
    ("Girl", "Sorcerist"): [GM + "girlmage normal all.png",
                            GM + "girl mage upgraded weapon attack.png",
                            GM + "girlmage fuly equip.png",
                            GM + "girl mage with mask on.png",
                            GM + "girl mage full equip with mask an auraa attack.png",
                            GM + "final form with scythe attack.png"],
}
# 0 start, 1 great weapon, 2 armor, 3 helmet/mask, 4 shield/aura, 5 final form (wings / scythe)
OUTFIT_STAGES = 6


# Hand-picked frame cuts (x positions) for sheets whose poses overlap. Others use "auto".
HERO_CUTS = {
    "character/boymage/boy mage basic all.png": [245, 495, 745, 1140, 1555, 1835, 2008],
    "character/boymage/mageboyattck.png": [245, 500, 780, 1185, 1590, 1750, 1980],
    "character/girlsword/girl sword basic ala.png": [245, 495, 745, 1095, 1515, 1765, 1995],
    "character/girlmage/girlmage normal all.png": [245, 500, 745, 1105, 1560, 1812, 2000],
    "character/girlmage/girl mage upgraded weapon attack.png": [237, 495, 754, 1029, 1471, 1720, 1926],
    "character/girlmage/final form with scythe attack.png": [285, 522, 786, 1047, 1545, 1739, 1957],
    "character/girlmage/girlmage fuly equip.png": [245, 500, 745, 1090, 1520, 1770, 1990],
    # pose 6 of this sheet is only the flying orb, so it is kept together with the cast pose
    "character/boymage/mage boy basic cloth upgraded eapon attack.png": [251, 501, 752, 1120, 1796, 2013],
    "character/boymage/final form with scythe attack.png": [268, 525, 751, 1078, 1524, 1807, 1998],
    "character/girlsword/fully equipped with mask and shield attack.png": [216, 442, 692, 968, 1327, 1665, 1946],
    "character/girlmage/girl mage full equip with mask an auraa attack.png": [251, 502, 783, 1045, 1445, 1673, 1913],
}


# Outfits without a drawn idle get one generated from their resting pose
# (see tools/make_idle_sprites.py): attack sheet -> generated idle sheet.
GENERATED_IDLE_FRAMES = 8
GENERATED_IDLES = {
    BM + "boy mage basic all.png": BM + "idle animation normal all (generated).png",
    GM + "girlmage normal all.png": GM + "idle animation normal all (generated).png",
    BS + "boy sword fuly equipped with helmet.png": BS + "idle animation helmet (generated).png",
    BS + "boy sword fully equipped with shield.png": BS + "idle animation shield (generated).png",
    BS + "final form with wings attack.png": BS + "idle animation final form (generated).png",
    BM + "boy mage attack mask equipped.png": BM + "idle animation mask (generated).png",
    BM + "final form with scythe attack.png": BM + "idle animation final form (generated).png",
    GS + "final form with wings attack (cells).png": GS + "idle animation final form (generated).png",
    GM + "girl mage with mask on.png": GM + "idle animation mask (generated).png",
}


def _gen(path):
    return (path, GENERATED_IDLE_FRAMES, 1)


# Idle loop for each outfit stage: (sheet, cols, rows). cols works like in assets.load_frames;
# grid sheets (rows > 1) are lined up on the character's feet frame by frame.
HERO_IDLE = {
    ("Boy", "Swordsman"): [(BS + "idle animation boy normal all equipment.png", [214, 405, 595, 783, 967, 1151, 1342], 1),
                           (BS + "boy sword basic cloth idle.png", "auto", 1),
                           (BS + "idle animation fully equipped (calm).png", 4, 1),   # the 3 standing poses of his sheet
                           _gen(BS + "idle animation helmet (generated).png"),
                           _gen(BS + "idle animation shield (generated).png"),
                           _gen(BS + "idle animation final form (generated).png")],
    ("Boy", "Sorcerist"): [_gen(BM + "idle animation normal all (generated).png"),
                           (BM + "mage boy basic cloth upgraded weapon idle.png", "auto", 1),
                           (BM + "idle animaiton fully equipped.png", "auto", 1),
                           _gen(BM + "idle animation mask (generated).png"),
                           (BM + "mage fully equipped with mask and aura idle.png", "auto", 1),
                           _gen(BM + "idle animation final form (generated).png")],
    ("Girl", "Swordsman"): [(GS + "idle animation basic all.png", 4, 2),
                            (GS + "girl sword greatsword idle (aligned).png", 8, 1),
                            (GS + "girl sword armor idle (aligned).png", 8, 1),
                            (GS + "idle animation mask (generated).png", 4, 2),   # drawn by hand
                            (GS + "complete equippedwith mask and shield idle.png", 4, 2),
                            _gen(GS + "idle animation final form (generated).png")],
    ("Girl", "Sorcerist"): [_gen(GM + "idle animation normal all (generated).png"),
                            (GM + "girl mage upgraded weapon idle.png", [250, 521, 793, 1059, 1325, 1596, 1868], 1),
                            (GM + "idle animation mage fully equip.png", "auto", 1),
                            _gen(GM + "idle animation mask (generated).png"),
                            (GM + "girl mage aura idle (aligned).png", 8, 1),
                            (GM + "girl mage final form idle (cells).png", 7, 1)],
}
HURT_FRAMES = 8


def hurt_sheet_path(idle_path: str) -> str:
    """Where the generated hurt sheet for an idle sheet lives (see tools/make_hurt_sprites.py)."""
    folder, name = idle_path.rsplit("/", 1)
    return f"{folder}/hurt - {name}"


# Sheets with a colored halo left from a removed background: cleaned when loaded
HERO_DEFRINGE = {
    GS + "girl sword greatsword attack.png",
    GS + "girl sword armor attack (cells).png",
}

# Attack sheets drawn as a grid (cols x rows) instead of one row
HERO_GRIDS = {
    GS + "girl sword greatsword attack.png": (4, 2),
    GS + "girl sword armor attack (cells).png": (8, 1),
    GS + "final form with wings attack (cells).png": (8, 1),
}


def load_attack(sheet, height):
    """Attack frames of a hero sheet: one row (cut at HERO_CUTS or automatically), or a grid.
    Grid sheets are lined up on the lower body and cleaned of halos and neighbouring poses."""
    if sheet in HERO_GRIDS:
        cols, rows = HERO_GRIDS[sheet]
        return assets.load_frames(sheet, cols, rows, target_h=height, anchor="body-wide", clean_edges=True,
                                  defringe=True)
    return assets.load_frames(sheet, HERO_CUTS.get(sheet, "auto"), 1, target_h=height, clean_edges=True,
                              defringe=sheet in HERO_DEFRINGE)


def hero_sprite(gender: str, char_class: str, stage: int, height: int = 250) -> AnimatedSprite:
    """The hero in the outfit for `stage` (number of floors cleared)."""
    sheets = HERO_SHEETS.get((gender, char_class), [])
    if not sheets:
        return AnimatedSprite({})
    tier = max(0, min(stage, len(sheets) - 1))
    sheet = sheets[tier]
    attack = load_attack(sheet, height)
    clips = {"attack": attack, "idle": attack[:1]}   # attack frame 0 is the fallback still pose

    idles = HERO_IDLE.get((gender, char_class), [])
    if tier < len(idles):
        idle_path, cols, rows = idles[tier]
        idle = assets.load_frames(idle_path, cols, rows, target_h=height, anchor="body-wide" if rows > 1 else "cell",
                                  clean_edges=rows > 1,   # grid sheets: remove bits of neighbouring poses
                                  defringe=rows > 1)      # and any colored halo left from a removed background
        if idle:
            clips["idle"] = idle
        clips["hurt"] = assets.load_frames(hurt_sheet_path(idle_path), HURT_FRAMES, 1, target_h=height)
    _match_stance(clips)
    # short idle loops (a few hand-drawn poses) play slower, so the breathing isn't rushed
    idle_ms = 120 * max(1.0, 8 / max(1, len(clips.get("idle", [])))) ** 0.75
    return AnimatedSprite(clips, {"attack": 75, "idle": int(idle_ms), "hurt": 60})


def _match_stance(clips):
    """Shifts the idle and hurt clips sideways so the character stands on the same spot as in
    the attack's first (resting) frame; otherwise switching clips makes them jump."""
    attack = clips.get("attack")
    if not attack:
        return

    def body_x(frame):
        surf, (ox, _) = frame
        return ox + assets._body_feet(surf, surf.get_bounding_rect(20), band_frac=0.35)[0]
    target = body_x(attack[0])
    for name in ("idle", "hurt"):     # each measured on its own first frame (hurt starts from the idle pose)
        frames = clips.get(name)
        if not frames or frames[0] is attack[0]:
            continue
        dx = round(target - body_x(frames[0]))
        if abs(dx) >= 2:
            clips[name] = [(surf, (ox + dx, oy)) for surf, (ox, oy) in frames]


def enemy_sprite(spec: dict, height: int, tint=None) -> AnimatedSprite:
    """spec maps clip name -> (sheet path, cols, rows, frame count or None[, start frame[, drawn]]).

    drawn=True marks hand-drawn sheets whose frames aren't placed consistently in
    their cells: they get spill-over cleanup and per-frame feet alignment.
    drawn can also be an anchor mode name (see assets.load_frames).
    """
    clips = {}
    for clip, (sheet, cols, rows, count, *extra) in spec.items():
        start = extra[0] if extra else 0
        drawn = extra[1] if len(extra) > 1 else bool(start)
        if drawn in (True, False):
            anchor = "body" if drawn else "cell"
        else:
            anchor, drawn = drawn, False       # an explicit anchor mode, no spill-over cleanup
        clips[clip] = assets.load_frames(sheet, cols, rows, target_h=height, count=count, tint=tint,
                                         start=start, clean_edges=drawn, anchor=anchor)
    if "idle" not in clips or not clips["idle"]:
        base = clips.get("attack") or clips.get("hurt") or []
        clips["idle"] = [assets.isolate_main_shape(base[0])] if base else []
    return AnimatedSprite(clips)
