"""The player's weapons: their pixel art, idle animations and firing effects.

Each weapon is pixel art, drawn pixel by pixel in code into small images
(one image per animation frame). The images are drawn scaled up with
pixelated filtering, so every art pixel becomes a crisp block on screen.
In the art, the weapon points right (+x, out of the muzzle).

In the player's "hand", the weapon sits off the hexagon's right side and
points exactly the way the hexagon faces, so shots travel parallel to the
hexagon's front.

Hold the left mouse button to fire. Each weapon's hits() checks whether its
shots touch something (a circle); beams hit everything along them, bullets
are used up by what they hit.
"""

import math
import random

import arcade
from PIL import Image, ImageDraw

from player import PLAYER_RADIUS

HELD_PIXEL = 4          # Screen pixels per art pixel in the player's hand
# Where the weapon is held: off the hexagon's right side, a little forward.
HOLD_SIDE = PLAYER_RADIUS * math.cos(math.radians(30)) + 26
HOLD_FORWARD = 8


def _texture(image, name):
    return arcade.Texture(image, hash=f"weapon-{name}")


def _distance_to_segment(px, py, ax, ay, bx, by):
    """Distance from point p to the line segment from a to b."""
    dx, dy = bx - ax, by - ay
    length_squared = dx * dx + dy * dy
    t = 0.0 if length_squared == 0 else ((px - ax) * dx + (py - ay) * dy) / length_squared
    t = min(1.0, max(0.0, t))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


class Weapon:
    NAME = ""
    # Where the weapon is held, and where shots come out, in art pixels
    # (from the image's top-left corner).
    ORIGIN = (0.0, 0.0)
    MUZZLE_X = 0.0

    def __init__(self):
        self.time = 0.0
        self.firing = False
        # Where it's being held and which way it points (set by aim()).
        self.x = self.y = self.angle = 0.0

    def aim(self, player):
        """Hold the weapon beside the player, pointing the same way the player faces."""
        self.angle = facing = player.angle
        right_x, right_y = math.sin(facing), -math.cos(facing)
        self.x = player.x + right_x * HOLD_SIDE + math.cos(facing) * HOLD_FORWARD
        self.y = player.y + right_y * HOLD_SIDE + math.sin(facing) * HOLD_FORWARD

    def muzzle(self):
        reach = (self.MUZZLE_X - self.ORIGIN[0]) * HELD_PIXEL
        return self.x + math.cos(self.angle) * reach, self.y + math.sin(self.angle) * reach

    def update(self, delta_time):
        self.time += delta_time

    def frame(self):
        """The texture for the current moment of the animation."""
        raise NotImplementedError

    def draw_held(self):
        self.draw(self.x, self.y, self.angle, HELD_PIXEL)

    def draw(self, x, y, angle, pixel):
        """Draw with the weapon's ORIGIN at (x, y), pointing at angle (radians)."""
        texture = self.frame()
        # Offset from the origin to the image's center, turned to the weapon's angle.
        # (Image rows count down, which is the weapon's right side.)
        forward = (texture.width / 2 - self.ORIGIN[0]) * pixel
        left = (self.ORIGIN[1] - texture.height / 2) * pixel
        cx = x + forward * math.cos(angle) - left * math.sin(angle)
        cy = y + forward * math.sin(angle) + left * math.cos(angle)
        arcade.draw_texture_rect(
            texture, arcade.XYWH(cx, cy, texture.width * pixel, texture.height * pixel),
            angle=-math.degrees(angle),   # Arcade turns clockwise for positive angles
            pixelated=True,
        )

    def draw_centered(self, cx, cy, pixel):
        """Draw pointing right with the image centered on (cx, cy), e.g. in an Armory box."""
        texture = self.frame()
        arcade.draw_texture_rect(
            texture, arcade.XYWH(cx, cy, texture.width * pixel, texture.height * pixel),
            pixelated=True)

    def draw_effects(self):
        """Draw shots (beams, bullets). Called before draw_held, so the gun sits on top."""

    def hits(self, x, y, radius):
        """Do this weapon's shots touch the circle at (x, y)?"""
        return False

    def _beam_hits(self, length, width, x, y, radius):
        """For straight beams: is the circle within the beam from the muzzle?"""
        if not self.firing:
            return False
        sx, sy = self.muzzle()
        ex, ey = sx + math.cos(self.angle) * length, sy + math.sin(self.angle) * length
        return _distance_to_segment(x, y, sx, sy, ex, ey) <= radius + width / 2


