"""The hexagon player."""

import math

import arcade

from character_design import design as shared_design

PLAYER_RADIUS = 56       # Center to corner, in pixels
PLAYER_SPEED = 400       # Pixels per second
# How close a shot has to come to hit: the distance from the center to the
# middle of a side (a bit inside the corners, so near-misses at a corner miss).
HIT_RADIUS = PLAYER_RADIUS * math.cos(math.radians(30))
MAX_HEALTH = 100
HURT_FLASH = 0.15        # Seconds the hexagon flashes red after being hurt
HURT_COLOR = (255, 40, 40, 150)

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
        self.health = MAX_HEALTH
        self.flash = 0.0  # Seconds left of the red "hurt" flash

    def hurt(self, amount):
        self.health = max(0, self.health - amount)
        self.flash = HURT_FLASH

    @property
    def alive(self):
        return self.health > 0

    def update(self, delta_time):
        self.flash = max(0.0, self.flash - delta_time)

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
                                        self.design.fills[portion].color)

        # Borders go on top of all the fills so neighbors don't cover them.
        for portion, (a, b) in PORTION_CORNERS.items():
            for side, (start, end) in self._portion_edges(corners[a], corners[b]).items():
                border = self.design.borders[portion][side]
                if border.enabled and border.length > 0 and border.thickness > 0:
                    self._draw_border(start, end, border)

        if self.flash > 0:
            arcade.draw_polygon_filled(corners, HURT_COLOR)

    def _portion_edges(self, corner_a, corner_b):
        """The bottom, left and right edges of the portion between two corners.

        Picture the triangle with its outer edge at the bottom and its point
        (the hexagon's center) at the top. Seen that way, "right" is the
        outward direction turned 90 degrees counterclockwise.
        """
        center = (self.x, self.y)
        outward_x = (corner_a[0] + corner_b[0]) / 2 - self.x
        outward_y = (corner_a[1] + corner_b[1]) / 2 - self.y
        right_x, right_y = -outward_y, outward_x
        a_is_right = (corner_a[0] - self.x) * right_x + (corner_a[1] - self.y) * right_y > 0
        right, left = (corner_a, corner_b) if a_is_right else (corner_b, corner_a)
        return {"bottom": (corner_a, corner_b), "left": (center, left), "right": (center, right)}

    @staticmethod
    def _draw_border(start, end, border):
        """A line along an edge, shortened from both ends to border.length of it."""
        mid_x, mid_y = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
        half_x = (end[0] - start[0]) / 2 * border.length
        half_y = (end[1] - start[1]) / 2 * border.length
        arcade.draw_line(mid_x - half_x, mid_y - half_y, mid_x + half_x, mid_y + half_y,
                         border.color, border.thickness)
