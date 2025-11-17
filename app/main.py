import math
import random
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


def draw_centered_text(y: int, text: str, color: int):
    w = len(text)*4
    x = (pyxel.width - w)//2
    pyxel.text(x, y, text, color)


# Gameplay tuning
# Minimum toroidal distance from ship for spawning fresh asteroids
SAFE_SPAWN_DIST = 80  # pixels
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
        pyxel.text(int(sx) - 2, int(sy) - 2, glyph, 0)


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


class App:
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT, fps=60, title="Drifter - Asteroids Prototype")
        self.ship = Ship()
        self.bullets = []
        # Initialize score first so difficulty-based counts use it
        self.score = 0
        # Spawn initial asteroids away from the ship using difficulty-based minimum
        self.asteroids = [self.spawn_asteroid_away(SAFE_SPAWN_DIST) for _ in range(self.current_min_asteroids())]
        self.shoot_cooldown = 0
        self.ship_alive = True
        # Powerups
        self.powerups = []
        self.powerup_spawn_timer = random.randint(POWERUP_SPAWN_MIN, POWERUP_SPAWN_MAX)
        self.laser_timer = 0
        pyxel.run(self.update, self.draw)

    def current_min_asteroids(self) -> int:
        """Compute current minimum asteroid count based on score for difficulty ramp."""
        steps = self.score // DIFFICULTY_SCORE_STEP
        target = BASE_MIN_ASTEROIDS + steps * ASTEROIDS_PER_STEP
        return max(BASE_MIN_ASTEROIDS, min(MAX_MIN_ASTEROIDS, int(target)))

    def spawn_asteroid_away(self, min_dist: float, r: int | None = None) -> "Asteroid":
        """Spawn a new asteroid at a random position at least min_dist away from the ship (toroidal).
        Falls back after a number of attempts by relaxing the constraint slightly to avoid infinite loops.
        """
        sx, sy = self.ship.x, self.ship.y

        def toroidal_dist_sq(x1, y1, x2, y2):
            dx = abs(x1 - x2)
            dy = abs(y1 - y2)
            dx = min(dx, WIDTH - dx)
            dy = min(dy, HEIGHT - dy)
            return dx * dx + dy * dy

        attempts = 0
        max_attempts = 256
        min_dist_sq = min_dist * min_dist
        chosen = None
        while attempts < max_attempts:
            attempts += 1
            x = random.uniform(0, WIDTH)
            y = random.uniform(0, HEIGHT)
            if toroidal_dist_sq(x, y, sx, sy) >= min_dist_sq:
                chosen = (x, y)
                break
        if chosen is None:
            # Could not find within attempts; accept any but nudge to opposite side of ship
            x = (sx + WIDTH / 2) % WIDTH
            y = (sy + HEIGHT / 2) % HEIGHT
            chosen = (x, y)
        x, y = chosen
        return Asteroid(x, y, r if r is not None else 8)

    def spawn_powerup_away(self, min_dist: float) -> "Powerup":
        sx, sy = self.ship.x, self.ship.y

        def toroidal_dist_sq(x1, y1, x2, y2):
            dx = abs(x1 - x2)
            dy = abs(y1 - y2)
            dx = min(dx, WIDTH - dx)
            dy = min(dy, HEIGHT - dy)
            return dx * dx + dy * dy

        min_dist_sq = min_dist * min_dist
        for _ in range(256):
            x = random.uniform(0, WIDTH)
            y = random.uniform(0, HEIGHT)
            if toroidal_dist_sq(x, y, sx, sy) >= min_dist_sq:
                break
        kind = random.choice(['laser', 'points', 'bomb'])
        return Powerup(x, y, kind)

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        # Restart if destroyed
        if not self.ship_alive and pyxel.btnp(pyxel.KEY_R):
            self.ship = Ship()
            self.bullets = []
            self.score = 0
            self.asteroids = [self.spawn_asteroid_away(SAFE_SPAWN_DIST) for _ in range(self.current_min_asteroids())]
            self.shoot_cooldown = 0
            self.ship_alive = True
            self.powerups = []
            self.powerup_spawn_timer = random.randint(POWERUP_SPAWN_MIN, POWERUP_SPAWN_MAX)
            self.laser_timer = 0

        # Update ship only if alive
        if self.ship_alive:
            self.ship.update()

        # Shooting
        if self.ship_alive:
            if self.shoot_cooldown > 0:
                self.shoot_cooldown -= 1
            if pyxel.btn(pyxel.KEY_SPACE) and self.shoot_cooldown == 0:
                nose_x, nose_y = self.ship.nose_pos()
                self.bullets.append(Bullet(nose_x, nose_y, self.ship.angle))
                self.shoot_cooldown = 8  # small delay

        # Update bullets and remove expired
        updated_bullets = []
        for b in self.bullets:
            if b.update():
                updated_bullets.append(b)
        self.bullets = updated_bullets

        # Update asteroids
        for a in self.asteroids:
            a.update()

        # Update powerups (spawn, tick, pickup)
        if self.powerup_spawn_timer > 0:
            self.powerup_spawn_timer -= 1
        else:
            if len(self.powerups) < POWERUP_CAP:
                self.powerups.append(self.spawn_powerup_away(SAFE_SPAWN_DIST))
            self.powerup_spawn_timer = random.randint(POWERUP_SPAWN_MIN, POWERUP_SPAWN_MAX)

        updated_powerups = []
        for p in self.powerups:
            if p.update():
                updated_powerups.append(p)
        self.powerups = updated_powerups

        # Laser power timer
        if self.laser_timer > 0:
            self.laser_timer -= 1

        # Ship-Asteroid collision (destroy ship on contact)
        if self.ship_alive and self.asteroids:
            sx, sy = self.ship.x, self.ship.y
            sr = self.ship.radius
            for a in self.asteroids:
                dx = abs(a.x - sx)
                dy = abs(a.y - sy)
                # wrap-aware shortest deltas
                dx = min(dx, WIDTH - dx)
                dy = min(dy, HEIGHT - dy)
                if dx * dx + dy * dy <= (a.r + sr) * (a.r + sr):
                    self.ship_alive = False
                    break

        # Handle powerup pickup (wrap-aware) only if ship alive
        if self.ship_alive and self.powerups:
            sx, sy = self.ship.x, self.ship.y
            sr = self.ship.radius
            remaining = []
            for p in self.powerups:
                dx = abs(p.x - sx)
                dy = abs(p.y - sy)
                dx = min(dx, WIDTH - dx)
                dy = min(dy, HEIGHT - dy)
                if dx * dx + dy * dy <= (p.r + sr) * (p.r + sr):
                    # apply effect
                    if p.kind == 'laser':
                        self.laser_timer = LASER_POWER_DURATION
                    elif p.kind == 'points':
                        self.score += POINTS_POWER_VALUE
                    elif p.kind == 'bomb':
                        destroyed = len(self.asteroids)
                        if destroyed:
                            self.score += 10 * destroyed
                        self.asteroids = []
                    # consumed, do not keep
                else:
                    remaining.append(p)
            self.powerups = remaining

        # Bullet-Asteroid collisions and asteroid splitting
        if self.bullets and self.asteroids:
            surviving_asteroids = []
            new_asteroids = []
            bullets_to_keep = []
            hit_set = set()
            laser_on = self.laser_timer > 0

            for b in self.bullets:
                hit_index = -1
                # find first asteroid this bullet hits
                for i, a in enumerate(self.asteroids):
                    dx = b.x - a.x
                    dy = b.y - a.y
                    if dx * dx + dy * dy <= (a.r + b.radius) ** 2:
                        hit_index = i
                        break
                if hit_index == -1:
                    bullets_to_keep.append(b)
                else:
                    # mark asteroid as hit
                    hit_set.add(hit_index)
                    # split asteroid at hit_index
                    a = self.asteroids[hit_index]
                    if a.r > 3:
                        pieces = random.randint(2, 3)
                        child_r = max(2, int(a.r * 0.6))
                        for _ in range(pieces):
                            child = Asteroid(a.x, a.y, child_r)
                            speed_boost = random.uniform(0.0, 0.3)
                            angle = random.uniform(0, math.tau)
                            child.vx += math.cos(angle) * speed_boost
                            child.vy += math.sin(angle) * speed_boost
                            new_asteroids.append(child)
                    # keep bullet if laser is active (piercing), else consume
                    if laser_on:
                        bullets_to_keep.append(b)

            # Keep asteroids not hit
            for idx, a in enumerate(self.asteroids):
                if idx not in hit_set:
                    surviving_asteroids.append(a)

            if hit_set:
                self.score += 10 * len(hit_set)

            self.asteroids = surviving_asteroids + new_asteroids
            self.bullets = bullets_to_keep

        # Ensure minimum asteroid count (difficulty-based); spawn away from ship
        target_min = self.current_min_asteroids()
        if len(self.asteroids) < target_min:
            needed = target_min - len(self.asteroids)
            for _ in range(needed):
                self.asteroids.append(self.spawn_asteroid_away(SAFE_SPAWN_DIST))

    def draw(self):
        pyxel.cls(0)

        # Camera: keep ship centered. Convert world -> screen using toroidal shortest offset.
        cx = self.ship.x
        cy = self.ship.y

        def to_screen(wx, wy):
            # delta in wrap space mapped to [-W/2, W/2), same for H
            dx = ((wx - cx + WIDTH / 2) % WIDTH) - WIDTH / 2
            dy = ((wy - cy + HEIGHT / 2) % HEIGHT) - HEIGHT / 2
            return WIDTH / 2 + dx, HEIGHT / 2 + dy

        # Draw asteroids relative to camera
        for a in self.asteroids:
            sx, sy = to_screen(a.x, a.y)
            pyxel.circb(int(sx), int(sy), int(a.r), 5)

        # Draw bullets relative to camera
        for b in self.bullets:
            sx, sy = to_screen(b.x, b.y)
            pyxel.circ(int(sx), int(sy), b.radius, 10)

        # Draw powerups
        for p in self.powerups:
            p.draw(to_screen)

        # Draw ship at screen center using its angle (only if alive)
        if self.ship_alive:
            cx_scr = WIDTH / 2
            cy_scr = HEIGHT / 2
            r = self.ship.radius
            ang = self.ship.angle
            nose = (cx_scr + math.cos(ang) * r, cy_scr + math.sin(ang) * r)
            left = (cx_scr + math.cos(ang + 2.5) * r, cy_scr + math.sin(ang + 2.5) * r)
            right = (cx_scr + math.cos(ang - 2.5) * r, cy_scr + math.sin(ang - 2.5) * r)
            pyxel.line(int(nose[0]), int(nose[1]), int(left[0]), int(left[1]), 7)
            pyxel.line(int(nose[0]), int(nose[1]), int(right[0]), int(right[1]), 7)
            pyxel.line(int(left[0]), int(left[1]), int(right[0]), int(right[1]), 7)

        # UI
        if self.ship_alive:
            draw_centered_text(2, "A/D turn  W accel  S reverse  SPACE shoot  Q quit", 13)
        else:
            draw_centered_text(56, "Destroyed! Press R to restart", 8)

        # Score HUD (top-right)
        score_text = f"Score: {self.score}"
        if self.ship_alive:
            pyxel.text(WIDTH - 4 - len(score_text)*4, 2, score_text, 11)
        else:
            draw_centered_text(65, score_text, 11)

        # Difficulty HUD (top-left): show a simple level derived from current minimum asteroids
        # Level 1 at base, increases as min asteroids increases with score
        min_count = self.current_min_asteroids()
        level = 1 + max(0, (min_count - BASE_MIN_ASTEROIDS) // ASTEROIDS_PER_STEP)
        diff_text = f"Diff: {level}"
        pyxel.text(2, 2, diff_text, 9)

        # Power HUD: laser indicator with remaining seconds
        if self.laser_timer > 0:
            secs = self.laser_timer // 60
            pyxel.text(2, 10, f"Laser: {secs}s", 12)


App()
