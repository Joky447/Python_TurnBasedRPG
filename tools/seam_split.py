"""Re-lays a one-row sprite sheet whose poses overlap sideways (a blade or aura of one pose
reaching past where the next one starts), so the game can slice it into equal cells.

Run from the project folder:
    python tools/seam_split.py "<sheet.png>" x1 x2 ... (rough frame borders)

Between each pair of poses a curved cut is found from top to bottom that crosses as
little art as possible (seam carving: each row's cut may shift a few px from the row above),
within WINDOW px of the rough border. A separate piece the cut runs through (a blade tip)
goes whole to the pose that holds most of it. Each pose is then copied into its own equal-width cell,
at the same height. Writes "<sheet> (cells).png"; load it with cols=<number of frames>.
"""
import os
import sys

import pygame

WINDOW = (-60, 90)   # how far left/right of the rough border the cut may run
STEP = 2             # max px the cut moves sideways per row


def seam(alpha, w, h, border):
    lo, hi = max(0, border + WINDOW[0]), min(w - 1, border + WINDOW[1])
    xs = range(lo, hi + 1)
    INF = float("inf")
    cost = {x: alpha[0][x] for x in xs}
    back = []
    for y in range(1, h):
        new, prev = {}, {}
        for x in xs:
            best = min((cost[p], p) for p in range(max(lo, x - STEP), min(hi, x + STEP) + 1))
            # a small pull toward the rough border keeps the cut from wandering in empty space
            new[x] = best[0] + alpha[y][x] + abs(x - border) * 0.002
            prev[x] = best[1]
        back.append(prev)
        cost = new
    x = min(xs, key=lambda k: cost[k])
    path = [x]
    for prev in reversed(back):
        x = prev[x]
        path.append(x)
    return list(reversed(path))       # cut x for each row


def main():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    pygame.display.set_mode((1, 1))
    path, borders = sys.argv[1], [int(v) for v in sys.argv[2:]]
    sheet = pygame.image.load(path).convert_alpha()
    w, h = sheet.get_size()
    alpha = [[sheet.get_at((x, y)).a for x in range(w)] for y in range(h)]
    seams = [[0] * h] + [seam(alpha, w, h, b) for b in borders] + [[w] * h]
    n = len(seams) - 1

    def side(x, y):
        return next(k for k in range(n) if x < seams[k + 1][y])

    # a separate piece of art the cut runs through (a blade tip) goes whole to the pose
    # that holds most of it, instead of being sliced
    owner = {}
    for comp in pygame.mask.from_surface(sheet, 20).connected_components():
        box = comp.get_bounding_rects()[0]
        if not any(box.left < seams[k][y] < box.right for k in range(1, n) for y in range(box.top, box.bottom)):
            continue
        votes = [0] * n
        pts = [(x, y) for y in range(box.top, box.bottom) for x in range(box.left, box.right) if comp.get_at((x, y))]
        for x, y in pts:
            votes[side(x, y)] += 1
        k = max(range(n), key=lambda i: votes[i])
        if votes[k] > len(pts) * 0.6:           # clearly one pose's piece
            for p in pts:
                owner[p] = k

    frames = [pygame.Surface((w, h), pygame.SRCALPHA) for _ in range(n)]
    for y in range(h):
        for k in range(n):
            x0, x1 = seams[k][y], seams[k + 1][y]
            if x1 > x0:
                frames[k].blit(sheet, (x0, y), (x0, y, x1 - x0, 1))
    for (x, y), k in owner.items():
        c = sheet.get_at((x, y))
        for i in range(n):
            frames[i].set_at((x, y), c if i == k else (0, 0, 0, 0))
    def columns(f):      # crop sideways only, so every pose keeps its height on the sheet
        r = f.get_bounding_rect(1)
        return f.subsurface((r.x, 0, r.width, h)).copy()
    frames = [columns(f) for f in frames]
    # Every pose stands with its feet in the middle of its cell, so the animation doesn't
    # slide sideways (the game lines these frames up by their cells)
    def feet_x(f):
        m = pygame.mask.from_surface(f, 150)
        r = m.get_bounding_rects()[0]
        band = range(r.bottom - max(4, r.height // 16), r.bottom)
        xs = sorted(x for y in band for x in range(f.get_width()) if m.get_at((x, y)))
        return xs[len(xs) // 2]
    feet = [feet_x(f) for f in frames]
    half = max(max(fx, f.get_width() - fx) for f, fx in zip(frames, feet))
    # wide margins: the game drops small pieces touching a cell's edge as bits of a neighbour
    margin = half // 5 + 4
    cell = 2 * (half + margin)
    out = pygame.Surface((cell * len(frames), h), pygame.SRCALPHA)
    for k, (f, fx) in enumerate(zip(frames, feet)):
        out.blit(f, (k * cell + cell // 2 - fx, 0))
    dst = os.path.splitext(path)[0] + " (cells).png"
    pygame.image.save(out, dst)
    print("wrote", dst, len(frames), "frames")


if __name__ == "__main__":
    main()
