"""Asset loading helpers: paths, cached images/fonts/animations, and optional sounds."""
import os

import pygame

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOUND_DIR = os.path.join(BASE_DIR, "sounds")

_image_cache = {}
_font_cache = {}
_sound_cache = {}


def path(*parts):
    """Absolute path to a project file, so the game runs from any working directory."""
    return os.path.join(BASE_DIR, *parts)


def font(size, bold=False):
    key = (size, bold)
    if key not in _font_cache:
        _font_cache[key] = pygame.font.SysFont("Arial", size, bold=bold)
    return _font_cache[key]


def load_background(rel_path, size):
    """Loads an opaque image scaled to fill `size`. Returns None if missing."""
    key = ("bg", rel_path, size)
    if key not in _image_cache:
        full = path(rel_path)
        img = None
        if os.path.exists(full):
            img = pygame.transform.smoothscale(pygame.image.load(full).convert(), size)
        _image_cache[key] = img
    return _image_cache[key]


def load_frames(rel_path, cols, rows=1, target_h=300, count=None, flip=False, tint=None):
    """Slices a sprite sheet into animation frames.

    cols can be:
      - a number: an even grid of cols x rows
      - "auto": a single-row sheet with unevenly spaced poses; cuts go in the gaps
      - a list of x positions: a single-row sheet cut exactly there (for sheets
        where poses overlap too much for "auto")

    Every frame is scaled by the same factor (so frame 0's character is `target_h`
    tall) and cropped to its visible pixels. Returns a list of (surface, offset)
    where offset is the frame's top-left relative to the character's feet, which
    keeps the animation steady instead of jittering. Returns [] if missing.
    """
    key = ("frames", rel_path, tuple(cols) if isinstance(cols, list) else cols, rows, target_h, count, flip, tint)
    if key in _image_cache:
        return _image_cache[key]

    full = path(rel_path)
    if not os.path.exists(full):
        _image_cache[key] = []
        return []

    sheet = pygame.image.load(full)
    opaque = not (sheet.get_bitsize() == 32 and sheet.get_at((0, 0)).a < 255)
    sheet = sheet.convert_alpha()
    if opaque:
        sheet = _remove_light_background(sheet)

    single_row = cols == "auto" or isinstance(cols, (list, tuple))
    if single_row:
        if cols == "auto":
            spans = _find_pose_columns(sheet)
        else:
            edges = [0] + list(cols) + [sheet.get_width()]
            spans = list(zip(edges, edges[1:]))
        cells = [_drop_edge_slivers(sheet.subsurface((x0, 0, x1 - x0, sheet.get_height())).copy()) for x0, x1 in spans]
    else:
        cell_w, cell_h = sheet.get_width() // cols, sheet.get_height() // rows
        cells = [sheet.subsurface((c * cell_w, r * cell_h, cell_w, cell_h))
                 for r in range(rows) for c in range(cols)]
    cells = cells[:count]

    # Scale factor and ground line come from frame 0 (the resting pose)
    first_bounds = cells[0].get_bounding_rect(min_alpha=20)
    scale = target_h / max(1, first_bounds.height)
    ground = first_bounds.bottom * scale

    frames = []
    for cell in cells:
        size = (max(1, int(cell.get_width() * scale)), max(1, int(cell.get_height() * scale)))
        img = pygame.transform.smoothscale(cell, size)
        if tint:
            img.fill(tint, special_flags=pygame.BLEND_RGB_MULT)
        bounds = img.get_bounding_rect(min_alpha=20)
        if not bounds.width:
            bounds = pygame.Rect(0, 0, 1, 1)
        # Horizontal anchor: grid cells share frame 0's position, auto frames use their own feet
        if single_row:
            anchor_x = _feet_x(img, bounds)
        else:
            anchor_x = first_bounds.centerx * scale
        cropped = img.subsurface(bounds).copy()
        ox, oy = bounds.x - anchor_x, bounds.y - ground
        if flip:
            cropped = pygame.transform.flip(cropped, True, False)
            ox = -(ox + bounds.width)
        frames.append((cropped, (int(ox), int(oy))))

    _image_cache[key] = frames
    return frames


def _find_pose_columns(sheet, min_width_ratio=0.2):
    """Finds the x-ranges of the poses in a single-row sheet by cutting at the emptiest columns."""
    w, h = sheet.get_size()
    # Only look at the characters' lower bodies (hips to shins) and only at solid
    # pixels: spell blasts and sword trails float at arm height or are see-through,
    # and would otherwise bridge the gap between two poses.
    mask = pygame.mask.from_surface(sheet, 200)
    body = mask.get_bounding_rects()
    top = min(r.top for r in body) if body else 0
    bottom = max(r.bottom for r in body) if body else h
    band = range(int(top + (bottom - top) * 0.5), int(top + (bottom - top) * 0.9), 2)
    counts = [sum(mask.get_at((x, y)) for y in band) for x in range(w)]
    win = 12
    smooth = [sum(counts[max(0, x - win):x + win]) / (2 * win) for x in range(w)]
    threshold = max(smooth) * 0.15

    # One cut at the lowest point of every sparse stretch of columns
    cuts, x = [], 0
    while x < w:
        if smooth[x] < threshold:
            run_start = x
            while x < w and smooth[x] < threshold:
                x += 1
            if run_start > 0 and x < w:
                best = min(range(run_start, x), key=lambda i: smooth[i])
                cuts.append(best)
        x += 1

    # Poses can't be thinner than this; drop the weakest cut next to any sliver
    min_w = h * min_width_ratio
    while True:
        edges = [0] + cuts + [w]
        slivers = [i for i in range(len(edges) - 1) if edges[i + 1] - edges[i] < min_w]
        if not slivers or not cuts:
            break
        i = slivers[0]
        candidates = [c for c in (i - 1, i) if 0 <= c < len(cuts)]
        cuts.pop(max(candidates, key=lambda c: smooth[cuts[c]]))

    edges = [0] + cuts + [w]
    return [(edges[i], edges[i + 1]) for i in range(len(edges) - 1)]


