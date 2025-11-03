import os
import time
import math
from random import choice, randint, randrange
import config
import time_utils

class Scene:
    """Base class for all scenes"""
    
    def __init__(self, display, png_decoder):
        self.display = display
        self.png_decoder = png_decoder
        self.width, self.height = display.get_bounds()
    
    def update(self, delta_time):
        """Update scene state (animation, scrolling, etc.)"""
        pass
    
    def render(self):
        """Render scene content to display"""
        pass
    
    def cleanup(self):
        """Clean up resources when scene ends"""
        pass

class ScrollingImageScene(Scene):
    """Scene that displays a scrolling background image"""

    def __init__(self, display, png_decoder, image_path=None, scroll_speed=None, display_mode=None):
        super().__init__(display, png_decoder)

        # Use provided image or select random one
        if image_path is None:
            image_filename = choice(os.listdir(config.IMAGES_PATH))
            self.image_path = f"{config.IMAGES_PATH}/{image_filename}"
        else:
            self.image_path = image_path

        # Resolve mode-specific image variant (e.g., _night.png for dark mode)
        mode = display_mode if display_mode is not None else "normal"
        self.resolved_image_path = time_utils.resolve_image_path_for_mode(self.image_path, mode)

        self.scroll_speed = scroll_speed if scroll_speed is not None else config.SCROLL_SPEED
        self.x_pos = 0.0  # Initialize as float to handle fractional scroll speeds

        # Load the resolved image (night variant if available in dark mode)
        self.png_decoder.open_file(self.resolved_image_path)
        print(f"ScrollingImageScene loaded: {self.resolved_image_path}")
    
    def update(self, delta_time):
        """Update scrolling position"""
        # Reset position when image has scrolled completely off screen
        if self.x_pos < -self.width:
            self.x_pos = 0.0  # Ensure it's a clean float
        
        self.x_pos -= self.scroll_speed
        
        # Prevent extreme negative values that might cause precision issues
        if self.x_pos < -self.width * 2:
            self.x_pos = 0.0
    
    def render(self):
        """Render scrolling image"""
        # Convert position to integer for PNG decoder
        x_int = int(self.x_pos)
        
        # Ensure all parameters are proper types for PNG decoder
        try:
            # Render primary image at current position
            self.png_decoder.decode(x_int, 0, scale=config.IMG_SCALE)
            
            # Render secondary image for seamless scrolling when primary is partially off-screen
            if self.x_pos < config.IMG_WIDTH:
                self.png_decoder.decode(x_int + config.IMG_WIDTH, 0, scale=config.IMG_SCALE)
        except TypeError as e:
            print(f"PNG decode error: {e}")
            print(f"x_int={x_int}, type={type(x_int)}")
            print(f"scale={config.IMG_SCALE}, type={type(config.IMG_SCALE)}")
            raise
    
    def cleanup(self):
        """Clean up resources"""
        print(f"ScrollingImageScene cleanup: {self.resolved_image_path}")
        # PNG decoder will be reused by next scene, no explicit cleanup needed

class StaticImageScene(Scene):
    """Scene that displays a static background image"""

    def __init__(self, display, png_decoder, image_path=None, display_mode=None):
        super().__init__(display, png_decoder)

        # Use provided image or select random one
        if image_path is None:
            image_filename = choice(os.listdir(config.IMAGES_PATH))
            self.image_path = f"{config.IMAGES_PATH}/{image_filename}"
        else:
            self.image_path = image_path

        # Resolve mode-specific image variant (e.g., _night.png for dark mode)
        mode = display_mode if display_mode is not None else "normal"
        self.resolved_image_path = time_utils.resolve_image_path_for_mode(self.image_path, mode)

        # Load the resolved image (night variant if available in dark mode)
        self.png_decoder.open_file(self.resolved_image_path)
        print(f"StaticImageScene loaded: {self.resolved_image_path}")
    
    def update(self, delta_time):
        """No updates needed for static image"""
        pass
    
    def render(self):
        """Render static image"""
        self.png_decoder.decode(0, 0, scale=config.IMG_SCALE)
    
    def cleanup(self):
        """Clean up resources"""
        print(f"StaticImageScene cleanup: {self.resolved_image_path}")
        # PNG decoder will be reused by next scene, no explicit cleanup needed

