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
