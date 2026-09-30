"""The hexagon player."""

import math

import arcade

from character_design import design as shared_design

PLAYER_RADIUS = 56       # Center to corner, in pixels
PLAYER_SPEED = 400       # Pixels per second

# The six triangles ("portions") run from the center out to one side. Each
# side is between two corners, counted counterclockwise from the front
# corner (0), which points at the mouse. With the front pointing up, corner 1
# is upper-left, so portion 1 (top-left) is between corners 0 and 1, etc.
PORTION_CORNERS = {
    1: (0, 1),  # Top left
    2: (5, 0),  # Top right
    3: (1, 2),  # Middle left
    4: (4, 5),  # Middle right
    5: (2, 3),  # Bottom left
    6: (3, 4),  # Bottom right
}


class Player:
    """A hexagon that moves with WASD and always faces the mouse."""

    def __init__(self, x, y, design=shared_design):
        self.x = x
        self.y = y
        self.design = design
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

    def move(self, dx, dy, delta_time, bounds):
        """Move in direction (dx, dy), staying inside bounds (left, bottom, right, top)."""
        length = math.hypot(dx, dy)
        if length:
            # Normalize so diagonal movement isn't faster than straight.
            self.x += dx / length * PLAYER_SPEED * delta_time
            self.y += dy / length * PLAYER_SPEED * delta_time
        left, bottom, right, top = bounds
        self.x = min(max(self.x, left + PLAYER_RADIUS), right - PLAYER_RADIUS)
        self.y = min(max(self.y, bottom + PLAYER_RADIUS), top - PLAYER_RADIUS)

    def draw(self):
        # Drawn from the design every frame, so changes show up immediately.
        corners = self._corners()
        for portion, (a, b) in PORTION_CORNERS.items():
            arcade.draw_triangle_filled(self.x, self.y, *corners[a], *corners[b],
                                        self.design.colors[portion])
