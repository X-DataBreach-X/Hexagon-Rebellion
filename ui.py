"""Shared pieces for menu screens: buttons, sliders, text boxes and UI scaling."""

import time

import arcade

import pixel_font

# Sizes are for a 1280x720 window; screens scale them with ui_scale().
BUTTON_WIDTH = 300
BUTTON_HEIGHT = 64
BUTTON_TEXT_SCALE = 4
BUTTON_TEXT_BOLD = 2       # Extra stroke thickness, in screen pixels
BUTTON_BORDER = 6
BUTTON_COLOR = (128, 128, 128)
BUTTON_BORDER_COLOR = (0, 0, 0)
TEXT_COLOR = (0, 0, 0)
TEXT_HOVER_COLOR = (255, 255, 255)

TITLE_COLOR = (0, 0, 0)
TITLE_OUTLINE_COLOR = (255, 255, 255)


def ui_scale(width, height):
    """How much to scale UI sizes for a window, relative to 1280x720."""
    return max(0.5, min(width / 1280, height / 720))


def draw_title(text, center_x, center_y, scale, outlined=True):
    """Big black pixel text, with a thin white border unless outlined=False."""
    # The border is about a quarter of a font pixel thick.
    outline = max(2, round(scale / 4)) if outlined else 0
    pixel_font.draw_text(text, center_x, center_y, scale, TITLE_COLOR,
                         outline=outline, outline_color=TITLE_OUTLINE_COLOR)