# ----- 1. Electric orb -----

ORB_SIZE = 17
ORB_FRAMES = 10
ORB_FRAME_TIME = 0.07
ORB_GLOW = (120, 200, 255)
SPARK_COLOR = (215, 245, 255)
BOLT_RANGE = 560
BOLT_SEGMENTS = 18
BOLT_JITTER = 14
BOLT_REFRESH = 0.035   # Seconds between new bolt shapes (the flicker)


def _orb_frames():
    """Crackling orb frames: a glowing ball with random sparks and arcs."""
    rng = random.Random(7)   # Same frames every run
    center = ORB_SIZE / 2
    frames = []
    for n in range(ORB_FRAMES):
        image = Image.new("RGBA", (ORB_SIZE, ORB_SIZE), (0, 0, 0, 0))
        for row in range(ORB_SIZE):
            for column in range(ORB_SIZE):
                d = math.hypot(column + 0.5 - center, row + 0.5 - center)
                if d <= 1.5:
                    color = (255, 255, 255, 255)
                elif d <= 3:
                    color = (220, 245, 255, 255)
                elif d <= 5:
                    color = (150, 220, 255, 255)
                elif d <= 6.5:
                    color = (*ORB_GLOW, 150)
                elif d <= 8:
                    color = (*ORB_GLOW, 60)
                else:
                    continue
                image.putpixel((column, row), color)

        draw = ImageDraw.Draw(image)
        # Two jagged arcs crackling across the ball.
        for _ in range(2):
            angle = rng.uniform(0, 2 * math.pi)
            points = []
            for step in range(4):
                r = rng.uniform(2, 7)
                a = angle + step * 0.6
                points.append((center + math.cos(a) * r, center - math.sin(a) * r))
            draw.line(points, fill=(*SPARK_COLOR, 255), width=1)
        # Sparkles around the edge.
        for _ in range(3):
            a = rng.uniform(0, 2 * math.pi)
            r = rng.uniform(6.5, 8)
            image.putpixel((min(ORB_SIZE - 1, int(center + math.cos(a) * r)),
                            min(ORB_SIZE - 1, int(center - math.sin(a) * r))),
                           (255, 255, 255, 255))
        frames.append(_texture(image, f"orb-{n}"))
    return frames


