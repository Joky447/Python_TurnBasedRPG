"""Lines up the poses of an idle sheet so the character doesn't drift sideways or bob on
the ground: every pose is placed by its body (chest to hips) and its feet.

Run from the project folder:
    python tools/align_idle.py "<sheet.png>" x1 x2 ...     (one row, cut at these x's)
    python tools/align_idle.py "<sheet.png>" grid COLS ROWS

Writes "<sheet> (aligned).png": the poses side by side in equal cells (load it with
cols=<number of poses>, rows=1).
"""
import os
import sys

import pygame


def body_anchor(f):
    """(x of the body's middle, y of the feet) in the pose's own pixels."""
    m = pygame.mask.from_surface(f, 150)
    rects = m.get_bounding_rects()
    r = rects[0].unionall(rects)
    band = range(r.top + int(r.height * 0.2), r.top + int(r.height * 0.55))     # chest to hips
    xs = sorted(x for y in band for x in range(f.get_width()) if m.get_at((x, y)))
    return xs[len(xs) // 2], r.bottom


def poses(sheet, args):
    w, h = sheet.get_size()
    if args[0] == "grid":
        cols, rows = int(args[1]), int(args[2])
        cw, ch = w // cols, h // rows
        return [sheet.subsurface((c * cw, r * ch, cw, ch)).copy() for r in range(rows) for c in range(cols)]
    cuts = [0] + [int(v) for v in args] + [w]
    return [sheet.subsurface((a, 0, b - a, h)).copy() for a, b in zip(cuts, cuts[1:])]


def main():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    pygame.display.set_mode((1, 1))
    path = sys.argv[1]
    frames = poses(pygame.image.load(path).convert_alpha(), sys.argv[2:])
    anchors = [body_anchor(f) for f in frames]
    left = max(ax for ax, _ in anchors)
    right = max(f.get_width() - ax for f, (ax, _) in zip(frames, anchors))
    up = max(by for _, by in anchors)
    margin = (left + right) // 10 + 4       # the game drops small pieces touching a cell's edge
    cell = left + right + 2 * margin
    out = pygame.Surface((cell * len(frames), up + 8), pygame.SRCALPHA)
    for k, (f, (ax, by)) in enumerate(zip(frames, anchors)):
        out.blit(f, (k * cell + margin + left - ax, up - by))
    dst = os.path.splitext(path)[0] + " (aligned).png"
    pygame.image.save(out, dst)
    print("wrote", dst, len(frames), "poses")


if __name__ == "__main__":
    main()
