"""Entry point for Hexagon Rebellion."""

import arcade

from game_window import GameWindow
from menu_view import MenuView


def main():
    window = GameWindow()
    window.show_view(MenuView())
    arcade.run()


if __name__ == "__main__":
    main()
