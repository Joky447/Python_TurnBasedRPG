"""Shared colors and drawing helpers used by every screen."""
import math

import pygame

import assets
from character.entity import STATUS_INFO

# --- Palette (taken from the Spells x Blades start screen art) ------------------
BG = (8, 16, 38)
PANEL = (10, 24, 58)             # deep night blue
PANEL_BORDER = (201, 152, 72)    # antique gold trim
BUTTON = (14, 52, 118)           # royal blue, like "Start Game"
BUTTON_HOVER = (28, 78, 158)
BUTTON_DISABLED = (26, 32, 50)
BUTTON_RED = (104, 18, 24)       # crimson, like "Quit"
BUTTON_RED_HOVER = (150, 30, 36)
SELECTED = (30, 92, 170)
TEXT = (246, 240, 226)           # warm parchment white
TEXT_DIM = (170, 176, 196)
GOLD = (240, 196, 98)
GOLD_LIGHT = (255, 236, 176)
GOLD_DARK = (120, 82, 34)
RED = (210, 60, 60)
HP_GREEN = (60, 185, 70)
HP_BACK = (90, 28, 28)
BLOCK_BLUE = (90, 150, 230)
ENERGY = (90, 190, 255)


# Rendered text and panel backgrounds are kept and reused: the same labels and panels are
# drawn every frame, and rebuilding them each time is most of the drawing work.
_render_cache: dict = {}
_panel_cache: dict = {}
CACHE_LIMIT = 3000


def _rendered(msg, size, color, bold=False, display=False):
    key = (msg, size, tuple(color), bold, display)
    surf = _render_cache.get(key)
    if surf is None:
        if len(_render_cache) > CACHE_LIMIT:      # changing numbers (damage, HP) would pile up
            _render_cache.clear()
        surf = _render_cache[key] = assets.font(size, bold, display=display).render(msg, True, color)
    return surf


def text(screen, msg, size, color=TEXT, bold=False, **anchor):
    """Draws text. Pass an anchor like center=(x, y) or topleft=(x, y). Returns the rect."""
    surf = _rendered(str(msg), size, color, bold)
    rect = surf.get_rect(**(anchor or {"topleft": (0, 0)}))
    screen.blit(surf, rect)
    return rect


def text_shadow(screen, msg, size, color=TEXT, bold=True, **anchor):
    """Text with a dark outline so it stays readable on busy backgrounds.
    Large text (titles) uses the engraved display font from the title art."""
    display = size >= 40
    surf = _rendered(str(msg), size, color, bold, display)
    shadow = _rendered(str(msg), size, (6, 10, 24), bold, display)
    rect = surf.get_rect(**anchor)
    # small text gets a thin outline (a thick one smears the letters together)
    k = 1 if size < 24 else 2
    for dx, dy in ((-k, 0), (k, 0), (0, -k), (0, k), (-k, -k), (k, -k), (-k, k), (k, k)):
        screen.blit(shadow, rect.move(dx, dy))
    screen.blit(surf, rect)
    return rect


def wrap(msg, size, width, bold=False):
    f = assets.font(size, bold)
    lines, line = [], ""
    for word in str(msg).split():
        trial = f"{line} {word}".strip()
        if f.size(trial)[0] <= width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def text_wrapped(screen, msg, size, rect, color=TEXT, bold=False, line_gap=4, center=False):
    y = rect.top
    for line in wrap(msg, size, rect.width, bold):
        if center:
            text(screen, line, size, color, bold, midtop=(rect.centerx, y))
        else:
            text(screen, line, size, color, bold, topleft=(rect.left, y))
        y += assets.font(size, bold).get_linesize() + line_gap - 4
    return y


def _themed(color):
    """Screens pass older grey tones; turn neutral greys into the matching night blue."""
    r, g, b = color[:3]
    if max(r, g, b) - min(r, g, b) < 30:
        v = (r + g + b) / 3
        return (int(v * 0.45), int(v * 0.8), int(min(255, v * 1.7 + 8)))
    return color


def _themed_border(color):
    if color is None:
        return None
    r, g, b = color[:3]
    if max(r, g, b) - min(r, g, b) < 30:       # grey border -> gold, dimmer for darker greys
        k = 0.35 + 0.5 * (r / 255)
        return tuple(int(c * k) + 12 for c in PANEL_BORDER)
    return color


def _gradient(size, top, bottom, alpha=255):
    w, h = size
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        t = y / max(1, h - 1)
        c = [int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)]
        pygame.draw.line(surf, (*c, alpha), (0, y), (w, y))
    return surf


