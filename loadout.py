"""What the player takes into the game, shared by the Armory screen and the game.

Like the character design, there is one shared loadout, so a weapon chosen
in the Armory is the one the game uses.
"""

from weapons import WEAPON_TYPES

WEAPONS = [weapon_type.NAME for weapon_type in WEAPON_TYPES]


class Loadout:
    def __init__(self):
        self.weapon = 0   # Index into WEAPONS (and weapons.WEAPON_TYPES)


loadout = Loadout()
