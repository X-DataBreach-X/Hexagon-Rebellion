"""Triangle enemies: shiny purple triangles that swarm around the player.

Each triangle is drawn as smooth, sharp-edged shapes (like the hexagon), cut
into three facets of different purples so it looks like a gem, with a shine
that sweeps across it every so often. It spins at a speed that keeps
changing, from very slow to very fast.

Movement: each triangle has its own orbit around the player (distance,
direction and speed), plus a slow random drift, so together they swarm
around the player like bees. They steer toward that moving spot rather than
jumping there, and push away from each other so they don't pile up.

Every so often, a triangle near the player fires a purple laser bolt at
them. Bolts fly straight, like bullets.

When hit, a triangle explodes into tiny purple shards that spin across the
floor, slow down and fade away.
"""

import math
import random

import arcade

SIZE = 24                      # Center to corner, in pixels
RADIUS = 22                    # How close a shot has to come to hit, in pixels

# Facet colors, going around from the facet beside the tip.
FACET_COLORS = [(185, 115, 240), (140, 60, 200), (95, 35, 150)]
SHINE_COLOR = (235, 205, 255, 210)
SHINE_CORE = (255, 255, 255)
SHINE_WIDTH = 5                # Half-width of the shine band, in pixels
SHINE_CORE_WIDTH = 1.5
SHINE_DURATION = 0.35          # Seconds for the shine to sweep across
SHINE_EVERY = (1.2, 2.6)       # Seconds between shines
SHINE_DIRECTION = math.radians(-35)   # Which way the band sweeps, relative to the triangle

SPIN_RANGE = (0.3, 14.0)       # Radians per second, from very slow to very fast
SPIN_CHANGE_EVERY = (1.0, 4.0)  # Seconds between picking a new spin speed
SPIN_EASING = 1.5              # How quickly the spin speed changes

ORBIT_DISTANCE = (240, 360)    # Pixels from the player
ORBIT_SPEED = (0.35, 0.9)      # Radians per second around the player
WANDER_DISTANCE = 70           # How far the random drift can pull it off its orbit
MAX_SPEED = 380                # Pixels per second
STEERING = 3.0                 # How strongly it heads for its spot
TURNING = 4.0                  # How quickly its velocity can change
SEPARATION = 80                # Triangles closer than this push apart
SEPARATION_PUSH = 3.0          # How hard they push apart (compared to MAX_SPEED)

FIRE_EVERY = (1.5, 3.5)        # Seconds between shots
FIRE_RANGE = 700               # Only fires when the player is this close
BOLT_SPEED = 420               # Pixels per second (slow enough to dodge)
BOLT_LIFE = 3.0                # Seconds before a missed bolt disappears
BOLT_LENGTH = 20
BOLT_GLOW = (190, 80, 255, 110)
BOLT_CORE = (240, 200, 255)

SHARD_COUNT = (12, 16)
SHARD_SPEED = (150, 480)
SHARD_LIFE = (1.5, 3.0)
SHARD_SIZE = (3, 8)            # Center to corner, in pixels
SHARD_SPIN = 12                # Radians per second, at most
SHARD_FRICTION = 1.6           # How quickly shards slow down
SHARD_COLORS = [*FACET_COLORS, (225, 190, 255)]


def _clip(polygon, nx, ny, limit):
    """The part of a polygon where (x * nx + y * ny) <= limit (one side of a line)."""
    result = []
    for i, (x1, y1) in enumerate(polygon):
        x2, y2 = polygon[(i + 1) % len(polygon)]
        d1, d2 = x1 * nx + y1 * ny - limit, x2 * nx + y2 * ny - limit
        if d1 <= 0:
            result.append((x1, y1))
        if (d1 < 0) != (d2 < 0):
            t = d1 / (d1 - d2)
            result.append((x1 + (x2 - x1) * t, y1 + (y2 - y1) * t))
    return result


def _band(polygon, nx, ny, center, half_width):
    """The part of a polygon inside a straight band (a strip between two parallel lines)."""
    inside = _clip(polygon, nx, ny, center + half_width)
    return _clip(inside, -nx, -ny, -(center - half_width))


