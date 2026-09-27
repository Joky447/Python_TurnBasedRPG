"""Turns the Base Camp and Create Character mockups in menu_ui/ into live UI templates.

Run from the project folder after changing a mockup:
    python tools/make_ui_templates.py

The mockups show sample content (Seraphine, the Iron Sword, one selected tab...).
This tool erases everything that changes during play by blending the colors on
either side of each area across it, and saves:
  menu_ui/generated/<screen>.png        the screen with the changing parts erased
  menu_ui/generated/<part>.png          blank buttons/tabs in each state, cut from the mockup
  menu_ui/generated/icon_<name>.png     icons cut out of the mockup (gender, class)
  items/Iron Sword.png, items/Novice Staff.png   weapon art cut from the mockup buttons
The coordinates below are in the mockup's own pixels; game_state/ui_layouts.py uses the same numbers.
"""
import os
import sys

import pygame

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from game_state.ui_layouts import CAMP, CREATE  # noqa: E402

OUT = os.path.join(ROOT, "menu_ui", "generated")


def _avg(surf, x, y, n=3):
    w, h = surf.get_size()
    cols = [surf.get_at((min(w - 1, max(0, x + k)), y)) for k in range(-n, n + 1)]
    return [sum(c[i] for c in cols) / len(cols) for i in range(3)]


def _blur(vals, smooth):
    out = []
    for i in range(len(vals)):
        win = vals[max(0, i - smooth):i + smooth + 1]
        out.append([sum(v[c] for v in win) / len(win) for c in range(3)])
    return out


