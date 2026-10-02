"""Triangle spawners: pixel-art black holes that the triangle enemies come out of.

Each spawner is a swirling black hole drawn as pixel art (one image per
animation frame, drawn scaled up with pixelated filtering), with white
pixel particles streaming out of it.

Picture of the swirl: every art pixel's color comes from its distance and
angle from the center. Spiral arms are bands where (angle + twist * distance)
lines up; shifting that by a phase each frame makes the arms turn.
"""

import math
import random

import arcade
from PIL import Image

ART_SIZE = 33                # Art pixels across (odd, so there's a center pixel)
PIXEL = 4                    # Screen pixels per art pixel
FRAMES = 12                  # Frames for the swirl to turn one arm's width
FRAME_TIME = 0.06            # Seconds per frame
ARMS = 3
TWIST = 0.45                 # How tightly the arms spiral
CORE_RADIUS = 5              # Pure black center, in art pixels
RIM_RADIUS = 16              # Where the swirl fades out
TOUCH_RADIUS = (RIM_RADIUS - 3) * PIXEL   # Screen pixels: the solid part of the swirl

# Swirl colors, from the dark gaps between arms to the brightest part of an arm.
SWIRL_COLORS = [(12, 6, 22), (34, 18, 54), (62, 38, 96), (98, 70, 140)]
RING_COLOR = (170, 140, 220)   # Faint edge of the black center

PARTICLE_RATE = 14           # Particles per second
PARTICLE_SPEED = (45, 95)    # Pixels per second, outward
PARTICLE_SPIN = 60           # Sideways speed (pixels per second), so particles curve with the swirl
PARTICLE_LIFE = (1.2, 2.2)   # Seconds


def _swirl_frame(phase):
    """One frame of the black hole at a given swirl phase (radians)."""
    image = Image.new("RGBA", (ART_SIZE, ART_SIZE), (0, 0, 0, 0))
    center = ART_SIZE / 2
    for row in range(ART_SIZE):
        for column in range(ART_SIZE):
            dx, dy = column + 0.5 - center, center - (row + 0.5)
            r = math.hypot(dx, dy)
            if r > RIM_RADIUS:
                continue
            if r <= CORE_RADIUS:
                image.putpixel((column, row), (0, 0, 0, 255))
                continue
            if r <= CORE_RADIUS + 1:
                image.putpixel((column, row), (*RING_COLOR, 255))
                continue

            # How much this pixel is on a spiral arm (0-1), dimmer toward the rim.
            angle = math.atan2(dy, dx)
            arm = (math.sin(ARMS * angle + TWIST * r * ARMS - phase) + 1) / 2
            fade = 1 - (r - CORE_RADIUS) / (RIM_RADIUS - CORE_RADIUS)
            level = arm * (0.35 + 0.65 * fade)
            # A few flat color steps (instead of a smooth blend) keep it pixel-art.
            color = SWIRL_COLORS[min(len(SWIRL_COLORS) - 1, int(level * len(SWIRL_COLORS)))]
            # The outer edge is see-through so it melts into the floor.
            alpha = 255 if r < RIM_RADIUS - 3 else int(255 * (RIM_RADIUS - r) / 3)
            image.putpixel((column, row), (*color, alpha))
    return image


class Spawner:
    _frames = None   # Shared by every spawner

    def __init__(self, x, y):
        if Spawner._frames is None:
            # One arm's width is 2*pi/ARMS of phase; spread the frames across it.
            Spawner._frames = [
                arcade.Texture(_swirl_frame(n / FRAMES * 2 * math.pi), hash=f"spawner-{n}")
                for n in range(FRAMES)
            ]
        self.x, self.y = x, y
        self.time = random.uniform(0, 10)   # So the spawners don't swirl in sync
        self.particles = []   # [x, y, velocity x, velocity y, seconds left, total life, size]
        self.particle_timer = 0.0

    def update(self, delta_time):
        self.time += delta_time

        self.particle_timer -= delta_time
        while self.particle_timer <= 0:
            self.particle_timer += 1 / PARTICLE_RATE
            self._emit()

        for p in self.particles:
            p[0] += p[2] * delta_time
            p[1] += p[3] * delta_time
            p[4] -= delta_time
        self.particles = [p for p in self.particles if p[4] > 0]

    def _emit(self):
        """A particle leaving the edge of the black center, curving with the swirl."""
        angle = random.uniform(0, 2 * math.pi)
        start = (CORE_RADIUS + 1) * PIXEL
        out_x, out_y = math.cos(angle), math.sin(angle)
        speed = random.uniform(*PARTICLE_SPEED)
        life = random.uniform(*PARTICLE_LIFE)
        size = random.choice((1, 1, 2)) * PIXEL
        self.particles.append([
            self.x + out_x * start, self.y + out_y * start,
            out_x * speed - out_y * PARTICLE_SPIN, out_y * speed + out_x * PARTICLE_SPIN,
            life, life, size,
        ])

    def draw(self):
        texture = self._frames[int(self.time / FRAME_TIME) % FRAMES]
        size = ART_SIZE * PIXEL
        arcade.draw_texture_rect(texture, arcade.XYWH(self.x, self.y, size, size),
                                 pixelated=True)

        for x, y, _, _, left, life, size in self.particles:
            # Snap to the art-pixel grid so particles stay blocky, and fade out.
            gx, gy = round(x / PIXEL) * PIXEL, round(y / PIXEL) * PIXEL
            alpha = int(255 * min(1.0, left / life * 1.5))
            arcade.draw_rect_filled(arcade.XYWH(gx, gy, size, size), (255, 255, 255, alpha))
