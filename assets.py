"""Asset loading helpers: paths, cached images/fonts/animations, and optional sounds."""
import json
import os
import sys

import pygame

FROZEN = getattr(sys, "frozen", False)          # True when running as the packaged .exe
BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))   # game files (art, sound)
# Where the player's files go (saves, settings): next to the .exe, or the project folder when run from source
APP_DIR = os.path.dirname(sys.executable) if FROZEN else BASE_DIR
SOUND_DIR = os.path.join(BASE_DIR, "sounds")

# Named sound effects: name -> (file, volume, max play time in ms or None).
# Sounds pygame can't read (.m4a/.webm/.mkv) were converted to .ogg
# ("(trimmed)" copies also skip silence at the start, so the sound lines up with the action).
SFX = "sound_effects/"
SOUNDS = {
    "sword_basic": (SFX + "sword effects/Metal sword effect.ogg", 0.7, None),
    "sword_great": (SFX + "sword effects/Great Sword Sound Effect.mp3", 0.7, 1800),   # the file runs ~5 s
    "wand_basic":  (SFX + "mage attack effect/normal wand.ogg", 0.7, None),
    "wand_great":  (SFX + "mage attack effect/upgraded mage weapon (trimmed).ogg", 0.7, 2200),
    "victory":     (SFX + "victory effect/victory (trimmed).ogg", 0.5, None),
    "defeat":      (SFX + "defeat_sound/Factorio Defeat Sound Effect (Audio).mp3", 0.8, None),
}
# Music: name -> (file, volume[, start at this many seconds into the track])
MUSIC = {
    "title": (SFX + "startscreen music/Teller of the Tales.mp3", 0.5),
    "map": (SFX + "map music background/That Zen Moment.mp3", 0.6, 22),   # skip the near-silent intro
    "battle": (SFX + "fighting scene/Darkling.mp3", 0.2),
    "final_boss": (SFX + "floor 5 final boss music/Burnt Spirit.mp3", 0.5),
}
_current_music = None
_music_base = 1.0

# Player options, saved between sessions in settings.json
SETTINGS_FILE = os.path.join(APP_DIR, "settings.json")
settings = {"music": 1.0, "sfx": 1.0, "fullscreen": False}


def load_settings():
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return
    for key in ("music", "sfx"):
        if isinstance(data.get(key), (int, float)):
            settings[key] = min(1.0, max(0.0, float(data[key])))
    if isinstance(data.get("fullscreen"), bool):
        settings["fullscreen"] = data["fullscreen"]


def save_settings():
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=1)
    except OSError as e:
        print("Could not save settings:", e)


def apply_music_volume():
    if pygame.mixer.get_init():
        pygame.mixer.music.set_volume(_music_base * settings["music"])


_image_cache = {}
_font_cache = {}
_sound_cache = {}
_sound_base = {}


def path(*parts):
    """Absolute path to a project file, so the game runs from any working directory."""
    return os.path.join(BASE_DIR, *parts)


# Serif fonts in the style of the title art. The first one installed is used.
BODY_FONTS = "cambria,constantia,georgia,palatinolinotype,timesnewroman"
DISPLAY_FONTS = "trajanprobold,trajanpro,cambria,georgia,timesnewroman"


def font(size, bold=False, display=False):
    """Body text font, or the engraved display font for big titles."""
    key = (size, bold, display)
    if key not in _font_cache:
        _font_cache[key] = pygame.font.SysFont(DISPLAY_FONTS if display else BODY_FONTS, size, bold=bold)
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


def load_part(rel_path, size):
    """Loads a UI part (with transparency) stretched to exactly `size`. Returns None if missing."""
    key = ("part", rel_path, size)
    if key not in _image_cache:
        full = path(rel_path)
        _image_cache[key] = (pygame.transform.smoothscale(pygame.image.load(full).convert_alpha(), size)
                             if os.path.exists(full) else None)
    return _image_cache[key]


