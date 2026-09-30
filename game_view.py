"""The gameplay screen: the player walking around the cobblestone world."""

import arcade

from floor import BLOCK_SIZE, STONE_SIZE, ChunkedFloor
from player import Player

# World size, measured in average-sized cobblestones (200 x 56px = 11,200px).
WORLD_STONES_WIDE = 200
WORLD_STONES_HIGH = 200
WORLD_WIDTH = WORLD_STONES_WIDE * STONE_SIZE * BLOCK_SIZE
WORLD_HEIGHT = WORLD_STONES_HIGH * STONE_SIZE * BLOCK_SIZE

MOVE_KEYS = {
    arcade.key.W: (0, 1), arcade.key.UP: (0, 1),
    arcade.key.S: (0, -1), arcade.key.DOWN: (0, -1),
    arcade.key.A: (-1, 0), arcade.key.LEFT: (-1, 0),
    arcade.key.D: (1, 0), arcade.key.RIGHT: (1, 0),
}


class GameView(arcade.View):
    """The player moves with WASD, faces the mouse, and the camera follows."""

    def __init__(self):
        super().__init__()
        self.floor = ChunkedFloor(WORLD_WIDTH, WORLD_HEIGHT)
        self.camera = arcade.Camera2D()
        self.player = Player(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)

        self.keys_held = set()
        # Mouse position on screen. Kept so the player keeps aiming at it
        # even when the camera moves and the mouse doesn't.
        self.mouse_x = self.width / 2 + 1
        self.mouse_y = self.height / 2
        self._update_camera()

    def _update_camera(self):
        """Center the camera on the player without showing past the world edges."""
        half_w, half_h = self.width / 2, self.height / 2
        x = min(max(self.player.x, half_w), WORLD_WIDTH - half_w)
        y = min(max(self.player.y, half_h), WORLD_HEIGHT - half_h)
        self.camera.position = (x, y)

    def _view_rect(self):
        """The part of the world currently on screen: (left, bottom, width, height)."""
        x, y = self.camera.position
        return x - self.width / 2, y - self.height / 2, self.width, self.height

    def on_show_view(self):
        self.camera.match_window()
        self._update_camera()

    def on_update(self, delta_time):
        dx = sum(MOVE_KEYS[key][0] for key in self.keys_held)
        dy = sum(MOVE_KEYS[key][1] for key in self.keys_held)
        self.player.move(dx, dy, delta_time, (0, 0, WORLD_WIDTH, WORLD_HEIGHT))
        self._update_camera()

        # Convert the mouse from screen coordinates to world coordinates.
        left, bottom, _, _ = self._view_rect()
        self.player.face(left + self.mouse_x, bottom + self.mouse_y)

        self.floor.update(*self._view_rect())

    def on_draw(self):
        self.clear()
        self.camera.use()
        self.floor.draw(*self._view_rect())
        self.player.draw()

    def on_resize(self, width, height):
        self.camera.match_window()
        self._update_camera()

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x, self.mouse_y = x, y

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.mouse_x, self.mouse_y = x, y

    def on_key_press(self, key, modifiers):
        if key in MOVE_KEYS:
            self.keys_held.add(key)

    def on_key_release(self, key, modifiers):
        self.keys_held.discard(key)