class Button:
    """A gray rectangle with pixel text that turns white on hover."""

    def __init__(self, label, on_click, text_scale=BUTTON_TEXT_SCALE):
        self.label = label
        self.on_click = on_click
        self.hovered = False
        self.rect = arcade.XYWH(0, 0, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.base_text_scale = text_scale
        self.text_scale = text_scale

    def place(self, center_x, center_y, width, height, ui):
        """Position and size the button; ui is the current ui_scale()."""
        self.rect = arcade.XYWH(center_x, center_y, width, height)
        self.text_scale = max(2, round(self.base_text_scale * ui))

    def contains(self, x, y):
        return self.rect.point_in_rect((x, y))

    def draw(self):
        arcade.draw_rect_filled(self.rect, BUTTON_COLOR)
        arcade.draw_rect_outline(self.rect, BUTTON_BORDER_COLOR, BUTTON_BORDER)
        color = TEXT_HOVER_COLOR if self.hovered else TEXT_COLOR
        pixel_font.draw_text(self.label, self.rect.x, self.rect.y, self.text_scale, color,
                             bold=BUTTON_TEXT_BOLD)


class DropdownHeader(Button):
    """A clickable row of text with an arrow: points left when closed, down when open.

    No box or border is drawn; the whole row (self.rect) is clickable.
    """

    ARROW_GAP = 3   # Space between the label and the arrow, in font pixels

    def __init__(self, label, on_click, text_scale=BUTTON_TEXT_SCALE):
        super().__init__(label, on_click, text_scale)
        self.expanded = False

    def draw(self):
        color = TEXT_HOVER_COLOR if self.hovered else TEXT_COLOR
        scale = self.text_scale

        # Left-aligned label.
        label_width = pixel_font.text_width(self.label) * scale
        pixel_font.draw_text(self.label, self.rect.left + label_width / 2, self.rect.y,
                             scale, color, bold=BUTTON_TEXT_BOLD)

        # Arrow just to the right of the label.
        arrow = "v" if self.expanded else "<"
        arrow_width = pixel_font.text_width(arrow) * scale
        arrow_x = self.rect.left + label_width + self.ARROW_GAP * scale + arrow_width / 2
        pixel_font.draw_text(arrow, arrow_x, self.rect.y, scale, color, bold=BUTTON_TEXT_BOLD)


class ToggleButton(Button):
    """A small button that switches on and off. While on, it's lighter with white text."""

    BORDER = 3
    ON_COLOR = (176, 176, 176)

    def __init__(self, label, on_click, text_scale=2):
        super().__init__(label, on_click, text_scale)
        self.on = False

    def draw(self):
        arcade.draw_rect_filled(self.rect, self.ON_COLOR if self.on else BUTTON_COLOR)
        arcade.draw_rect_outline(self.rect, BUTTON_BORDER_COLOR, self.BORDER)
        color = TEXT_HOVER_COLOR if self.on or self.hovered else TEXT_COLOR
        pixel_font.draw_text(self.label, self.rect.x, self.rect.y, self.text_scale, color,
                             bold=BUTTON_TEXT_BOLD // 2)


class Slider:
    """A labeled horizontal slider. Its value is a fraction from 0 (left) to 1 (right).

    The label sits to the left of the track. A caption, if given, sits
    centered above the track instead (for words too long to fit on the left). align_with
    reserves room for that text on the left, so sliders with different
    labels can line their tracks up.

    The slider doesn't store the value; the screen passes it in to draw() and
    reads a new one from fraction_at() while the knob is dragged.
    """

    TRACK_THICKNESS = 4
    KNOB_WIDTH = 10
    KNOB_HEIGHT = 18
    LABEL_GAP = 8

    CAPTION_GAP = 6       # Space between a caption and the track below it
    CAPTION_SCALE = 0.75  # Captions are a little smaller than labels

    def __init__(self, label, text_scale=2, caption="", align_with=None):
        self.label = label
        self.caption = caption
        self.align_with = align_with or label
        self.base_text_scale = text_scale
        self.text_scale = text_scale
        self.track = arcade.LBWH(0, 0, 100, self.TRACK_THICKNESS)
        self.label_pos = (0, 0)
        self.caption_pos = (0, 0)
        self.ui = 1

    def place(self, left, center_y, width, ui):
        """Put the label at left and the track after it, filling width in total."""
        self.ui = ui
        self.text_scale = max(1, round(self.base_text_scale * ui))
        scale = self.text_scale
        if self.label:
            self.label_pos = (left + pixel_font.text_width(self.label) * scale / 2, center_y)
        track_left = left + pixel_font.text_width(self.align_with) * scale + self.LABEL_GAP * ui
        thickness = self.TRACK_THICKNESS * ui
        self.track = arcade.LBWH(track_left, center_y - thickness / 2,
                                 left + width - track_left, thickness)
        if self.caption:
            self.caption_scale = scale * self.CAPTION_SCALE
            caption_y = (center_y + self.KNOB_HEIGHT * ui / 2 + self.CAPTION_GAP * ui
                         + pixel_font.GLYPH_HEIGHT * self.caption_scale / 2)
            self.caption_pos = (self.track.x, caption_y)   # Centered over the track

    def contains(self, x, y):
        """True if (x, y) is on the track or close enough to grab the knob."""
        reach = self.KNOB_HEIGHT * self.ui / 2
        return (self.track.left - reach <= x <= self.track.right + reach
                and abs(y - self.track.y) <= reach)

    def fraction_at(self, x):
        return min(1.0, max(0.0, (x - self.track.left) / self.track.width))

    def draw(self, fraction):
        if self.label:
            pixel_font.draw_text(self.label, *self.label_pos, self.text_scale, TEXT_COLOR,
                                 bold=BUTTON_TEXT_BOLD // 2)
        if self.caption:
            pixel_font.draw_text(self.caption, *self.caption_pos, self.caption_scale, TEXT_COLOR,
                                 bold=BUTTON_TEXT_BOLD // 2)
        arcade.draw_rect_filled(self.track, BUTTON_BORDER_COLOR)
        knob = arcade.XYWH(self.track.left + fraction * self.track.width, self.track.y,
                           self.KNOB_WIDTH * self.ui, self.KNOB_HEIGHT * self.ui)
        arcade.draw_rect_filled(knob, BUTTON_COLOR)
        arcade.draw_rect_outline(knob, BUTTON_BORDER_COLOR, 2)


HEALTH_FILL = (210, 45, 45)
HEALTH_EMPTY = (60, 20, 20)


def draw_health_bar(left, top, width, height, health, max_health, ui):
    """A labeled bar ("HEALTH 87") that empties from right to left."""
    text_scale = max(1, round(2 * ui))
    label = f"Health {health}"
    label_height = pixel_font.GLYPH_HEIGHT * text_scale
    pixel_font.draw_text(label, left + pixel_font.text_width(label) * text_scale / 2,
                         top - label_height / 2, text_scale, TEXT_HOVER_COLOR,
                         bold=BUTTON_TEXT_BOLD // 2, outline=max(1, text_scale // 2),
                         outline_color=BUTTON_BORDER_COLOR)
    bar = arcade.LBWH(left, top - label_height - 6 * ui - height, width, height)
    arcade.draw_rect_filled(bar, HEALTH_EMPTY)
    filled = width * max(0, health) / max_health
    if filled > 0:
        arcade.draw_rect_filled(arcade.LBWH(bar.left, bar.bottom, filled, height), HEALTH_FILL)
    arcade.draw_rect_outline(bar, BUTTON_BORDER_COLOR, 3)


def update_hover(buttons, x, y):
    for button in buttons:
        button.hovered = button.contains(x, y)


def click(buttons, x, y):
    """Run the clicked button's action. Returns True if a button was clicked."""
    for button in buttons:
        if button.contains(x, y):
            button.on_click()
            return True
    return False


HEX_DIGITS = "0123456789ABCDEF"
TEXT_BOX_BORDER = 3
CURSOR_BLINK = 0.5   # Seconds the cursor stays on (and then off)


def color_to_hex(color):
    """(255, 128, 0) -> "FF8000" """
    return "".join(f"{channel:02X}" for channel in color[:3])


class TextBox:
    """A small box you can click and type into.

    Subclasses choose which characters are allowed, how long the text can
    be, what's shown around it (like "#" or "%"), and how the text turns
    into a value. type_char() and backspace() return the new value whenever
    the text is a complete, valid value, so it can be applied right away.
    """

    ALLOWED = ""
    MAX_LENGTH = 0
    PREFIX = ""
    SUFFIX = ""

    def __init__(self, text_scale=2):
        self.rect = arcade.XYWH(0, 0, 100, 32)
        self.base_text_scale = text_scale
        self.text_scale = text_scale
        self.focused = False
        self.text = ""
        self.hovered = False

    def place(self, center_x, center_y, width, height, ui):
        self.rect = arcade.XYWH(center_x, center_y, width, height)
        self.text_scale = max(1, round(self.base_text_scale * ui))

    def contains(self, x, y):
        return self.rect.point_in_rect((x, y))

    def focus(self, current_value):
        """Start editing, beginning from the current value's text."""
        self.focused = True
        self.text = self.to_text(current_value)

    def unfocus(self):
        self.focused = False

    def type_char(self, char):
        """Add a typed character if it's allowed. Returns the value if the text is valid."""
        char = char.upper()
        if char not in self.ALLOWED or len(self.text) >= self.MAX_LENGTH:
            return None
        if self.value(self.text + char) is None and len(self.text) + 1 == self.MAX_LENGTH:
            return None   # Would make the text invalid with no way to fix it by typing more
        self.text += char
        return self.value(self.text)

    def backspace(self):
        """Delete the last character. Returns the value if what's left is valid."""
        self.text = self.text[:-1]
        return self.value(self.text)

    def to_text(self, value):
        raise NotImplementedError

    def value(self, text):
        """The value for some text, or None if it isn't complete or valid."""
        raise NotImplementedError

    def draw(self, current_value):
        arcade.draw_rect_filled(self.rect, BUTTON_COLOR)
        arcade.draw_rect_outline(self.rect, BUTTON_BORDER_COLOR, TEXT_BOX_BORDER)

        # Shows what's being typed while editing, otherwise the current value.
        typed = self.PREFIX + (self.text if self.focused else self.to_text(current_value))
        color = TEXT_HOVER_COLOR if self.focused or self.hovered else TEXT_COLOR
        scale = self.text_scale
        left = self.rect.left + 4 * scale
        width = pixel_font.text_width(typed) * scale if typed else 0
        if typed:
            pixel_font.draw_text(typed, left + width / 2, self.rect.y, scale, color)
        right = left + width

        # Blinking cursor after the typed text while editing.
        if self.focused and int(time.monotonic() / CURSOR_BLINK) % 2 == 0:
            height = pixel_font.GLYPH_HEIGHT * scale
            arcade.draw_rect_filled(
                arcade.LBWH(right + scale, self.rect.y - height / 2, scale, height), color)
        if self.SUFFIX:
            suffix_width = pixel_font.text_width(self.SUFFIX) * scale
            pixel_font.draw_text(self.SUFFIX, right + 3 * scale + suffix_width / 2, self.rect.y,
                                 scale, color)


class HexColorBox(TextBox):
    """A text box for typing a color as a 6-digit hex code, like #FF8000."""

    ALLOWED = HEX_DIGITS
    MAX_LENGTH = 6
    PREFIX = "#"

    def to_text(self, color):
        return color_to_hex(color)

    def value(self, text):
        if len(text) != 6:
            return None
        return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))


class PercentBox(TextBox):
    """A text box for a percentage from 0 to 100. Its values are fractions (0-1)."""

    ALLOWED = "0123456789"
    MAX_LENGTH = 3
    SUFFIX = "%"

    def to_text(self, fraction):
        return str(round(fraction * 100))

    def value(self, text):
        if not text or int(text) > 100:
            return None
        return int(text) / 100