class Triangle:
    def __init__(self, x, y):
        self.x, self.y = x, y
        # Burst out of the spawner in a random direction.
        burst = random.uniform(0, 2 * math.pi)
        self.velocity_x = math.cos(burst) * MAX_SPEED
        self.velocity_y = math.sin(burst) * MAX_SPEED

        self.angle = random.uniform(0, 2 * math.pi)
        self.spin_direction = random.choice((-1, 1))
        self.spin = self.spin_target = random.uniform(*SPIN_RANGE)
        self.spin_timer = random.uniform(*SPIN_CHANGE_EVERY)

        self.orbit_distance = random.uniform(*ORBIT_DISTANCE)
        self.orbit_speed = random.uniform(*ORBIT_SPEED) * random.choice((-1, 1))
        self.orbit_angle = random.uniform(0, 2 * math.pi)
        self.wander = [random.uniform(0.3, 1.0) for _ in range(2)]   # Drift speeds
        self.wander_phase = [random.uniform(0, 2 * math.pi) for _ in range(2)]

        self.time = 0.0
        self.fire_timer = random.uniform(*FIRE_EVERY)
        self.shine_timer = random.uniform(*SHINE_EVERY)
        self.shine_time = None   # Seconds into the current shine, or None

    def update(self, delta_time, player, others, bounds):
        self.time += delta_time
        self._update_spin(delta_time)
        self._update_shine(delta_time)

        # The spot to head for: on its orbit around the player, plus its drift.
        self.orbit_angle += self.orbit_speed * delta_time
        target_x = (player.x + math.cos(self.orbit_angle) * self.orbit_distance
                    + math.sin(self.time * self.wander[0] + self.wander_phase[0]) * WANDER_DISTANCE)
        target_y = (player.y + math.sin(self.orbit_angle) * self.orbit_distance
                    + math.cos(self.time * self.wander[1] + self.wander_phase[1]) * WANDER_DISTANCE)

        # Steer: aim for the spot (no faster than MAX_SPEED), away from crowding neighbors.
        want_x, want_y = (target_x - self.x) * STEERING, (target_y - self.y) * STEERING
        for other in others:
            if other is self:
                continue
            dx, dy = self.x - other.x, self.y - other.y
            distance = math.hypot(dx, dy)
            if 0 < distance < SEPARATION:
                push = (SEPARATION - distance) / SEPARATION * MAX_SPEED * SEPARATION_PUSH
                want_x += dx / distance * push
                want_y += dy / distance * push
        speed = math.hypot(want_x, want_y)
        if speed > MAX_SPEED:
            want_x, want_y = want_x / speed * MAX_SPEED, want_y / speed * MAX_SPEED
        turn = min(1.0, delta_time * TURNING)
        self.velocity_x += (want_x - self.velocity_x) * turn
        self.velocity_y += (want_y - self.velocity_y) * turn

        left, bottom, right, top = bounds
        self.x = min(max(self.x + self.velocity_x * delta_time, left + RADIUS), right - RADIUS)
        self.y = min(max(self.y + self.velocity_y * delta_time, bottom + RADIUS), top - RADIUS)

    def fire(self, delta_time, player):
        """Count down to the next shot. Returns a new Bolt aimed at the player, or None."""
        self.fire_timer -= delta_time
        if self.fire_timer > 0:
            return None
        self.fire_timer = random.uniform(*FIRE_EVERY)
        dx, dy = player.x - self.x, player.y - self.y
        distance = math.hypot(dx, dy)
        if distance > FIRE_RANGE or distance == 0:
            return None
        # Leave from the triangle's edge, heading straight at the player.
        aim_x, aim_y = dx / distance, dy / distance
        return Bolt(self.x + aim_x * SIZE, self.y + aim_y * SIZE, aim_x, aim_y)

    def _update_spin(self, delta_time):
        # Every so often pick a new spin speed, then ease toward it.
        self.spin_timer -= delta_time
        if self.spin_timer <= 0:
            self.spin_timer = random.uniform(*SPIN_CHANGE_EVERY)
            self.spin_target = random.uniform(*SPIN_RANGE)
        self.spin += (self.spin_target - self.spin) * min(1.0, delta_time * SPIN_EASING)
        self.angle += self.spin * self.spin_direction * delta_time

    def _update_shine(self, delta_time):
        if self.shine_time is not None:
            self.shine_time += delta_time
            if self.shine_time >= SHINE_DURATION:
                self.shine_time = None
        else:
            self.shine_timer -= delta_time
            if self.shine_timer <= 0:
                self.shine_timer = random.uniform(*SHINE_EVERY)
                self.shine_time = 0.0

    def corners(self):
        """The three corners, starting with the tip, going counterclockwise."""
        return [(self.x + math.cos(self.angle + i * 2 * math.pi / 3) * SIZE,
                 self.y + math.sin(self.angle + i * 2 * math.pi / 3) * SIZE)
                for i in range(3)]

    def draw(self):
        corners = self.corners()
        # Three facets, each from the center to one side, in different purples.
        for i, color in enumerate(FACET_COLORS):
            arcade.draw_triangle_filled(self.x, self.y, *corners[i], *corners[(i + 1) % 3], color)

        if self.shine_time is not None:
            # A band of light, sweeping across from one side to the other,
            # cut to the triangle's exact shape.
            direction = self.angle + SHINE_DIRECTION
            nx, ny = math.cos(direction), math.sin(direction)
            local = [(x - self.x, y - self.y) for x, y in corners]
            progress = self.shine_time / SHINE_DURATION
            center = -SIZE + progress * 2 * SIZE
            for half_width, color in ((SHINE_WIDTH, SHINE_COLOR), (SHINE_CORE_WIDTH, SHINE_CORE)):
                band = _band(local, nx, ny, center, half_width)
                if len(band) >= 3:
                    arcade.draw_polygon_filled([(self.x + x, self.y + y) for x, y in band], color)


