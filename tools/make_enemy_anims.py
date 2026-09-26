"""Generates idle and hurt animations for enemies that have a drawn attack sheet.

Run from the project folder after adding or changing an enemy's attack sheet:
    python tools/make_enemy_anims.py            # all enemies with a sheet
    python tools/make_enemy_anims.py "ignis"    # only names containing "ignis"

Uses the rest frame set in mobs_boss/enemy_library.py (sheet=(file, rest frame)).
Writes two 8-frame sheets next to the attack sheet:
  "<sheet name> idle.png"  breathing loop with a pulsing glow on fire/ice/magic
  "<sheet name> hurt.png"  white flash, red recoil away from the hero, recovery
"""
import math
import os
import sys

import pygame

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import assets  # noqa: E402
from mobs_boss.enemy_library import GENERATED_FRAMES, TEMPLATES, generated_path, sheet_layout  # noqa: E402

BREATH = 0.018      # how far the head sinks, as a fraction of height
SWAY = 0.004        # sideways sway of the head, as a fraction of height
STRIP = 2           # px per horizontal slice when bending the sprite

# Hurt keyframes: (lean back in degrees, slide back as a fraction of height, look)
HURT_KEYS = [(0, 0.01, "flash"), (4, 0.04, "flash_soft"), (8, 0.07, "red"), (10, 0.08, "red"),
             (8, 0.07, "red_soft"), (5, 0.05, None), (2, 0.03, None), (0, 0.01, None)]


def rest_pose(path, rest, cols, rows):
    """The calm frame at full resolution, cleaned of bits of neighbouring frames. Returns (surface, feet).

    Uses the same feet alignment as the attack animation, and trims anything
    below the feet, so idle, attack and hurt all stand on the same spot.
    """
    surf, (ox, oy) = assets.load_frames(path, cols, rows, target_h=None, start=rest, clean_edges=True,
                                        anchor="body")[0]
    cleaned = assets._drop_edge_slivers(surf.copy())
    feet = (-ox, -oy)
    trimmed = cleaned.subsurface((0, 0, cleaned.get_width(), max(1, min(cleaned.get_height(), feet[1])))).copy()
    return trimmed, feet


def glow_layer(base):
    """Copy of the bright, strongly coloured pixels (flames, ice, magic) used for the pulse."""
    glow = pygame.Surface(base.get_size(), pygame.SRCALPHA)
    src = pygame.PixelArray(base)
    dst = pygame.PixelArray(glow)
    w, h = base.get_size()
    for x in range(w):
        for y in range(h):
            c = base.unmap_rgb(src[x, y])
            hi, lo = max(c.r, c.g, c.b), min(c.r, c.g, c.b)
            if c.a > 60 and hi > 170 and hi - lo > 90:
                dst[x, y] = (c.r, c.g, c.b, 255)
    del src, dst
    return glow


def breathe(base, t):
    """Bends the pose: rows near the head move the most, rows at the feet don't move."""
    w, h = base.get_size()
    out = pygame.Surface((w, h), pygame.SRCALPHA)
    sink = BREATH * h * t
    sway = SWAY * h * math.sin(t * math.pi)
    for y in range(0, h, STRIP):
        weight = (1 - y / h) ** 1.5
        out.blit(base, (-sway * weight, y + sink * weight), (0, y, w, STRIP + 1))
    return out


def idle_sheet(base, glow):
    w, h = base.get_size()
    pad = int(h * 0.05)
    cell_w, cell_h = w + 20, h + pad
    sheet = pygame.Surface((cell_w * GENERATED_FRAMES, cell_h), pygame.SRCALPHA)
    for i in range(GENERATED_FRAMES):
        t = (1 - math.cos(2 * math.pi * i / GENERATED_FRAMES)) / 2
        frame = breathe(base, t)
        pulse = breathe(glow, t)
        k = int(90 * t)
        pulse.fill((k, k, k), special_flags=pygame.BLEND_RGB_MULT)
        frame.blit(pulse, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        sheet.blit(frame, (i * cell_w + 10, pad))
    return sheet


def styled(surf, look):
    surf = surf.copy()
    if look == "flash":
        surf.fill((200, 200, 200), special_flags=pygame.BLEND_RGB_ADD)
    elif look == "flash_soft":
        surf.fill((90, 90, 90), special_flags=pygame.BLEND_RGB_ADD)
    elif look == "red":
        surf.fill((255, 150, 150), special_flags=pygame.BLEND_RGB_MULT)
        surf.fill((45, 0, 0), special_flags=pygame.BLEND_RGB_ADD)
    elif look == "red_soft":
        surf.fill((255, 205, 205), special_flags=pygame.BLEND_RGB_MULT)
    return surf


def rotate_about(surf, pivot, angle):
    center = pygame.math.Vector2(surf.get_width() / 2, surf.get_height() / 2)
    offset = pygame.math.Vector2(pivot) - center
    rotated = pygame.transform.rotozoom(surf, angle, 1)
    new_center = pygame.math.Vector2(rotated.get_width() / 2, rotated.get_height() / 2)
    return rotated, new_center + offset.rotate(-angle)


def hurt_sheet(base, feet):
    """Enemies face left, so a hit knocks them back to the right (clockwise lean)."""
    w, h = base.get_size()
    cell_w, cell_h = int(w * 1.6), int(h * 1.15)
    ground = (cell_w * 0.4, cell_h - 4)
    sheet = pygame.Surface((cell_w * len(HURT_KEYS), cell_h), pygame.SRCALPHA)
    for i, (angle, slide, look) in enumerate(HURT_KEYS):
        img, pivot = rotate_about(styled(base, look), feet, -angle)
        sheet.blit(img, (i * cell_w + ground[0] + slide * h - pivot.x, ground[1] - pivot.y))
    return sheet


def main():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    pygame.display.set_mode((1, 1))
    only = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    for name, t in TEMPLATES.items():
        sheet = t.get("sheet")
        if not sheet or (only and only not in name.lower()):
            continue
        path, rest, cols, rows = sheet_layout(sheet)
        if not os.path.exists(assets.path(path)):
            print("missing", path)
            continue
        base, feet = rest_pose(path, rest, cols, rows)
        pygame.image.save(idle_sheet(base, glow_layer(base)), assets.path(generated_path(path, "idle")))
        pygame.image.save(hurt_sheet(base, feet), assets.path(generated_path(path, "hurt")))
        print("wrote idle + hurt for", name)


if __name__ == "__main__":
    main()
