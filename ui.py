"""Shared colors and drawing helpers used by every screen."""
import math

import pygame

import assets
from character.entity import STATUS_INFO

# --- Palette ---------------------------------------------------------------
BG = (24, 24, 34)
PANEL = (18, 18, 26)
PANEL_BORDER = (110, 100, 80)
BUTTON = (62, 62, 84)
BUTTON_HOVER = (92, 92, 124)
BUTTON_DISABLED = (38, 38, 48)
SELECTED = (70, 120, 80)
TEXT = (240, 240, 240)
TEXT_DIM = (160, 160, 175)
GOLD = (235, 195, 90)
RED = (200, 55, 55)
HP_GREEN = (60, 185, 70)
HP_BACK = (90, 28, 28)
BLOCK_BLUE = (90, 150, 230)
ENERGY = (90, 190, 255)


def text(screen, msg, size, color=TEXT, bold=False, **anchor):
    """Draws text. Pass an anchor like center=(x, y) or topleft=(x, y). Returns the rect."""
    surf = assets.font(size, bold).render(str(msg), True, color)
    rect = surf.get_rect(**(anchor or {"topleft": (0, 0)}))
    screen.blit(surf, rect)
    return rect


def text_shadow(screen, msg, size, color=TEXT, bold=True, **anchor):
    """Text with a dark outline so it stays readable on busy backgrounds."""
    f = assets.font(size, bold)
    surf = f.render(str(msg), True, color)
    shadow = f.render(str(msg), True, (0, 0, 0))
    rect = surf.get_rect(**anchor)
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
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


def panel(screen, rect, color=PANEL, border=PANEL_BORDER, alpha=225, radius=12):
    surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(surf, (*color, alpha), surf.get_rect(), border_radius=radius)
    screen.blit(surf, rect.topleft)
    if border:
        pygame.draw.rect(screen, border, rect, 2, border_radius=radius)


def button(screen, rect, label, hovered=False, enabled=True, color=None, hover_color=None, size=24, selected=False):
    if not enabled:
        fill = BUTTON_DISABLED
    elif selected:
        fill = SELECTED
    elif hovered:
        fill = hover_color or BUTTON_HOVER
    else:
        fill = color or BUTTON
    pygame.draw.rect(screen, fill, rect, border_radius=10)
    pygame.draw.rect(screen, GOLD if (hovered and enabled) or selected else (200, 200, 210), rect, 2, border_radius=10)
    text(screen, label, size, TEXT if enabled else TEXT_DIM, True, center=rect.center)


def dim(screen, alpha=150):
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, alpha))
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


def tooltip(screen, lines, pos, width=280):
    """Tooltip box near pos that stays on-screen. lines: list of (text, color)."""
    wrapped = []
    for msg, color in lines:
        wrapped += [(l, color) for l in wrap(msg, 17, width - 20)]
    h = 16 + 22 * len(wrapped)
    rect = pygame.Rect(0, 0, width, h)
    rect.bottomleft = (pos[0] + 12, pos[1] - 8)
    rect.clamp_ip(screen.get_rect())
    panel(screen, rect, (12, 12, 18), GOLD, 240, 8)
    y = rect.y + 8
    for msg, color in wrapped:
        text(screen, msg, 17, color, topleft=(rect.x + 10, y))
        y += 22
