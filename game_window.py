"""The main game window for Hexagon Rebellion.

The window itself only handles things that apply to every screen (size,
fullscreen). Each screen - the menu, the game - is an arcade.View that the
window switches between with show_view().
"""

import arcade

SCREEN_TITLE = "Hexagon Rebellion"
DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 720
MIN_WIDTH = 480
MIN_HEIGHT = 270
BACKGROUND_COLOR = arcade.color.BLACK


class GameWindow(arcade.Window):
    """A resizable window that can toggle fullscreen with F11."""

    def __init__(self):
        super().__init__(DEFAULT_WIDTH, DEFAULT_HEIGHT, SCREEN_TITLE, resizable=True)
        self.set_minimum_size(MIN_WIDTH, MIN_HEIGHT)
        self.background_color = BACKGROUND_COLOR

    def on_key_press(self, key, modifiers):
        if key == arcade.key.F11:
            self.set_fullscreen(not self.fullscreen)
        elif key == arcade.key.ESCAPE and self.fullscreen:
            self.set_fullscreen(False)
