import math

import pyxel

from helper import WIDTH, HEIGHT, wrap_position


class Ship:
    def __init__(self):
        self.x = WIDTH / 2
        self.y = HEIGHT / 2
        self.vx = 0.0
        self.vy = 0.0
        self.angle = -math.pi / 2  # facing up
        self.radius = 5
        self.max_speed = 2.5
        self.thrust = 0.06
        self.brake = 0.04
        self.friction = 0.002

    def update(self):
        # Rotation
        if pyxel.btn(pyxel.KEY_A):
            self.angle -= 0.06
        if pyxel.btn(pyxel.KEY_D):
            self.angle += 0.06

        # Acceleration / reverse acceleration
        if pyxel.btn(pyxel.KEY_W):
            ax = math.cos(self.angle) * self.thrust
            ay = math.sin(self.angle) * self.thrust
            self.vx += ax
            self.vy += ay
        if pyxel.btn(pyxel.KEY_S):
            # reverse thrust: accelerate backwards relative to facing
            ax = -math.cos(self.angle) * self.thrust
            ay = -math.sin(self.angle) * self.thrust
            self.vx += ax
            self.vy += ay

        # Friction
        self.vx *= (1.0 - self.friction)
        self.vy *= (1.0 - self.friction)

        # Clamp speed
        speed = math.hypot(self.vx, self.vy)
        if speed > self.max_speed:
            scale = self.max_speed / speed
            self.vx *= scale
            self.vy *= scale

        # Integrate and wrap
        self.x += self.vx
        self.y += self.vy
        self.x, self.y = wrap_position(self.x, self.y)

    def nose_pos(self):
        return (
            self.x + math.cos(self.angle) * self.radius,
            self.y + math.sin(self.angle) * self.radius,
        )

    def triangle_points(self):
        # Triangle ship points
        nose = self.nose_pos()
        left = (
            self.x + math.cos(self.angle + 2.5) * self.radius,
            self.y + math.sin(self.angle + 2.5) * self.radius,
        )
        right = (
            self.x + math.cos(self.angle - 2.5) * self.radius,
            self.y + math.sin(self.angle - 2.5) * self.radius,
        )
        return nose, left, right

    def draw(self):
        nose, left, right = self.triangle_points()
        # Draw outline triangle (white)
        pyxel.line(int(nose[0]), int(nose[1]), int(left[0]), int(left[1]), 7)
        pyxel.line(int(nose[0]), int(nose[1]), int(right[0]), int(right[1]), 7)
        pyxel.line(int(left[0]), int(left[1]), int(right[0]), int(right[1]), 7)