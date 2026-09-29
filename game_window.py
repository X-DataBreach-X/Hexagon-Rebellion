"""The main game window for Hexagon Rebellion."""

import arcade

from floor import BLOCK_SIZE, STONE_SIZE, ChunkedFloor

SCREEN_TITLE = "Hexagon Rebellion"
DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 720
MIN_WIDTH = 480
MIN_HEIGHT = 270
BACKGROUND_COLOR = arcade.color.BLACK

# World size, measured in average-sized cobblestones (200 x 56px = 11,200px).
WORLD_STONES_WIDE = 200
WORLD_STONES_HIGH = 200
WORLD_WIDTH = WORLD_STONES_WIDE * STONE_SIZE * BLOCK_SIZE
WORLD_HEIGHT = WORLD_STONES_HIGH * STONE_SIZE * BLOCK_SIZE

# Temporary: moves the camera with WASD/arrows until the player exists.
CAMERA_SPEED = 600  # pixels per second

MOVE_KEYS = {
    arcade.key.W: (0, 1), arcade.key.UP: (0, 1),
    arcade.key.S: (0, -1), arcade.key.DOWN: (0, -1),
    arcade.key.A: (-1, 0), arcade.key.LEFT: (-1, 0),
    arcade.key.D: (1, 0), arcade.key.RIGHT: (1, 0),
}


class GameWindow(arcade.Window):
    """A resizable window that can toggle fullscreen with F11."""

    def __init__(self):
        super().__init__(DEFAULT_WIDTH, DEFAULT_HEIGHT, SCREEN_TITLE, resizable=True)
        self.set_minimum_size(MIN_WIDTH, MIN_HEIGHT)
        self.background_color = BACKGROUND_COLOR

        self.floor = ChunkedFloor(WORLD_WIDTH, WORLD_HEIGHT)
        self.camera = arcade.Camera2D()

        # The point the camera follows. Starts in the middle of the world.
        self.focus_x = WORLD_WIDTH / 2
        self.focus_y = WORLD_HEIGHT / 2
        self.keys_held = set()
        self._update_camera()

    def _update_camera(self):
        """Center the camera on the focus point without showing past the edges."""
        half_w, half_h = self.width / 2, self.height / 2
        x = min(max(self.focus_x, half_w), WORLD_WIDTH - half_w)
        y = min(max(self.focus_y, half_h), WORLD_HEIGHT - half_h)
        self.camera.position = (x, y)

    def _view_rect(self):
        """The part of the world currently on screen: (left, bottom, width, height)."""
        x, y = self.camera.position
        return x - self.width / 2, y - self.height / 2, self.width, self.height

    def on_update(self, delta_time):
        dx = sum(MOVE_KEYS[key][0] for key in self.keys_held)
        dy = sum(MOVE_KEYS[key][1] for key in self.keys_held)
        dx, dy = max(-1, min(1, dx)), max(-1, min(1, dy))
        self.focus_x = min(max(self.focus_x + dx * CAMERA_SPEED * delta_time, 0), WORLD_WIDTH)
        self.focus_y = min(max(self.focus_y + dy * CAMERA_SPEED * delta_time, 0), WORLD_HEIGHT)
        self._update_camera()
        self.floor.update(*self._view_rect())

    def on_draw(self):
        self.clear()
        self.camera.use()
        self.floor.draw(*self._view_rect())

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self.camera.match_window()
        self._update_camera()

    def on_key_press(self, key, modifiers):
        if key in MOVE_KEYS:
            self.keys_held.add(key)
        elif key == arcade.key.F11:
            self.set_fullscreen(not self.fullscreen)
        elif key == arcade.key.ESCAPE and self.fullscreen:
            self.set_fullscreen(False)

    def on_key_release(self, key, modifiers):
        self.keys_held.discard(key)
