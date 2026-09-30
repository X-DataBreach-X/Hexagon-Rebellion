"""The character screen: a small cobblestone box to test-drive the character.

The left half of the screen is a window onto the middle of the game map,
shown at the same scale as in the level, so the stones and the player are
exactly the size they are during play. The player moves around inside it
with the same controls as in the level. The right half holds the
customization options: one drop-down per portion (triangle) of the hexagon.
"""

import arcade

import pixel_font
import ui
from character_design import design
from color_wheel import ColorWheel
from floor import ChunkedFloor
from game_view import MOVE_KEYS, WORLD_HEIGHT, WORLD_WIDTH
from granite import GraniteBackground
from player import Player

BOX_BORDER = 6
BOX_BORDER_COLOR = (0, 0, 0)
BOX_FILL = 0.75     # Box size as a fraction of the space available on the left half
MARGIN = 40         # Space from the screen edges

BACK_BUTTON_WIDTH = 120
BACK_BUTTON_HEIGHT = 40
BACK_BUTTON_TEXT_SCALE = 3

PANEL_TITLE = "Character"
PANEL_TITLE_SCALE = 8                    # A bit smaller than the main menu title
PANEL_TITLE_RAISE = 40                   # How far the title sits above the box's top edge
UNDERLINE_COLOR = (255, 255, 255, 110)   # See-through white
UNDERLINE_THICKNESS = 4
UNDERLINE_GAP = 16                       # Space between the title and the line
UNDERLINE_WIDTH = 0.8                    # Fraction of the right half's width

# The hexagon is made of 6 triangles ("portions"), named as if the front
# corner points up: 1-2 top, 3-4 middle, 5-6 bottom, left then right.
# Each portion has a drop-down, plus Portion 0 above them: an override
# that changes all six portions at once. Only one is open at a time.
PORTION_COUNT = 6
OVERRIDE = 0                             # Portion 0 is the override
DROPDOWN_HEIGHT = 36                     # Height of each "PORTION #" row
DROPDOWN_TEXT_SCALE = 3
DROPDOWN_GAP = 16                        # Space between rows
DROPDOWNS_GAP = 20                       # Space between the underline and the first row
OPTIONS_HEIGHT = 110                     # Height of an open portion's options (1-6)

# Options inside an open portion: a "COLOR" label, a box showing the
# selected color, then the color wheel.
OPTIONS_INDENT = 24                      # How far options sit in from the row text
OPTION_TEXT_SCALE = 2
OPTION_SPACING = 16                      # Space between the label, color box and wheel
SWATCH_SIZE = 28
SWATCH_BORDER = 3
WHEEL_SIZE = 100

# The box looks at this spot on the game map (where the player starts a level).
BOX_CENTER = (WORLD_WIDTH / 2, WORLD_HEIGHT / 2)


