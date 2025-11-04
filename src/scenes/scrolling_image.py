import os
from random import choice
import config
import time_utils
from .base import Scene


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
