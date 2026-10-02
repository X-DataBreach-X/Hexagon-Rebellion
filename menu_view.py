"""The main menu: the title and the Play / Character / Armory / Settings buttons."""

import arcade

import pixel_font
import ui
from granite import GraniteBackground

TITLE = "Hexagon Rebellion"
TITLE_MAX_SCALE = 12        # Screen pixels per font pixel, at most

BUTTON_GAP = 20             # Space between buttons
BUTTON_OFFSET_Y = -40       # Shifts the button stack down from the screen center


class MenuView(arcade.View):
    """The first screen shown when the game opens."""

    def __init__(self):
        super().__init__()
        self.background = GraniteBackground(self.width, self.height)
        self.buttons = [
            ui.Button("Play", self.start_game),
            ui.Button("Character", self.open_character),
            ui.Button("Armory", self.open_armory),
            ui.Button("Settings", lambda: None),    # Not built yet
        ]
        self.title_scale = TITLE_MAX_SCALE
        self.title_y = 0
        self._layout()

    def _layout(self):
        """Position everything for the current window size."""
        scale = ui.ui_scale(self.width, self.height)
        width, height = ui.BUTTON_WIDTH * scale, ui.BUTTON_HEIGHT * scale
        gap = BUTTON_GAP * scale

        # Stack the buttons around the center of the screen.
        center_x, center_y = self.width / 2, self.height / 2 + BUTTON_OFFSET_Y * scale
        middle = (len(self.buttons) - 1) / 2
        for i, button in enumerate(self.buttons):
            button.place(center_x, center_y + (middle - i) * (height + gap), width, height, scale)

        # Title: as big as fits, centered between the top button and the top
        # of the screen. Whole-number scales keep the pixels perfectly square.
        top_of_buttons = self.buttons[0].rect.top
        fit_width = int(self.width * 0.9 / pixel_font.text_width(TITLE))
        fit_height = int((self.height - top_of_buttons) * 0.8 / pixel_font.GLYPH_HEIGHT)
        self.title_scale = max(1, min(TITLE_MAX_SCALE, fit_width, fit_height))
        self.title_y = (top_of_buttons + self.height) / 2

    # Screens are imported inside these methods because they import this
    # file for their Back buttons, and importing both ways at the top of
    # the files would be a circular import.
    def start_game(self):
        from game_view import GameView
        self.window.show_view(GameView())

    def open_character(self):
        from character_view import CharacterView
        self.window.show_view(CharacterView())

    def open_armory(self):
        from armory_view import ArmoryView
        self.window.show_view(ArmoryView())

    def on_show_view(self):
        self._layout()

    def on_resize(self, width, height):
        self.background.resize(width, height)
        self._layout()

    def on_draw(self):
        self.clear()
        self.window.default_camera.use()
        self.background.draw()

        ui.draw_title(TITLE, self.width / 2, self.title_y, self.title_scale)
        for button in self.buttons:
            button.draw()

    def on_mouse_motion(self, x, y, dx, dy):
        ui.update_hover(self.buttons, x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        ui.click(self.buttons, x, y)
