"""The main game window for Hexagon Rebellion."""

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

        self.title_text = arcade.Text(
            SCREEN_TITLE,
            x=self.width / 2,
            y=self.height / 2,
            color=arcade.color.WHITE,
            font_size=36,
            anchor_x="center",
            anchor_y="center",
        )
        self.hint_text = arcade.Text(
            "F11: toggle fullscreen   Esc: exit fullscreen",
            x=self.width / 2,
            y=self.height / 2 - 50,
            color=arcade.color.GRAY,
            font_size=14,
            anchor_x="center",
            anchor_y="center",
        )

    def on_draw(self):
        self.clear()
        self.title_text.draw()
        self.hint_text.draw()

    def on_resize(self, width, height):
        # Let Arcade update the viewport, then re-center the text.
        super().on_resize(width, height)
        self.title_text.position = (width / 2, height / 2)
        self.hint_text.position = (width / 2, height / 2 - 50)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.F11:
            self.set_fullscreen(not self.fullscreen)
        elif key == arcade.key.ESCAPE and self.fullscreen:
            self.set_fullscreen(False)
