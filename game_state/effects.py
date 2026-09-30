"""Small visual effects for skills: fire, ice, poison, arcane, holy, slashes, Block, healing and buffs.

skill_effects() looks at what a skill does (its element, damage, hits, Block, heal and status effects)
and returns the effects to play. CombatState updates and draws them.
"""
import math
import random

import pygame

FIRE = [(255, 120, 40), (255, 190, 60), (255, 70, 30)]
ICE = [(170, 230, 255), (230, 250, 255), (120, 200, 255)]
POISON = [(110, 220, 80), (70, 160, 60), (160, 240, 110)]
ARCANE = [(190, 120, 255), (230, 180, 255), (140, 90, 230)]
HOLY = [(255, 230, 120), (255, 250, 200), (255, 210, 90)]
BLOCK = (90, 150, 230)
HEAL = (90, 230, 100)


def _layer(w, h):
    return pygame.Surface((max(1, int(w)), max(1, int(h))), pygame.SRCALPHA)


class FX:
    """Base effect. `delay` postpones it (for staggered hits); p is progress from 0 to 1."""
    def __init__(self, life, delay=0):
        self.life = self.max_life = life
        self.delay = delay

    @property
    def alive(self):
        return self.life > 0

    def update(self, dt):
        if self.delay > 0:
            self.delay -= dt
            return
        self.life -= dt
        self.step(dt)

    def step(self, dt):
        pass

    def draw(self, screen):
        if self.delay <= 0 and self.life > 0:
            self.render(screen, 1 - self.life / self.max_life)

    def render(self, screen, p):
        pass


