"""The Game Over screen, shown when the player runs out of health."""

import arcade

import pixel_font
import ui
from granite import GraniteBackground

TITLE = "Game Over"
TITLE_MAX_SCALE = 12
BUTTON_GAP = 20


class GameOverView(arcade.View):
    def __init__(self):
        super().__init__()
        self.background = GraniteBackground(self.width, self.height)
        self.buttons = [
            ui.Button("Play Again", self.play_again),
            ui.Button("Main Menu", self.main_menu),
        ]
        self._layout()

    def _layout(self):
        scale = ui.ui_scale(self.width, self.height)
        width, height = ui.BUTTON_WIDTH * scale, ui.BUTTON_HEIGHT * scale
        gap = BUTTON_GAP * scale
        for i, button in enumerate(self.buttons):
            button.place(self.width / 2, self.height * 0.4 - i * (height + gap),
                         width, height, scale)
        fit = int(self.width * 0.9 / pixel_font.text_width(TITLE))
        self.title_scale = max(1, min(round(TITLE_MAX_SCALE * scale), fit))
        self.title_y = self.height * 0.68

    def play_again(self):
        from game_view import GameView
        self.window.show_view(GameView())

    def main_menu(self):
        from menu_view import MenuView
        self.window.show_view(MenuView())

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
