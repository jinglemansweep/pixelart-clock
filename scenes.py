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

class Tetromino:
    """Tetris piece (tetromino) with 7 classic shapes"""

    # Tetromino shapes defined as relative block positions (x, y)
    # Each shape has 4 rotation states
    SHAPES = {
        'I': [
            [(0, 1), (1, 1), (2, 1), (3, 1)],  # Horizontal
            [(2, 0), (2, 1), (2, 2), (2, 3)],  # Vertical
            [(0, 2), (1, 2), (2, 2), (3, 2)],  # Horizontal
            [(1, 0), (1, 1), (1, 2), (1, 3)],  # Vertical
        ],
        'O': [
            [(1, 0), (2, 0), (1, 1), (2, 1)],  # Square (all rotations same)
            [(1, 0), (2, 0), (1, 1), (2, 1)],
            [(1, 0), (2, 0), (1, 1), (2, 1)],
            [(1, 0), (2, 0), (1, 1), (2, 1)],
        ],
        'T': [
            [(1, 0), (0, 1), (1, 1), (2, 1)],
            [(1, 0), (1, 1), (2, 1), (1, 2)],
            [(0, 1), (1, 1), (2, 1), (1, 2)],
            [(1, 0), (0, 1), (1, 1), (1, 2)],
        ],
        'S': [
            [(1, 0), (2, 0), (0, 1), (1, 1)],
            [(1, 0), (1, 1), (2, 1), (2, 2)],
            [(1, 1), (2, 1), (0, 2), (1, 2)],
            [(0, 0), (0, 1), (1, 1), (1, 2)],
        ],
        'Z': [
            [(0, 0), (1, 0), (1, 1), (2, 1)],
            [(2, 0), (1, 1), (2, 1), (1, 2)],
            [(0, 1), (1, 1), (1, 2), (2, 2)],
            [(1, 0), (0, 1), (1, 1), (0, 2)],
        ],
        'J': [
            [(0, 0), (0, 1), (1, 1), (2, 1)],
            [(1, 0), (2, 0), (1, 1), (1, 2)],
            [(0, 1), (1, 1), (2, 1), (2, 2)],
            [(1, 0), (1, 1), (0, 2), (1, 2)],
        ],
        'L': [
            [(2, 0), (0, 1), (1, 1), (2, 1)],
            [(1, 0), (1, 1), (1, 2), (2, 2)],
            [(0, 1), (1, 1), (2, 1), (0, 2)],
            [(0, 0), (1, 0), (1, 1), (1, 2)],
        ],
    }

    def __init__(self, shape_type, x, y, color):
        """
        Initialize a tetromino.

        Args:
            shape_type: One of 'I', 'O', 'T', 'S', 'Z', 'J', 'L'
            x, y: Grid position (top-left of bounding box)
            color: Tuple of (r, g, b)
        """
        self.shape_type = shape_type
        self.x = x
        self.y = y
        self.rotation = 0
        self.color = color

    def get_blocks(self):
        """Get absolute positions of the 4 blocks for current rotation"""
        relative_blocks = self.SHAPES[self.shape_type][self.rotation]
        return [(self.x + dx, self.y + dy) for dx, dy in relative_blocks]

    def rotate(self):
        """Rotate piece 90 degrees clockwise"""
        self.rotation = (self.rotation + 1) % 4

