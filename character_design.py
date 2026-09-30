"""The player's look, shared by the character screen and the game.

The hexagon is made of 6 triangles ("portions"), named as if its front
corner points up: 1-2 top, 3-4 middle, 5-6 bottom, left then right.
There is one shared design, so a change on the character screen shows up
everywhere the player is drawn, right away.
"""

PORTIONS = range(1, 7)
DEFAULT_COLOR = (255, 255, 255)


class CharacterDesign:
    def __init__(self):
        self.colors = {portion: DEFAULT_COLOR for portion in PORTIONS}


design = CharacterDesign()
