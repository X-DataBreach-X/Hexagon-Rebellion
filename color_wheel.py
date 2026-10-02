"""A smooth, round color wheel for picking colors.

Going around the circle changes the hue (red, yellow, green, ...); going
from the center out changes how strong the color is, from white in the
middle to full color at the edge. A black ring borders the wheel, and a
small ring marks the selected color.

The wheel image is generated once at a high resolution (with soft,
anti-aliased edges) and drawn scaled down smoothly, so it stays round at
any size. Colors are worked out from the exact mouse position, so any hue
and strength can be picked.
"""

import colorsys
import math

import arcade
import numpy as np
from PIL import Image

TEXTURE_SIZE = 256     # Resolution of the generated wheel image
BORDER_COLOR = (0, 0, 0)
BORDER_WIDTH = 3       # Screen pixels
MARKER_RADIUS = 5      # Screen pixels
MARKER_COLORS = ((0, 0, 0), (255, 255, 255))   # Outer and inner ring


def _wheel_image(size):
    """An RGBA image of the wheel: hue by angle, strength by distance from center."""
    radius = size / 2
    rows, columns = np.mgrid[0:size, 0:size] + 0.5
    dx = columns - radius
    dy = radius - rows                      # Rows count down; flip so up is positive
    distance = np.hypot(dx, dy)

    hue = (np.arctan2(dy, dx) / (2 * np.pi)) % 1
    saturation = np.clip(distance / radius, 0, 1)

    # HSV -> RGB with full brightness, done for every pixel at once.
    sector = hue * 6
    rgb = np.empty((size, size, 3))
    for channel, offset in enumerate((5, 3, 1)):   # Red, green, blue
        k = (offset + sector) % 6
        amount = np.clip(np.minimum(k, 4 - k), 0, 1)
        rgb[..., channel] = 1 - saturation * amount

    # Soft edge: fade out over the last pixel so the circle isn't jagged.
    alpha = np.clip(radius - distance, 0, 1)
    pixels = np.dstack([rgb * 255, alpha * 255]).round().astype(np.uint8)
    return Image.fromarray(pixels, "RGBA")


class ColorWheel:
    _texture = None   # Built once and shared by every wheel

    def __init__(self):
        if ColorWheel._texture is None:
            ColorWheel._texture = arcade.Texture(_wheel_image(TEXTURE_SIZE),
                                                 hash=f"smooth-color-wheel-{TEXTURE_SIZE}")
        self.texture = ColorWheel._texture
        self.rect = arcade.XYWH(0, 0, 100, 100)

    def place(self, center_x, center_y, diameter):
        self.rect = arcade.XYWH(center_x, center_y, diameter, diameter)

    def color_at(self, x, y, clamp=False):
        """The color under a screen point, or None if it's off the wheel.

        With clamp=True, points outside the wheel give the color at the
        nearest spot on its edge (handy while dragging).
        """
        radius = self.rect.width / 2
        dx, dy = x - self.rect.x, y - self.rect.y
        distance = math.hypot(dx, dy)
        if distance > radius and not clamp:
            return None
        hue = (math.atan2(dy, dx) / (2 * math.pi)) % 1
        saturation = min(1.0, distance / radius)
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, 1.0)
        return round(r * 255), round(g * 255), round(b * 255)

    def draw(self, selected_color):
        arcade.draw_texture_rect(self.texture, self.rect)
        radius = self.rect.width / 2
        arcade.draw_circle_outline(self.rect.x, self.rect.y, radius + BORDER_WIDTH / 2,
                                   BORDER_COLOR, BORDER_WIDTH, num_segments=96)

        # Mark the selected color, if it's one the wheel has (full brightness).
        hue, saturation, value = colorsys.rgb_to_hsv(*(c / 255 for c in selected_color[:3]))
        if value > 0.99:
            angle = hue * 2 * math.pi
            x = self.rect.x + math.cos(angle) * saturation * radius
            y = self.rect.y + math.sin(angle) * saturation * radius
            outer, inner = MARKER_COLORS
            arcade.draw_circle_outline(x, y, MARKER_RADIUS, outer, 3)
            arcade.draw_circle_outline(x, y, MARKER_RADIUS - 1.5, inner, 1.5)
