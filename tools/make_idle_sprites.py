"""Generates idle animation sheets for hero outfits that only have an attack sheet.

Run from the project folder:
    python tools/make_idle_sprites.py

The idle is built from the attack sheet's first (resting) pose: 8 frames of a
gentle breathing motion (the upper body rises and sinks while the feet stay
planted, with a slight sway) and a soft pulse on bright magic glows such as a
staff orb. Which sheets get one is set in animation.GENERATED_IDLES.
"""
import math
import os
import sys

import pygame

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import assets  # noqa: E402
import animation  # noqa: E402

FRAMES = animation.GENERATED_IDLE_FRAMES
BREATH = 0.02       # how far the head sinks, as a fraction of the character's height
SWAY = 0.004        # sideways sway of the head, as a fraction of height
STRIP = 2           # px per horizontal slice when bending the sprite


def breathe(base, t):
    """Bends the pose: rows near the head move the most, rows at the feet don't move."""
    w, h = base.get_size()
    out = pygame.Surface((w, h), pygame.SRCALPHA)
    sink = BREATH * h * t
    sway = SWAY * h * math.sin(t * math.pi)
    for y in range(0, h, STRIP):
        weight = (1 - y / h) ** 1.5          # 1 at the head, 0 at the feet
        dy = sink * weight
        dx = sway * weight
        out.blit(base, (dx, y + dy), (0, y, w, STRIP + 1))
    return out


def glow_pulse(surf, strength):
    """Brightens bright, strongly blue pixels (magic glow) by `strength` (0..1)."""
    if strength <= 0:
        return surf
    surf = surf.copy()
    px = pygame.PixelArray(surf)
    w, h = surf.get_size()
    boost = int(70 * strength)
    for x in range(w):
        for y in range(h):
            c = surf.unmap_rgb(px[x, y])
            if c.a > 40 and c.b > 150 and c.b > c.r + 50:
                px[x, y] = (min(255, c.r + boost // 2), min(255, c.g + boost), min(255, c.b + boost), c.a)
    del px
    return surf


def make_idle_sheet(attack_path):
    base, (ox, oy) = animation.load_attack(attack_path, None)[0]
    feet_x = -ox
    w, h = base.get_size()

    # Every cell has the feet at the same spot so the grid loader keeps it steady
    pad_top = int(h * 0.05)
    cell_w, cell_h = w + 20, h + pad_top
    sheet = pygame.Surface((cell_w * FRAMES, cell_h), pygame.SRCALPHA)
    for i in range(FRAMES):
        t = (1 - math.cos(2 * math.pi * i / FRAMES)) / 2      # 0 -> 1 -> 0 over the loop
        frame = glow_pulse(breathe(base, t), t)
        sheet.blit(frame, (i * cell_w + 10, pad_top))
    return sheet, feet_x


def main():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    pygame.display.set_mode((1, 1))
    for attack_path, out_path in animation.GENERATED_IDLES.items():
        if not os.path.exists(assets.path(attack_path)):
            continue
        sheet, _ = make_idle_sheet(attack_path)
        pygame.image.save(sheet, assets.path(out_path))
        print("wrote", out_path)


if __name__ == "__main__":
    main()
