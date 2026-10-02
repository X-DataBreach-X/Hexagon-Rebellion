"""The Armory screen: pick which weapon to take into the game.

Each weapon has its own box, and the boxes sit in a centered row. Each box
shows its weapon playing its idle animation. Clicking a box selects that
weapon.
"""

import arcade

import pixel_font
import ui
from granite import GraniteBackground
from loadout import loadout
from weapons import WEAPON_TYPES

TITLE = "Armory"
TITLE_SCALE = 9
TITLE_TOP = 60                           # Space from the top of the screen to the title
UNDERLINE_COLOR = (255, 255, 255, 110)   # See-through white, like the Character screen
UNDERLINE_THICKNESS = 4
UNDERLINE_GAP = 16                       # Space between the title and the line
UNDERLINE_WIDTH = 0.8                    # Fraction of the screen's width
MARGIN = 40

BACK_BUTTON_WIDTH = 120
BACK_BUTTON_HEIGHT = 40
BACK_BUTTON_TEXT_SCALE = 3

# Sizes are for a 1280x720 window; everything scales with the window.
BOX_SIZE = 200
BOX_GAP = 40                             # Space between boxes
BOX_BORDER = 6
BOX_TEXT_SCALE = 2
WEAPON_PIXEL = 7                         # Screen pixels per art pixel in the boxes (at most)
WEAPON_FILL = 0.85                       # Widest a weapon can be, as a fraction of its box
WEAPON_RAISE = 16                        # How far above the box's center the weapon sits
BOX_LABEL_MARGIN = 24                    # Label's distance from the bottom of its box
SELECTED_COLOR = (176, 176, 176)


class WeaponBox:
    """A selectable box for one weapon: the weapon, animating, with its name below."""

    def __init__(self, weapon):
        self.weapon = weapon
        self.label = weapon.NAME
        self.rect = arcade.XYWH(0, 0, BOX_SIZE, BOX_SIZE)
        self.text_scale = BOX_TEXT_SCALE
        self.label_y = 0
        self.hovered = False
        self.selected = False

    def place(self, center_x, center_y, size, scale):
        self.rect = arcade.XYWH(center_x, center_y, size, size)
        self.scale = scale
        self.text_scale = max(1, round(BOX_TEXT_SCALE * scale))
        self.label_y = (self.rect.bottom + BOX_LABEL_MARGIN * scale
                        + pixel_font.GLYPH_HEIGHT * self.text_scale / 2)

    def contains(self, x, y):
        return self.rect.point_in_rect((x, y))

    def draw(self):
        arcade.draw_rect_filled(self.rect, SELECTED_COLOR if self.selected else ui.BUTTON_COLOR)
        arcade.draw_rect_outline(self.rect, ui.BUTTON_BORDER_COLOR, BOX_BORDER)
        color = ui.TEXT_HOVER_COLOR if self.selected or self.hovered else ui.TEXT_COLOR
        pixel_font.draw_text(self.label, self.rect.x, self.label_y, self.text_scale, color,
                             bold=ui.BUTTON_TEXT_BOLD)

        # The weapon, pointing right, as big as fits (whole pixels keep it crisp).
        art_width = self.weapon.frame().width
        pixel = max(1, min(round(WEAPON_PIXEL * self.scale),
                           int(self.rect.width * WEAPON_FILL / art_width)))
        self.weapon.draw_centered(self.rect.x, self.rect.y + WEAPON_RAISE * self.scale, pixel)


class ArmoryView(arcade.View):
    def __init__(self):
        super().__init__()
        self.background = GraniteBackground(self.width, self.height)
        self.back_button = ui.Button("Back", self.go_back, BACK_BUTTON_TEXT_SCALE)
        self.weapon_boxes = [WeaponBox(weapon_type()) for weapon_type in WEAPON_TYPES]
        self._show_selection()
        self._layout()

    def _layout(self):
        """Position everything for the current window size."""
        scale = ui.ui_scale(self.width, self.height)
        margin = MARGIN * scale

        width, height = BACK_BUTTON_WIDTH * scale, BACK_BUTTON_HEIGHT * scale
        self.back_button.place(margin + width / 2, margin + height / 2, width, height, scale)

        # Title and underline at the top, centered.
        self.title_scale = max(2, round(TITLE_SCALE * scale))
        title_height = pixel_font.GLYPH_HEIGHT * self.title_scale
        self.title_y = self.height - TITLE_TOP * scale - title_height / 2
        self.underline = arcade.XYWH(
            self.width / 2,
            self.title_y - title_height / 2 - UNDERLINE_GAP * scale,
            self.width * UNDERLINE_WIDTH,
            max(2, UNDERLINE_THICKNESS * scale),
        )

        # Weapon boxes: a row centered across the screen, in the space below the underline.
        size, gap = BOX_SIZE * scale, BOX_GAP * scale
        row_width = len(self.weapon_boxes) * size + (len(self.weapon_boxes) - 1) * gap
        center_y = self.underline.bottom / 2
        for i, box in enumerate(self.weapon_boxes):
            x = self.width / 2 - row_width / 2 + size / 2 + i * (size + gap)
            box.place(x, center_y, size, scale)

    def _show_selection(self):
        for i, box in enumerate(self.weapon_boxes):
            box.selected = i == loadout.weapon

    def select_weapon(self, index):
        loadout.weapon = index
        self._show_selection()

    def go_back(self):
        from menu_view import MenuView
        self.window.show_view(MenuView())

    def on_show_view(self):
        self._layout()

    def on_resize(self, width, height):
        self.background.resize(width, height)
        self._layout()

    def on_update(self, delta_time):
        for box in self.weapon_boxes:
            box.weapon.update(delta_time)

    def on_draw(self):
        self.clear()
        self.window.default_camera.use()
        self.background.draw()
        ui.draw_title(TITLE, self.width / 2, self.title_y, self.title_scale, outlined=False)
        arcade.draw_rect_filled(self.underline, UNDERLINE_COLOR)
        for box in self.weapon_boxes:
            box.draw()
        self.back_button.draw()

    def on_mouse_motion(self, x, y, dx, dy):
        ui.update_hover([self.back_button, *self.weapon_boxes], x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if ui.click([self.back_button], x, y):
            return
        for i, box in enumerate(self.weapon_boxes):
            if box.contains(x, y):
                self.select_weapon(i)
                return
