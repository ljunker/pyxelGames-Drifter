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
# Keep at least this many asteroids on screen (will auto-replenish)
MIN_ASTEROIDS = 6


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

        # Acceleration / deceleration
        if pyxel.btn(pyxel.KEY_W):
            ax = math.cos(self.angle) * self.thrust
            ay = math.sin(self.angle) * self.thrust
            self.vx += ax
            self.vy += ay
        if pyxel.btn(pyxel.KEY_S):
            # brake opposite to current velocity
            speed = math.hypot(self.vx, self.vy)
            if speed > 0:
                bx = -self.vx / max(speed, 1e-6) * self.brake
                by = -self.vy / max(speed, 1e-6) * self.brake
                self.vx += bx
                self.vy += by

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
        # Spawn initial asteroids away from the ship
        self.asteroids = [self.spawn_asteroid_away(SAFE_SPAWN_DIST) for _ in range(MIN_ASTEROIDS)]
        self.shoot_cooldown = 0
        self.score = 0
        self.ship_alive = True
        pyxel.run(self.update, self.draw)

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

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        # Restart if destroyed
        if not self.ship_alive and pyxel.btnp(pyxel.KEY_R):
            self.ship = Ship()
            self.bullets = []
            self.asteroids = [self.spawn_asteroid_away(SAFE_SPAWN_DIST) for _ in range(MIN_ASTEROIDS)]
            self.shoot_cooldown = 0
            self.score = 0
            self.ship_alive = True

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

        # Bullet-Asteroid collisions and asteroid splitting
        if self.bullets and self.asteroids:
            surviving_asteroids = []
            new_asteroids = []
            bullets_to_keep = []

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
                    # split asteroid at hit_index
                    a = self.asteroids[hit_index]
                    # children only if big enough
                    if a.r > 3:
                        # spawn 2-3 children with smaller radius
                        pieces = random.randint(2, 3)
                        child_r = max(2, int(a.r * 0.6))
                        for _ in range(pieces):
                            child = Asteroid(a.x, a.y, child_r)
                            # give children a bit more speed randomness
                            speed_boost = random.uniform(0.0, 0.3)
                            angle = random.uniform(0, math.tau)
                            child.vx += math.cos(angle) * speed_boost
                            child.vy += math.sin(angle) * speed_boost
                            new_asteroids.append(child)
                    # remove the hit asteroid by skipping it later
                    # mark all other asteroids to surviving_asteroids after iteration

                # Rebuild asteroid list after each bullet? We'll do once after loop

            # Build surviving asteroids list: keep those not hit
            hit_set = set()
            # Determine which asteroids were hit by checking collisions again against kept bullets? No.
            # Instead, we tracked only one hit per bullet, but need to remove any asteroid hit by any bullet.
            # Recompute hits using original bullets list minus kept ones.
            for b in self.bullets:
                if b in bullets_to_keep:
                    continue
                for idx, a in enumerate(self.asteroids):
                    dx = b.x - a.x
                    dy = b.y - a.y
                    if dx * dx + dy * dy <= (a.r + b.radius) ** 2:
                        hit_set.add(idx)
                        break

            for idx, a in enumerate(self.asteroids):
                if idx not in hit_set:
                    surviving_asteroids.append(a)

            # Update score for destroyed asteroids
            if hit_set:
                # Simple scoring: +10 per asteroid destroyed
                self.score += 10 * len(hit_set)

            self.asteroids = surviving_asteroids + new_asteroids
            self.bullets = bullets_to_keep

        # Ensure minimum asteroid count; spawn away from ship
        if len(self.asteroids) < MIN_ASTEROIDS:
            needed = MIN_ASTEROIDS - len(self.asteroids)
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
            draw_centered_text(2, "A/D turn  W accel  S brake  SPACE shoot  Q quit", 13)
        else:
            draw_centered_text(56, "Destroyed! Press R to restart", 8)

        # Score HUD (top-right)
        score_text = f"Score: {self.score}"
        if self.ship_alive:
            pyxel.text(WIDTH - 4 - len(score_text)*4, 2, score_text, 11)
        else:
            draw_centered_text(65, score_text, 11)


App()