def _diamond(screen, center, r, color, outline=GOLD_DARK):
    x, y = center
    pts = [(x, y - r), (x + r, y), (x, y + r), (x - r, y)]
    pygame.draw.polygon(screen, color, pts)
    pygame.draw.polygon(screen, outline, pts, 1)


def panel(screen, rect, color=PANEL, border=PANEL_BORDER, alpha=225, radius=12):
    """A night-blue panel with a gold double frame and small gold corner gems."""
    color, border = _themed(color), _themed_border(border)
    radius = min(radius, 8)
    key = (rect.size, tuple(color), alpha, radius)
    body = _panel_cache.get(key)
    if body is None:
        if len(_panel_cache) > 400:
            _panel_cache.clear()
        top = tuple(min(255, int(c * 1.35) + 6) for c in color)
        bottom = tuple(int(c * 0.7) for c in color)
        body = _gradient(rect.size, top, bottom, alpha)
        mask = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
        body.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        _panel_cache[key] = body
    screen.blit(body, rect.topleft)
    if not border:
        return
    pygame.draw.rect(screen, (4, 8, 20), rect, 4, border_radius=radius)
    pygame.draw.rect(screen, border, rect, 2, border_radius=radius)
    if rect.width > 40 and rect.height > 40:
        inner = rect.inflate(-10, -10)
        pygame.draw.rect(screen, tuple(int(c * 0.55) for c in border), inner, 1, border_radius=max(0, radius - 3))
        if rect.width > 120 and rect.height > 80:
            for corner in (rect.topleft, rect.topright, rect.bottomleft, rect.bottomright):
                _diamond(screen, corner, 5, border)


