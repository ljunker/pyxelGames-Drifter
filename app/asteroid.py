import math
import random

import pyxel

from helper import WIDTH, HEIGHT, wrap_position


class Asteroid:
    def __init__(self, x=None, y=None, r=8):
        self.x = x if x is not None else random.uniform(0, WIDTH)
        self.y = y if y is not None else random.uniform(0, HEIGHT)
        angle = random.uniform(0, math.tau)
        # Slower default asteroid speed
        speed = random.uniform(0.08, 0.4)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.r = r

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.x, self.y = wrap_position(self.x, self.y)

    def draw(self):
        pyxel.circb(int(self.x), int(self.y), int(self.r), 5)