def _median(colors):
    if not colors:
        return [0, 0, 0]
    out = []
    for k in range(3):
        vals = sorted(c[k] for c in colors)
        out.append(vals[len(vals) // 2])
    return out


def _side_color(surf, rect, side, gap=4, depth=14, plain=False):
    """Median color of a strip just outside one side of rect. The median ignores text,
    gold lines and small details, so it gives the plain panel color there."""
    x0, y0, x1, y1 = rect
    w, h = surf.get_size()
    pts = []
    if side in ("top", "bottom"):
        ys = range(y0 - gap - depth, y0 - gap) if side == "top" else range(y1 + gap, y1 + gap + depth)
        pts = [(x, y) for y in ys for x in range(x0, x1, 3)]
    else:
        xs = range(x0 - gap - depth, x0 - gap) if side == "left" else range(x1 + gap, x1 + gap + depth)
        pts = [(x, y) for x in xs for y in range(y0, y1, 3)]
    colors = [surf.get_at((min(w - 1, max(0, x)), min(h - 1, max(0, y)))) for x, y in pts]
    # Keep only the navy panel tones: gold trim, foliage and wood (red/green above blue) are left out
    navy = [c for c in colors if c.b >= c.r + 8 and c.b >= c.g and c.r + c.g + c.b < 330]
    return _median(navy if not plain and len(navy) >= len(colors) // 5 else colors)


def _row_fill(surf, rect, depth=8):
    """Fills each row with the median color just left of the area, so a button's vertical
    gradient continues through it with no seam; blends into the right side over the last 20%."""
    x0, y0, x1, y1 = rect
    rows = []
    for y in range(y0, y1):
        lc = _median([surf.get_at((x, y)) for x in range(x0 - depth - 2, x0 - 2)])
        rc = _median([surf.get_at((x, y)) for x in range(x1 + 2, x1 + depth + 2)])
        # use whichever side is plain button color (bluest), not an icon or trim next to the label
        rows.append(max((lc, rc), key=lambda c: c[2] - max(c[0], c[1])))
    rows = _blur(rows, 3)
    W = x1 - x0
    for j, y in enumerate(range(y0, y1)):
        for x in range(x0, x1):
            surf.set_at((x, y), [int(v) for v in rows[j]])


def inpaint(surf, rect, feather=10, plain=False):
    """Erases rect with a clean fill of the surrounding panel color.

    The plain color on each side is found with a median (so text, lines and icons next to
    the area don't bleed in), blended smoothly across the area, and faded out over
    `feather` px beyond the edges so no box outline shows. Numbers after the first four
    are (x0, y0, x1, y1[, feather]).
    """
    x0, y0, x1, y1 = rect[:4]
    if len(rect) > 4 and rect[4] == "row":
        _row_fill(surf, (x0, y0, x1, y1))
        return
    if len(rect) > 4:
        feather = rect[4]
    w, h = surf.get_size()
    x0, x1, y0, y1 = max(0, x0), min(w, x1), max(0, y0), min(h, y1)
    W, H = x1 - x0, y1 - y0
    if W < 2 or H < 2:
        return
    box = (x0, y0, x1, y1)
    top, bottom = _side_color(surf, box, "top", plain=plain), _side_color(surf, box, "bottom", plain=plain)
    left, right = _side_color(surf, box, "left", plain=plain), _side_color(surf, box, "right", plain=plain)

    def fill_at(u, v):
        # smooth mix: vertical gradient from top to bottom, nudged toward the side colors near the sides
        vert = [top[k] + (bottom[k] - top[k]) * v for k in range(3)]
        side = [left[k] + (right[k] - left[k]) * u for k in range(3)]
        wside = 0.2 * (1 - min(1.0, 4 * min(u, 1 - u)))        # only near the left/right edges
        return [vert[k] * (1 - wside) + side[k] * wside for k in range(3)]

    ex0, ey0 = max(0, x0 - feather), max(0, y0 - feather)
    ex1, ey1 = min(w, x1 + feather), min(h, y1 + feather)
    for y in range(ey0, ey1):
        v = min(1.0, max(0.0, (y - y0) / max(1, H - 1)))
        for x in range(ex0, ex1):
            u = min(1.0, max(0.0, (x - x0) / max(1, W - 1)))
            dx = max(x0 - x, 0, x - (x1 - 1))
            dy = max(y0 - y, 0, y - (y1 - 1))
            dist = max(dx, dy)
            if dist == 0:
                t = 1.0
            else:
                t = max(0.0, 1 - dist / (feather + 1)) ** 2
                if t <= 0:
                    continue
            c = fill_at(u, v)
            if t < 1:
                o = surf.get_at((x, y))
                c = [o[k] * (1 - t) + c[k] * t for k in range(3)]
            surf.set_at((x, y), [max(0, min(255, int(q))) for q in c])


def crop(surf, rect):
    x0, y0, x1, y1 = rect
    return surf.subsurface(pygame.Rect(x0, y0, x1 - x0, y1 - y0)).copy()


def cutout(original, cleaned, rect, threshold=40):
    """The pixels inside rect that differ from the erased version, on a transparent background."""
    x0, y0, x1, y1 = rect
    out = pygame.Surface((x1 - x0, y1 - y0), pygame.SRCALPHA)
    for y in range(y0, y1):
        for x in range(x0, x1):
            a, b = original.get_at((x, y)), cleaned.get_at((x, y))
            d = abs(a.r - b.r) + abs(a.g - b.g) + abs(a.b - b.b)
            if d > threshold:
                out.set_at((x - x0, y - y0), (a.r, a.g, a.b, min(255, int((d - threshold) * 3))))
    bounds = out.get_bounding_rect(min_alpha=30)
    return out.subsurface(bounds).copy() if bounds.width else out


def blank_part(art, rect, erase):
    """A button/tab cut from the mockup with its label erased (erase is relative to the full image)."""
    part = art.copy()
    for r in erase:
        inpaint(part, r, feather=6, plain=True)
    return crop(part, rect)


def over_background(part, background, threshold=18, soft=40):
    """Makes a cut-out button transparent wherever it matches the panel behind it, fading in
    over `soft` levels of difference, so its glow stays soft and no rectangle shows."""
    w, h = part.get_size()
    out = part.convert_alpha()
    for y in range(h):
        for x in range(w):
            a, b = part.get_at((x, y)), background.get_at((x, y))
            d = abs(a.r - b.r) + abs(a.g - b.g) + abs(a.b - b.b)
            alpha = max(0, min(255, int((d - threshold) * 255 / soft)))
            out.set_at((x, y), (a.r, a.g, a.b, alpha))
    return out


def banner(surf, tip_ratio=0.31):
    """Keeps only the pointed-banner shape of a button; the corners outside it become transparent
    (they held a bit of the mockup's panel, which showed as dark patches elsewhere)."""
    w, h = surf.get_size()
    tip = h * tip_ratio
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(mask, (255, 255, 255, 255), [(tip - 1, -1), (w - tip, -1), (w + 1, h / 2), (w - tip, h),
                                                     (tip - 1, h), (-2, h / 2)])
    out = surf.convert_alpha()
    out.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return out


def erase_figure(surf, rect, grow=4):
    """Erases the character standing in rect, keeping the scene behind it sharp.

    The character is the largest blob of warm or bright pixels (the scene behind is blue);
    only that outline (grown by `grow` px) is filled, each pixel from the scene just past the
    outline in the four directions, weighted by distance (left/right counts more, since the
    pillars and light beam run vertically)."""
    x0, y0, x1, y1 = rect
    W, H = x1 - x0, y1 - y0
    px = [[surf.get_at((x0 + i, y0 + j)) for i in range(W)] for j in range(H)]
    warm = [[c.r > c.b - 12 or c.r + c.g + c.b > 420 for c in row] for row in px]
    seen = [[False] * W for _ in range(H)]
    best = []
    for j in range(H):
        for i in range(W):
            if warm[j][i] and not seen[j][i]:
                seen[j][i] = True
                stack, comp = [(i, j)], []
                while stack:
                    a, b = stack.pop()
                    comp.append((a, b))
                    for na in (a - 1, a, a + 1):
                        for nb in (b - 1, b, b + 1):
                            if 0 <= na < W and 0 <= nb < H and warm[nb][na] and not seen[nb][na]:
                                seen[nb][na] = True
                                stack.append((na, nb))
                if len(comp) > len(best):
                    best = comp
    mask = [[False] * W for _ in range(H)]
    for a, b in best:
        for nb in range(max(0, b - grow), min(H, b + grow + 1)):
            for na in range(max(0, a - grow), min(W, a + grow + 1)):
                mask[nb][na] = True
    for j in range(H):
        for i in range(W):
            if not mask[j][i]:
                continue
            total, acc = 0.0, [0.0, 0.0, 0.0]
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                a, b, d = i, j, 0
                while 0 <= a < W and 0 <= b < H and mask[b][a]:
                    a, b, d = a + di, b + dj, d + 1
                if not (0 <= a < W and 0 <= b < H):
                    continue
                # median of a few pixels past the edge, so small details there don't streak
                samp = [px[min(H - 1, max(0, b + dj * k))][min(W - 1, max(0, a + di * k))] for k in range(5)]
                c = [sorted(s[q] for s in samp)[2] for q in range(3)]
                w = (0.35 if dj else 1.0) / d ** 2
                total += w
                acc = [acc[q] + c[q] * w for q in range(3)]
            if total:
                surf.set_at((x0 + i, y0 + j), [int(v / total) for v in acc])


GLASS_ALPHA = 160   # how solid the see-through panels are (255 = not see-through)


def glass(surf, rects=None, alpha=GLASS_ALPHA):
    """Makes the dark navy of the panels in `rects` (all of surf if None) partly see-through,
    so the game's background shows behind them. Gold trim, text and bright glows stay solid."""
    out = surf.convert_alpha()
    w, h = out.get_size()
    for x0, y0, x1, y1 in rects or [(0, 0, w, h)]:
        for y in range(max(0, y0), min(h, y1)):
            for x in range(max(0, x0), min(w, x1)):
                c = out.get_at((x, y))
                if c.r > c.b + 10:        # gold / warm: keep
                    continue
                t = min(1.0, max(0.0, (c.r + c.g + c.b - 170) / 120))
                out.set_at((x, y), (c.r, c.g, c.b, min(c.a, int(alpha + (255 - alpha) * t))))
    return out


def straight_title(art, rect, letters_bottom, top_pad=6):
    """Cuts a gold title out of the mockup and evens it out: each letter is stretched so all
    of them share one top and one baseline (the hand-drawn letters wave up and down).
    The ornament line under the letters (below `letters_bottom`) is kept as it is."""
    x0, y0, x1, y1 = rect
    W, H = x1 - x0, y1 - y0
    cut = pygame.Surface((W, H), pygame.SRCALPHA)
    for y in range(H):
        for x in range(W):
            c = art.get_at((x0 + x, y0 + y))
            # gold, or the pale highlights on it (bright and not blue like the sky and stars)
            warm = (c.r - c.b - 12) * 255 / 60
            bright = (c.r + c.g + c.b - 200) * 255 / 150 if c.r >= c.b else 0
            a = min(255, max(0, int(max(warm, bright))))
            if a:
                cut.set_at((x, y), (c.r, c.g, c.b, a))
    base = letters_bottom - y0
    solid = lambda x, y: cut.get_at((x, y)).a > 120
    cols = [any(solid(x, y) for y in range(base)) for x in range(W)]
    letters, start = [], None
    for x, on in enumerate(cols + [False]):
        if on and start is None:
            start = x
        elif not on and start is not None:
            ys = [y for y in range(base) for xx in range(start, x) if solid(xx, y)]
            if x - start > 12:                          # skip specks and ornament bits
                letters.append((start, x, min(ys), max(ys) + 1))
            start = None
    top = sorted(t for _, _, t, _ in letters)[len(letters) // 2]
    bottom = sorted(b for _, _, _, b in letters)[len(letters) // 2]
    out = pygame.Surface((W, H), pygame.SRCALPHA)
    out.blit(cut, (0, base), pygame.Rect(0, base, W, H - base))       # the ornament line
    for lx0, lx1, t, b in letters:
        # a few px of margin so the soft edges come along
        src = cut.subsurface(pygame.Rect(max(0, lx0 - 2), max(0, t - 2), min(W, lx1 + 2) - max(0, lx0 - 2),
                                         min(base, b + 2) - max(0, t - 2)))
        h = (bottom - top) + 4
        out.blit(pygame.transform.smoothscale(src, (src.get_width(), h)), (max(0, lx0 - 2), top - 2))
    # drop specks left over (a star, the tip of the ornament's diamond)
    for blob in pygame.mask.from_surface(out, 40).connected_components():
        if blob.count() < 40:
            r = blob.get_bounding_rects()[0]
            for y in range(r.top, r.bottom):
                for x in range(r.left, r.right):
                    if blob.get_at((x, y)):
                        out.set_at((x, y), (0, 0, 0, 0))
    return out


def save(surf, name):
    pygame.image.save(surf, os.path.join(OUT, name))
    print("wrote", name)


def make_create():
    art = pygame.image.load(os.path.join(ROOT, CREATE["art"])).convert()
    L = CREATE
    # Parts in each state, cut before the screen is cleaned
    save(banner(blank_part(art, L["btn_boy"], [L["erase_boy"]])), "create_btn_on.png")
    save(banner(blank_part(art, L["btn_girl"], [L["erase_girl"]])), "create_btn_off.png")
    save(banner(blank_part(art, L["btn_sword"], [L["erase_sword"]])), "create_btn_on_2.png")
    save(banner(blank_part(art, L["btn_sorc"], [L["erase_sorc"]])), "create_btn_off_2.png")

    clean = art.copy()
    erase_figure(clean, L["erase_figure"])
    for r in L["erase"]:
        inpaint(clean, r)
    # Button icons: compare against a copy with the button labels (and their icons) erased
    no_labels = art.copy()
    for key in ("erase_boy", "erase_girl", "erase_sword", "erase_sorc"):
        inpaint(no_labels, L[key], feather=6, plain=True)
    for key, name in (("icon_male", "icon_male.png"), ("icon_female", "icon_female.png"),
                      ("icon_sword", "icon_sword.png"), ("icon_staff", "icon_staff.png")):
        save(cutout(art, no_labels, L[key], threshold=110), name)
    # Art for the starting weapons: the sword from the weapon frame, the staff from the class button
    os.makedirs(os.path.join(ROOT, "items"), exist_ok=True)
    pygame.image.save(cutout(art, clean, L["weapon_icon_art"]), os.path.join(ROOT, "items", "Iron Sword.png"))
    pygame.image.save(cutout(art, no_labels, L["icon_staff"], threshold=110),
                      os.path.join(ROOT, "items", "Novice Staff.png"))
    print("wrote items/Iron Sword.png, items/Novice Staff.png")
    save(glass(clean, L["glass"]), "create.png")


def make_camp():
    art = pygame.image.load(os.path.join(ROOT, CAMP["art"])).convert()
    L = CAMP
    save(straight_title(art, L["title"], L["title_letters_bottom"]), "camp_title.png")
    clean = art.copy()
    inpaint(clean, L["title"], feather=12)
    for r in L["erase"]:
        inpaint(clean, r)

    def part(key, erase):
        cut = blank_part(art, L[key], [erase])
        return over_background(cut, crop(clean, L[key]))
    save(part("tab_skills", L["erase_tab_skills"]), "camp_tab_off.png")
    save(part("tab_equipment", L["erase_tab_equipment"]), "camp_tab_on.png")
    save(banner(blank_part(art, L["btn_selected"], [L["erase_btn_selected"]])), "camp_btn_on.png")
    save(banner(blank_part(art, L["btn_delete"], [L["erase_btn_delete"]])), "camp_btn_off.png")
    save(part("create_btn", L["erase_create_label"]), "camp_wide_btn.png")
    save(banner(blank_part(art, L["menu_btn"], [L["erase_menu_label"]])), "camp_back_btn.png")    # Create screen's Back button
    save(glass(blank_part(art, L["slot_boxes"][1], [L["erase_slot_inner"][1]])), "camp_slot.png")
    save(glass(blank_part(art, L["slot_boxes"][2], [L["erase_slot_inner"][2]])), "camp_slot_on.png")
    for n, (cx, cy) in enumerate(L["stat_icons"]):      # icons erased with the stat column, redrawn in game
        save(cutout(art, clean, (cx - 20, cy - 21, cx + 21, cy + 20), threshold=110), f"camp_stat_{n}.png")
    save(glass(crop(clean, L["roster_rows"][0])), "camp_row.png")
    save(glass(clean, L["glass"]), "camp.png")

    # Skills tab: the whole area under the tabs as a plain panel
    skills = clean.copy()
    inpaint(skills, L["erase_right_content"])
    save(glass(skills, L["glass"]), "camp_skills.png")


def main():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    pygame.display.set_mode((1, 1))
    os.makedirs(OUT, exist_ok=True)
    make_create()
    make_camp()


if __name__ == "__main__":
    main()