class ElectricOrb(Weapon):
    NAME = "Electric Orb"
    ORIGIN = (ORB_SIZE / 2, ORB_SIZE / 2)
    MUZZLE_X = ORB_SIZE / 2   # Lightning comes from the middle of the ball
    _frames = None

    def __init__(self):
        super().__init__()
        if ElectricOrb._frames is None:
            ElectricOrb._frames = _orb_frames()
        self.bolts = []
        self.bolt_timer = 0.0

    def frame(self):
        # Crackles faster while firing.
        speed = 2 if self.firing else 1
        return self._frames[int(self.time * speed / ORB_FRAME_TIME) % ORB_FRAMES]

    def update(self, delta_time):
        super().update(delta_time)
        self.bolt_timer -= delta_time
        if self.firing and self.bolt_timer <= 0:
            self.bolt_timer = BOLT_REFRESH
            self.bolts = self._make_bolts()
        if not self.firing:
            self.bolts = []

    def _bolt(self, start, angle, length, jitter):
        """A jagged line of points from start, heading in a direction."""
        sx, sy = start
        normal_x, normal_y = -math.sin(angle), math.cos(angle)
        points = []
        for i in range(BOLT_SEGMENTS + 1):
            t = i / BOLT_SEGMENTS
            # No wobble at the very start, the most in the middle of the bolt.
            wobble = random.uniform(-jitter, jitter) * math.sin(math.pi * t) if i else 0
            points.append((sx + math.cos(angle) * length * t + normal_x * wobble,
                           sy + math.sin(angle) * length * t + normal_y * wobble))
        return points

    def _make_bolts(self):
        main = self._bolt(self.muzzle(), self.angle, BOLT_RANGE, BOLT_JITTER)
        bolts = [main, self._bolt(self.muzzle(), self.angle, BOLT_RANGE, BOLT_JITTER * 1.6)]
        # A few forks branching off the main bolt.
        for _ in range(3):
            start = main[random.randint(3, BOLT_SEGMENTS - 3)]
            fork_angle = self.angle + random.choice((-1, 1)) * random.uniform(0.3, 0.8)
            bolts.append(self._bolt(start, fork_angle, random.uniform(40, 110), BOLT_JITTER / 2))
        return bolts

    def hits(self, x, y, radius):
        return self._beam_hits(BOLT_RANGE, BOLT_JITTER * 2, x, y, radius)

    def draw_effects(self):
        for i, bolt in enumerate(self.bolts):
            main = i == 0
            arcade.draw_line_strip(bolt, (*ORB_GLOW, 60), 18 if main else 8)
            arcade.draw_line_strip(bolt, (*ORB_GLOW, 140), 8 if main else 4)
            arcade.draw_line_strip(bolt, SPARK_COLOR, 4 if main else 2)
            if main:
                arcade.draw_line_strip(bolt, (255, 255, 255), 2)


# ----- 2. Minigun -----

MINIGUN_SIZE = (34, 11)
MINIGUN_MUZZLE = 28            # First column past the barrels (where the flash starts)
BARREL_COUNT = 6
SPIN_FRAMES = 6                # Frames for the barrels to turn one barrel's width
GUN_LIGHT = (100, 100, 108)
GUN_BODY = (72, 72, 78)
GUN_DARK = (42, 42, 47)
IDLE_SPIN = 2.5                # Barrel spin speed (radians/sec) while not firing
FIRING_SPIN = 45
FIRE_RATE = 30                 # Bullets per second
BULLET_SPEED = 1700            # Pixels per second
BULLET_LIFE = 0.35             # Seconds
BULLET_LENGTH = 22


def _minigun_image(spin_phase, flash):
    width, height = MINIGUN_SIZE
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    middle = height // 2

    # Ammo drum, body (lit on top, shaded underneath) and barrel housing.
    draw.ellipse((0, 3, 6, 10), fill=GUN_DARK)
    draw.rectangle((3, 2, 11, 8), fill=GUN_BODY)
    draw.line((3, 2, 11, 2), fill=GUN_LIGHT)
    draw.line((3, 8, 11, 8), fill=GUN_DARK)
    draw.rectangle((12, 1, 13, 9), fill=GUN_DARK)

    # Barrels around the gun's axis: each one's row is its place around the
    # circle, and the ones nearer the front are drawn later and lighter.
    barrels = []
    for i in range(BARREL_COUNT):
        phase = spin_phase + i * 2 * math.pi / BARREL_COUNT
        barrels.append((math.cos(phase), middle + round(math.sin(phase) * 3)))
    for depth, row in sorted(barrels):
        shade = int(90 + 80 * (depth + 1) / 2)
        draw.line((14, row, MINIGUN_MUZZLE - 2, row), fill=(shade, shade, shade + 6))

    draw.rectangle((19, 1, 20, 9), fill=GUN_DARK)                                # Clamp
    draw.rectangle((MINIGUN_MUZZLE - 2, 1, MINIGUN_MUZZLE - 1, 9), fill=GUN_DARK)  # Muzzle

    if flash:
        x = MINIGUN_MUZZLE
        draw.line((x, middle - 3, x + 1, middle - 3), fill=(255, 200, 60))
        draw.line((x, middle + 3, x + 1, middle + 3), fill=(255, 200, 60))
        draw.line((x, middle - 2, x + 3, middle - 2), fill=(255, 220, 90))
        draw.line((x, middle + 2, x + 3, middle + 2), fill=(255, 220, 90))
        draw.line((x, middle - 1, x + 4, middle - 1), fill=(255, 240, 150))
        draw.line((x, middle + 1, x + 4, middle + 1), fill=(255, 240, 150))
        draw.line((x, middle, width - 1, middle), fill=(255, 255, 230))
    return image


