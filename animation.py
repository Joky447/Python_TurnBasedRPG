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
# Hero sheets: one row of unevenly spaced poses, frame 0 = idle pose. Outfit improves with weapon tier.
HERO_SHEETS = {
    ("Boy", "Swordsman"): ["character/boysword/boy sowrd basic cloth.png",
                           "character/boysword/boy sword basic all.png",
                           "character/boysword/boy sword fully equip.png"],
    ("Boy", "Sorcerist"): ["character/boymage/mage boy basic cloth.png",
                           "character/boymage/boy mage basic all.png",
                           "character/boymage/mageboyattck.png"],
    ("Girl", "Swordsman"): ["character/girlsword/girl sword basic ala.png",
                            "character/girlsword/girl sword fully equips no aura.png",
                            "character/girlsword/girl sword fully equip.png"],
    ("Girl", "Sorcerist"): ["character/girlmage/girl mage normal cloth.png",
                            "character/girlmage/girlmage normal all.png",
                            "character/girlmage/girlmage fuly equip.png"],
}


# Hand-picked frame cuts (x positions) for sheets whose poses overlap. Others use "auto".
HERO_CUTS = {
    "character/boymage/mage boy basic cloth.png": [245, 490, 745, 1195, 1565, 1800, 2012],
    "character/boymage/boy mage basic all.png": [245, 495, 745, 1140, 1555, 1835, 2008],
    "character/boymage/mageboyattck.png": [245, 500, 780, 1185, 1590, 1750, 1980],
    "character/girlsword/girl sword basic ala.png": [245, 495, 745, 1095, 1515, 1765, 1995],
    "character/girlsword/girl sword fully equip.png": [250, 500, 745, 1015, 1510, 1760, 2000],
    "character/girlmage/girl mage normal cloth.png": [245, 495, 745, 1128, 1545, 1811, 1993],
    "character/girlmage/girlmage normal all.png": [245, 500, 745, 1105, 1560, 1812, 2000],
    "character/girlmage/girlmage fuly equip.png": [245, 500, 745, 1090, 1520, 1770, 1990],
}


def hero_sprite(gender: str, char_class: str, tier: int, height: int = 250) -> AnimatedSprite:
    sheets = HERO_SHEETS.get((gender, char_class), [])
    if not sheets:
        return AnimatedSprite({})
    sheet = sheets[max(0, min(tier, len(sheets) - 1))]
    frames = assets.load_frames(sheet, HERO_CUTS.get(sheet, "auto"), 1, target_h=height)
    # The sheet is an attack; its first frame doubles as the idle pose.
    return AnimatedSprite({"idle": frames[:1], "attack": frames}, {"attack": 75})


def enemy_sprite(spec: dict, height: int, tint=None) -> AnimatedSprite:
    """spec maps clip name -> (sheet path, cols, rows, frame count or None)."""
    clips = {}
    for clip, (sheet, cols, rows, count) in spec.items():
        clips[clip] = assets.load_frames(sheet, cols, rows, target_h=height, count=count, tint=tint)
    if "idle" not in clips or not clips["idle"]:
        base = clips.get("attack") or clips.get("hurt") or []
        clips["idle"] = [assets.isolate_main_shape(base[0])] if base else []
    return AnimatedSprite(clips)