def load_icon(rel_path, size):
    """Loads an image scaled to fit inside `size` (keeping its shape). Returns None if missing."""
    key = ("icon", rel_path, size)
    if key not in _image_cache:
        full = path(rel_path)
        img = None
        if os.path.exists(full):
            raw = pygame.image.load(full)
            opaque = not (raw.get_bitsize() == 32 and raw.get_at((0, 0)).a < 255)
            raw = raw.convert_alpha()
            if opaque:   # art saved with a white or checkered background
                raw = _remove_light_background(raw, raw.get_width() * raw.get_height())
            bounds = raw.get_bounding_rect(min_alpha=10)
            if bounds.width and bounds.height:
                raw = raw.subsurface(bounds)
            scale = min(size[0] / raw.get_width(), size[1] / raw.get_height())
            img = pygame.transform.smoothscale(raw, (max(1, int(raw.get_width() * scale)),
                                                     max(1, int(raw.get_height() * scale))))
        _image_cache[key] = img
    return _image_cache[key]


def load_frames(rel_path, cols, rows=1, target_h=300, count=None, flip=False, tint=None, start=0,
                clean_edges=False, anchor="cell", defringe=False):
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

    anchor="cell": frames keep their position inside the sheet (for sheets drawn
    on a consistent grid). anchor="body": every frame is lined up on where the
    character's own feet are, ignoring glowing effects, so characters drawn at a
    different spot in each cell don't jump around or float. anchor="first-body":
    the feet found in frame 0 are used for every frame (for generated idle and
    hurt sheets, whose frames already share one position).
    """
    key = ("frames", rel_path, tuple(cols) if isinstance(cols, list) else cols, rows, target_h, count, flip, tint,
           start, clean_edges, anchor, defringe)
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
        # Enclosed light areas bigger than this (e.g. inside a bow) count as background too
        frames_guess = cols * rows if isinstance(cols, int) else 8
        sheet = _cleaned_sheet(rel_path, sheet, sheet.get_width() * sheet.get_height() // (400 * frames_guess))

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
    if clean_edges:
        cells = [_drop_edge_bleed(c.copy()) for c in cells]
    if start:
        # Play from the resting pose and return to it (for sheets whose calm frame isn't first)
        cells = cells[start:] + cells[:start] + [cells[start]]

    # Scale factor and ground line come from frame 0 (the resting pose)
    first_bounds = cells[0].get_bounding_rect(min_alpha=20)
    scale = 1 if target_h is None else target_h / max(1, first_bounds.height)
    ground = first_bounds.bottom * scale
    first_feet = None

    frames = []
    for cell in cells:
        size = (max(1, int(cell.get_width() * scale)), max(1, int(cell.get_height() * scale)))
        img = pygame.transform.smoothscale(cell, size)
        if defringe:
            img = _defringe(img)
        if tint:
            img.fill(tint, special_flags=pygame.BLEND_RGB_MULT)
        bounds = img.get_bounding_rect(min_alpha=20)
        if not bounds.width:
            bounds = pygame.Rect(0, 0, 1, 1)
        # Horizontal anchor: grid cells share frame 0's feet, single-row frames use their own feet
        if anchor == "body":
            anchor_x, ground = _body_feet(img, bounds)
        elif anchor == "body-wide":     # lower third of the body: stable for wide stances
            anchor_x, ground = _body_feet(img, bounds, band_frac=0.35)
        elif anchor == "first-body":
            if first_feet is None:
                first_feet, ground = _body_feet(img, bounds)
            anchor_x = first_feet
        elif single_row:
            anchor_x = _feet_x(img, bounds)
        else:
            if first_feet is None:
                first_feet = _feet_x(img, bounds)
            anchor_x = first_feet
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


def _defringe(img, passes=3):
    """Removes a reddish halo along a sprite's outline (left over when a background was cut
    away) and tiny loose specks. Only outline pixels that are much redder than they are green
    are removed, so gold hair and armor stay."""
    img = img.copy()
    w, h = img.get_size()
    brush = pygame.mask.Mask((3, 3), fill=True)
    for _ in range(passes):
        solid = pygame.mask.from_surface(img, 20)
        grown = solid.copy()
        grown.invert()
        grown = grown.convolve(brush)             # transparent area grown by 1 px
        outline = solid.overlap_mask(grown, (-1, -1))
        img.lock()
        for x, y in _points(outline):
            c = img.get_at((x, y))
            if c.a and c.r > 60 and c.r > 1.7 * c.g and c.r > 1.5 * c.b:
                img.set_at((x, y), (0, 0, 0, 0))
        img.unlock()
    solid = pygame.mask.from_surface(img, 20)
    total = solid.count()
    for comp in solid.connected_components(minimum=1):
        if comp.count() < total * 0.003:
            comp.to_surface(img, setcolor=(0, 0, 0, 0), unsetsurface=img)
    return img


def _points(mask):
    w, h = mask.get_size()
    for rect in mask.get_bounding_rects():
        for y in range(rect.top, rect.bottom):
            for x in range(rect.left, rect.right):
                if mask.get_at((x, y)):
                    yield x, y


def _drop_edge_bleed(cell, max_share=0.15):
    """Removes pieces of neighbouring frames that spill over a grid cell's edge.

    A piece is dropped when it touches the cell border, isn't part of the main
    figure, and is small compared to everything drawn in the cell. Effects that
    belong to this frame (a beam from the staff, a swirl around the body) are
    connected to the figure, so they stay. Detached pieces sitting entirely in
    the outer quarter of the cell are treated as spill-over too.
    """
    w, h = cell.get_size()
    mask = pygame.mask.from_surface(cell, 20)
    total = mask.count()
    if not total:
        return cell
    main = mask.connected_component()
    for comp in mask.connected_components(minimum=1):
        rect = comp.get_bounding_rects()[0]
        if comp.overlap(main, (0, 0)):
            continue
        touches = rect.left <= 1 or rect.top <= 1 or rect.right >= w - 1 or rect.bottom >= h - 1
        in_side_band = rect.right <= w * 0.25 or rect.left >= w * 0.75   # detached, hugging a side
        if (touches and comp.count() < total * max_share) or in_side_band:
            comp.to_surface(cell, setcolor=(0, 0, 0, 0), unsetsurface=cell)
    return cell


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


def _body_feet(img, bounds, step=4, band_frac=0.1):
    """(feet x, ground y) of the character in a frame, ignoring glowing effects.

    Works on a reduced copy for speed: bright, strongly coloured pixels (fire,
    ice, magic, slash trails) are left out, the largest remaining blob is taken
    as the body, and its lowest part is where the feet are.
    """
    w, h = img.get_size()
    sw, sh = max(1, w // step), max(1, h // step)
    small = pygame.transform.scale(img, (sw, sh))
    body = pygame.mask.Mask((sw, sh))
    small.lock()
    for y in range(sh):
        for x in range(sw):
            c = small.get_at((x, y))
            if c.a > 150:
                hi, lo = max(c.r, c.g, c.b), min(c.r, c.g, c.b)
                if not (hi > 170 and hi - lo > 90):
                    body.set_at((x, y))
    small.unlock()
    main = body.connected_component()
    if main.count() < 20:
        return _feet_x(img, bounds), bounds.bottom
    rect = main.get_bounding_rects()[0].unionall(main.get_bounding_rects()[1:])
    band = max(1, int(rect.height * band_frac))
    feet = pygame.mask.Mask((sw, sh))
    feet.draw(main, (0, 0))
    feet.erase(pygame.mask.Mask((sw, rect.bottom - band), fill=True), (0, 0))
    feet_cx = _median_x(feet, pygame.Rect(0, rect.bottom - band, sw, band))
    return feet_cx * step, rect.bottom * step


def _median_x(mask, rect):
    """x position that splits the mask's pixels inside rect in half (a weighted middle).

    Thin things that reach the ground, like a resting sword tip, barely move it,
    while the bulk of the boots decides where the feet are.
    """
    counts = []
    for x in range(rect.left, rect.right):
        counts.append(sum(mask.get_at((x, y)) for y in range(rect.top, rect.bottom)))
    total = sum(counts)
    if not total:
        return rect.centerx
    running = 0
    for i, c in enumerate(counts):
        running += c
        if running * 2 >= total:
            return rect.left + i + 0.5
    return rect.centerx


def _feet_x(img, bounds):
    """x position of the feet: the weighted middle of the lowest band of solid pixels."""
    band_h = max(4, bounds.height // 12)
    band = pygame.Rect(bounds.x, bounds.bottom - band_h, bounds.width, band_h)
    return _median_x(pygame.mask.from_surface(img, 60), band)


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


CACHE_DIR = path("cache")   # sheets with their white background already removed (safe to delete)


def _cleaned_sheet(rel_path, sheet, big_hole):
    """Background removal on a big sheet takes seconds, so the result is saved once in
    cache/ and reused. It is redone automatically when the original art changes."""
    src = path(rel_path)
    cached = os.path.join(CACHE_DIR, rel_path.replace("/", "__").replace("\\", "__"))
    if os.path.exists(cached) and (FROZEN or os.path.getmtime(cached) >= os.path.getmtime(src)):
        try:
            return pygame.image.load(cached).convert_alpha()
        except pygame.error:
            pass
    cleaned = _remove_light_background(sheet, big_hole)
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        pygame.image.save(cleaned, cached)
    except (OSError, pygame.error):
        pass
    return cleaned


def _remove_light_background(img, big_hole=None):
    """Makes near-white pixels connected to the image border transparent (for sheets saved without alpha)."""
    w, h = img.get_size()
    light = pygame.mask.from_threshold(img, (255, 255, 255, 255), (45, 45, 45, 255))
    border = pygame.Rect(0, 0, w, h)
    background = pygame.mask.Mask((w, h))
    big_hole = max(60, big_hole or w * h // 400)   # large enclosed light areas are background too
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
    """Plays a named sound from SOUNDS, or sounds/<name>.wav|.ogg|.mp3 if it exists.

    Silently does nothing when the sound or the audio device is missing.
    """
    if not pygame.mixer.get_init():
        return
    maxtime = 0
    if name not in _sound_cache:
        snd = None
        if name in SOUNDS:
            candidates = [path(SOUNDS[name][0])]
            volume = SOUNDS[name][1]
        else:
            candidates = [os.path.join(SOUND_DIR, name + ext) for ext in (".wav", ".ogg", ".mp3")]
        for full in candidates:
            if os.path.exists(full):
                try:
                    snd = pygame.mixer.Sound(full)
                    _sound_base[name] = volume
                except pygame.error:
                    snd = None
                break
        _sound_cache[name] = snd
    if name in SOUNDS and SOUNDS[name][2]:
        maxtime = SOUNDS[name][2]
    if _sound_cache[name]:
        _sound_cache[name].set_volume(_sound_base[name] * settings["sfx"])
        channel = _sound_cache[name].play(maxtime=maxtime)
        if channel and maxtime:
            channel.fadeout(maxtime)


def play_music(name, fade_ms=800):
    """Loops a track from MUSIC. Keeps playing if it's already on."""
    global _current_music, _music_base
    if not pygame.mixer.get_init() or name not in MUSIC or _current_music == name:
        return
    file, volume, *start = MUSIC[name]
    try:
        pygame.mixer.music.load(path(file))
        _music_base = volume
        pygame.mixer.music.set_volume(volume * settings["music"])
        pygame.mixer.music.play(-1, start=start[0] if start else 0.0, fade_ms=fade_ms)
        _current_music = name
    except pygame.error:
        _current_music = None


def stop_music(fade_ms=800):
    global _current_music
    if pygame.mixer.get_init() and _current_music:
        pygame.mixer.music.fadeout(fade_ms)
    _current_music = None
