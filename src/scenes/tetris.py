from random import choice, randint
import config
from .base import Scene


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
    GRID_WIDTH = 16
    GRID_HEIGHT = 6  # Visible height (4 rows hidden at top for spawning)
    TOTAL_HEIGHT = 10  # Total including spawn area

    def __init__(self, display, png_decoder, fall_speed=0.1, reset_interval=60.0, display_mode=None):
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

                    # Dim in night mode
                    if self.display_mode == "night":
                        r, g, b = config.dim_color(r, g, b)

                    pen = self.display.create_pen(r, g, b)
                    self.display.set_pen(pen)

                    px = self.grid_x + x * self.block_size
                    py = self.grid_y + screen_y * self.block_size
                    self.display.rectangle(px, py, self.block_size - 1, self.block_size - 1)

        # Draw current falling piece
        if self.current_piece:
            r, g, b = self.current_piece.color

            # Dim in night mode
            if self.display_mode == "night":
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
