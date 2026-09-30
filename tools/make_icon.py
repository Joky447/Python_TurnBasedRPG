"""Draws the game's icon (crossed swords around a glowing spell star) and saves it as
icon.ico (for the .exe) and menu_ui/game_icon.png (for the game window).

Run from the project folder:
    python tools/make_icon.py
"""
import math
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 1024            # drawn big, then scaled down
C = S // 2

NAVY_TOP, NAVY_BOT = (28, 52, 120), (8, 16, 44)
GOLD, GOLD_LIGHT, GOLD_DARK = (240, 196, 98), (255, 236, 176), (150, 100, 36)
STEEL, STEEL_LIGHT, STEEL_DARK = (205, 214, 232), (248, 250, 255), (110, 124, 156)
SC = 1.32            # sword size
UP = -36             # where the blades cross (a bit above the middle)


def xform(points, angle, scale=SC, offset=(0, UP)):
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    return [(C + offset[0] + (x * ca - y * sa) * scale, C + offset[1] + (x * sa + y * ca) * scale) for x, y in points]


def sword(surf, angle):
    """A sword pointing up (before rotating by angle), centered so the blades cross in the middle."""
    def poly(pts, color, width=0):
        pygame.draw.polygon(surf, color, xform(pts, angle), width)

    def line(a, b, color, w):
        p = xform([a, b], angle)
        pygame.draw.line(surf, color, p[0], p[1], int(w * SC))

    off = 40
    blade = [(0, -400 + off), (34, -300 + off), (38, 70 + off), (-38, 70 + off), (-34, -300 + off)]
    poly(blade, STEEL_DARK)
    poly([(0, -388 + off), (26, -298 + off), (28, 66 + off), (0, 66 + off)], STEEL)          # lit half
    poly([(0, -388 + off), (-26, -298 + off), (-28, 66 + off), (0, 66 + off)], STEEL_LIGHT)
    line((0, -300 + off), (0, 40 + off), STEEL_DARK, 6)                                     # fuller
    # crossguard
    poly([(-112, 62 + off), (112, 62 + off), (124, 92 + off), (-124, 92 + off)], GOLD_DARK)
    poly([(-108, 66 + off), (108, 66 + off), (116, 84 + off), (-116, 84 + off)], GOLD)
    for sx in (-1, 1):
        p = xform([(sx * 124, 76 + off)], angle)[0]
        pygame.draw.circle(surf, GOLD_DARK, p, int(21 * SC))
        pygame.draw.circle(surf, GOLD_LIGHT, p, int(14 * SC))
    # grip and pommel
    poly([(-15, 92 + off), (15, 92 + off), (15, 200 + off), (-15, 200 + off)], (90, 40, 34))
    for k in range(4):
        line((-15, 112 + off + k * 26), (15, 122 + off + k * 26), (60, 24, 22), 4)
    p = xform([(0, 226 + off)], angle)[0]
    pygame.draw.circle(surf, GOLD_DARK, p, int(34 * SC))
    pygame.draw.circle(surf, GOLD, p, int(27 * SC))
    pygame.draw.circle(surf, GOLD_LIGHT, (p[0] - 8, p[1] - 9), int(9 * SC))


def glow(surf, center, radius, color, steps=26, peak=190):
    layer = pygame.Surface((S, S), pygame.SRCALPHA)
    for i in range(steps, 0, -1):
        k = i / steps
        pygame.draw.circle(layer, (*color, int(peak * (1 - k) ** 1.6 / 4)), center, int(radius * k))
    surf.blit(layer, (0, 0))


def star(surf, center, r, color, inner=0.16):
    """A four-point sparkle."""
    cx, cy = center
    pts = []
    for i in range(8):
        a = i * math.pi / 4 - math.pi / 2
        d = r if i % 2 == 0 else r * inner
        pts.append((cx + math.cos(a) * d, cy + math.sin(a) * d))
    pygame.draw.polygon(surf, color, pts)


def build():
    img = pygame.Surface((S, S), pygame.SRCALPHA)

    # rounded badge with a vertical navy gradient
    badge = pygame.Surface((S, S), pygame.SRCALPHA)
    for y in range(S):
        t = y / S
        col = tuple(int(NAVY_TOP[i] + (NAVY_BOT[i] - NAVY_TOP[i]) * t) for i in range(3))
        pygame.draw.line(badge, col, (0, y), (S, y))
    mask = pygame.Surface((S, S), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (24, 24, S - 48, S - 48), border_radius=190)
    badge.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    img.blit(badge, (0, 0))
    pygame.draw.rect(img, GOLD_DARK, (24, 24, S - 48, S - 48), 30, border_radius=190)
    pygame.draw.rect(img, GOLD, (36, 36, S - 72, S - 72), 16, border_radius=180)
    pygame.draw.rect(img, GOLD_LIGHT, (48, 48, S - 96, S - 96), 4, border_radius=170)

    # soft magical haze behind the swords
    glow(img, (C, C - 10), 430, (110, 90, 255), peak=150)

    sword(img, -42)
    sword(img, 42)

    # spell star where the blades cross
    mid = (C, C + UP)
    glow(img, mid, 230, (160, 130, 255), peak=255)
    glow(img, mid, 120, (235, 225, 255), peak=255)
    star(img, mid, 175, (190, 160, 255), inner=0.2)
    star(img, mid, 140, (255, 255, 255), inner=0.17)
    pygame.draw.circle(img, (255, 255, 255), mid, 30)
    for (x, y, r) in [(C - 300, C - 290, 30), (C + 300, C - 250, 24), (C + 275, C + 250, 22), (C - 290, C + 270, 20)]:
        star(img, (x, y), r * 1.8, (255, 240, 200), inner=0.2)
    return img


def main():
    pygame.init()
    big = build()
    png_path = os.path.join(ROOT, "menu_ui", "game_icon.png")
    ico_path = os.path.join(ROOT, "icon.ico")
    pygame.image.save(pygame.transform.smoothscale(big, (256, 256)), png_path)
    raw = pygame.image.tobytes(big, "RGBA")
    pil = Image.frombytes("RGBA", (S, S), raw)
    pil.save(ico_path, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    pil.resize((512, 512), Image.LANCZOS).save(os.path.join(ROOT, "icon_preview.png"))
    print("wrote", ico_path, "and", png_path)


if __name__ == "__main__":
    main()