class Bolt:
    """A purple laser bolt fired by a triangle. It flies straight, like a bullet."""

    def __init__(self, x, y, direction_x, direction_y):
        self.x, self.y = x, y
        self.last_x, self.last_y = x, y   # Where it was last frame (so it can't skip past)
        self.velocity_x, self.velocity_y = direction_x * BOLT_SPEED, direction_y * BOLT_SPEED
        self.time_left = BOLT_LIFE

    def update(self, delta_time):
        self.last_x, self.last_y = self.x, self.y
        self.x += self.velocity_x * delta_time
        self.y += self.velocity_y * delta_time
        self.time_left -= delta_time

    @property
    def alive(self):
        return self.time_left > 0

    def hits(self, x, y, radius):
        """Did this bolt's path since last frame pass within radius of (x, y)?"""
        dx, dy = self.x - self.last_x, self.y - self.last_y
        length_squared = dx * dx + dy * dy
        t = 0.0 if length_squared == 0 else (
            ((x - self.last_x) * dx + (y - self.last_y) * dy) / length_squared)
        t = min(1.0, max(0.0, t))
        return math.hypot(x - (self.last_x + t * dx), y - (self.last_y + t * dy)) <= radius

    def draw(self):
        tail_x = self.x - self.velocity_x / BOLT_SPEED * BOLT_LENGTH
        tail_y = self.y - self.velocity_y / BOLT_SPEED * BOLT_LENGTH
        arcade.draw_line(tail_x, tail_y, self.x, self.y, BOLT_GLOW, 8)
        arcade.draw_line(tail_x, tail_y, self.x, self.y, BOLT_CORE, 3)


class Shard:
    """A tiny purple triangle from an exploded triangle, spinning off and fading out."""

    def __init__(self, x, y):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(*SHARD_SPEED)
        self.x, self.y = x, y
        self.velocity_x, self.velocity_y = math.cos(angle) * speed, math.sin(angle) * speed
        self.life = self.time_left = random.uniform(*SHARD_LIFE)
        self.size = random.uniform(*SHARD_SIZE)
        self.color = random.choice(SHARD_COLORS)
        self.angle = random.uniform(0, 2 * math.pi)
        self.spin = random.uniform(-SHARD_SPIN, SHARD_SPIN)

    def update(self, delta_time):
        slow = max(0.0, 1 - SHARD_FRICTION * delta_time)
        self.velocity_x *= slow
        self.velocity_y *= slow
        self.spin *= slow
        self.x += self.velocity_x * delta_time
        self.y += self.velocity_y * delta_time
        self.angle += self.spin * delta_time
        self.time_left -= delta_time

    @property
    def alive(self):
        return self.time_left > 0

    def draw(self):
        # A thin, pointy triangle (a sliver), fading out near the end.
        alpha = int(255 * min(1.0, self.time_left / self.life * 2))
        points = [(self.x + math.cos(self.angle + a) * self.size * stretch,
                   self.y + math.sin(self.angle + a) * self.size * stretch)
                  for a, stretch in ((0, 1.4), (2.3, 0.8), (-2.3, 0.8))]
        arcade.draw_polygon_filled(points, (*self.color, alpha))


def explode(triangle):
    """The shards a triangle breaks into."""
    return [Shard(triangle.x, triangle.y) for _ in range(random.randint(*SHARD_COUNT))]
