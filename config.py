# Configuration for Pixelart Clock

# Display Configuration
SCROLL_SPEED = 1
SCROLL_DELAY = 0.01
IMG_WIDTH = 256
IMG_HEIGHT = 64
IMG_SCALE = (1, 1)

# Scene Configuration
SCENE_DURATION = 30 # seconds - how long each scene runs
SCENE_SELECTION = "sequential"  # "sequential" or "random"
IMAGES_PATH = "images"

# Manual Scene Configuration
# Each scene is defined as a tuple: (scene_class_name, args, kwargs, schedule)
# scene_class_name: "ScrollingImageScene", "StaticImageScene", "CubeScene", etc.
# args: positional arguments (e.g., image_path)
# kwargs: keyword arguments (e.g., scroll_speed=2)
# schedule: optional dict with "hour_start" and "hour_end" (0-23)
#   - hour_start=21, hour_end=9 means 9pm to 9am (cross-midnight)
#   - omit schedule for always-active scenes

SCENES = [
    ("CubeScene", (), {"num_cubes": 3}, {"hour_start": 12, "hour_end": 18}),
    ("ScrollingImageScene", ("images/bg1.png",), {"scroll_speed": 1}),
    ("ScrollingImageScene", ("images/bg2.png",), {"scroll_speed": 1}),
    ("ScrollingImageScene", ("images/bg3.png",), {"scroll_speed": 1}),
]

# Fallback behavior when SCENES is empty or images don't exist
USE_AUTO_SCENES = True  # If True, automatically create scenes from images/ directory when SCENES is empty

# HUD Configuration
TIME_POSITION = (2, 1)
TIME_SCALE = 2
DATE_POSITION = (2, 14)
DATE_SCALE = 1

# Text Rendering Options
USE_TEXT_OUTLINE = True   # Full 8-direction outline for maximum contrast
USE_TEXT_SHADOW = False   # Simple bottom-right shadow (used if outline is False)

# Color Definitions
C_BLACK = None  # Will be set from display.create_pen(0, 0, 0)
C_WHITE = None  # Will be set from display.create_pen(255, 255, 255)  
C_ORANGE = None  # Will be set from display.create_pen(255, 117, 24)

# Day Names
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

def init_colors(display):
    """Initialize color pens from display object"""
    global C_BLACK, C_WHITE, C_ORANGE
    C_BLACK = display.create_pen(0, 0, 0)
    C_WHITE = display.create_pen(255, 255, 255)
    C_ORANGE = display.create_pen(255, 117, 24)