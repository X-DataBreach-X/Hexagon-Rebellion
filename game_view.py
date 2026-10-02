"""The gameplay screen: the player walking around the cobblestone world."""

import math

import arcade

import ui
from enemies import RADIUS as TRIANGLE_RADIUS
from enemies import Triangle, explode
from floor import BLOCK_SIZE, STONE_SIZE, ChunkedFloor
from loadout import loadout
from player import HIT_RADIUS, MAX_HEALTH, Player
from spawners import TOUCH_RADIUS, Spawner
from weapons import make_weapon

# World size, measured in average-sized cobblestones (200 x 56px = 11,200px).
WORLD_STONES_WIDE = 200
WORLD_STONES_HIGH = 200
WORLD_WIDTH = WORLD_STONES_WIDE * STONE_SIZE * BLOCK_SIZE
WORLD_HEIGHT = WORLD_STONES_HIGH * STONE_SIZE * BLOCK_SIZE

# Triangle spawners: three, in a big triangle around the player's starting point.
SPAWNER_COUNT = 3
SPAWNER_DISTANCE = 2200      # From the middle of the world
WAVE_EVERY = 3               # Seconds between waves (the first comes after this long too)
# Each wave, every spawner releases one triangle: 3 triangles per wave in total.
MAX_TRIANGLES = 60

BOLT_DAMAGE = 1              # Health lost to one triangle laser bolt
BLACK_HOLE_DAMAGE = 5        # Health lost for touching a black hole...
BLACK_HOLE_COOLDOWN = 1.0    # ...at most once per this many seconds

# Health bar in the top-left corner (sizes for a 1280x720 window).
HEALTH_BAR_MARGIN = 24
HEALTH_BAR_WIDTH = 260
HEALTH_BAR_HEIGHT = 20

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
        self.weapon = make_weapon(loadout.weapon)
        self.spawners = [
            Spawner(WORLD_WIDTH / 2 + math.cos(angle) * SPAWNER_DISTANCE,
                    WORLD_HEIGHT / 2 + math.sin(angle) * SPAWNER_DISTANCE)
            for angle in (math.radians(90 + 120 * i) for i in range(SPAWNER_COUNT))
        ]
        self.wave_timer = WAVE_EVERY
        self.triangles = []
        self.shards = []
        self.enemy_bolts = []
        self.black_hole_cooldown = 0.0

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
        self.weapon.aim(self.player)
        self.weapon.update(delta_time)
        for spawner in self.spawners:
            spawner.update(delta_time)
        self.wave_timer -= delta_time
        if self.wave_timer <= 0:
            self.wave_timer += WAVE_EVERY
            for spawner in self.spawners:
                if len(self.triangles) < MAX_TRIANGLES:
                    self.triangles.append(Triangle(spawner.x, spawner.y))

        world = (0, 0, WORLD_WIDTH, WORLD_HEIGHT)
        for triangle in self.triangles:
            triangle.update(delta_time, self.player, self.triangles, world)
            bolt = triangle.fire(delta_time, self.player)
            if bolt:
                self.enemy_bolts.append(bolt)

        # Anything the weapon hits explodes into shards.
        for triangle in [t for t in self.triangles
                         if self.weapon.hits(t.x, t.y, TRIANGLE_RADIUS)]:
            self.triangles.remove(triangle)
            self.shards += explode(triangle)
        for shard in self.shards:
            shard.update(delta_time)
        self.shards = [shard for shard in self.shards if shard.alive]

        self._update_damage(delta_time)
        if not self.player.alive:
            from game_over_view import GameOverView
            self.window.show_view(GameOverView())

    def _update_damage(self, delta_time):
        """Triangle bolts and black holes hurt the player."""
        self.player.update(delta_time)
        for bolt in self.enemy_bolts:
            bolt.update(delta_time)
        hits = [bolt for bolt in self.enemy_bolts
                if bolt.hits(self.player.x, self.player.y, HIT_RADIUS)]
        for bolt in hits:
            self.player.hurt(BOLT_DAMAGE)
        self.enemy_bolts = [bolt for bolt in self.enemy_bolts
                            if bolt.alive and bolt not in hits]

        # Touching a black hole hurts, but only once per cooldown while you stay in it.
        self.black_hole_cooldown = max(0.0, self.black_hole_cooldown - delta_time)
        touching = any(math.hypot(self.player.x - s.x, self.player.y - s.y)
                       < TOUCH_RADIUS + HIT_RADIUS for s in self.spawners)
        if touching and self.black_hole_cooldown == 0:
            self.player.hurt(BLACK_HOLE_DAMAGE)
            self.black_hole_cooldown = BLACK_HOLE_COOLDOWN

        self.floor.update(*self._view_rect())

    def on_draw(self):
        self.clear()
        self.camera.use()
        self.floor.draw(*self._view_rect())
        for spawner in self.spawners:
            spawner.draw()
        for shard in self.shards:
            shard.draw()
        for triangle in self.triangles:
            triangle.draw()
        for bolt in self.enemy_bolts:
            bolt.draw()
        self.player.draw()
        self.weapon.draw_effects()
        self.weapon.draw_held()

        # The health bar stays put on screen, so it's drawn with the window's camera.
        self.window.default_camera.use()
        scale = ui.ui_scale(self.width, self.height)
        margin = HEALTH_BAR_MARGIN * scale
        ui.draw_health_bar(margin, self.height - margin, HEALTH_BAR_WIDTH * scale,
                           HEALTH_BAR_HEIGHT * scale, self.player.health, MAX_HEALTH, scale)

    def on_resize(self, width, height):
        self.camera.match_window()
        self._update_camera()

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x, self.mouse_y = x, y

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.mouse_x, self.mouse_y = x, y

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.weapon.firing = True

    def on_mouse_release(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.weapon.firing = False

    def on_key_press(self, key, modifiers):
        if key in MOVE_KEYS:
            self.keys_held.add(key)

    def on_key_release(self, key, modifiers):
        self.keys_held.discard(key)
