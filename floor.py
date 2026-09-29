"""Procedurally generated pixel-art cobblestone floor.

The floor is built from square "blocks" (chunky pixels). Each block is
colored based on which cobblestone it belongs to, how close it is to the
stone's edge, and a moss map. Every block is drawn as a BLOCK_SIZE x
BLOCK_SIZE square on screen.

Techniques used (standard procedural-generation math, written from scratch):
- Weighted Voronoi cells for stones: each stone has a center and a size
  weight, and a block belongs to whichever stone is "closest" once distance
  is divided by that stone's size. Bigger weights claim more blocks.
- Fractal value noise with domain warping for moss: several layers of
  smooth noise are added together, and the sample position is bent by
  another noise field so patches grow in irregular, natural-looking shapes.
- Chunking: the world is far too big to hold as one image, so it is split
  into square chunks that are generated when they come near the screen and
  thrown away when they're far off. Every block's color comes from a hash
  of its position, so a regenerated chunk looks exactly the same.

numpy is used to compute a whole chunk of blocks at once instead of one
block at a time, which is fast enough to generate chunks while the game runs.
"""

import math

import arcade
import numpy as np
from PIL import Image

BLOCK_SIZE = 8        # Screen pixels per floor block
STONE_SIZE = 7        # Average cobblestone width, in blocks
MOSS_SCALE = 18       # Size of the largest moss patches, in blocks
MOSS_AMOUNT = 0.5     # 0 = no moss, 1 = moss everywhere
SEED = 310

CHUNK_BLOCKS = 64                         # Chunk width/height, in blocks
CHUNK_PIXELS = CHUNK_BLOCKS * BLOCK_SIZE  # Chunk width/height, in pixels
PREFETCH_CHUNKS = 1   # Extra ring of chunks generated just off screen
KEEP_CHUNKS = 3       # Chunks further off screen than this are thrown away
PREFETCH_PER_FRAME = 1

# Chance of each stone size, and the range of size weights for it.
STONE_SIZES = [
    (0.60, 0.90, 1.10),   # average
    (0.25, 1.25, 1.45),   # a little bigger
    (0.15, 0.55, 0.70),   # really small
]
PEBBLE_CHANCE = 0.2   # Chance of an extra tiny stone squeezed into a cell

MORTAR = (38, 36, 40)
PEBBLE = (74, 72, 76)
CRACK = (58, 56, 60)
STONE_COLORS = np.array([
    (112, 110, 108),
    (98, 97, 102),
    (124, 119, 111),
    (90, 92, 97),
    (105, 103, 96),
    (80, 81, 88),     # dark slate
    (134, 128, 118),  # pale sandstone
    (116, 121, 128),  # cool blue-gray
])
MOSS_DARK = (46, 78, 40)
MOSS_MID = (68, 108, 50)
MOSS_LIGHT = (96, 138, 62)

_MASK = 0xFFFFFFFF


def _rand(x, y, salt=0):
    """Repeatable pseudo-random floats in [0, 1) for integer grid points.

    Works on whole numpy arrays at once. The math wraps around at 32 bits,
    so any integer position (even negative) gives a stable result.
    """
    x = np.asarray(x, dtype=np.int64).astype(np.uint64)
    y = np.asarray(y, dtype=np.int64).astype(np.uint64)
    salt = np.asarray(salt, dtype=np.int64).astype(np.uint64)
    h = (x * 374761393 + y * 668265263 + salt * 2246822519 + SEED) & _MASK
    h = ((h ^ (h >> 13)) * 1274126177) & _MASK
    h ^= h >> 16
    return h / 0x100000000


def _value_noise(x, y, scale, salt):
    """Smooth 0-1 noise: random values on a grid, blended between points."""
    fx, fy = x / scale, y / scale
    ix, iy = np.floor(fx), np.floor(fy)
    tx, ty = fx - ix, fy - iy
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    ix, iy = ix.astype(np.int64), iy.astype(np.int64)
    top = _rand(ix, iy, salt) * (1 - tx) + _rand(ix + 1, iy, salt) * tx
    bottom = _rand(ix, iy + 1, salt) * (1 - tx) + _rand(ix + 1, iy + 1, salt) * tx
    return top * (1 - ty) + bottom * ty


