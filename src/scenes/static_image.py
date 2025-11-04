import os
from random import choice
import config
import time_utils
from .base import Scene


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

        # Resolve mode-specific image variant (e.g., _night.png for night mode)
        mode = display_mode if display_mode is not None else "normal"
        self.resolved_image_path = time_utils.resolve_image_path_for_mode(self.image_path, mode)

        # Load the resolved image (night variant if available in night mode)
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
