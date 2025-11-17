import math

import pyxel

from helper import wrap_position


class Bullet:
    def __init__(self, x, y, angle):
        speed = 4.0
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.ttl = 60  # frames
        self.radius = 1

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.x, self.y = wrap_position(self.x, self.y)
        self.ttl -= 1
        return self.ttl > 0

    def draw(self):
        pyxel.circ(int(self.x), int(self.y), self.radius, 10)