def _drop_edge_slivers(cell, max_share=0.12, glow_reach=12):
    """Removes bits of neighbouring poses that stick in from the left/right edge.

    Solid pieces touching an edge that are small compared to the pose are dropped,
    and faint glow is only kept when it sits near a solid part that was kept
    (so a neighbour's semi-transparent aura can't sneak in).
    """
    w, h = cell.get_size()
    solid = pygame.mask.from_surface(cell, 128)
    total = solid.count()
    keep = pygame.mask.Mask((w, h))
    for comp in solid.connected_components(minimum=1):
        rect = comp.get_bounding_rects()[0]
        near_edge = rect.left <= w * 0.04 or rect.right >= w * 0.96
        speck = comp.count() < total * 0.004
        if not speck and not (near_edge and comp.count() < total * max_share):
            keep.draw(comp, (0, 0))

    # Grow the kept solid area by glow_reach px, then keep only visible pixels inside it
    r = glow_reach
    brush = pygame.mask.Mask((2 * r + 1, 2 * r + 1))
    for y in range(2 * r + 1):
        for x in range(2 * r + 1):
            if (x - r) ** 2 + (y - r) ** 2 <= r * r:
                brush.set_at((x, y))
    near = keep.convolve(brush)
    visible = pygame.mask.from_surface(cell, 1).overlap_mask(near, (-r, -r))

    out = pygame.Surface((w, h), pygame.SRCALPHA)
    visible.to_surface(out, setsurface=cell, unsetcolor=(0, 0, 0, 0))
    return out


def _feet_x(img, bounds):
    """x-center of the lowest band of pixels in a frame (where the character stands)."""
    band_h = max(4, bounds.height // 12)
    band = pygame.Rect(bounds.x, bounds.bottom - band_h, bounds.width, band_h)
    feet = img.subsurface(band).get_bounding_rect(min_alpha=60)
    return band.x + (feet.centerx if feet.width else band.width / 2)


def isolate_main_shape(frame):
    """Keeps only the largest connected blob of a (surface, offset) frame.

    Used for still poses cut from sheets where neighbouring frames' effects bleed in.
    """
    surf, (ox, oy) = frame
    main = pygame.mask.from_surface(surf, 20).connected_component()
    if not main.count():
        return frame
    bounds = main.get_bounding_rects()[0]
    clean = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    main.to_surface(clean, setsurface=surf, unsetcolor=(0, 0, 0, 0))
    return clean.subsurface(bounds).copy(), (ox + bounds.x, oy + bounds.y)


def _remove_light_background(img):
    """Makes near-white pixels connected to the image border transparent (for sheets saved without alpha)."""
    w, h = img.get_size()
    light = pygame.mask.from_threshold(img, (255, 255, 255, 255), (45, 45, 45, 255))
    border = pygame.Rect(0, 0, w, h)
    background = pygame.mask.Mask((w, h))
    big_hole = max(60, w * h // 400)   # large enclosed light areas (e.g. inside a bow) are background too
    for comp in light.connected_components(minimum=1):
        rect = comp.get_bounding_rects()[0] if comp.count() else None
        touches_border = rect and (rect.left == 0 or rect.top == 0 or rect.right == border.right or rect.bottom == border.bottom)
        if touches_border or comp.count() > big_hole:
            background.draw(comp, (0, 0))
    background.invert()
    out = pygame.Surface((w, h), pygame.SRCALPHA)
    background.to_surface(out, setsurface=img, unsetcolor=(0, 0, 0, 0))
    return out


def play_sound(name, volume=0.6):
    """Plays sounds/<name>.wav|.ogg|.mp3 if it exists. Silently does nothing otherwise."""
    if not pygame.mixer.get_init():
        return
    if name not in _sound_cache:
        snd = None
        for ext in (".wav", ".ogg", ".mp3"):
            full = os.path.join(SOUND_DIR, name + ext)
            if os.path.exists(full):
                try:
                    snd = pygame.mixer.Sound(full)
                    snd.set_volume(volume)
                except pygame.error:
                    snd = None
                break
        _sound_cache[name] = snd
    if _sound_cache[name]:
        _sound_cache[name].play()
