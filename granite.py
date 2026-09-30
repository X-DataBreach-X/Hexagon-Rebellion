"""Procedurally generated pixel-art gray granite, used behind the menus.

Built from scratch in three layers:
1. Grain clusters: smooth noise picks one of several gray tones for each
   pixel, so tones clump together in irregular patches like crystal grains.
2. Speckles: a few random pixels become dark or light flecks.
3. Jitter: every pixel gets a small random color change, so no two pixels
   are exactly alike.
"""

import numpy as np
from PIL import Image

import arcade
from floor import STONE_COLORS, _value_noise

PIXEL_SIZE = 8       # Screen pixels per granite pixel
SEED = 2026

# Every tone is built from one of the cobblestone floor's stone colors
# (index 4, the olive gray) so the menu matches the game.
BASE_COLOR = STONE_COLORS[4]
GRAIN_TONES = np.array([BASE_COLOR + shift for shift in (-16, -8, 0, 8, 16)])
DARK_FLECK = tuple(BASE_COLOR - 30)
LIGHT_FLECK = tuple(BASE_COLOR + 34)
DARK_FLECK_CHANCE = 0.05
LIGHT_FLECK_CHANCE = 0.04
JITTER = 6           # Max per-pixel color change, up or down


def granite_pixels(width, height):
    """(height, width, 3) array of granite colors."""
    rng = np.random.default_rng(SEED)
    y, x = np.mgrid[0:height, 0:width].astype(float)

    # Two noise sizes blended: medium grains with smaller grains inside them.
    grain = 0.65 * _value_noise(x, y, 3.0, 101) + 0.35 * _value_noise(x, y, 1.5, 102)
    # Add a little randomness so tone boundaries are ragged, not smooth.
    grain = np.clip(grain + rng.uniform(-0.12, 0.12, grain.shape), 0, 0.999)
    color = GRAIN_TONES[(grain * len(GRAIN_TONES)).astype(int)]

    roll = rng.random((height, width))
    color[roll < DARK_FLECK_CHANCE] = DARK_FLECK
    color[roll > 1 - LIGHT_FLECK_CHANCE] = LIGHT_FLECK

    # Shift all three channels together so pixels vary in brightness,
    # with a tiny bit of per-channel difference for color texture.
    shift = rng.integers(-JITTER, JITTER + 1, (height, width, 1))
    tint = rng.integers(-2, 3, (height, width, 3))
    return np.clip(color + shift + tint, 0, 255).astype(np.uint8)


def create_granite_texture(width, height):
    """A granite texture covering at least width x height screen pixels.

    The texture holds one image pixel per granite pixel; draw it scaled by
    PIXEL_SIZE with pixelated=True.
    """
    columns = -(-int(width) // PIXEL_SIZE)
    rows = -(-int(height) // PIXEL_SIZE)
    image = Image.fromarray(granite_pixels(columns, rows), "RGB").convert("RGBA")
    return arcade.Texture(image, hash=f"granite-{SEED}-{columns}x{rows}")