class Cube:
    """3D Cube object for the CubeScene"""
    
    # The corners of the cube
    vertices = [[-1, -1, 1],
                [1, -1, 1],
                [1, -1, -1],
                [-1, -1, -1],
                [-1, 1, 1],
                [1, 1, 1],
                [1, 1, -1],
                [-1, 1, -1]]

    # The corners that will be connected together to make a cube
    edges = [(0, 1), (1, 2), (2, 3), (3, 0),
             (4, 5), (5, 6), (6, 7), (7, 4),
             (0, 4), (1, 5), (2, 6), (3, 7)]

    def __init__(self, fov, distance, x, y, speed):
        self.tick = time.ticks_ms() / 1000.0
        self.cos = math.cos(self.tick)
        self.sin = math.sin(self.tick)
        self.fov = fov
        self.distance = distance
        self.pos_x = x
        self.pos_y = y
        self.speed = speed
        self.cube_points = []

    def to_2d(self, x, y, z, pos_x, pos_y, fov, distance):
        """Project 3D points to 2D screen coordinates"""
        factor = fov / (distance + z)
        x = x * factor + pos_x
        y = -y * factor + pos_y
        return int(x), int(y)

    def _update(self):
        """Clear points and recalculate sin/cos values"""
        self.cube_points = []
        self.tick = time.ticks_ms() / (self.speed * 1000)
        self.cos = math.cos(self.tick)
        self.sin = math.sin(self.tick)

    def set_fov(self, fov):
        self.fov = fov

    def get_fov(self):
        return self.fov

    def rotate(self):
        """Rotate cube on XYZ axes and save new points"""
        # Clear previous points and update timing
        self._update()
        
        for v in self.vertices:
            start_x, start_y, start_z = v

            # X rotation
            y = start_y * self.cos - start_z * self.sin
            z = start_y * self.sin + start_z * self.cos

            # Y rotation
            x = start_x * self.cos - z * self.sin
            z = start_x * self.sin + z * self.cos

            # Z rotation
            n_y = x * self.sin + y * self.cos
            n_x = x * self.cos - y * self.sin

            y = n_y
            x = n_x

            point = self.to_2d(x, y, z, self.pos_x, self.pos_y, self.fov, self.distance)
            self.cube_points.append(point)

    def draw(self, display):
        """Draw the cube edges"""
        # Ensure we have points to draw (safety check)
        if len(self.cube_points) < len(self.vertices):
            return
            
        for edge in self.edges:
            if edge[0] < len(self.cube_points) and edge[1] < len(self.cube_points):
                x1, y1 = self.cube_points[edge[0]]
                x2, y2 = self.cube_points[edge[1]]
                display.line(x1, y1, x2, y2)

class CubeScene(Scene):
    """3D rotating cubes scene"""

    def __init__(self, display, png_decoder, num_cubes=3, display_mode=None):
        super().__init__(display, png_decoder)
        self.num_cubes = num_cubes
        self.cubes = []
        self.color_time = 0.0
        self.display_mode = display_mode if display_mode is not None else "normal"
        
        # Initialize cubes with different parameters
        for i in range(num_cubes):
            cube = Cube(
                fov=randint(8, 32),
                distance=8,
                x=randint(10, self.width - 10),
                y=randint(10, self.height - 10),
                speed=randrange(4, 15) / 10.0
            )
            # Ensure initial points are calculated
            cube.rotate()
            self.cubes.append(cube)
        
        print(f"CubeScene loaded with {num_cubes} cubes")
    
    def update(self, delta_time):
        """Update cube animations"""
        self.color_time += delta_time * 20  # Speed up color cycling
        
        # Update each cube
        for i, cube in enumerate(self.cubes):
            fov = cube.get_fov()
            fov += 3  # Increase FOV to make cubes appear closer
            cube.set_fov(fov)
            cube.rotate()
            
            # Reset cube when it gets too close (high FOV)
            if fov > randint(250, 600):
                new_cube = Cube(
                    fov=8,
                    distance=8,
                    x=randint(10, self.width - 10),
                    y=randint(10, self.height - 10),
                    speed=randrange(4, 15) / 10.0
                )
                # Ensure new cube has initial points by calling rotate
                new_cube.rotate()
                self.cubes[i] = new_cube
    
    def render(self):
        """Render the cubes"""
        # Create dynamic color based on time (HSV color cycling)
        # MicroPython's create_pen_hsv might not be available, so use RGB cycling
        r = int(128 + 127 * math.sin(self.color_time))
        g = int(128 + 127 * math.sin(self.color_time + 2.094))  # 120 degrees
        b = int(128 + 127 * math.sin(self.color_time + 4.188))  # 240 degrees

        # Ensure RGB values are in valid range
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))

        # Dim colors in dark mode
        if self.display_mode == "dark":
            r, g, b = config.dim_color(r, g, b)

        cube_pen = self.display.create_pen(r, g, b)
        self.display.set_pen(cube_pen)

        # Draw all cubes
        for cube in self.cubes:
            cube.draw(self.display)
    
    def cleanup(self):
        """Clean up resources"""
        print("CubeScene cleanup")
        self.cubes = []