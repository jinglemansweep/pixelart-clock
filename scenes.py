import os
from random import choice
import config

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
    
    def __init__(self, display, png_decoder, image_path=None, scroll_speed=None):
        super().__init__(display, png_decoder)
        
        # Use provided image or select random one
        if image_path is None:
            image_filename = choice(os.listdir(config.IMAGES_PATH))
            self.image_path = f"{config.IMAGES_PATH}/{image_filename}"
        else:
            self.image_path = image_path
            
        self.scroll_speed = scroll_speed if scroll_speed is not None else config.SCROLL_SPEED
        self.x_pos = 0
        
        # Load the image
        self.png_decoder.open_file(self.image_path)
        print(f"ScrollingImageScene loaded: {self.image_path}")
    
    def update(self, delta_time):
        """Update scrolling position"""
        # Reset position when image has scrolled completely off screen
        if self.x_pos < -self.width:
            self.x_pos = 0
        
        self.x_pos -= self.scroll_speed
    
    def render(self):
        """Render scrolling image"""
        # Convert position to integer for PNG decoder
        x_int = int(self.x_pos)
        
        # Render primary image at current position
        self.png_decoder.decode(x_int, 0, scale=config.IMG_SCALE)
        
        # Render secondary image for seamless scrolling when primary is partially off-screen
        if self.x_pos < config.IMG_WIDTH:
            self.png_decoder.decode(x_int + config.IMG_WIDTH, 0, scale=config.IMG_SCALE)
    
    def cleanup(self):
        """Clean up resources"""
        print(f"ScrollingImageScene cleanup: {self.image_path}")
        # PNG decoder will be reused by next scene, no explicit cleanup needed

class StaticImageScene(Scene):
    """Scene that displays a static background image"""
    
    def __init__(self, display, png_decoder, image_path=None):
        super().__init__(display, png_decoder)
        
        # Use provided image or select random one
        if image_path is None:
            image_filename = choice(os.listdir(config.IMAGES_PATH))
            self.image_path = f"{config.IMAGES_PATH}/{image_filename}"
        else:
            self.image_path = image_path
        
        # Load the image
        self.png_decoder.open_file(self.image_path)
        print(f"StaticImageScene loaded: {self.image_path}")
    
    def update(self, delta_time):
        """No updates needed for static image"""
        pass
    
    def render(self):
        """Render static image"""
        self.png_decoder.decode(0, 0, scale=config.IMG_SCALE)
    
    def cleanup(self):
        """Clean up resources"""
        print(f"StaticImageScene cleanup: {self.image_path}")
        # PNG decoder will be reused by next scene, no explicit cleanup needed