class Minigun(Weapon):
    NAME = "Minigun"
    ORIGIN = (7, MINIGUN_SIZE[1] / 2)
    MUZZLE_X = MINIGUN_MUZZLE
    _frames = None   # [flash off frames, flash on frames]

    def __init__(self):
        super().__init__()
        if Minigun._frames is None:
            Minigun._frames = [
                [_texture(_minigun_image(n / SPIN_FRAMES * 2 * math.pi / BARREL_COUNT, flash),
                          f"minigun-{n}-{flash}")
                 for n in range(SPIN_FRAMES)]
                for flash in (False, True)
            ]
        self.spin = 0.0
        self.spin_speed = IDLE_SPIN
        self.cooldown = 0.0
        # [x, y, velocity x, velocity y, seconds left, x last frame, y last frame]
        self.bullets = []

    def frame(self):
        step = 2 * math.pi / BARREL_COUNT / SPIN_FRAMES
        flash = self.firing and int(self.time * 40) % 2 == 0
        return self._frames[flash][int(self.spin / step) % SPIN_FRAMES]

    def update(self, delta_time):
        super().update(delta_time)
        # Barrels spin up while firing and wind back down after.
        target = FIRING_SPIN if self.firing else IDLE_SPIN
        self.spin_speed += (target - self.spin_speed) * min(1.0, delta_time * 4)
        self.spin += self.spin_speed * delta_time

        self.cooldown -= delta_time
        while self.firing and self.cooldown <= 0:
            self.cooldown += 1 / FIRE_RATE
            x, y = self.muzzle()
            self.bullets.append([x, y, math.cos(self.angle) * BULLET_SPEED,
                                 math.sin(self.angle) * BULLET_SPEED, BULLET_LIFE, x, y])
        if not self.firing:
            self.cooldown = max(self.cooldown, 0)

        for bullet in self.bullets:
            bullet[5], bullet[6] = bullet[0], bullet[1]
            bullet[0] += bullet[2] * delta_time
            bullet[1] += bullet[3] * delta_time
            bullet[4] -= delta_time
        self.bullets = [bullet for bullet in self.bullets if bullet[4] > 0]

    def hits(self, x, y, radius):
        """A bullet hits if its path since last frame passes through the circle; it's used up."""
        for bullet in self.bullets:
            if _distance_to_segment(x, y, bullet[5], bullet[6], bullet[0], bullet[1]) <= radius:
                self.bullets.remove(bullet)
                return True
        return False

    def draw_effects(self):
        for x, y, vx, vy, *_ in self.bullets:
            speed = math.hypot(vx, vy)
            tail_x, tail_y = x - vx / speed * BULLET_LENGTH, y - vy / speed * BULLET_LENGTH
            arcade.draw_line(tail_x, tail_y, x, y, (255, 190, 50, 150), 6)
            arcade.draw_line(tail_x, tail_y, x, y, (255, 250, 200), 2.5)


# ----- 3. Sun gun -----

SUN_GUN_SIZE = (29, 11)
SUN_GUN_MUZZLE = 27
SUN_CENTER = (7, 5)
SUN_FRAMES = 6                 # Frames for the sun to turn one ray's width
GOLD_LIGHT = (240, 205, 95)
GOLD = (205, 165, 60)
GOLD_DARK = (130, 95, 30)
SUN_COLOR = (255, 215, 50)
RAY_COLOR = (255, 240, 150)
BEAM_RANGE = 650


