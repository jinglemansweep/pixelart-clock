import time
from random import randint
import config
import os
import time_utils

class SceneManager:
    """Manages scene transitions and timing"""

    def __init__(self, display, png_decoder, rtc, scene_classes=None):
        self.display = display
        self.png_decoder = png_decoder
        self.rtc = rtc
        self.scene_classes = scene_classes or []  # List of (scene_class, args, kwargs, preference)

        self.current_scene = None
        self.current_scene_index = 0
        self.scene_start_time = time.time()
        self.scene_duration = config.SCENE_DURATION

        # Initialize current mode based on RTC and schedule
        self.current_mode = time_utils.get_current_mode(self.rtc, config.MODE_SCHEDULE)

        # Note: First scene initialization is deferred to after all scenes are added
        # to ensure mode-aware scene selection
    
    def add_scene_class(self, scene_class, preference=None, *args, **kwargs):
        """Add a scene class with its constructor arguments and optional time preference"""
        self.scene_classes.append((scene_class, args, kwargs, preference))
    
    def create_scene(self, scene_index):
        """Create a scene instance from scene class and arguments"""
        if scene_index < 0 or scene_index >= len(self.scene_classes):
            return None

        scene_data = self.scene_classes[scene_index]
        if len(scene_data) == 4:
            scene_class, args, kwargs, preference = scene_data
        else:
            # Backward compatibility
            scene_class, args, kwargs = scene_data
            preference = None

        # Pass current display mode to scene (for mode-aware image loading)
        kwargs_with_mode = kwargs.copy()
        kwargs_with_mode['display_mode'] = self.current_mode

        return scene_class(self.display, self.png_decoder, *args, **kwargs_with_mode)
    
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
    
    def get_active_scene_indices(self):
        """Get indices of scenes that should be active for the current display mode"""
        mode = time_utils.get_current_mode(self.rtc, config.MODE_SCHEDULE)
        active_indices = []

        for i, scene_data in enumerate(self.scene_classes):
            # Extract preference from scene data
            if len(scene_data) == 4:
                scene_class, args, kwargs, preference = scene_data
            else:
                scene_class, args, kwargs = scene_data
                preference = None

            if time_utils.is_scene_active_in_mode(preference, mode):
                active_indices.append(i)

        # If no scenes are active (e.g., in off mode or no matching preferences),
        # return empty list
        if not active_indices:
            print(f"No scenes available for mode '{mode}'")

        return active_indices
    
    def should_check_mode(self):
        """Check if we need to re-evaluate display mode (mode changed)"""
        mode = time_utils.get_current_mode(self.rtc, config.MODE_SCHEDULE)
        if self.current_mode != mode:
            self.current_mode = mode
            return True
        return False
    
    def switch_to_next_scene_scheduled(self):
        """Switch to next scene considering schedules"""
        active_indices = self.get_active_scene_indices()
        
        if not active_indices:
            return
        
        if config.SCENE_SELECTION == "random":
            # Random selection from active scenes
            if len(active_indices) > 1:
                # Try to avoid current scene if possible
                available_indices = [i for i in active_indices if i != self.current_scene_index]
                if available_indices:
                    next_index = available_indices[randint(0, len(available_indices) - 1)]
                else:
                    next_index = active_indices[randint(0, len(active_indices) - 1)]
            else:
                next_index = active_indices[0]
        else:
            # Sequential selection from active scenes
            try:
                current_pos = active_indices.index(self.current_scene_index)
                next_index = active_indices[(current_pos + 1) % len(active_indices)]
            except ValueError:
                # Current scene not in active list, start from first active scene
                next_index = active_indices[0]
        
        self.switch_to_scene(next_index)
    
    def update(self, delta_time):
        """Update scene manager and current scene"""
        # Check if display mode needs re-evaluation (mode changed)
        if self.should_check_mode():
            active_indices = self.get_active_scene_indices()
            mode = self.current_mode
            print(f"Display mode changed to '{mode}', active scenes: {active_indices}")

            # If current scene is no longer active, switch immediately
            if active_indices and self.current_scene_index not in active_indices:
                print(f"Current scene {self.current_scene_index} no longer active, switching...")
                self.switch_to_next_scene_scheduled()

        # Skip scene updates in off mode
        if self.current_mode == "off":
            return

        # Check if it's time to switch scenes (normal timing)
        if time.time() - self.scene_start_time >= self.scene_duration:
            self.switch_to_next_scene_scheduled()

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

def create_scene_manager_from_config(display, png_decoder, rtc):
    """Create a scene manager using manual scene configuration from config.py"""
    from scenes import ScrollingImageScene, StaticImageScene, CubeScene
    
    # Map scene class names to actual classes
    scene_classes = {
        "ScrollingImageScene": ScrollingImageScene,
        "StaticImageScene": StaticImageScene,
        "CubeScene": CubeScene,
        # Add new scene types here as they're created
    }
    
    scene_manager = SceneManager(display, png_decoder, rtc)
    
    # Use manual scene configuration if provided
    if config.SCENES:
        print(f"Loading {len(config.SCENES)} manually configured scenes...")

        for scene_config in config.SCENES:
            if len(scene_config) == 4:
                scene_class_name, args, kwargs, preference = scene_config
            elif len(scene_config) == 3:
                scene_class_name, args, kwargs = scene_config
                preference = None
            elif len(scene_config) == 2:
                scene_class_name, args = scene_config
                kwargs = {}
                preference = None
            else:
                print(f"Invalid scene configuration: {scene_config}")
                continue

            # Get the scene class
            if scene_class_name not in scene_classes:
                print(f"Unknown scene class: {scene_class_name}")
                continue

            scene_class = scene_classes[scene_class_name]

            # Add the scene to manager
            scene_manager.add_scene_class(scene_class, preference, *args, **kwargs)
            pref_desc = f"preference: {preference}" if preference else "all modes"
            print(f"Added scene: {scene_class_name} ({pref_desc}) with args={args}, kwargs={kwargs}")

        # Initialize the first scene after adding all scenes
        # Use mode-aware scene selection to ensure we start with a valid scene
        if scene_manager.scene_classes and not scene_manager.current_scene:
            scene_manager.switch_to_next_scene_scheduled()
    
    # Fallback to auto-generated scenes if no manual config or USE_AUTO_SCENES is True
    elif config.USE_AUTO_SCENES:
        print("No manual scenes configured, using auto-generated scenes...")
        scene_manager = _create_auto_scenes(display, png_decoder, rtc, scene_classes)
    else:
        print("No scenes configured and auto-scenes disabled!")
    
    return scene_manager

def _create_auto_scenes(display, png_decoder, rtc, scene_classes):
    """Create scenes automatically from images directory (fallback behavior)"""
    ScrollingImageScene = scene_classes["ScrollingImageScene"]
    scene_manager = SceneManager(display, png_decoder, rtc)
    
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

    # Initialize the first scene (auto-generated scenes have no time preference)
    if scene_manager.scene_classes and not scene_manager.current_scene:
        scene_manager.switch_to_next_scene_scheduled()

    return scene_manager

# Keep the old function name for backwards compatibility
def create_default_scene_manager(display, png_decoder, rtc=None):
    """Backwards compatibility wrapper"""
    if rtc is None:
        print("Warning: RTC not provided to create_default_scene_manager, scheduling will not work")
    return create_scene_manager_from_config(display, png_decoder, rtc)