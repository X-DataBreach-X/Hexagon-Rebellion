"""The hexagon player."""

import math

import arcade

PLAYER_RADIUS = 56       # Center to corner, in pixels
PLAYER_SPEED = 400       # Pixels per second

BODY_COLOR = (255, 255, 255)     # White (placeholder until character design)


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
