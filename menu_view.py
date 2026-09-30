"""The main menu: the title and the Play / Character / Settings buttons."""

import arcade

import pixel_font
from granite import PIXEL_SIZE, create_granite_texture
from game_view import GameView

TITLE = "Hexagon Rebellion"
TITLE_COLOR = (0, 0, 0)
TITLE_MAX_SCALE = 12        # Screen pixels per font pixel, at most
TITLE_OUTLINE_COLOR = (255, 255, 255)

# Sizes are for a 1280x720 window; everything scales with the window.
BUTTON_WIDTH = 300
BUTTON_HEIGHT = 64
BUTTON_GAP = 20             # Space between buttons
BUTTON_OFFSET_Y = -40       # Shifts the button stack down from the screen center
BUTTON_TEXT_SCALE = 4
BUTTON_TEXT_BOLD = 2       # Extra stroke thickness, in screen pixels
BUTTON_BORDER = 6
BUTTON_COLOR = (128, 128, 128)
BUTTON_BORDER_COLOR = (0, 0, 0)
TEXT_COLOR = (0, 0, 0)
TEXT_HOVER_COLOR = (255, 255, 255)


class Button:
    """A gray rectangle with pixel text that turns white on hover."""

    def __init__(self, label, on_click):
        self.label = label
        self.on_click = on_click
        self.hovered = False
        self.rect = arcade.XYWH(0, 0, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.text_scale = BUTTON_TEXT_SCALE

    def contains(self, x, y):
        return self.rect.point_in_rect((x, y))

    def draw(self):
        arcade.draw_rect_filled(self.rect, BUTTON_COLOR)
        arcade.draw_rect_outline(self.rect, BUTTON_BORDER_COLOR, BUTTON_BORDER)
        color = TEXT_HOVER_COLOR if self.hovered else TEXT_COLOR
        pixel_font.draw_text(self.label, self.rect.x, self.rect.y, self.text_scale, color,
                             bold=BUTTON_TEXT_BOLD)


class MenuView(arcade.View):
    """The first screen shown when the game opens."""

    def __init__(self):
        super().__init__()
        # Built big enough for fullscreen so resizing doesn't rebuild it.
        screen_w, screen_h = arcade.get_display_size()
        self.background = create_granite_texture(max(screen_w, self.width),
                                                 max(screen_h, self.height))
        self.buttons = [
            Button("Play", self.start_game),
            Button("Character", lambda: None),   # Not built yet
            Button("Settings", lambda: None),    # Not built yet
        ]
        self.title_scale = TITLE_MAX_SCALE
        self.title_y = 0
        self._layout()

    def _layout(self):
        """Position everything for the current window size."""
        ui = max(0.5, min(self.width / 1280, self.height / 720))
        width, height, gap = BUTTON_WIDTH * ui, BUTTON_HEIGHT * ui, BUTTON_GAP * ui

        # Stack the buttons around the center of the screen.
        center_x, center_y = self.width / 2, self.height / 2 + BUTTON_OFFSET_Y * ui
        for i, button in enumerate(self.buttons):
            y = center_y + (1 - i) * (height + gap)
            button.rect = arcade.XYWH(center_x, y, width, height)
            button.text_scale = max(2, round(BUTTON_TEXT_SCALE * ui))

        # Title: as big as fits, centered between the top button and the top
        # of the screen. Whole-number scales keep the pixels perfectly square.
        top_of_buttons = self.buttons[0].rect.top
        fit_width = int(self.width * 0.9 / pixel_font.text_width(TITLE))
        fit_height = int((self.height - top_of_buttons) * 0.8 / pixel_font.GLYPH_HEIGHT)
        self.title_scale = max(1, min(TITLE_MAX_SCALE, fit_width, fit_height))
        self.title_y = (top_of_buttons + self.height) / 2

    def start_game(self):
        self.window.show_view(GameView())

    def on_show_view(self):
        self._layout()

    def on_resize(self, width, height):
        if width > self.background.width * PIXEL_SIZE or height > self.background.height * PIXEL_SIZE:
            self.background = create_granite_texture(width, height)
        self._layout()

    def on_draw(self):
        self.clear()
        self.window.default_camera.use()

        arcade.draw_texture_rect(
            self.background,
            arcade.LBWH(0, 0, self.background.width * PIXEL_SIZE,
                        self.background.height * PIXEL_SIZE),
            pixelated=True,
        )

        # A thin white border (about a quarter of a font pixel) makes the title pop.
        outline = max(2, round(self.title_scale / 4))
        pixel_font.draw_text(TITLE, self.width / 2, self.title_y, self.title_scale, TITLE_COLOR,
                             outline=outline, outline_color=TITLE_OUTLINE_COLOR)
        for button in self.buttons:
            button.draw()

    def on_mouse_motion(self, x, y, dx, dy):
        for button in self.buttons:
            button.hovered = button.contains(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        for menu_button in self.buttons:
            if menu_button.contains(x, y):
                menu_button.on_click()
                return