def _moss_amount(x, y):
    """How mossy each spot is (0-1), shaped to look like natural growth."""
    # Domain warp: bend the sample position so patches aren't grid-shaped.
    warp = MOSS_SCALE * 0.6
    wx = x + (_value_noise(x, y, MOSS_SCALE * 1.3, 11) - 0.5) * 2 * warp
    wy = y + (_value_noise(x, y, MOSS_SCALE * 1.3, 12) - 0.5) * 2 * warp

    # Fractal noise: big patches + medium clumps + fine ragged edges.
    moss = (
        0.55 * _value_noise(wx, wy, MOSS_SCALE, 13)
        + 0.30 * _value_noise(wx, wy, MOSS_SCALE / 2.5, 14)
        + 0.15 * _value_noise(x, y, MOSS_SCALE / 6, 15)
    )
    return moss + (MOSS_AMOUNT - 0.5) * 0.5


def _cell_stones(i, j):
    """Stone data for grid cells (i, j): one main stone, maybe a pebble."""
    roll = _rand(i, j, 6)
    is_average = roll < STONE_SIZES[0][0]
    is_big = ~is_average & (roll - STONE_SIZES[0][0] < STONE_SIZES[1][0])
    low = np.select([is_average, is_big], [STONE_SIZES[0][1], STONE_SIZES[1][1]],
                    STONE_SIZES[2][1])
    high = np.select([is_average, is_big], [STONE_SIZES[0][2], STONE_SIZES[1][2]],
                     STONE_SIZES[2][2])
    size = low + _rand(i, j, 8) * (high - low)
    cx = i * STONE_SIZE + 1 + _rand(i, j, 1) * (STONE_SIZE - 2)
    cy = j * STONE_SIZE + 1 + _rand(i, j, 2) * (STONE_SIZE - 2)

    has_pebble = _rand(i, j, 9) < PEBBLE_CHANCE
    px = i * STONE_SIZE + _rand(i, j, 10) * STONE_SIZE
    py = j * STONE_SIZE + _rand(i, j, 16) * STONE_SIZE
    return (cx, cy, size), (px, py, has_pebble)


def _nearest_stones(x, y):
    """For each block, find the stone that owns it and its distance to an edge."""
    gx, gy = x // STONE_SIZE, y // STONE_SIZE

    # Work out every stone near this area once, then look them up per block.
    i0, j0 = gx.min() - 2, gy.min() - 2
    ci, cj = np.meshgrid(np.arange(i0, gx.max() + 3), np.arange(j0, gy.max() + 3),
                         indexing="ij")
    (scx, scy, ssize), (pcx, pcy, has_pebble) = _cell_stones(ci, cj)

    px, py = x + 0.5, y + 0.5
    best = np.full(x.shape, np.inf)
    second = np.full(x.shape, np.inf)
    owner = {name: np.zeros(x.shape) for name in ("cx", "cy", "size", "i", "j", "k")}

    def consider(d, cx, cy, size, i, j, k):
        closer = d < best
        second[...] = np.where(closer, best, np.minimum(second, d))
        best[...] = np.where(closer, d, best)
        for name, value in (("cx", cx), ("cy", cy), ("size", size),
                            ("i", i), ("j", j), ("k", k)):
            owner[name] = np.where(closer, value, owner[name])

    # Search 2 cells out, since big stones can reach past their own cell.
    for di in range(-2, 3):
        for dj in range(-2, 3):
            i, j = gx + di, gy + dj
            a, b = i - i0, j - j0
            cx, cy, size = scx[a, b], scy[a, b], ssize[a, b]
            consider(np.hypot(px - cx, py - cy) / size, cx, cy, size, i, j, 0)

            cx, cy = pcx[a, b], pcy[a, b]
            d = np.where(has_pebble[a, b], np.hypot(px - cx, py - cy) / 0.55, np.inf)
            consider(d, cx, cy, 0.55, i, j, 1)

    # Convert the weighted gap back into roughly "blocks from the edge".
    edge = (second - best) * owner["size"]
    return owner, edge


