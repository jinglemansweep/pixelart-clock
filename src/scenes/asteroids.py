import time
import math
from random import randint, randrange, uniform, choice
import config
from .base import Scene


class Ship:
    """Player ship with vector graphics and physics"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.angle = 0.0  # Degrees, 0 = pointing up
        self.size = 6

        # Behavior timers
        self.action_timer = 0.0
        self.thrust_timer = 0.0
        self.fire_timer = 0.0

        # Visual state
        self.thrusting = False

    def update(self, delta_time, width, height):
        """Update ship physics and behavior"""
        # Occasional random actions
        self.action_timer += delta_time
        if self.action_timer > 1.0:  # Check every second
            self.action_timer = 0.0

            # 50% chance to rotate
            if randint(1, 100) <= 50:
                self.angle += uniform(-60, 60)
                self.angle = self.angle % 360

            # 70% chance to thrust
            if randint(1, 100) <= 70:
                self.thrust_timer = uniform(0.8, 1.5)

        # Apply thrust if active
        if self.thrust_timer > 0:
            self.thrust_timer -= delta_time
            self.thrusting = True

            # Apply acceleration in facing direction
            angle_rad = math.radians(self.angle)
            ax = math.sin(angle_rad) * 100 * delta_time
            ay = -math.cos(angle_rad) * 100 * delta_time
            self.vx += ax
            self.vy += ay
        else:
            self.thrusting = False

        # Apply friction
        self.vx *= 0.94
        self.vy *= 0.94

        # Clamp velocity
        speed = math.sqrt(self.vx**2 + self.vy**2)
        if speed > 80:
            self.vx = (self.vx / speed) * 80
            self.vy = (self.vy / speed) * 80

        # Update position
        self.x += self.vx * delta_time
        self.y += self.vy * delta_time

        # Wrap around screen
        self.x = self.x % width
        self.y = self.y % height

    def should_fire(self, delta_time):
        """Determine if ship should fire laser"""
        self.fire_timer += delta_time
        if self.fire_timer > 0.8:  # Fire every 0.8-1.5 seconds
            if randint(1, 100) <= 60:  # 60% chance
                self.fire_timer = 0.0
                return True
        return False

    def get_points(self):
        """Get ship triangle points"""
        angle_rad = math.radians(self.angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        # Ship triangle (pointing up when angle=0)
        points = [
            (0, -self.size),      # Nose
            (-self.size/2, self.size/2),   # Left wing
            (self.size/2, self.size/2),    # Right wing
        ]

        # Rotate and translate points
        rotated = []
        for px, py in points:
            rx = px * cos_a - py * sin_a + self.x
            ry = px * sin_a + py * cos_a + self.y
            rotated.append((int(rx), int(ry)))

        return rotated

    def get_thrust_points(self):
        """Get thrust flame points when thrusting"""
        if not self.thrusting:
            return None

        angle_rad = math.radians(self.angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        # Flame points (behind ship)
        flame_length = self.size if int(time.time() * 10) % 2 else self.size * 0.7
        points = [
            (-self.size/3, self.size/2),
            (0, self.size/2 + flame_length),
            (self.size/3, self.size/2),
        ]

        # Rotate and translate
        rotated = []
        for px, py in points:
            rx = px * cos_a - py * sin_a + self.x
            ry = px * sin_a + py * cos_a + self.y
            rotated.append((int(rx), int(ry)))

        return rotated


class Asteroid:
    """Asteroid with random polygon shape"""

    # Size definitions
    SIZES = {
        'large': {'radius': 14, 'points': 8, 'speed_range': (10, 20)},
        'medium': {'radius': 9, 'points': 7, 'speed_range': (20, 35)},
        'small': {'radius': 5, 'points': 6, 'speed_range': (35, 50)},
    }

    def __init__(self, x, y, size='large', vx=None, vy=None):
        self.x = x
        self.y = y
        self.size = size
        self.radius = self.SIZES[size]['radius']

        # Generate random polygon shape
        num_points = self.SIZES[size]['points']
        self.shape = []
        for i in range(num_points):
            angle = (360 / num_points) * i + randint(-15, 15)
            radius = self.radius * uniform(0.7, 1.0)
            px = radius * math.cos(math.radians(angle))
            py = radius * math.sin(math.radians(angle))
            self.shape.append((px, py))

        # Physics
        if vx is None or vy is None:
            speed_min, speed_max = self.SIZES[size]['speed_range']
            angle = uniform(0, 360)
            speed = uniform(speed_min, speed_max)
            self.vx = speed * math.cos(math.radians(angle))
            self.vy = speed * math.sin(math.radians(angle))
        else:
            self.vx = vx
            self.vy = vy

        self.rotation = 0.0
        self.rotation_speed = uniform(-90, 90)  # Degrees per second

    def update(self, delta_time, width, height):
        """Update asteroid position and rotation"""
        self.x += self.vx * delta_time
        self.y += self.vy * delta_time
        self.rotation += self.rotation_speed * delta_time

        # Wrap around screen
        self.x = self.x % width
        self.y = self.y % height

    def get_points(self):
        """Get rotated asteroid polygon points"""
        angle_rad = math.radians(self.rotation)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        points = []
        for px, py in self.shape:
            rx = px * cos_a - py * sin_a + self.x
            ry = px * sin_a + py * cos_a + self.y
            points.append((int(rx), int(ry)))

        return points

    def split(self):
        """Split asteroid into smaller pieces"""
        if self.size == 'large':
            next_size = 'medium'
            count = randint(2, 3)
        elif self.size == 'medium':
            next_size = 'small'
            count = randint(2, 3)
        else:
            return []  # Small asteroids don't split

        # Create smaller asteroids with velocity variations
        pieces = []
        for i in range(count):
            angle = uniform(0, 360)
            speed_boost = uniform(1.2, 1.5)
            new_vx = self.vx * speed_boost * math.cos(math.radians(angle))
            new_vy = self.vy * speed_boost * math.sin(math.radians(angle))
            pieces.append(Asteroid(self.x, self.y, next_size, new_vx, new_vy))

        return pieces


class Laser:
    """Laser projectile"""

    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle  # Degrees
        self.speed = 120  # Pixels per second
        self.length = 4
        self.lifetime = 1.5  # Seconds
        self.age = 0.0

        # Calculate velocity
        angle_rad = math.radians(angle)
        self.vx = math.sin(angle_rad) * self.speed
        self.vy = -math.cos(angle_rad) * self.speed

    def update(self, delta_time, width, height):
        """Update laser position"""
        self.x += self.vx * delta_time
        self.y += self.vy * delta_time
        self.age += delta_time

        # Wrap around screen
        self.x = self.x % width
        self.y = self.y % height

        return self.age < self.lifetime

    def get_line(self):
        """Get laser line endpoints"""
        angle_rad = math.radians(self.angle)
        x2 = self.x + math.sin(angle_rad) * self.length
        y2 = self.y - math.cos(angle_rad) * self.length
        return (int(self.x), int(self.y), int(x2), int(y2))

    def check_collision(self, asteroid):
        """Check if laser hit asteroid (simple circle collision)"""
        dx = self.x - asteroid.x
        dy = self.y - asteroid.y
        distance = math.sqrt(dx*dx + dy*dy)
        return distance < asteroid.radius


class AsteroidsScene(Scene):
    """Asteroids game scene with automated ship"""

    def __init__(self, display, png_decoder, num_asteroids=5, display_mode=None):
        super().__init__(display, png_decoder)
        self.display_mode = display_mode if display_mode is not None else "normal"

        # Initialize ship at center
        self.ship = Ship(self.width / 2, self.height / 2)

        # Initialize asteroids
        self.asteroids = []
        self.target_asteroid_count = max(3, min(8, num_asteroids))
        for _ in range(self.target_asteroid_count):
            self._spawn_asteroid()

        # Lasers
        self.lasers = []
        self.max_lasers = 6

        print(f"AsteroidsScene loaded (asteroids={self.target_asteroid_count})")

    def _spawn_asteroid(self, size='large'):
        """Spawn a new asteroid at a safe location"""
        # Spawn at edges, not near center (where ship starts)
        if randint(0, 1):
            x = uniform(0, self.width)
            y = 0 if randint(0, 1) else self.height
        else:
            x = 0 if randint(0, 1) else self.width
            y = uniform(0, self.height)

        self.asteroids.append(Asteroid(x, y, size))

    def update(self, delta_time):
        """Update scene state"""
        # Update ship
        self.ship.update(delta_time, self.width, self.height)

        # Ship fires laser
        if self.ship.should_fire(delta_time) and len(self.lasers) < self.max_lasers:
            laser = Laser(self.ship.x, self.ship.y, self.ship.angle)
            self.lasers.append(laser)

        # Update asteroids
        for asteroid in self.asteroids:
            asteroid.update(delta_time, self.width, self.height)

        # Update lasers and check collisions
        active_lasers = []
        for laser in self.lasers:
            if laser.update(delta_time, self.width, self.height):
                # Check collisions with asteroids
                hit = False
                for asteroid in self.asteroids[:]:  # Copy list for safe removal
                    if laser.check_collision(asteroid):
                        # Hit! Remove asteroid and laser
                        self.asteroids.remove(asteroid)
                        # Split asteroid into smaller pieces
                        pieces = asteroid.split()
                        self.asteroids.extend(pieces)
                        hit = True
                        break

                if not hit:
                    active_lasers.append(laser)

        self.lasers = active_lasers

        # Maintain asteroid count (spawn new large ones if needed)
        large_count = sum(1 for a in self.asteroids if a.size == 'large')
        if large_count < self.target_asteroid_count:
            self._spawn_asteroid('large')

    def render(self):
        """Render scene"""
        # Calculate color with night mode dimming
        ship_color = (0, 255, 255)  # Cyan
        asteroid_color = (220, 220, 220)  # Light gray
        laser_color = (255, 255, 200)  # Yellow-white

        if self.display_mode == "night":
            ship_color = config.dim_color(*ship_color)
            asteroid_color = config.dim_color(*asteroid_color)
            laser_color = config.dim_color(*laser_color)

        # Draw asteroids
        asteroid_pen = self.display.create_pen(*asteroid_color)
        self.display.set_pen(asteroid_pen)
        for asteroid in self.asteroids:
            points = asteroid.get_points()
            for i in range(len(points)):
                x1, y1 = points[i]
                x2, y2 = points[(i + 1) % len(points)]
                self.display.line(x1, y1, x2, y2)

        # Draw lasers
        laser_pen = self.display.create_pen(*laser_color)
        self.display.set_pen(laser_pen)
        for laser in self.lasers:
            x1, y1, x2, y2 = laser.get_line()
            self.display.line(x1, y1, x2, y2)

        # Draw ship
        ship_pen = self.display.create_pen(*ship_color)
        self.display.set_pen(ship_pen)

        # Ship body
        points = self.ship.get_points()
        for i in range(len(points)):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % len(points)]
            self.display.line(x1, y1, x2, y2)

        # Thrust flame
        thrust_points = self.ship.get_thrust_points()
        if thrust_points:
            for i in range(len(thrust_points) - 1):
                x1, y1 = thrust_points[i]
                x2, y2 = thrust_points[i + 1]
                self.display.line(x1, y1, x2, y2)

    def cleanup(self):
        """Clean up resources"""
        print("AsteroidsScene cleanup")
        self.asteroids = []
        self.lasers = []
        self.ship = None
