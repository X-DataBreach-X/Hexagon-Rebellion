"""The player's look, shared by the character screen and the game.

The hexagon is made of 6 triangles ("portions"), named as if its front
corner points up: 1-2 top, 3-4 middle, 5-6 bottom, left then right.
Portion 0 is an override: changing a setting there changes it on all six
portions at once. There is one shared design, so a change on the character
screen shows up everywhere the player is drawn, right away.

Each portion has a fill and three borders. Picture the portion's triangle
with its outer edge (part of the hexagon's outline) at the bottom and its
point at the hexagon's center at the top: that outer edge is the "bottom"
border, and the two edges running to the center are "left" and "right".
"""

import colorsys
from dataclasses import dataclass

PORTIONS = range(1, 7)
OVERRIDE = 0          # Portion 0

SIDES = ("bottom", "left", "right")
MAX_BORDER_THICKNESS = 12   # Pixels


@dataclass
class Shade:
    """A color picked on a color wheel, plus how bright to make it."""
    wheel_color: tuple = (255, 255, 255)
    brightness: float = 1.0      # 0 = black, 1 = the wheel color as-is

    @property
    def color(self):
        """The color actually drawn: the wheel color, darkened by brightness."""
        return tuple(round(channel * self.brightness) for channel in self.wheel_color)


@dataclass
class Border(Shade):
    enabled: bool = False
    length: float = 1.0          # Fraction of the edge covered (0-1), centered on the edge
    thickness: float = 4         # Pixels (0 to MAX_BORDER_THICKNESS)
    brightness: float = 0.0      # Borders start black


def shade_of(color):
    """The wheel color and brightness that make an exact color (e.g. one typed as hex).

    Returns (wheel_color, brightness). For pure black the wheel color can't be
    worked out, so it's None (meaning "keep whatever it was").
    """
    hue, saturation, value = colorsys.rgb_to_hsv(*(channel / 255 for channel in color))
    if value == 0:
        return None, 0.0
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, 1.0)
    return (round(r * 255), round(g * 255), round(b * 255)), value


class CharacterDesign:
    def __init__(self):
        self.fills = {portion: Shade() for portion in PORTIONS}
        self.borders = {portion: {side: Border() for side in SIDES} for portion in PORTIONS}
        # The last settings made through Portion 0 (what its controls show).
        self.override_fill = Shade()
        self.override_borders = {side: Border() for side in SIDES}

    @staticmethod
    def _change(targets, changes):
        for target in targets:
            for name, value in changes.items():
                setattr(target, name, value)

    def get_fill(self, portion):
        """A portion's fill; for Portion 0, the override's."""
        return self.override_fill if portion == OVERRIDE else self.fills[portion]

    def set_fill(self, portion, **changes):
        """Change a portion's fill, e.g. set_fill(3, brightness=0.5).

        For Portion 0, the change is made to every portion's fill. Only the
        settings passed in are changed.
        """
        if portion == OVERRIDE:
            targets = [self.override_fill, *self.fills.values()]
        else:
            targets = [self.fills[portion]]
        self._change(targets, changes)

    def set_fill_color(self, portion, color):
        """Make a portion's fill exactly this color (wheel color and brightness to match)."""
        wheel_color, brightness = shade_of(color)
        if wheel_color is None:
            self.set_fill(portion, brightness=brightness)
        else:
            self.set_fill(portion, wheel_color=wheel_color, brightness=brightness)

    def get_border(self, portion, side):
        """One border's settings; for Portion 0, the override's."""
        if portion == OVERRIDE:
            return self.override_borders[side]
        return self.borders[portion][side]

    def set_border(self, portion, side, **changes):
        """Change settings on one border, e.g. set_border(2, "left", enabled=True).

        For Portion 0, the change is made to that border on every portion.
        Only the settings passed in are changed.
        """
        if portion == OVERRIDE:
            targets = [self.override_borders[side]]
            targets += [self.borders[each][side] for each in PORTIONS]
        else:
            targets = [self.borders[portion][side]]
        self._change(targets, changes)


design = CharacterDesign()
