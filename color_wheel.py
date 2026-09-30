"""A pixel-art color wheel for picking colors.

The wheel is a small grid of square pixels. Going around the circle
changes the hue (red, yellow, green, ...); going from the center out
changes how strong the color is, from white in the middle to full color
at the edge.
"""

import colorsys
import math

import arcade
from PIL import Image

WHEEL_PIXELS = 25   # Width of the wheel in wheel pixels (odd, so there's a center pixel)
MARKER_COLOR = (0, 0, 0)
MARKER_WIDTH = 2


def _build_colors():
    """Map each (column, row) inside the circle to its RGB color."""
    radius = WHEEL_PIXELS / 2
    colors = {}
    for row in range(WHEEL_PIXELS):
        for column in range(WHEEL_PIXELS):
            dx = column + 0.5 - radius
            dy = radius - (row + 0.5)   # Rows count down; flip so up is positive
            distance = math.hypot(dx, dy)
            if distance > radius:
                continue
            hue = (math.atan2(dy, dx) / (2 * math.pi)) % 1
            saturation = min(1.0, distance / (radius - 0.5))
            r, g, b = colorsys.hsv_to_rgb(hue, saturation, 1.0)
            colors[(column, row)] = (round(r * 255), round(g * 255), round(b * 255))
    return colors


class ColorWheel:
    colors = _build_colors()
    cells_by_color = {color: cell for cell, color in colors.items()}

    def __init__(self):
        image = Image.new("RGBA", (WHEEL_PIXELS, WHEEL_PIXELS), (0, 0, 0, 0))
        for cell, color in self.colors.items():
            image.putpixel(cell, (*color, 255))
        self.texture = arcade.Texture(image, hash=f"color-wheel-{WHEEL_PIXELS}")
        self.rect = arcade.XYWH(0, 0, WHEEL_PIXELS, WHEEL_PIXELS)

    def place(self, center_x, center_y, diameter):
        self.rect = arcade.XYWH(center_x, center_y, diameter, diameter)

    def _cell_size(self):
        return self.rect.width / WHEEL_PIXELS

    def cell_at(self, x, y):
        """The wheel pixel under a screen point, or None if it's off the wheel."""
        if not self.rect.point_in_rect((x, y)):
            return None
        size = self._cell_size()
        cell = (int((x - self.rect.left) / size), int((self.rect.top - y) / size))
        return cell if cell in self.colors else None

    def draw(self, selected_color):
        arcade.draw_texture_rect(self.texture, self.rect, pixelated=True)

        # Outline the pixel that matches the selected color, if there is one.
        cell = self.cells_by_color.get(tuple(selected_color))
        if cell:
            size = self._cell_size()
            column, row = cell
            arcade.draw_rect_outline(
                arcade.LBWH(self.rect.left + column * size,
                            self.rect.top - (row + 1) * size, size, size),
                MARKER_COLOR, MARKER_WIDTH,
            )
