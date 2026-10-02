"""The character screen: a small cobblestone box to test-drive the character.

The left half of the screen is a window onto the middle of the game map,
shown at the same scale as in the level, so the stones and the player are
exactly the size they are during play. The player moves around inside it
with the same controls as in the level. The right half holds the
customization options: one drop-down per portion (triangle) of the hexagon,
in a panel that scrolls with the mouse wheel when it doesn't fit.
"""

import arcade

import pixel_font
import ui
from character_design import MAX_BORDER_THICKNESS, OVERRIDE, design
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
PANEL_TITLE_SCALE = 9                    # A bit smaller than the main menu title
PANEL_TITLE_RAISE = 47                   # How far the title sits above the box's top edge
UNDERLINE_COLOR = (255, 255, 255, 110)   # See-through white
UNDERLINE_THICKNESS = 4
UNDERLINE_GAP = 16                       # Space between the title and the line
UNDERLINE_WIDTH = 0.8                    # Fraction of the right half's width
PANEL_PADDING = 12                       # Extra room around the scrolling panel
SCROLL_SPEED = 40                        # Pixels per mouse-wheel notch

# The hexagon is made of 6 triangles ("portions"), named as if the front
# corner points up: 1-2 top, 3-4 middle, 5-6 bottom, left then right.
# Each portion has a drop-down, plus Portion 0 above them: an override
# that changes all six portions at once. Only one is open at a time.
PORTION_COUNT = 6
DROPDOWN_HEIGHT = 36                     # Height of each "PORTION #" row
DROPDOWN_TEXT_SCALE = 3
DROPDOWN_GAP = 16                        # Space between rows
DROPDOWNS_GAP = 20                       # Space between the underline and the first row

# Options inside an open portion, in two sections:
#   COLOR:   a box showing the color, a color wheel, a hex code box, and a
#            brightness slider with a percent box.
#   BORDERS: a row per border (bottom, left, right) with an on/off button,
#            X (length), Y (thickness) and brightness sliders, each with a
#            percent box, and a color wheel. Portion 0 has a "sides" row instead of left
#            and right, which changes both at once.
OPTIONS_INDENT = 24                      # How far options sit in from the row text
OPTION_TEXT_SCALE = 2
OPTION_TOP_GAP = 10                      # Space between the PORTION row and the first title
OPTION_TITLE_GAP = 10                    # Space between a small title and its controls
OPTION_SECTION_GAP = 20                  # Space between the COLOR and BORDERS sections
OPTION_SPACING = 16                      # Space between controls in a row
SWATCH_SIZE = 28
SWATCH_BORDER = 3
WHEEL_SIZE = 100
HEX_BOX_WIDTH = 110
HEX_BOX_HEIGHT = 32
FILL_SLIDER_WIDTH = 110

BORDER_ROW_HEIGHT = 112
BORDER_ROW_GAP = 8
BORDER_SPACING = 28                      # Space between the button, sliders and wheel
BORDER_BUTTON_WIDTH = 96
BORDER_BUTTON_HEIGHT = 28
SLIDER_WIDTH = 130
# Slider heights in a border row, measured from the row's center.
LENGTH_SLIDER_Y = 38
THICKNESS_SLIDER_Y = 10
BRIGHTNESS_SLIDER_Y = -36                # Its caption sits above it
PERCENT_BOX_GAP = 8                      # Space between a slider and its percent box
PERCENT_BOX_WIDTH = 64
PERCENT_BOX_HEIGHT = 24

# The box looks at this spot on the game map (where the player starts a level).
BOX_CENTER = (WORLD_WIDTH / 2, WORLD_HEIGHT / 2)


