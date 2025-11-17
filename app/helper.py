import math

import pyxel

WIDTH = 320
HEIGHT = 240


def wrap_position(x: float, y: float):
    if x < 0:
        x += WIDTH
    elif x >= WIDTH:
        x -= WIDTH
    if y < 0:
        y += HEIGHT
    elif y >= HEIGHT:
        y -= HEIGHT
    return x, y


def toroidal_dist_sq(x1, y1, x2, y2):
    dx = abs(x1 - x2)
    dy = abs(y1 - y2)
    dx = min(dx, WIDTH - dx)
    dy = min(dy, HEIGHT - dy)
    return dx * dx + dy * dy

def toroidal_dist(x1, y1, x2, y2):
    dx = abs(x1 - x2)
    dy = abs(y1 - y2)
    dx = min(dx, WIDTH - dx)
    dy = min(dy, HEIGHT - dy)
    return math.sqrt(dx * dx + dy * dy)


def draw_centered_text(y: int, text: str, color: int):
    w = len(text)*4
    x = (pyxel.width - w)//2
    pyxel.text(x, y, text, color)


# Gameplay tuning
# Minimum toroidal distance from ship for spawning fresh asteroids
SAFE_SPAWN_DIST = WIDTH//2  # pixels
# Dynamic difficulty: minimum asteroids scales with score
# Base minimum on screen (auto-replenished if below)
BASE_MIN_ASTEROIDS = 10
# Every DIFFICULTY_SCORE_STEP points, raise the minimum by ASTEROIDS_PER_STEP
DIFFICULTY_SCORE_STEP = 100
ASTEROIDS_PER_STEP = 2
# Cap the minimum to avoid overwhelming the screen
MAX_MIN_ASTEROIDS = 16

# Powerup tuning
# How often to try spawning a powerup (in frames) and maximum concurrent powerups
POWERUP_SPAWN_MIN = 480  # 8 seconds at 60fps
POWERUP_SPAWN_MAX = 900  # 15 seconds
POWERUP_CAP = 3
POWERUP_TTL = 20 * 60  # 20 seconds lifetime
POWERUP_RADIUS = 4
LASER_POWER_DURATION = 12 * 60  # 12 seconds of piercing bullets
POINTS_POWER_VALUE = 50
EXPLOSION_SPD = 3