def _sun_gun_image(sun_phase, glowing):
    width, height = SUN_GUN_SIZE
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Gold body, then the pale barrel and its glowing tip.
    draw.rectangle((1, 2, 18, 8), fill=GOLD)
    draw.line((1, 2, 18, 2), fill=GOLD_LIGHT)
    draw.line((1, 8, 18, 8), fill=GOLD_DARK)
    draw.line((1, 2, 1, 8), fill=GOLD_DARK)
    draw.rectangle((19, 3, 25, 7), fill=(235, 230, 215))
    draw.line((19, 7, 25, 7), fill=(170, 165, 150))
    tip = (255, 255, 230) if glowing else (255, 230, 140)
    draw.line((26, 4, 26, 6), fill=tip)
    if glowing:
        image.putpixel((SUN_GUN_MUZZLE, 5), (255, 255, 255))

    # The sun: rays at a turning angle, then the disc on top.
    cx, cy = SUN_CENTER
    for i in range(8):
        a = sun_phase + i * math.pi / 4
        for r in (3.6, 4.6):
            image.putpixel((cx + round(math.cos(a) * r), cy - round(math.sin(a) * r)), RAY_COLOR)
    for row in range(cy - 3, cy + 4):
        for column in range(cx - 3, cx + 4):
            d = math.hypot(column - cx, row - cy)
            if d <= 1:
                image.putpixel((column, row), (255, 250, 210))
            elif d <= 2.5:
                image.putpixel((column, row), SUN_COLOR)
    return image


class SunGun(Weapon):
    NAME = "Sun Gun"
    ORIGIN = (9, SUN_GUN_SIZE[1] / 2)
    MUZZLE_X = SUN_GUN_MUZZLE
    _frames = None   # [not glowing, glowing]

    def __init__(self):
        super().__init__()
        if SunGun._frames is None:
            SunGun._frames = [
                [_texture(_sun_gun_image(n / SUN_FRAMES * math.pi / 4, glowing),
                          f"sun-gun-{n}-{glowing}")
                 for n in range(SUN_FRAMES)]
                for glowing in (False, True)
            ]

    def frame(self):
        # The sun spins faster while firing; the tip pulses.
        spin = self.time * (6 if self.firing else 1.5)
        step = math.pi / 4 / SUN_FRAMES
        glowing = self.firing or int(self.time * 2) % 2 == 0
        return self._frames[glowing][int(spin / step) % SUN_FRAMES]

    def hits(self, x, y, radius):
        return self._beam_hits(BEAM_RANGE, 20, x, y, radius)

    def draw_effects(self):
        if not self.firing:
            return
        sx, sy = self.muzzle()
        ex = sx + math.cos(self.angle) * BEAM_RANGE
        ey = sy + math.sin(self.angle) * BEAM_RANGE
        pulse = 1 + 0.25 * math.sin(self.time * 35)
        arcade.draw_line(sx, sy, ex, ey, (255, 190, 30, 90), 34 * pulse)
        arcade.draw_line(sx, sy, ex, ey, (255, 220, 60, 170), 20 * pulse)
        arcade.draw_line(sx, sy, ex, ey, (255, 245, 150), 11 * pulse)
        arcade.draw_line(sx, sy, ex, ey, (255, 255, 255), 5 * pulse)
        # A burst where the beam ends, and a flare at the muzzle.
        arcade.draw_circle_filled(ex, ey, 24 * pulse, (255, 210, 60, 110))
        arcade.draw_circle_filled(ex, ey, 12 * pulse, (255, 255, 230))
        arcade.draw_circle_filled(sx, sy, 14 * pulse, (255, 245, 180, 170))
        arcade.draw_circle_filled(sx, sy, 7 * pulse, (255, 255, 255))


WEAPON_TYPES = [ElectricOrb, Minigun, SunGun]


def make_weapon(index):
    return WEAPON_TYPES[index]()