class BorderControls:
    """One row of border controls: an on/off button, X/Y sliders (with percent
    boxes) and a color wheel. A row can control more than one side at once
    (Portion 0's "sides" row controls left and right together).
    """

    def __init__(self, view, label, sides):
        self.sides = sides
        self.toggle = ui.ToggleButton(label, lambda: view.toggle_border(self), OPTION_TEXT_SCALE)
        self.length_slider = ui.Slider("X", OPTION_TEXT_SCALE)
        self.thickness_slider = ui.Slider("Y", OPTION_TEXT_SCALE)
        self.brightness_slider = ui.Slider("", OPTION_TEXT_SCALE, caption="Brightness",
                                           align_with="X")
        self.length_box = ui.PercentBox(OPTION_TEXT_SCALE)
        self.thickness_box = ui.PercentBox(OPTION_TEXT_SCALE)
        self.brightness_box = ui.PercentBox(OPTION_TEXT_SCALE)
        self.wheel = ColorWheel()

    def get(self, portion):
        """The settings shown by this row (from its first side)."""
        return design.get_border(portion, self.sides[0])

    def set(self, portion, **changes):
        for side in self.sides:
            design.set_border(portion, side, **changes)


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
        self.open_portion = None   # Key of the open drop-down, or None

        self.color_wheel = ColorWheel()
        self.hex_box = ui.HexColorBox(OPTION_TEXT_SCALE)
        self.fill_brightness_slider = ui.Slider("", OPTION_TEXT_SCALE, caption="Brightness")
        self.fill_brightness_box = ui.PercentBox(OPTION_TEXT_SCALE)
        self.border_rows = {
            "bottom": BorderControls(self, "Bottom", ("bottom",)),
            "left": BorderControls(self, "Left", ("left",)),
            "right": BorderControls(self, "Right", ("right",)),
            "sides": BorderControls(self, "Sides", ("left", "right")),
        }
        # The text box being typed in, and the function that applies its value.
        self.editing = None
        # While the mouse is held on a wheel or slider, this applies each new
        # mouse position to it (so dragging keeps changing the value).
        self.dragging = None

        self.floor = ChunkedFloor(WORLD_WIDTH, WORLD_HEIGHT)
        self.player = Player(*BOX_CENTER)
        self.keys_held = set()
        self.mouse_x = self.mouse_y = 0

        # A second camera that draws only inside the box. Its viewport is where
        # on screen it draws; its projection is set to the same size in game
        # pixels, so nothing is shrunk or stretched (1 game pixel = 1 screen pixel).
        self.box_camera = arcade.Camera2D(position=BOX_CENTER)

        # A third camera for the scrolling options panel. Everything in the
        # panel is laid out as if it weren't scrolled; moving this camera by
        # self.scroll slides it all up, and anything outside the panel is cut off.
        self.panel_camera = arcade.Camera2D()
        self.scroll = 0
        self._layout()

    # ----- Layout -----

    def _layout(self):
        """Position everything for the current window size."""
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

        # The scrolling panel: under the underline, down to the bottom margin.
        padding = PANEL_PADDING * scale
        self.panel = arcade.LRBT(self.underline.left - padding, self.underline.right + padding,
                                 margin, self.underline.bottom - padding / 2)
        self.panel_camera.viewport = self.panel
        self.panel_camera.projection = arcade.XYWH(0, 0, self.panel.width, self.panel.height)

        self._layout_panel()

    def _layout_panel(self):
        """Stack the portion rows (and the open one's options) inside the panel."""
        scale = ui.ui_scale(self.width, self.height)
        row_height = DROPDOWN_HEIGHT * scale
        y = self.underline.bottom - DROPDOWNS_GAP * scale
        for dropdown in self.dropdowns:
            dropdown.place(self.underline.x, y - row_height / 2,
                           self.underline.width, row_height, scale)
            y -= row_height
            if dropdown.expanded:
                y = self._layout_options(y, scale)
            y -= DROPDOWN_GAP * scale

        # How far the panel can scroll: enough to bring the bottom into view.
        self.max_scroll = max(0, self.panel.bottom - y)
        self._set_scroll(self.scroll)

    def _small_title(self, text, x, top):
        """Position for a small left-aligned title whose top edge is at top."""
        height = pixel_font.GLYPH_HEIGHT * self.option_text_scale
        width = pixel_font.text_width(text) * self.option_text_scale
        return (x + width / 2, top - height / 2), top - height

    def _layout_options(self, top, scale):
        """Lay out the open portion's options starting at top. Returns the bottom."""
        self.option_text_scale = max(1, round(OPTION_TEXT_SCALE * scale))
        left = self.underline.left + OPTIONS_INDENT * scale
        spacing = OPTION_SPACING * scale

        # COLOR: color box, wheel, hex box, then brightness slider and its box in a row.
        self.color_title_pos, y = self._small_title("Color", left, top - OPTION_TOP_GAP * scale)
        wheel = WHEEL_SIZE * scale
        row_y = y - OPTION_TITLE_GAP * scale - wheel / 2
        swatch = SWATCH_SIZE * scale
        self.swatch_rect = arcade.LBWH(left, row_y - swatch / 2, swatch, swatch)
        x = left + swatch + spacing
        self.color_wheel.place(x + wheel / 2, row_y, wheel)
        x += wheel + spacing
        width, height = HEX_BOX_WIDTH * scale, HEX_BOX_HEIGHT * scale
        self.hex_box.place(x + width / 2, row_y, width, height, scale)
        x += width + spacing
        self.fill_brightness_slider.place(x, row_y, FILL_SLIDER_WIDTH * scale, scale)
        x += FILL_SLIDER_WIDTH * scale + PERCENT_BOX_GAP * scale
        box_width, box_height = PERCENT_BOX_WIDTH * scale, PERCENT_BOX_HEIGHT * scale
        self.fill_brightness_box.place(x + box_width / 2, row_y, box_width, box_height, scale)
        y = row_y - wheel / 2

        # BORDERS: one row of controls per border (see _open_border_rows).
        self.borders_title_pos, y = self._small_title("Borders", left,
                                                      y - OPTION_SECTION_GAP * scale)
        y -= OPTION_TITLE_GAP * scale
        row_height = BORDER_ROW_HEIGHT * scale
        border_spacing = BORDER_SPACING * scale
        for controls in self._open_border_rows():
            center = y - row_height / 2
            controls.toggle.place(left + BORDER_BUTTON_WIDTH * scale / 2, center,
                                  BORDER_BUTTON_WIDTH * scale, BORDER_BUTTON_HEIGHT * scale,
                                  scale)
            x = left + BORDER_BUTTON_WIDTH * scale + border_spacing

            # X, Y and brightness stacked, each followed by its percent box.
            slider_width = SLIDER_WIDTH * scale
            box_width, box_height = PERCENT_BOX_WIDTH * scale, PERCENT_BOX_HEIGHT * scale
            box_x = x + slider_width + PERCENT_BOX_GAP * scale + box_width / 2
            for slider, box, slider_y in (
                (controls.length_slider, controls.length_box,
                 center + LENGTH_SLIDER_Y * scale),
                (controls.thickness_slider, controls.thickness_box,
                 center + THICKNESS_SLIDER_Y * scale),
                (controls.brightness_slider, controls.brightness_box,
                 center + BRIGHTNESS_SLIDER_Y * scale),
            ):
                slider.place(x, slider_y, slider_width, scale)
                box.place(box_x, slider_y, box_width, box_height, scale)
            x = box_x + box_width / 2 + border_spacing

            controls.wheel.place(x + wheel / 2, center, wheel)
            y -= row_height + BORDER_ROW_GAP * scale
        return y

    def _open_border_rows(self):
        """The border rows for the open portion: bottom, left, right, or for
        Portion 0, bottom and sides."""
        if self.open_portion is None:
            return []
        if self.open_portion == OVERRIDE:
            names = ("bottom", "sides")
        else:
            names = ("bottom", "left", "right")
        return [self.border_rows[name] for name in names]

    def _set_scroll(self, scroll):
        self.scroll = min(max(scroll, 0), self.max_scroll)
        # Point the camera at the panel, shifted down by the scroll amount, so
        # the contents appear shifted up.
        self.panel_camera.position = (self.panel.x, self.panel.y - self.scroll)

    def _to_panel(self, x, y):
        """Convert a screen point to panel coordinates (undoing the scroll)."""
        return x, y - self.scroll

    def _box_bounds(self):
        """The part of the game map inside the box: (left, bottom, right, top)."""
        half = self.box_camera.viewport.width / 2
        x, y = BOX_CENTER
        return x - half, y - half, x + half, y + half

    # ----- Actions -----

    def toggle_portion(self, key):
        """Open a drop-down (closing any other), or close it if it's already open."""
        self._stop_editing()
        self.open_portion = None if self.open_portion == key else key
        for dropdown_key, dropdown in zip(self.portion_keys, self.dropdowns):
            dropdown.expanded = dropdown_key == self.open_portion
        self._layout_panel()

        # Scroll so the opened row is at the top of the panel (as far as possible).
        if self.open_portion is not None:
            header = self.dropdowns[self.portion_keys.index(key)].rect
            gap = DROPDOWNS_GAP / 2 * ui.ui_scale(self.width, self.height)
            self._set_scroll(self.panel.top - gap - header.top)

    def toggle_border(self, controls):
        controls.set(self.open_portion, enabled=not controls.get(self.open_portion).enabled)

    def go_back(self):
        from menu_view import MenuView
        self.window.show_view(MenuView())

    def _panel_buttons(self):
        """Clickable buttons inside the panel."""
        return [*self.dropdowns, *(controls.toggle for controls in self._open_border_rows())]

    def _text_boxes(self):
        """Each text box showing in the open portion, as (box, current value, apply)."""
        portion = self.open_portion
        if portion is None:
            return []
        fill = design.get_fill(portion)
        boxes = [
            (self.hex_box, fill.color, lambda color: design.set_fill_color(portion, color)),
            (self.fill_brightness_box, fill.brightness,
             lambda f: design.set_fill(portion, brightness=f)),
        ]
        for controls in self._open_border_rows():
            border = controls.get(portion)
            boxes.append((controls.length_box, border.length,
                          lambda f, c=controls: c.set(portion, length=f)))
            boxes.append((controls.thickness_box, border.thickness / MAX_BORDER_THICKNESS,
                          lambda f, c=controls: c.set(portion,
                                                      thickness=f * MAX_BORDER_THICKNESS)))
            boxes.append((controls.brightness_box, border.brightness,
                          lambda f, c=controls: c.set(portion, brightness=f)))
        return boxes

    def _stop_editing(self):
        if self.editing:
            self.editing[0].unfocus()
            self.editing = None

    def _drag_target(self, x, y):
        """If (x, y) (in panel coordinates) is on a wheel or slider, return a
        function that applies a mouse position to it. Otherwise None."""
        portion = self.open_portion
        if portion is None:
            return None

        def wheel_target(wheel, apply):
            # Once grabbed, dragging past the edge keeps picking along the edge.
            return lambda px, py: apply(wheel.color_at(px, py, clamp=True))

        if self.color_wheel.color_at(x, y) is not None:
            # Picking a color while it's fully dark brightens it, so the click shows.
            if design.get_fill(portion).brightness == 0:
                design.set_fill(portion, brightness=1.0)
            return wheel_target(self.color_wheel,
                                lambda color: design.set_fill(portion, wheel_color=color))
        slider = self.fill_brightness_slider
        if slider.contains(x, y):
            return lambda px, py: design.set_fill(portion, brightness=slider.fraction_at(px))

        for controls in self._open_border_rows():
            if controls.wheel.color_at(x, y) is not None:
                # Picking a color while it's fully dark brightens it, so the click shows.
                if controls.get(portion).brightness == 0:
                    controls.set(portion, brightness=1.0)
                return wheel_target(controls.wheel,
                                    lambda color, c=controls: c.set(portion, wheel_color=color))
            slider = controls.length_slider
            if slider.contains(x, y):
                return lambda px, py, c=controls, slider=slider: c.set(
                    portion, length=slider.fraction_at(px))
            slider = controls.thickness_slider
            if slider.contains(x, y):
                return lambda px, py, c=controls, slider=slider: c.set(
                    portion, thickness=slider.fraction_at(px) * MAX_BORDER_THICKNESS)
            slider = controls.brightness_slider
            if slider.contains(x, y):
                return lambda px, py, c=controls, slider=slider: c.set(
                    portion, brightness=slider.fraction_at(px))
        return None

    # ----- Events -----

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
        ui.draw_title(PANEL_TITLE, self.panel_x, self.title_y, self.title_scale, outlined=False)
        arcade.draw_rect_filled(self.underline, UNDERLINE_COLOR)

        self.panel_camera.use()
        for dropdown in self.dropdowns:
            dropdown.draw()
        if self.open_portion is not None:
            self._draw_options()

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

    def _draw_options(self):
        portion = self.open_portion
        text_scale = self.option_text_scale
        bold = ui.BUTTON_TEXT_BOLD

        fill = design.get_fill(portion)
        pixel_font.draw_text("Color", *self.color_title_pos, text_scale, ui.TEXT_COLOR, bold=bold)
        arcade.draw_rect_filled(self.swatch_rect, fill.color)
        arcade.draw_rect_outline(self.swatch_rect, ui.BUTTON_BORDER_COLOR, SWATCH_BORDER)
        self.color_wheel.draw(fill.wheel_color)
        self.hex_box.draw(fill.color)
        self.fill_brightness_slider.draw(fill.brightness)
        self.fill_brightness_box.draw(fill.brightness)

        pixel_font.draw_text("Borders", *self.borders_title_pos, text_scale, ui.TEXT_COLOR,
                             bold=bold)
        for controls in self._open_border_rows():
            border = controls.get(portion)
            controls.toggle.on = border.enabled
            controls.toggle.draw()
            controls.length_slider.draw(border.length)
            controls.thickness_slider.draw(border.thickness / MAX_BORDER_THICKNESS)
            controls.length_box.draw(border.length)
            controls.thickness_box.draw(border.thickness / MAX_BORDER_THICKNESS)
            controls.brightness_slider.draw(border.brightness)
            controls.brightness_box.draw(border.brightness)
            controls.wheel.draw(border.wheel_color)

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x, self.mouse_y = x, y
        self._update_hover()

    def _update_hover(self):
        x, y = self.mouse_x, self.mouse_y
        ui.update_hover([self.back_button], x, y)
        in_panel = self.panel.point_in_rect((x, y))
        px, py = self._to_panel(x, y)
        for button in self._panel_buttons():
            button.hovered = in_panel and button.contains(px, py)
        for box, _, _ in self._text_boxes():
            box.hovered = in_panel and box.contains(px, py)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if self.panel.point_in_rect((x, y)):
            self._set_scroll(self.scroll - scroll_y * SCROLL_SPEED)
            self._update_hover()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.mouse_x, self.mouse_y = x, y
        if self.dragging:
            self.dragging(*self._to_panel(x, y))

    def on_mouse_press(self, x, y, button, modifiers):
        if ui.click([self.back_button], x, y):
            return
        self._stop_editing()
        if not self.panel.point_in_rect((x, y)):
            return
        px, py = self._to_panel(x, y)

        for box, current, apply in self._text_boxes():
            if box.contains(px, py):
                box.focus(current)
                self.editing = (box, apply)
                self.keys_held.clear()   # Stop walking; keys now type into the box
                return
        self.dragging = self._drag_target(px, py)
        if self.dragging:
            self.dragging(px, py)
        else:
            ui.click(self._panel_buttons(), px, py)

    def on_mouse_release(self, x, y, button, modifiers):
        self.dragging = None

    def on_text(self, text):
        """Typed characters go into the text box being edited, if there is one."""
        if not self.editing:
            return
        box, apply = self.editing
        for char in text:
            value = box.type_char(char)
            if value is not None:
                apply(value)

    def on_key_press(self, key, modifiers):
        if self.editing:
            # While typing in a box, keys edit it instead of moving the player.
            box, apply = self.editing
            if key == arcade.key.BACKSPACE:
                value = box.backspace()
                if value is not None:
                    apply(value)
            elif key in (arcade.key.ENTER, arcade.key.NUM_ENTER, arcade.key.ESCAPE):
                self._stop_editing()
            return
        if key in MOVE_KEYS:
            self.keys_held.add(key)

    def on_key_release(self, key, modifiers):
        self.keys_held.discard(key)