def generate_blocks(x0, y0, width, height):
    """Colors for a width x height area of blocks starting at (x0, y0).

    Block y counts downward, like image rows. Returns a (height, width, 3)
    array of RGB values.
    """
    y, x = np.mgrid[y0:y0 + height, x0:x0 + width]
    owner, edge = _nearest_stones(x, y)
    moss = _moss_amount(x, y)
    r = _rand(x, y, 3)

    # Stones: base color per stone, slight per-block variation, then a bevel.
    # Light comes from the top-left, so those edges are brighter. Small
    # stones get a thinner bevel so they don't turn solid light/dark.
    shade_index = (_rand(owner["i"].astype(np.int64), owner["j"].astype(np.int64),
                         owner["k"].astype(np.int64)) * len(STONE_COLORS)).astype(int)
    color = STONE_COLORS[shade_index]
    color = np.clip(color + np.trunc((_rand(x, y, 5) - 0.5) * 10)[..., None], 0, 255)
    bevel = edge < np.minimum(2.0, 1.0 + owner["size"])
    facing_light = (x + 0.5 - owner["cx"]) + (y + 0.5 - owner["cy"]) < 0
    bevel_shade = np.where(facing_light, 22, -24)
    color = np.where(bevel[..., None],
                     np.clip(color + bevel_shade[..., None], 0, 255), color)

    # Small surface details.
    crack = r < 0.035
    fleck = ~crack & (r > 0.975)
    moss_spot = ~crack & ~fleck & (moss > 0.68) & (r < 0.18)
    color = np.where(fleck[..., None], np.clip(color + 28, 0, 255), color)
    color[crack] = CRACK
    color[moss_spot] = MOSS_DARK

    # Moss creeps further over stone edges where it grows thickest.
    creep = 1.0 + np.maximum(0.0, moss - 0.55) * 12
    mortar = edge < 1.0
    moss_edge = ~mortar & (moss > 0.55) & (edge < creep) & (r < 0.75)
    color[moss_edge & (r < 0.25)] = MOSS_LIGHT
    color[moss_edge & (r >= 0.25)] = MOSS_MID

    # Gaps between stones: dark mortar, filled with moss in mossy areas.
    heavy = moss > 0.52
    light = ~heavy & (moss > 0.46) & (r < 0.35)
    pebble = ~heavy & ~light & (r < 0.08)
    color[mortar] = MORTAR
    color[mortar & pebble] = PEBBLE
    color[mortar & (heavy | light)] = MOSS_DARK
    color[mortar & heavy & (r < 0.6)] = MOSS_MID

    return color.astype(np.uint8)


class ChunkedFloor:
    """Draws the floor for a huge world by generating chunks on demand."""

    def __init__(self, world_width, world_height):
        self.max_chunk_x = math.ceil(world_width / CHUNK_PIXELS) - 1
        self.max_chunk_y = math.ceil(world_height / CHUNK_PIXELS) - 1
        self.chunks = {}

    def _chunk_range(self, left, bottom, width, height, margin):
        """Chunk coordinates covering a view rectangle, plus a margin."""
        x_start = max(0, math.floor(left / CHUNK_PIXELS) - margin)
        x_end = min(self.max_chunk_x, math.floor((left + width) / CHUNK_PIXELS) + margin)
        y_start = max(0, math.floor(bottom / CHUNK_PIXELS) - margin)
        y_end = min(self.max_chunk_y, math.floor((bottom + height) / CHUNK_PIXELS) + margin)
        return [(cx, cy) for cx in range(x_start, x_end + 1)
                for cy in range(y_start, y_end + 1)]

    def _get_chunk(self, cx, cy):
        if (cx, cy) not in self.chunks:
            # World y points up but image rows point down, so the chunk's top
            # row is the one furthest up in the world.
            top_row = -(cy + 1) * CHUNK_BLOCKS
            blocks = generate_blocks(cx * CHUNK_BLOCKS, top_row, CHUNK_BLOCKS, CHUNK_BLOCKS)
            image = Image.fromarray(blocks, "RGB").convert("RGBA")
            self.chunks[(cx, cy)] = arcade.Texture(image, hash=f"floor-{SEED}-{cx}-{cy}")
        return self.chunks[(cx, cy)]

    def update(self, left, bottom, width, height):
        """Generate a few chunks just off screen and drop far-away ones."""
        budget = PREFETCH_PER_FRAME
        for key in self._chunk_range(left, bottom, width, height, PREFETCH_CHUNKS):
            if budget == 0:
                break
            if key not in self.chunks:
                self._get_chunk(*key)
                budget -= 1

        # Arcade frees a texture's GPU memory once nothing references it.
        keep = set(self._chunk_range(left, bottom, width, height, KEEP_CHUNKS))
        for key in [key for key in self.chunks if key not in keep]:
            del self.chunks[key]

    def draw(self, left, bottom, width, height):
        """Draw every chunk that overlaps the view rectangle."""
        for cx, cy in self._chunk_range(left, bottom, width, height, 0):
            arcade.draw_texture_rect(
                self._get_chunk(cx, cy),
                arcade.LBWH(cx * CHUNK_PIXELS, cy * CHUNK_PIXELS, CHUNK_PIXELS, CHUNK_PIXELS),
                pixelated=True,
            )
