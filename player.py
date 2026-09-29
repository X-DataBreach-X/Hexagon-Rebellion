"""The hexagon player."""

import math

import arcade

PLAYER_RADIUS = 56       # Center to corner, in pixels
PLAYER_SPEED = 400       # Pixels per second

BODY_COLOR = (38, 56, 104)       # Navy blue
OUTLINE_COLOR = (0, 0, 0)
OUTLINE_WIDTH = 3
EYE_COLOR = (0, 0, 0)
EYE_WIDTH = 4
EYE_DEPTH = 0.65   # How far the eyes sit from the center toward the sides (0-1)


class Player:
    """A hexagon that moves with WASD and always faces the mouse."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0.0  # Facing direction in radians (0 = right, counterclockwise)

    def _corners(self):
        # The first corner points straight at the facing direction, and the
        # rest follow every 60 degrees around.
        return [
            (
                self.x + PLAYER_RADIUS * math.cos(self.angle + math.radians(60 * i)),
                self.y + PLAYER_RADIUS * math.sin(self.angle + math.radians(60 * i)),
            )
            for i in range(6)
        ]

    def face(self, target_x, target_y):
        """Turn to face a point in the world (e.g. the mouse)."""
        if (target_x, target_y) != (self.x, self.y):
            self.angle = math.atan2(target_y - self.y, target_x - self.x)

    def move(self, dx, dy, delta_time, world_width, world_height):
        """Move in direction (dx, dy), staying inside the world."""
        length = math.hypot(dx, dy)
        if length:
            # Normalize so diagonal movement isn't faster than straight.
            self.x += dx / length * PLAYER_SPEED * delta_time
            self.y += dy / length * PLAYER_SPEED * delta_time
        self.x = min(max(self.x, PLAYER_RADIUS), world_width - PLAYER_RADIUS)
        self.y = min(max(self.y, PLAYER_RADIUS), world_height - PLAYER_RADIUS)

    def draw(self):
        corners = self._corners()
        arcade.draw_polygon_filled(corners, BODY_COLOR)
        arcade.draw_polygon_outline(corners, OUTLINE_COLOR, OUTLINE_WIDTH)
        self._draw_eyes()

    def _draw_eyes(self):
        """Two short lines parallel to the two sides next to the front corner.

        Each eye is 1/3 the length of a side, sits EYE_DEPTH of the way from
        the center out to its side, and is slid toward the back so its rear
        end lines up with the side's back corner (the one away from the mouse).
        (A regular hexagon's side length equals its radius, and the
        center-to-side distance is radius * cos(30).)
        """
        eye_length = PLAYER_RADIUS / 3
        distance = PLAYER_RADIUS * math.cos(math.radians(30)) * EYE_DEPTH
        for side_offset in (-30, 30):
            # Direction from the center straight out to the middle of the side.
            toward_side = self.angle + math.radians(side_offset)
            # The side runs perpendicular to that direction. Its back corner is
            # half a side length from the middle, on the side away from the front.
            along = toward_side + math.copysign(math.pi / 2, side_offset)
            back = PLAYER_RADIUS / 2
            front = back - eye_length

            base_x = self.x + distance * math.cos(toward_side)
            base_y = self.y + distance * math.sin(toward_side)
            arcade.draw_line(base_x + back * math.cos(along), base_y + back * math.sin(along),
                             base_x + front * math.cos(along), base_y + front * math.sin(along),
                             EYE_COLOR, EYE_WIDTH)
