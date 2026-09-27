"""Generates a hurt animation sheet for every hero idle sheet.

Run from the project folder after changing idle art:
    python tools/make_hurt_sprites.py

Each hurt sheet is 8 frames in one row, built from the idle pose: a white hit
flash, a red-tinted recoil that leans back and slides away from the enemy,
then a recovery back to the resting pose. Saved next to the idle sheet as
"hurt - <idle file name>.png".
"""
import os
import sys

import pygame

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import assets  # noqa: E402
import animation  # noqa: E402

# (lean back in degrees, slide back as a fraction of height, look)
KEYFRAMES = [
    (0, 0.01, "flash"),
    (4, 0.04, "flash_soft"),
    (8, 0.07, "red"),
    (10, 0.08, "red"),
    (8, 0.07, "red_soft"),
    (5, 0.05, None),
    (2, 0.03, None),
    (0, 0.01, None),
]


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
    """Rotates surf by angle (counter-clockwise) around pivot. Returns (image, new pivot inside image)."""
    center = pygame.math.Vector2(surf.get_width() / 2, surf.get_height() / 2)
    offset = pygame.math.Vector2(pivot) - center
    rotated = pygame.transform.rotozoom(surf, angle, 1)
    new_center = pygame.math.Vector2(rotated.get_width() / 2, rotated.get_height() / 2)
    return rotated, new_center + offset.rotate(-angle)


def make_hurt_sheet(idle_path, cols, rows):
    # Resting pose at full resolution, with its feet position
    grid = rows > 1
    base, (ox, oy) = assets.load_frames(idle_path, cols, rows, target_h=None, anchor="body-wide" if grid else "cell",
                                        clean_edges=grid, defringe=grid)[0]
    feet = (-ox, -oy)
    w, h = base.get_size()

    # The hero faces right, so recoiling means leaning back (counter-clockwise) and sliding left
    cell_w, cell_h = int(w * 1.6), int(h * 1.15)
    ground = (cell_w * 0.6, cell_h - 4)
    sheet = pygame.Surface((cell_w * len(KEYFRAMES), cell_h), pygame.SRCALPHA)
    for i, (angle, slide, look) in enumerate(KEYFRAMES):
        img, pivot = rotate_about(styled(base, look), feet, angle)
        x = i * cell_w + ground[0] - slide * h - pivot.x
        y = ground[1] - pivot.y
        sheet.blit(img, (x, y))
    return sheet


def main():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    pygame.display.set_mode((1, 1))
    done = set()
    for tiers in animation.HERO_IDLE.values():
        for idle_path, cols, rows in tiers:
            if idle_path in done or not os.path.exists(assets.path(idle_path)):
                continue
            done.add(idle_path)
            out = animation.hurt_sheet_path(idle_path)
            pygame.image.save(make_hurt_sheet(idle_path, cols, rows), assets.path(out))
            print("wrote", out)


if __name__ == "__main__":
    main()
