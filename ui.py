"""Shared pieces for menu screens: buttons and UI scaling."""

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


def draw_title(text, center_x, center_y, scale):
    """Big black pixel text with a thin white border, used for screen titles."""
    # The border is about a quarter of a font pixel thick.
    outline = max(2, round(scale / 4))
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
