import math
import random

import pyxel

from helper import POWERUP_RADIUS, POWERUP_TTL, wrap_position


class Powerup:
    """Simple powerup entity.
    Types: 'laser' (piercing shots), 'points' (+score), 'bomb' (clear all asteroids).
    """
    def __init__(self, x, y, kind: str):
        self.x = x
        self.y = y
        self.kind = kind
        self.r = POWERUP_RADIUS
        # gentle drift
        ang = random.uniform(0, math.tau)
        spd = random.uniform(0.02, 0.08)
        self.vx = math.cos(ang) * spd
        self.vy = math.sin(ang) * spd
        self.ttl = POWERUP_TTL

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.x, self.y = wrap_position(self.x, self.y)
        self.ttl -= 1
        return self.ttl > 0

    def draw(self, to_screen):
        sx, sy = to_screen(self.x, self.y)
        color = 7
        glyph = "?"
        if self.kind == 'laser':
            color = 12  # orange
            glyph = "L"
        elif self.kind == 'points':
            color = 11  # yellow
            glyph = "+"
        elif self.kind == 'bomb':
            color = 8   # red
            glyph = "B"
        pyxel.circ(int(sx), int(sy), self.r, color)
        # tiny label
        pyxel.text(int(sx) - 1, int(sy) - 2, glyph, 0)