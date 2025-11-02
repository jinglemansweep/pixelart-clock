import time
from random import randint
import config
import os

class SceneManager:
    """Manages scene transitions and timing"""
    
    def __init__(self, display, png_decoder, scene_classes=None):
        self.display = display
        self.png_decoder = png_decoder
        self.scene_classes = scene_classes or []
        
        self.current_scene = None
        self.current_scene_index = 0
        self.scene_start_time = time.time()
        self.scene_duration = config.SCENE_DURATION
        
        # Initialize first scene if scene classes are provided
        if self.scene_classes:
            self.switch_to_scene(0)
    
    def add_scene_class(self, scene_class, *args, **kwargs):
        """Add a scene class with its constructor arguments"""
        self.scene_classes.append((scene_class, args, kwargs))
    
    def create_scene(self, scene_index):
        """Create a scene instance from scene class and arguments"""
        if scene_index < 0 or scene_index >= len(self.scene_classes):
            return None
            
        scene_class, args, kwargs = self.scene_classes[scene_index]
        return scene_class(self.display, self.png_decoder, *args, **kwargs)
    
    def switch_to_scene(self, scene_index):
        """Switch to a specific scene by index"""
        # Clean up current scene
        if self.current_scene:
            self.current_scene.cleanup()
            self.current_scene = None
        
        # Create new scene
        self.current_scene = self.create_scene(scene_index)
        self.current_scene_index = scene_index
        self.scene_start_time = time.time()
        
        print(f"SceneManager: Switched to scene {scene_index}")
    
    def switch_to_next_scene(self):
        """Switch to the next scene based on selection mode"""
        if not self.scene_classes:
            return
        
        if config.SCENE_SELECTION == "random":
            # Random selection (avoid repeating current scene if possible)
            if len(self.scene_classes) > 1:
                next_index = self.current_scene_index
                while next_index == self.current_scene_index:
                    next_index = randint(0, len(self.scene_classes) - 1)
            else:
                next_index = 0
        else:
            # Sequential selection
            next_index = (self.current_scene_index + 1) % len(self.scene_classes)
        
        self.switch_to_scene(next_index)
    
    def update(self, delta_time):
        """Update scene manager and current scene"""
        # Check if it's time to switch scenes
        if time.time() - self.scene_start_time >= self.scene_duration:
            self.switch_to_next_scene()
        
        # Update current scene
        if self.current_scene:
            self.current_scene.update(delta_time)
    
    def render(self):
        """Render current scene"""
        if self.current_scene:
            self.current_scene.render()
    
    def get_scene_info(self):
        """Get information about current scene for debugging"""
        if self.current_scene:
            elapsed = time.time() - self.scene_start_time
            remaining = max(0, self.scene_duration - elapsed)
            return {
                'index': self.current_scene_index,
                'class': self.current_scene.__class__.__name__,
                'elapsed': elapsed,
                'remaining': remaining
            }
        return None

def create_scene_manager_from_config(display, png_decoder):
    """Create a scene manager using manual scene configuration from config.py"""
    from scenes import ScrollingImageScene, StaticImageScene
    
    # Map scene class names to actual classes
    scene_classes = {
        "ScrollingImageScene": ScrollingImageScene,
        "StaticImageScene": StaticImageScene,
        # Add new scene types here as they're created
    }
    
    scene_manager = SceneManager(display, png_decoder)
    
    # Use manual scene configuration if provided
    if config.SCENES:
        print(f"Loading {len(config.SCENES)} manually configured scenes...")
        
        for scene_config in config.SCENES:
            if len(scene_config) == 3:
                scene_class_name, args, kwargs = scene_config
            elif len(scene_config) == 2:
                scene_class_name, args = scene_config
                kwargs = {}
            else:
                print(f"Invalid scene configuration: {scene_config}")
                continue
            
            # Get the scene class
            if scene_class_name not in scene_classes:
                print(f"Unknown scene class: {scene_class_name}")
                continue
            
            scene_class = scene_classes[scene_class_name]
            
            # Add the scene to manager
            scene_manager.add_scene_class(scene_class, *args, **kwargs)
            print(f"Added scene: {scene_class_name} with args={args}, kwargs={kwargs}")
        
        # Initialize the first scene after adding all scenes
        if scene_manager.scene_classes and not scene_manager.current_scene:
            scene_manager.switch_to_scene(0)
    
    # Fallback to auto-generated scenes if no manual config or USE_AUTO_SCENES is True
    elif config.USE_AUTO_SCENES:
        print("No manual scenes configured, using auto-generated scenes...")
        scene_manager = _create_auto_scenes(display, png_decoder, scene_classes)
    else:
        print("No scenes configured and auto-scenes disabled!")
    
    return scene_manager

def _create_auto_scenes(display, png_decoder, scene_classes):
    """Create scenes automatically from images directory (fallback behavior)"""
    ScrollingImageScene = scene_classes["ScrollingImageScene"]
    scene_manager = SceneManager(display, png_decoder)
    
    # Check if images directory exists and has content
    try:
        image_files = os.listdir(config.IMAGES_PATH)
        if image_files:
            print(f"Found {len(image_files)} images for auto-generated scenes")
            
            # Add one scrolling scene for each image
            for image_file in image_files:
                image_path = f"{config.IMAGES_PATH}/{image_file}"
                scene_manager.add_scene_class(ScrollingImageScene, image_path)
        else:
            print("No images found, using default scrolling scene")
            scene_manager.add_scene_class(ScrollingImageScene)
    
    except OSError:
        print("Images directory not found, using default scrolling scene")
        scene_manager.add_scene_class(ScrollingImageScene)
    
    return scene_manager

# Keep the old function name for backwards compatibility
def create_default_scene_manager(display, png_decoder):
    """Backwards compatibility wrapper"""
    return create_scene_manager_from_config(display, png_decoder)