class TetrisScene(Scene):
    """Automated Tetris simulation scene with falling pieces and line clearing"""

    # Tetris grid dimensions
    GRID_WIDTH = 64
    GRID_HEIGHT = 16  # Visible height (4 rows hidden at top for spawning)
    TOTAL_HEIGHT = 20  # Total including spawn area

    def __init__(self, display, png_decoder, fall_speed=0.02, reset_interval=60.0, display_mode=None):
        super().__init__(display, png_decoder)
        self.display_mode = display_mode if display_mode is not None else "normal"

        # Calculate block size to fit display (256x64 pixels)
        # Reserve margins: 10px left/right, 2px top/bottom
        available_width = self.width - 20
        available_height = self.height - 4
        self.block_size = min(available_width // self.GRID_WIDTH, available_height // self.GRID_HEIGHT)

        # Calculate grid position (center it)
        grid_pixel_width = self.GRID_WIDTH * self.block_size
        grid_pixel_height = self.GRID_HEIGHT * self.block_size
        self.grid_x = (self.width - grid_pixel_width) // 2
        self.grid_y = (self.height - grid_pixel_height) // 2

        # Game state
        self.grid = [[None for _ in range(self.GRID_WIDTH)] for _ in range(self.TOTAL_HEIGHT)]
        self.current_piece = None
        self.fall_speed = fall_speed
        self.fall_timer = 0.0

        # Reset timer
        self.reset_interval = reset_interval
        self.reset_timer = 0.0

        # Spawn first piece
        self._spawn_piece()

        print(f"TetrisScene loaded (block_size={self.block_size}, grid_pos=({self.grid_x},{self.grid_y}))")

    def _spawn_piece(self):
        """Spawn a new random piece at the top"""
        shape_types = ['I', 'O', 'T', 'S', 'Z', 'J', 'L']
        shape_type = choice(shape_types)

        # Random color
        r = randint(100, 255)
        g = randint(100, 255)
        b = randint(100, 255)

        # Spawn at random X position across full grid width
        spawn_x = randint(0, self.GRID_WIDTH - 1)
        spawn_y = 0

        self.current_piece = Tetromino(shape_type, spawn_x, spawn_y, (r, g, b))

        # Random initial rotation
        initial_rotation = randint(0, 3)
        for _ in range(initial_rotation):
            self.current_piece.rotate()

    def _check_collision(self, piece, offset_x=0, offset_y=0):
        """Check if piece collides with grid or boundaries"""
        for bx, by in piece.get_blocks():
            test_x = bx + offset_x
            test_y = by + offset_y

            # Check boundaries
            if test_x < 0 or test_x >= self.GRID_WIDTH:
                return True
            if test_y >= self.TOTAL_HEIGHT:
                return True
            if test_y < 0:
                continue  # Allow pieces above grid during spawn

            # Check collision with locked blocks
            if self.grid[test_y][test_x] is not None:
                return True

        return False

    def _lock_piece(self):
        """Lock current piece into the grid"""
        for bx, by in self.current_piece.get_blocks():
            # Check both X and Y bounds before locking
            if 0 <= by < self.TOTAL_HEIGHT and 0 <= bx < self.GRID_WIDTH:
                self.grid[by][bx] = self.current_piece.color

    def update(self, delta_time):
        """Update Tetris game state"""

        # Update reset timer
        self.reset_timer += delta_time

        if self.reset_timer >= self.reset_interval:
            # Reset the grid
            self.grid = [[None for _ in range(self.GRID_WIDTH)] for _ in range(self.TOTAL_HEIGHT)]
            self.reset_timer = 0.0
            print(f"TetrisScene: Grid reset after {self.reset_interval} seconds")

        # Update fall timer
        self.fall_timer += delta_time

        if self.fall_timer >= self.fall_speed:
            self.fall_timer = 0.0

            # Random horizontal movement (30% chance)
            if randint(1, 10) <= 3:
                move_dir = choice([-1, 1])  # Left or right
                if not self._check_collision(self.current_piece, offset_x=move_dir):
                    self.current_piece.x += move_dir

            # Random rotation (20% chance)
            if randint(1, 10) <= 2:
                old_rotation = self.current_piece.rotation
                self.current_piece.rotate()
                # Undo rotation if it causes collision
                if self._check_collision(self.current_piece):
                    self.current_piece.rotation = old_rotation

            # Try to move piece down
            if not self._check_collision(self.current_piece, offset_y=1):
                self.current_piece.y += 1
            else:
                # Piece has landed - lock it and spawn new piece
                self._lock_piece()
                self._spawn_piece()

    def render(self):
        """Render Tetris game"""
        # Draw locked blocks in grid
        for y in range(self.TOTAL_HEIGHT):
            # Only draw visible rows (skip top 4 spawn rows)
            if y < (self.TOTAL_HEIGHT - self.GRID_HEIGHT):
                continue

            # Calculate screen y position (offset by spawn area)
            screen_y = y - (self.TOTAL_HEIGHT - self.GRID_HEIGHT)

            for x in range(self.GRID_WIDTH):
                if self.grid[y][x] is not None:
                    r, g, b = self.grid[y][x]

                    # Dim in dark mode
                    if self.display_mode == "dark":
                        r, g, b = config.dim_color(r, g, b)

                    pen = self.display.create_pen(r, g, b)
                    self.display.set_pen(pen)

                    px = self.grid_x + x * self.block_size
                    py = self.grid_y + screen_y * self.block_size
                    self.display.rectangle(px, py, self.block_size - 1, self.block_size - 1)

        # Draw current falling piece
        if self.current_piece:
            r, g, b = self.current_piece.color

            # Dim in dark mode
            if self.display_mode == "dark":
                r, g, b = config.dim_color(r, g, b)

            pen = self.display.create_pen(r, g, b)
            self.display.set_pen(pen)

            for bx, by in self.current_piece.get_blocks():
                # Only draw blocks in visible area
                if by >= (self.TOTAL_HEIGHT - self.GRID_HEIGHT):
                    screen_y = by - (self.TOTAL_HEIGHT - self.GRID_HEIGHT)
                    px = self.grid_x + bx * self.block_size
                    py = self.grid_y + screen_y * self.block_size
                    self.display.rectangle(px, py, self.block_size - 1, self.block_size - 1)

    def cleanup(self):
        """Clean up resources"""
        print("TetrisScene cleanup")
        self.grid = []
        self.current_piece = None