class CharacterView(arcade.View):
    def __init__(self):
        super().__init__()
        self.background = GraniteBackground(self.width, self.height)
        self.back_button = ui.Button("Back", self.go_back, BACK_BUTTON_TEXT_SCALE)
        # Drop-downs are keyed by portion number: 0 (override), then 1-6.
        self.portion_keys = list(range(OVERRIDE, PORTION_COUNT + 1))
        self.dropdowns = [
            ui.DropdownHeader(f"Portion {key}", lambda key=key: self.toggle_portion(key),
                              DROPDOWN_TEXT_SCALE)
            for key in self.portion_keys
        ]
        self.buttons = [self.back_button, *self.dropdowns]
        self.open_portion = None   # Key of the open drop-down, or None

        self.color_wheel = ColorWheel()
        self.picking_color = False  # True while dragging on the color wheel

        self.floor = ChunkedFloor(WORLD_WIDTH, WORLD_HEIGHT)
        self.player = Player(*BOX_CENTER)
        self.keys_held = set()
        self.mouse_x = self.mouse_y = 0

        # A second camera that draws only inside the box. Its viewport is where
        # on screen it draws; its projection is set to the same size in game
        # pixels, so nothing is shrunk or stretched (1 game pixel = 1 screen pixel).
        self.box_camera = arcade.Camera2D(position=BOX_CENTER)
        self._layout()

    def _layout(self):
        """Position the Back button and the box for the current window size."""
        scale = ui.ui_scale(self.width, self.height)
        margin = MARGIN * scale

        # Back button in the bottom-left corner.
        width, height = BACK_BUTTON_WIDTH * scale, BACK_BUTTON_HEIGHT * scale
        self.back_button.place(margin + width / 2, margin + height / 2, width, height, scale)

        # The box is centered in the left half of the screen.
        available = min(self.width / 2 - 2 * margin, self.height - 2 * margin)
        side = max(1, available * BOX_FILL)
        self.box_camera.viewport = arcade.XYWH(self.width / 4, self.height / 2, side, side)
        self.box_camera.projection = arcade.XYWH(0, 0, side, side)

        # Right half: the title sits a little above the top of the box.
        self.panel_x = self.width * 3 / 4
        panel_width = self.width / 2
        fit = int(panel_width * 0.9 / pixel_font.text_width(PANEL_TITLE))
        self.title_scale = max(2, min(round(PANEL_TITLE_SCALE * scale), fit))
        title_height = pixel_font.GLYPH_HEIGHT * self.title_scale
        self.title_y = (self.box_camera.viewport.top - title_height / 2
                        + PANEL_TITLE_RAISE * scale)

        self.underline = arcade.XYWH(
            self.panel_x,
            self.title_y - title_height / 2 - UNDERLINE_GAP * scale,
            panel_width * UNDERLINE_WIDTH,
            max(2, UNDERLINE_THICKNESS * scale),
        )

        self._layout_dropdowns()

    def _layout_dropdowns(self):
        """Stack the portion rows under the underline, leaving room under the open one."""
        scale = ui.ui_scale(self.width, self.height)
        row_height = DROPDOWN_HEIGHT * scale
        y = self.underline.bottom - DROPDOWNS_GAP * scale
        self.options_area = None
        for key, dropdown in zip(self.portion_keys, self.dropdowns):
            dropdown.place(self.underline.x, y - row_height / 2,
                           self.underline.width, row_height, scale)
            y -= row_height
            if dropdown.expanded:
                # The open portion's options go in this space. Portion 0
                # (the override) has no options yet.
                options_height = 0 if key == OVERRIDE else OPTIONS_HEIGHT * scale
                self.options_area = arcade.LRBT(self.underline.left, self.underline.right,
                                                y - options_height, y)
                y -= options_height
            y -= DROPDOWN_GAP * scale

        if self.options_area and self.options_area.height:
            self._layout_color_option(scale)

    def _layout_color_option(self, scale):
        """Place the COLOR label, color box and wheel in a row inside the options area."""
        area = self.options_area
        x = area.left + OPTIONS_INDENT * scale
        self.option_text_scale = max(1, round(OPTION_TEXT_SCALE * scale))

        label_width = pixel_font.text_width("Color") * self.option_text_scale
        self.color_label_pos = (x + label_width / 2, area.y)
        x += label_width + OPTION_SPACING * scale

        swatch = SWATCH_SIZE * scale
        self.swatch_rect = arcade.LBWH(x, area.y - swatch / 2, swatch, swatch)
        x += swatch + OPTION_SPACING * scale

        wheel = WHEEL_SIZE * scale
        self.color_wheel.place(x + wheel / 2, area.y, wheel)

    def _box_bounds(self):
        """The part of the game map inside the box: (left, bottom, right, top)."""
        half = self.box_camera.viewport.width / 2
        x, y = BOX_CENTER
        return x - half, y - half, x + half, y + half

    def toggle_portion(self, key):
        """Open a drop-down (closing any other), or close it if it's already open."""
        self.open_portion = None if self.open_portion == key else key
        for dropdown_key, dropdown in zip(self.portion_keys, self.dropdowns):
            dropdown.expanded = dropdown_key == self.open_portion
        self._layout_dropdowns()

    def _pick_color(self, x, y):
        """If (x, y) is on the wheel, give the open portion that color. Returns True if so."""
        if self.open_portion not in design.colors:
            return False
        cell = self.color_wheel.cell_at(x, y)
        if cell is None:
            return False
        design.colors[self.open_portion] = ColorWheel.colors[cell]
        return True

    def go_back(self):
        from menu_view import MenuView
        self.window.show_view(MenuView())

    def on_show_view(self):
        self._layout()

    def on_resize(self, width, height):
        self.background.resize(width, height)
        self._layout()

    def on_update(self, delta_time):
        dx = sum(MOVE_KEYS[key][0] for key in self.keys_held)
        dy = sum(MOVE_KEYS[key][1] for key in self.keys_held)
        self.player.move(dx, dy, delta_time, self._box_bounds())

        # Turn the on-screen mouse position into a spot on the map.
        target = self.box_camera.unproject((self.mouse_x, self.mouse_y))
        self.player.face(target.x, target.y)

    def on_draw(self):
        self.clear()
        self.window.default_camera.use()
        self.background.draw()
        self.back_button.draw()
        ui.draw_title(PANEL_TITLE, self.panel_x, self.title_y, self.title_scale)
        arcade.draw_rect_filled(self.underline, UNDERLINE_COLOR)
        for dropdown in self.dropdowns:
            dropdown.draw()
        if self.open_portion in design.colors:
            self._draw_color_option()

        self.box_camera.use()
        left, bottom, right, top = self._box_bounds()
        self.floor.draw(left, bottom, right - left, top - bottom)
        self.player.draw()

        self.window.default_camera.use()
        # Grow the rectangle by half the border so the border sits outside the box.
        box = self.box_camera.viewport
        arcade.draw_rect_outline(
            arcade.XYWH(box.x, box.y, box.width + BOX_BORDER, box.height + BOX_BORDER),
            BOX_BORDER_COLOR, BOX_BORDER,
        )

    def _draw_color_option(self):
        color = design.colors[self.open_portion]
        pixel_font.draw_text("Color", *self.color_label_pos, self.option_text_scale,
                             ui.TEXT_COLOR, bold=ui.BUTTON_TEXT_BOLD)
        arcade.draw_rect_filled(self.swatch_rect, color)
        arcade.draw_rect_outline(self.swatch_rect, ui.BUTTON_BORDER_COLOR, SWATCH_BORDER)
        self.color_wheel.draw(color)

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x, self.mouse_y = x, y
        ui.update_hover(self.buttons, x, y)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.mouse_x, self.mouse_y = x, y
        if self.picking_color:
            self._pick_color(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if self._pick_color(x, y):
            self.picking_color = True
        else:
            ui.click(self.buttons, x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        self.picking_color = False

    def on_key_press(self, key, modifiers):
        if key in MOVE_KEYS:
            self.keys_held.add(key)

    def on_key_release(self, key, modifiers):
        self.keys_held.discard(key)
