"""A small hand-made 5x7 pixel font for titles and buttons.

Each letter is a grid of 7 rows, where "#" is a filled pixel. Text is
rendered into a tiny image (1 image pixel per font pixel) and then drawn
scaled up with pixelated filtering, so every font pixel becomes a crisp
square on screen.
"""

import arcade
from PIL import Image

GLYPH_HEIGHT = 7
LETTER_SPACING = 1   # Empty columns between letters
SPACE_WIDTH = 3

GLYPHS = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    "J": ["..###", "...#.", "...#.", "...#.", "#..#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
}

_texture_cache = {}


def text_width(text):
    """Width of the text in font pixels (before scaling)."""
    widths = [SPACE_WIDTH if ch == " " else len(GLYPHS[ch][0]) for ch in text.upper()]
    return sum(widths) + LETTER_SPACING * (len(widths) - 1)


def text_texture(text, color):
    """A texture of the text at 1 image pixel per font pixel."""
    text = text.upper()
    key = (text, tuple(color))
    if key not in _texture_cache:
        image = Image.new("RGBA", (text_width(text), GLYPH_HEIGHT), (0, 0, 0, 0))
        x = 0
        for ch in text:
            if ch == " ":
                x += SPACE_WIDTH + LETTER_SPACING
                continue
            glyph = GLYPHS[ch]
            for row, line in enumerate(glyph):
                for col, cell in enumerate(line):
                    if cell == "#":
                        image.putpixel((x + col, row), (*color, 255))
            x += len(glyph[0]) + LETTER_SPACING
        _texture_cache[key] = arcade.Texture(image, hash=f"pixeltext-{text}-{key[1]}")
    return _texture_cache[key]


def _draw_texture(texture, center_x, center_y, scale):
    arcade.draw_texture_rect(
        texture,
        arcade.XYWH(center_x, center_y, texture.width * scale, texture.height * scale),
        pixelated=True,
    )


def draw_text(text, center_x, center_y, scale, color,
              bold=0, outline=0, outline_color=(255, 255, 255)):
    """Draw pixel text centered on a point.

    scale: screen pixels per font pixel.
    bold: thickens the strokes by this many screen pixels.
    outline: draws a border this many screen pixels thick around the text.
    """
    texture = text_texture(text, color)
    # Bold works by stamping the text a few times, shifted right and down,
    # then centering the combined result.
    stamps = [(dx, -dy) for dx in range(bold + 1) for dy in range(bold + 1)]
    center_x -= bold / 2
    center_y += bold / 2

    if outline:
        border = text_texture(text, outline_color)
        for sx, sy in stamps:
            for ox in (-outline, 0, outline):
                for oy in (-outline, 0, outline):
                    if ox or oy:
                        _draw_texture(border, center_x + sx + ox, center_y + sy + oy, scale)

    for sx, sy in stamps:
        _draw_texture(texture, center_x + sx, center_y + sy, scale)