def _button_shape(rect):
    """Banner with pointed ends, like the buttons on the title screen."""
    tip = min(16, rect.height // 3)
    return [(rect.left + tip, rect.top), (rect.right - tip, rect.top), (rect.right, rect.centery),
            (rect.right - tip, rect.bottom), (rect.left + tip, rect.bottom), (rect.left, rect.centery)]


def button(screen, rect, label, hovered=False, enabled=True, color=None, hover_color=None, size=24, selected=False,
           alpha=255):
    """Blue (or crimson) banner button with a gold frame and gem ends.
    Passing a reddish color gives the crimson "danger" style (Quit, Delete, End Turn).
    alpha < 255 makes the body see-through (the frame and label stay solid); hovering makes it solid."""
    red = color is not None and color[0] > color[1] + 30 and color[0] > color[2] + 30
    if not enabled:
        fill = BUTTON_DISABLED
    elif selected:
        fill = SELECTED
    elif red:
        fill = BUTTON_RED_HOVER if hovered else BUTTON_RED
    else:
        fill = BUTTON_HOVER if hovered else BUTTON
    lit = enabled and (hovered or selected)

    pts = _button_shape(rect)
    key = ("button", rect.size, tuple(fill), lit, alpha)
    body = _panel_cache.get(key)
    if body is None:
        top = tuple(min(255, int(c * 1.5) + 12) for c in fill)
        bottom = tuple(int(c * 0.6) for c in fill)
        body = _gradient(rect.size, top, bottom, 255 if lit else alpha)
        mask = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.polygon(mask, (255, 255, 255, 255), [(x - rect.x, y - rect.y) for x, y in pts])
        body.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        if lit:   # warm shine along the top edge
            shine = _gradient((rect.width, rect.height // 2), (70, 60, 36), (0, 0, 0), 255)
            body.blit(shine, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        _panel_cache[key] = body
    screen.blit(body, rect.topleft)

    frame = GOLD_LIGHT if lit else (GOLD if enabled else (92, 84, 70))
    pygame.draw.polygon(screen, (4, 8, 20), pts, 5)
    pygame.draw.polygon(screen, frame, pts, 2)
    inner = _button_shape(rect.inflate(-10, -10))
    pygame.draw.polygon(screen, tuple(int(c * 0.6) for c in frame), inner, 1)
    if rect.width >= 120:
        _diamond(screen, (rect.left + 1, rect.centery), 5, frame)
        _diamond(screen, (rect.right - 1, rect.centery), 5, frame)

    color_txt = (GOLD_LIGHT if lit else TEXT) if enabled else (120, 120, 132)
    f = assets.font(size, True)
    while f.size(str(label))[0] > rect.width - 30 and size > 12:
        size -= 1
        f = assets.font(size, True)
    surf = f.render(str(label), True, color_txt)
    shadow = f.render(str(label), True, (4, 8, 20))
    r = surf.get_rect(center=rect.center)
    screen.blit(shadow, r.move(1, 2))
    screen.blit(surf, r)


def dim(screen, alpha=150):
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((2, 6, 20, alpha))
    screen.blit(overlay, (0, 0))


# --- Combat widgets --------------------------------------------------------
def health_bar(screen, x, y, entity, width=220, height=22, shown_hp=None):
    """HP bar with a trailing 'recent damage' segment and a Block badge."""
    hp = entity.current_hp if shown_hp is None else shown_hp
    pygame.draw.rect(screen, HP_BACK, (x, y, width, height), border_radius=5)
    if hp > entity.current_hp:  # trailing white chunk for damage just taken
        pygame.draw.rect(screen, (235, 225, 200), (x, y, width * min(1, hp / entity.max_hp), height), border_radius=5)
    ratio = max(0, entity.current_hp / entity.max_hp)
    if ratio > 0:
        color = BLOCK_BLUE if entity.block else HP_GREEN
        pygame.draw.rect(screen, color, (x, y, max(6, width * ratio), height), border_radius=5)
    pygame.draw.rect(screen, (240, 240, 240), (x, y, width, height), 2, border_radius=5)
    text_shadow(screen, f"{entity.current_hp}/{entity.max_hp}", 16, center=(x + width // 2, y + height // 2))
    if entity.block:
        shield_icon(screen, (x - 4, y + height // 2), 15, entity.block)


def shield_icon(screen, center, r, value=None):
    cx, cy = center
    pts = [(cx - r, cy - r), (cx + r, cy - r), (cx + r, cy), (cx, cy + r + 4), (cx - r, cy)]
    pygame.draw.polygon(screen, BLOCK_BLUE, pts)
    pygame.draw.polygon(screen, (230, 240, 255), pts, 2)
    if value is not None:
        text_shadow(screen, value, 15, center=(cx, cy - 1))


def check_icon(screen, center, r, color=(140, 230, 140)):
    cx, cy = center
    pts = [(cx - r, cy), (cx - r // 3, cy + r * 2 // 3), (cx + r, cy - r * 2 // 3)]
    pygame.draw.lines(screen, (0, 0, 0), False, pts, 7)
    pygame.draw.lines(screen, color, False, pts, 4)


def sword_icon(screen, center, r):
    cx, cy = center
    pygame.draw.line(screen, (230, 230, 240), (cx - r, cy + r), (cx + r, cy - r), 5)
    pygame.draw.line(screen, (150, 110, 60), (cx - r + 2, cy + r - 10), (cx - r + 10, cy + r - 2), 5)
    pygame.draw.line(screen, (240, 70, 60), (cx - r, cy + r), (cx + r, cy - r), 2)


def intent_icon(screen, kind, center, r=16):
    cx, cy = center
    if kind == "attack":
        sword_icon(screen, center, r)
    elif kind == "defend":
        shield_icon(screen, center, r - 2)
    elif kind == "heal":
        pygame.draw.rect(screen, (70, 200, 90), (cx - 5, cy - r, 10, r * 2), border_radius=2)
        pygame.draw.rect(screen, (70, 200, 90), (cx - r, cy - 5, r * 2, 10), border_radius=2)
    elif kind == "buff":
        pygame.draw.polygon(screen, (240, 90, 70), [(cx, cy - r), (cx + r, cy + 2), (cx + 6, cy + 2),
                                                    (cx + 6, cy + r), (cx - 6, cy + r), (cx - 6, cy + 2), (cx - r, cy + 2)])
    elif kind == "debuff":
        pygame.draw.circle(screen, (170, 90, 220), (cx, cy + 4), r - 4)
        pygame.draw.polygon(screen, (170, 90, 220), [(cx - r + 5, cy + 1), (cx + r - 5, cy + 1), (cx, cy - r)])
        pygame.draw.circle(screen, (230, 200, 255), (cx - 4, cy + 3), 3)


def status_row(screen, entity, x, y):
    """Small colored badges for each active status. Returns list of (rect, name) for tooltips."""
    hits = []
    for name, stacks in entity.statuses.items():
        info = STATUS_INFO.get(name, {"color": (200, 200, 200)})
        rect = pygame.Rect(x, y, 34, 24)
        pygame.draw.rect(screen, (20, 20, 28), rect, border_radius=6)
        pygame.draw.rect(screen, info["color"], rect, 2, border_radius=6)
        text(screen, name[:2].title(), 13, info["color"], True, midleft=(rect.x + 4, rect.centery))
        text(screen, stacks, 13, TEXT, True, midright=(rect.right - 4, rect.centery))
        hits.append((rect, name))
        x += 38
    return hits


def energy_orb(screen, center, current, maximum):
    t = pygame.time.get_ticks() / 400
    r = 30 + (2 * math.sin(t) if current else 0)
    pygame.draw.circle(screen, (20, 40, 70), center, r + 4)
    pygame.draw.circle(screen, ENERGY if current else (60, 70, 90), center, r)
    pygame.draw.circle(screen, (220, 240, 255), center, r, 3)
    text_shadow(screen, f"{current}/{maximum}", 24, center=center)


def tooltip(screen, lines, pos, width=280, size=17, alpha=245):
    """Tooltip box near pos that stays on-screen. lines: list of (text, color)."""
    wrapped = []
    for msg, color in lines:
        wrapped += [(l, color) for l in wrap(msg, size, width - 20)]
    step = size + 5
    h = 14 + step * len(wrapped)
    rect = pygame.Rect(0, 0, width, h)
    rect.bottomleft = (pos[0] + 12, pos[1] - 8)
    rect.clamp_ip(screen.get_rect())
    panel(screen, rect, (8, 18, 44), GOLD, alpha, 6)
    y = rect.y + 7
    for msg, color in wrapped:
        text_shadow(screen, msg, size, color, False, topleft=(rect.x + 10, y)) if alpha < 200 else             text(screen, msg, size, color, topleft=(rect.x + 10, y))
        y += step


# --- Items -------------------------------------------------------------------
ITEM_COLORS = {"Helmet": (150, 170, 200), "Armor": (120, 150, 190), "Weapon": (210, 200, 180),
               "Shield": (190, 150, 90), "Wings": (240, 150, 90)}


def item_icon(screen, item, rect):
    """Draws an item's art (items/<name>.png) scaled into rect, or a simple drawn icon for its type."""
    art = assets.load_icon(item.icon_path, (rect.width - 8, rect.height - 8)) if item.icon_path else None
    if art:
        screen.blit(art, art.get_rect(center=rect.center))
        return
    type_icon(screen, item.type, rect, ITEM_COLORS.get(item.type, TEXT), glow=item.tier > 0)


def type_icon(screen, item_type, rect, color, glow=False):
    """Simple shape for an item type (also used for empty slots, in a dim color)."""
    cx, cy = rect.center
    r = min(rect.width, rect.height) * 0.32
    dark = tuple(int(c * 0.55) for c in color)
    if item_type == "Helmet":
        pygame.draw.ellipse(screen, color, (cx - r, cy - r, r * 2, r * 1.6))
        pygame.draw.rect(screen, color, (cx - r, cy - r * 0.2, r * 2, r * 0.9))
        pygame.draw.rect(screen, dark, (cx - r * 0.8, cy - r * 0.05, r * 1.6, r * 0.25))
    elif item_type == "Armor":
        pts = [(cx - r, cy - r * 0.8), (cx - r * 0.35, cy - r), (cx, cy - r * 0.7), (cx + r * 0.35, cy - r),
               (cx + r, cy - r * 0.8), (cx + r * 0.7, cy - r * 0.2), (cx + r * 0.6, cy + r), (cx - r * 0.6, cy + r),
               (cx - r * 0.7, cy - r * 0.2)]
        pygame.draw.polygon(screen, color, pts)
        pygame.draw.line(screen, dark, (cx, cy - r * 0.6), (cx, cy + r), 2)
    elif item_type == "Weapon":
        if glow:
            pygame.draw.line(screen, (255, 220, 120), (cx - r, cy + r), (cx + r, cy - r), 9)
        pygame.draw.line(screen, color, (cx - r, cy + r), (cx + r, cy - r), 5)
        pygame.draw.line(screen, dark, (cx - r * 0.75, cy + r * 0.25), (cx - r * 0.25, cy + r * 0.75), 5)
    elif item_type == "Shield":
        pts = [(cx - r, cy - r), (cx + r, cy - r), (cx + r, cy), (cx, cy + r * 1.2), (cx - r, cy)]
        pygame.draw.polygon(screen, color, pts)
        pygame.draw.polygon(screen, dark, pts, 3)
        pygame.draw.line(screen, dark, (cx, cy - r), (cx, cy + r * 1.1), 3)
    elif item_type == "Wings":
        for side in (-1, 1):
            pts = [(cx, cy), (cx + side * r * 1.2, cy - r), (cx + side * r * 1.1, cy - r * 0.2),
                   (cx + side * r * 0.9, cy + r * 0.5)]
            pygame.draw.polygon(screen, color, pts)
            pygame.draw.polygon(screen, dark, pts, 2)


def dim_rect(screen, rect, alpha=150):
    overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
    overlay.fill((0, 0, 0, alpha))
    screen.blit(overlay, rect.topleft)