class Particle(FX):
    def __init__(self, pos, vel, life, color, size, shape="glow", gravity=0.0, delay=0):
        super().__init__(life, delay)
        self.x, self.y = pos
        self.vx, self.vy = vel
        self.color, self.size, self.shape, self.gravity = color, size, shape, gravity

    def step(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt

    def render(self, screen, p):
        a = int(255 * (1 - p) ** 0.7)
        r = self.size
        s = _layer(r * 4 + 4, r * 4 + 4)
        c = r * 2 + 2
        col = (*self.color, a)
        if self.shape == "glow":
            pygame.draw.circle(s, (*self.color, a // 3), (c, c), int(r * 1.8))
            pygame.draw.circle(s, col, (c, c), max(1, int(r * (1 - p * 0.5))))
        elif self.shape == "shard":
            ang = math.atan2(self.vy, self.vx)
            ux, uy = math.cos(ang), math.sin(ang)
            pts = [(c + ux * r * 1.8, c + uy * r * 1.8), (c - uy * r * 0.6, c + ux * r * 0.6),
                   (c - ux * r * 1.2, c - uy * r * 1.2), (c + uy * r * 0.6, c - ux * r * 0.6)]
            pygame.draw.polygon(s, col, pts)
        elif self.shape == "spark":
            ang = math.atan2(self.vy, self.vx)
            pygame.draw.line(s, col, (c, c), (c - math.cos(ang) * r * 2.5, c - math.sin(ang) * r * 2.5), 3)
            pygame.draw.circle(s, (255, 255, 255, a), (c, c), max(1, r // 2))
        elif self.shape == "cross":
            t = max(2, r // 2)
            pygame.draw.rect(s, col, (c - r, c - t // 2, r * 2, t))
            pygame.draw.rect(s, col, (c - t // 2, c - r, t, r * 2))
        elif self.shape == "up":
            pygame.draw.polygon(s, col, [(c, c - r * 1.4), (c + r, c + r * 0.2), (c + r * 0.35, c + r * 0.2),
                                         (c + r * 0.35, c + r * 1.2), (c - r * 0.35, c + r * 1.2),
                                         (c - r * 0.35, c + r * 0.2), (c - r, c + r * 0.2)])
        elif self.shape == "down":
            pygame.draw.polygon(s, col, [(c, c + r * 1.4), (c + r, c - r * 0.2), (c + r * 0.35, c - r * 0.2),
                                         (c + r * 0.35, c - r * 1.2), (c - r * 0.35, c - r * 1.2),
                                         (c - r * 0.35, c - r * 0.2), (c - r, c - r * 0.2)])
        screen.blit(s, (self.x - c, self.y - c))


class Ring(FX):
    def __init__(self, pos, r0, r1, color, width=6, life=420, delay=0, squash=1.0):
        super().__init__(life, delay)
        self.pos, self.r0, self.r1, self.color, self.width = pos, r0, r1, color, width
        self.squash = squash

    def render(self, screen, p):
        ease = 1 - (1 - p) ** 2
        r = self.r0 + (self.r1 - self.r0) * ease
        s = _layer(r * 2 + 16, r * 2 + 16)
        a = int(255 * (1 - p))
        c = r + 8
        pygame.draw.circle(s, (*self.color, a // 3), (c, c), int(r), max(2, int(self.width * 2.2 * (1 - p))))
        pygame.draw.circle(s, (*self.color, a), (c, c), int(r), max(1, int(self.width * (1 - p))))
        if self.squash != 1.0:
            s = pygame.transform.smoothscale(s, (s.get_width(), max(1, int(s.get_height() * self.squash))))
            c_y = c * self.squash
        else:
            c_y = c
        screen.blit(s, (self.pos[0] - c, self.pos[1] - c_y))


class Pillar(FX):
    """A column of light coming down onto a spot."""
    def __init__(self, pos, color, height=380, width=80, life=600):
        super().__init__(life)
        self.pos, self.color, self.height, self.width = pos, color, height, width

    def render(self, screen, p):
        grow = min(1, p * 5)
        w = self.width * (1 - max(0, p - 0.3) / 0.7 * 0.8)
        a = 1 - max(0, p - 0.3) / 0.7
        h = int(self.height * grow)
        s = _layer(w + 4, h)
        for i in range(0, h, 6):
            fade = 0.35 + 0.65 * (i / max(1, h))
            pygame.draw.rect(s, (*self.color, int(120 * a * fade)), (0, i, w, 6))
            pygame.draw.rect(s, (255, 255, 255, int(200 * a * fade)), (w * 0.3, i, w * 0.4, 6))
        screen.blit(s, (self.pos[0] - w / 2, self.pos[1] - h))


class Slash(FX):
    """A curved blade streak."""
    def __init__(self, pos, start_deg, span_deg, radius, color=(255, 255, 255), life=260, delay=0):
        super().__init__(life, delay)
        self.pos, self.start, self.span, self.radius, self.color = pos, start_deg, span_deg, radius, color

    def render(self, screen, p):
        head = min(1.0, p * 2.0)
        tail = max(0.0, p * 2.0 - 0.7)
        if tail >= 1:
            return
        R = self.radius
        s = _layer(R * 2 + 30, R * 2 + 30)
        c = R + 15
        n = 14
        pts = []
        for i in range(n + 1):
            u = tail + (head - tail) * i / n
            ang = math.radians(self.start + self.span * u)
            pts.append((c + math.cos(ang) * R, c + math.sin(ang) * R))
        a = int(255 * (1 - p ** 2))
        if len(pts) > 1:
            pygame.draw.lines(s, (*self.color, a // 3), False, pts, 16)
            pygame.draw.lines(s, (*self.color, a), False, pts, 6)
            pygame.draw.lines(s, (255, 255, 255, a), False, pts, 2)
        screen.blit(s, (self.pos[0] - c, self.pos[1] - c))


class Lightning(FX):
    def __init__(self, target, color=(215, 170, 255), life=240, delay=0):
        super().__init__(life, delay)
        self.target, self.color = target, color
        self.points = []
        self.timer = 0
        self.top = (target[0] + random.randint(-70, 70), target[1] - 330)

    def zap(self):
        (x0, y0), (x1, y1) = self.top, self.target
        self.points = [(x0 + (x1 - x0) * i / 9 + (random.randint(-26, 26) if 0 < i < 9 else 0),
                        y0 + (y1 - y0) * i / 9) for i in range(10)]

    def step(self, dt):
        self.timer -= dt
        if self.timer <= 0 or not self.points:
            self.timer = 50
            self.zap()

    def render(self, screen, p):
        if len(self.points) < 2 or p > 0.85:
            return
        pygame.draw.lines(screen, self.color, False, self.points, 9)
        pygame.draw.lines(screen, (245, 235, 255), False, self.points, 4)
        pygame.draw.lines(screen, (255, 255, 255), False, self.points, 2)


class Orbit(FX):
    """Sparkles spiralling up around a spot (wind, energy, vortex)."""
    def __init__(self, pos, colors, n=16, radius=55, life=1000, rise=120, turns=2.0, delay=0):
        super().__init__(life, delay)
        self.pos, self.colors, self.n, self.radius, self.rise, self.turns = pos, colors, n, radius, rise, turns

    def render(self, screen, p):
        for i in range(self.n):
            frac = (p * 1.3 + i / self.n) % 1
            ang = i * 2.4 + p * self.turns * math.tau
            x = self.pos[0] + math.cos(ang) * self.radius * (0.6 + 0.4 * math.sin(frac * math.pi))
            y = self.pos[1] + 55 - self.rise * frac + math.sin(ang) * self.radius * 0.25
            a = int(255 * math.sin(frac * math.pi) * (1 - p ** 3))
            r = 5
            s = _layer(r * 4, r * 4)
            col = self.colors[i % len(self.colors)]
            pygame.draw.circle(s, (*col, a // 3), (r * 2, r * 2), r * 2)
            pygame.draw.circle(s, (*col, a), (r * 2, r * 2), r)
            screen.blit(s, (x - r * 2, y - r * 2))


class Crack(FX):
    """Jagged cracks spreading from a spot (armor breaking)."""
    def __init__(self, pos, color=(255, 235, 170), n=7, length=85, life=600):
        super().__init__(life)
        self.pos, self.color = pos, color
        self.lines = []
        for i in range(n):
            ang = i * math.tau / n + random.uniform(-0.25, 0.25)
            pts = []
            for k in range(6):
                d = length * k / 5 * random.uniform(0.85, 1.1)
                a2 = ang + random.uniform(-0.3, 0.3)
                pts.append((math.cos(a2) * d, math.sin(a2) * d))
            self.lines.append(pts)

    def render(self, screen, p):
        grow = min(1.0, p * 4)
        a = int(255 * (1 - max(0, p - 0.45) / 0.55))
        s = _layer(260, 260)
        for pts in self.lines:
            n = max(2, int(len(pts) * grow) + 1)
            line = [(130 + x, 130 + y) for x, y in pts[:n]]
            pygame.draw.lines(s, (*self.color, a // 2), False, line, 6)
            pygame.draw.lines(s, (255, 255, 255, a), False, line, 2)
        screen.blit(s, (self.pos[0] - 130, self.pos[1] - 130))


class Streak(FX):
    """A fast straight streak (a thrust)."""
    def __init__(self, start, end, color, life=220, width=9, delay=0):
        super().__init__(life, delay)
        self.start, self.end, self.color, self.width = start, end, color, width

    def render(self, screen, p):
        head = min(1.0, p * 2.5)
        tail = max(0.0, p * 2.5 - 1.0)
        a = (self.start[0] + (self.end[0] - self.start[0]) * tail, self.start[1] + (self.end[1] - self.start[1]) * tail)
        b = (self.start[0] + (self.end[0] - self.start[0]) * head, self.start[1] + (self.end[1] - self.start[1]) * head)
        w = max(1, int(self.width * (1 - p)))
        pygame.draw.line(screen, self.color, a, b, w * 2)
        pygame.draw.line(screen, (255, 255, 255), a, b, max(1, w // 2))


class Wall(FX):
    """Stone slabs rising from the ground (Iron Wall)."""
    def __init__(self, pos, life=900, height=120):
        super().__init__(life)
        self.pos, self.height = pos, height

    def render(self, screen, p):
        rise = min(1.0, p * 5)
        rise = 1 - (1 - rise) ** 3
        a = int(255 * (1 - max(0, p - 0.6) / 0.4))
        h = int(self.height * rise)
        s = _layer(130, self.height + 10)
        for i, dh in enumerate((0.8, 1.0, 0.85)):
            hh = int(h * dh)
            x = 6 + i * 40
            pygame.draw.rect(s, (110, 116, 132, a), (x, self.height - hh, 36, hh), border_radius=4)
            pygame.draw.rect(s, (170, 178, 196, a), (x, self.height - hh, 36, 8), border_radius=4)
            pygame.draw.rect(s, (60, 64, 78, a), (x, self.height - hh, 36, hh), 2, border_radius=4)
        screen.blit(s, (self.pos[0] - 62, self.pos[1] + 60 - self.height))


class Sigil(FX):
    """A rotating magic circle (Hex, Mana Shield)."""
    def __init__(self, pos, color, sides=5, radius=80, squash=1.0, life=800, delay=0):
        super().__init__(life, delay)
        self.pos, self.color, self.sides, self.radius, self.squash = pos, color, sides, radius, squash

    def render(self, screen, p):
        R = self.radius
        a = int(255 * math.sin(min(1.0, p * 1.15) * math.pi) ** 0.6)
        s = _layer(R * 2 + 20, R * 2 + 20)
        c = R + 10
        pygame.draw.circle(s, (*self.color, a), (c, c), R, 3)
        pygame.draw.circle(s, (*self.color, a // 2), (c, c), int(R * 0.72), 2)
        rot = p * 2.2
        pts = [(c + math.cos(rot + i * math.tau / self.sides) * R * 0.95,
                c + math.sin(rot + i * math.tau / self.sides) * R * 0.95) for i in range(self.sides)]
        step = 2 if self.sides % 2 else 1
        for i in range(self.sides):
            pygame.draw.line(s, (*self.color, a), pts[i], pts[(i + step) % self.sides], 2)
        if self.squash != 1.0:
            s = pygame.transform.smoothscale(s, (s.get_width(), max(1, int(s.get_height() * self.squash))))
        screen.blit(s, (self.pos[0] - s.get_width() / 2, self.pos[1] - s.get_height() / 2))


class Rays(FX):
    """Beams of light spreading out from a spot (Radiance)."""
    def __init__(self, pos, color, n=14, length=190, life=800):
        super().__init__(life)
        self.pos, self.color, self.n, self.length = pos, color, n, length

    def render(self, screen, p):
        a = int(230 * math.sin(p * math.pi))
        L = self.length * min(1.0, p * 3 + 0.2)
        s = _layer(L * 2 + 10, L * 2 + 10)
        c = L + 5
        for i in range(self.n):
            ang = i * math.tau / self.n + p * 0.6
            w = 0.06
            pts = [(c, c), (c + math.cos(ang - w) * L, c + math.sin(ang - w) * L),
                   (c + math.cos(ang + w) * L, c + math.sin(ang + w) * L)]
            pygame.draw.polygon(s, (*self.color, a // 2), pts)
        pygame.draw.circle(s, (255, 255, 255, a), (c, c), int(30 * (1 - p * 0.5)))
        screen.blit(s, (self.pos[0] - c, self.pos[1] - c))


def _burst(pos, n, colors, speed, life, size, shape, gravity=0.0, delay=0, spread=1.0):
    out = []
    for _ in range(n):
        ang = random.uniform(0, math.tau)
        v = random.uniform(speed * 0.4, speed)
        out.append(Particle((pos[0] + random.randint(-8, 8), pos[1] + random.randint(-8, 8)),
                            (math.cos(ang) * v, math.sin(ang) * v * spread), random.randint(*life),
                            random.choice(colors), random.randint(*size), shape, gravity, delay))
    return out


def _rising(pos, n, colors, life, size, shape, width=60, vy=(-0.2, -0.05), delay=0, gravity=0.0):
    return [Particle((pos[0] + random.randint(-width, width), pos[1] + random.randint(-20, 50)),
                     (random.uniform(-0.03, 0.03), random.uniform(*vy)), random.randint(*life),
                     random.choice(colors), random.randint(*size), shape, gravity, delay + random.randint(0, 200))
            for _ in range(n)]


def _ground(pos, dy=70):
    return pos[0], pos[1] + dy


def _fire_hit(t, big=1.0):
    fx = _burst(t, int(20 * big), FIRE, 0.22 * big, (400, 800), (4, int(8 * big)), "glow", gravity=-0.0002)
    fx += _rising(t, int(10 * big), FIRE, (500, 900), (4, 8), "glow", vy=(-0.3, -0.1))
    fx.append(Ring(t, 10, 100 * big, FIRE[0], 8))
    return fx


def _ice_hit(t):
    return (_burst(t, 16, ICE, 0.4, (500, 800), (4, 7), "shard", gravity=0.0004)
            + [Ring(t, 10, 95, ICE[0], 7), Ring(t, 5, 60, ICE[1], 4, delay=90)])


def _holy_hit(t):
    return ([Pillar((t[0], t[1] + 60), HOLY[0]), Ring((t[0], t[1] + 60), 10, 90, HOLY[2], 6)]
            + _rising(t, 12, HOLY, (600, 1000), (5, 9), "cross", vy=(-0.18, -0.06)))


def _heavy_strike(c, t):
    fx = [Slash(t, -125, 150, 135, life=340), Ring(_ground(t), 10, 130, (255, 230, 180), 8, squash=0.32, delay=140),
          Ring(_ground(t), 5, 80, (255, 255, 255), 4, squash=0.32, delay=170)]
    fx += _burst(_ground(t, 60), 14, [(190, 170, 140), (230, 210, 170)], 0.32, (350, 650), (3, 6), "glow",
                 gravity=0.0007, delay=140, spread=0.7)
    return fx


def _sunder(c, t):
    fx = [Slash(t, -60, 130, 100), Crack(t)]
    fx += _burst(t, 12, [(200, 200, 215), (255, 235, 170)], 0.3, (400, 700), (3, 6), "shard", gravity=0.0006, delay=120)
    return fx


def _battle_cry(c, t):
    return [Ring(c, 20, 210, (255, 140, 70), 8, life=600, delay=i * 150) for i in range(3)]


def _venom_stab(c, t):
    fx = [Streak((t[0] - 130, t[1] + 6), (t[0] + 60, t[1] - 4), POISON[0]),
          Streak((t[0] - 110, t[1] - 10), (t[0] + 40, t[1] + 10), (230, 255, 210), delay=70, width=6)]
    fx += _rising(t, 12, POISON, (700, 1100), (5, 10), "glow", width=40, vy=(-0.08, -0.02), delay=120)
    return fx


def _whirlwind(c, t):
    fx = [Slash(t, 200 + i * 120, 220, 90, delay=i * 120) for i in range(3)]
    fx.append(Orbit(c, [(235, 235, 245), (200, 210, 230)], n=18, radius=70, life=700, rise=90, turns=3.0))
    return fx


def _flame_slash(c, t):
    return [Slash(t, -70, 140, 100, FIRE[1])] + _fire_hit(t, 0.8)


def _frost_edge(c, t):
    return [Slash(t, -70, 140, 100, ICE[0])] + _ice_hit(t)


def _holy_blade(c, t):
    return [Slash(t, -70, 140, 100, HOLY[0])] + _holy_hit(t)


def _twin_cut(c, t):
    return [Slash(t, -55, 110, 90), Slash(t, 235, -110, 90, delay=130)]


def _second_wind(c, t):
    return [Orbit(c, [(190, 255, 190), (255, 255, 255), HEAL], n=16, radius=48, life=1100, rise=130, turns=2.5)]


def _shield_bash(c, t):
    fx = [Particle(t, (0, 0), 240, (255, 240, 200), 30, "glow"), Ring(t, 10, 80, (255, 230, 170), 8, life=300)]
    fx += _burst(t, 14, [(255, 240, 200), (255, 210, 120)], 0.42, (250, 450), (3, 5), "spark")
    return fx


def _parry(c, t):
    front = (c[0] + 55, c[1] - 10)
    fx = _burst(front, 14, [(255, 245, 210), (255, 220, 120)], 0.4, (200, 400), (3, 5), "spark")
    fx.append(Particle(front, (0, 0), 200, (255, 255, 255), 22, "glow"))
    return fx


def _iron_wall(c, t):
    return [Wall((c[0] + 70, c[1]))]


def _fireball(c, t):
    return _fire_hit(t, 1.5) + [Particle(t, (0, 0), 260, (255, 230, 150), 42, "glow")]


def _ice_lance(c, t):
    return _ice_hit(t) + _burst(t, 10, ICE, 0.5, (400, 700), (5, 8), "shard", gravity=0.0005)


def _meteor(c, t):
    fx = _fire_hit(t, 2.0)
    fx += [Particle(t, (0, 0), 320, (255, 240, 180), 60, "glow"),
           Ring(_ground(t), 10, 180, (255, 160, 60), 10, squash=0.32, life=600),
           Ring(_ground(t), 5, 120, (255, 220, 120), 5, squash=0.32, life=500, delay=80)]
    fx += _burst(_ground(t, 50), 18, [(90, 60, 45), (150, 100, 60), FIRE[1]], 0.4, (500, 900), (3, 7), "glow",
                 gravity=0.0008, spread=0.8)
    return fx


def _frost_nova(c, t):
    fx = [Ring(c, 20, 330, ICE[0], 10, life=650), Ring(c, 10, 240, ICE[1], 5, life=650, delay=90)]
    fx += _burst(c, 22, ICE, 0.55, (500, 900), (4, 7), "shard", gravity=0.0003)
    fx += _ice_hit(t)
    return fx


def _hex(c, t):
    fx = [Sigil(_ground(t, 60), ARCANE[0], 5, 90, squash=0.4, life=900), Sigil(t, ARCANE[1], 5, 70, life=700, delay=100)]
    fx += _rising(t, 8, [ARCANE[2], (60, 30, 90)], (700, 1000), (6, 10), "glow", vy=(-0.1, -0.03))
    return fx


def _arcane_surge(c, t):
    return [Orbit(c, ARCANE, n=20, radius=52, life=1100, rise=140, turns=3.0), Ring(c, 14, 90, ARCANE[0], 6)]


def _heal(c, t):
    return [Pillar((c[0], c[1] + 60), HEAL, life=800)]


def _radiance(c, t):
    return [Rays(c, HOLY[0], life=900), Ring(c, 20, 150, HOLY[2], 6, life=700)]


def _mana_shield(c, t):
    return [Sigil(c, ARCANE[0], 6, 82, life=900), Ring(c, 30, 95, BLOCK, 6)]


# name -> animation. Skills not listed use the generic effect for their element.
SPECIAL = {
    "Heavy Strike": _heavy_strike, "Sunder": _sunder, "Battle Cry": _battle_cry, "Venom Stab": _venom_stab,
    "Whirlwind": _whirlwind, "Flame Slash": _flame_slash, "Frost Edge": _frost_edge, "Holy Blade": _holy_blade,
    "Twin Cut": _twin_cut, "Second Wind": _second_wind, "Shield Bash": _shield_bash, "Parry": _parry,
    "Iron Wall": _iron_wall, "Fireball": _fireball, "Ice Lance": _ice_lance, "Meteor": _meteor,
    "Frost Nova": _frost_nova, "Hex": _hex, "Arcane Surge": _arcane_surge, "Heal": _heal,
    "Radiance": _radiance, "Mana Shield": _mana_shield,
}


def skill_effects(skill, caster, target, slash=False):
    """Effects for `skill` used by the fighter at `caster` on the fighter at `target` (body centres).
    slash=True adds blade streaks for a physical strike (the Swordsman and melee enemies)."""
    fx = []
    hits = max(1, skill.hits)
    special = SPECIAL.get(skill.name.rstrip("+"))
    if special:
        fx += special(caster, target)
    elif skill.damage or skill.effects:
        el = skill.element
        if slash and skill.damage:
            if skill.name.startswith("Whirlwind"):
                fx += [Slash(target, 200 + i * 120, 220, 90, delay=i * 120) for i in range(hits)]
            else:
                fx += [Slash(target, -70 if i % 2 == 0 else 250, 140 if i % 2 == 0 else -140, 100,
                             delay=i * 110) for i in range(hits)]
        if el == "fire":
            fx += _burst(target, 20, FIRE, 0.22, (400, 800), (4, 8), "glow", gravity=-0.0002)
            fx += _rising(target, 10, FIRE, (500, 900), (4, 8), "glow", vy=(-0.3, -0.1))
            fx.append(Ring(target, 10, 100, FIRE[0], 8))
        elif el == "ice":
            fx += _burst(target, 16, ICE, 0.4, (500, 800), (4, 7), "shard", gravity=0.0004)
            fx += [Ring(target, 10, 95, ICE[0], 7), Ring(target, 5, 60, ICE[1], 4, delay=90)]
        elif el == "poison":
            fx += _rising(target, 18, POISON, (900, 1300), (7, 14), "glow", width=55, vy=(-0.12, -0.03))
            fx.append(Ring(target, 8, 80, POISON[0], 6))
        elif el == "arcane":
            if skill.name.startswith("Chain Lightning"):
                fx += [Lightning((target[0] + random.randint(-25, 25), target[1]), delay=i * 140) for i in range(hits)]
                fx += _burst(target, 14, ARCANE, 0.35, (300, 500), (3, 5), "spark", delay=0)
            else:
                for i in range(hits):
                    fx += _burst(target, 12, ARCANE, 0.35, (350, 600), (3, 5), "spark", delay=i * 120)
                fx.append(Ring(target, 8, 90, ARCANE[0], 6))
        elif el == "holy":
            fx.append(Pillar((target[0], target[1] + 60), HOLY[0]))
            fx += _rising(target, 12, HOLY, (600, 1000), (5, 9), "cross", vy=(-0.18, -0.06))
            fx.append(Ring((target[0], target[1] + 60), 10, 90, HOLY[2], 6))
        elif not slash and skill.damage:
            fx += _burst(target, 10, [(255, 240, 200), (255, 210, 120)], 0.3, (250, 450), (3, 5), "spark")
    if skill.effects:
        if "weak" in skill.effects:
            fx += _rising((target[0], target[1] - 60), 6, [(170, 170, 210)], (700, 1000), (5, 8), "down",
                          vy=(0.03, 0.1), delay=150)
        if "vulnerable" in skill.effects and skill.name.rstrip("+") != "Hex":
            fx.append(Ring(target, 8, 70, (230, 80, 200), 5, delay=120))
            fx += _burst(target, 8, [(230, 80, 200), (255, 150, 230)], 0.25, (400, 600), (3, 5), "shard", delay=120)
    if skill.block:
        fx += [Ring(caster, 24, 88, BLOCK, 8), Ring(caster, 14, 70, (170, 210, 255), 4, delay=80)]
        fx += _burst(caster, 8, [BLOCK, (170, 210, 255)], 0.2, (300, 500), (3, 5), "glow")
    if skill.heal:
        fx += _rising(caster, 10, [HEAL, (170, 255, 170)], (800, 1200), (5, 8), "cross", vy=(-0.16, -0.05))
        fx.append(Ring(caster, 10, 70, HEAL, 5))
    if skill.self_effects:
        color = [(255, 90, 60), (255, 170, 80)] if skill.element == "physical" else \
            {"fire": FIRE, "ice": ICE, "poison": POISON, "arcane": ARCANE, "holy": HOLY}[skill.element]
        fx += _rising(caster, 10, color, (800, 1200), (6, 9), "up", vy=(-0.2, -0.08))
        fx.append(Ring(caster, 14, 80, color[0], 5))
    return fx
