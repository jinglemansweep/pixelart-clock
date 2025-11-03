# Configuration for Pixelart Clock

# Display Configuration
SCROLL_SPEED = 1
SCROLL_DELAY = 0.01
IMG_WIDTH = 256
IMG_HEIGHT = 64
IMG_SCALE = (1, 1)

# Scene Configuration
SCENE_DURATION = 60 # seconds - how long each scene runs
SCENE_SELECTION = "sequential"  # "sequential" or "random"
IMAGES_PATH = "images"

# Display Mode Configuration
# Maps hour (0-23) to display mode: "normal", "dark", or "off"
# Only specify hours where mode changes (mode persists until next change)
# Example: {9: "normal", 18: "dark", 1: "off"} means:
#   - 1am-8:59am: off
#   - 9am-5:59pm: normal
#   - 6pm-12:59am: dark
MODE_SCHEDULE = {
    9: "normal",   # 9am: switch to normal mode
    21: "dark",    # 6pm: switch to dark mode
    23: "off"       # 9pm: turn display off
}

# Night mode color dimming factor (0.0-1.0)
# Applied to HUD and vector scene colors in dark mode
NIGHT_MODE_DIM_FACTOR = 0.3  # 30% brightness

# Manual Scene Configuration
# Each scene is defined as a tuple: (scene_class_name, args, kwargs, time_preference)
# scene_class_name: "ScrollingImageScene", "StaticImageScene", "CubeScene", etc.
# args: positional arguments (e.g., image_path)
# kwargs: keyword arguments (e.g., scroll_speed=2)
# time_preference: "day", "night", or None (both)
#   - "day": shows only in normal mode
#   - "night": shows only in dark mode
#   - None: shows in both normal and dark modes (omit 4th element or set to None)

SCENES = [
    ("CubeScene", (), {"num_cubes": 3}),
    ("TetrisScene", (), {}),
    ("StaticImageScene", ("images/spectrum_dizzy.png",), {}),
    ("ScrollingImageScene", ("images/spectrum_jetpac.png",), {}),
    ("StaticImageScene", ("images/spectrum_jet_set_willy.png",), {}),
    ("ScrollingImageScene", ("images/spectrum_sabre_wolf.png",), {}),
    ("ScrollingImageScene", ("images/scene_purple_sunset.png",), {}),
    ("ScrollingImageScene", ("images/scene_neon_city.png",), {}),
    ("ScrollingImageScene", ("images/scene_future_family.png",), {}),
    # ("StaticImageScene", ("images/xmas_snow_animals.png",), {}),
    # ("StaticImageScene", ("images/xmas_snow_bridge.png",), {}),
    # ("ScrollingImageScene", ("images/xmas_fireplace.png",), {}),
]

# Fallback behavior when SCENES is empty or images don't exist
USE_AUTO_SCENES = True  # If True, automatically create scenes from images/ directory when SCENES is empty

# HUD Configuration
TIME_POSITION = (3, 1)
TIME_SCALE = 2
DATE_POSITION = (3, 15)
DATE_SCALE = 1

# Text Rendering Options
USE_TEXT_OUTLINE = True   # Full 8-direction outline for maximum contrast
USE_TEXT_SHADOW = False   # Simple bottom-right shadow (used if outline is False)

# Color Definitions
C_BLACK = None  # Will be set from display.create_pen(0, 0, 0)
C_WHITE = None  # Will be set from display.create_pen(255, 255, 255)  
C_ORANGE = None  # Will be set from display.create_pen(255, 117, 24)

# Date/Time Format Configuration
TIME_FORMAT = "HH:MM"  # Examples: "HH:MM:SS", "HH:MM", "hh:MM AP"
DATE_FORMAT = "DDD DD/MM/YYYY"  # Examples: "DDD DD/MM/YYYY", "DDDD, MMMM D, YYYY", "DD-MMM-YY"

# Day Names (short and long)
DAYS_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAYS_LONG = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Month Names (short and long)
MONTHS_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTHS_LONG = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

# Backwards compatibility
DAYS = DAYS_SHORT

def init_colors(display):
    """Initialize color pens from display object"""
    global C_BLACK, C_WHITE, C_ORANGE
    C_BLACK = display.create_pen(0, 0, 0)
    C_WHITE = display.create_pen(255, 255, 255)
    C_ORANGE = display.create_pen(255, 117, 24)

def dim_color(r, g, b, factor=None):
    """
    Dim RGB color values by a factor for night mode display.

    Args:
        r, g, b: RGB color values (0-255)
        factor: Dimming factor (0.0-1.0), defaults to NIGHT_MODE_DIM_FACTOR

    Returns:
        tuple: Dimmed (r, g, b) values
    """
    if factor is None:
        factor = NIGHT_MODE_DIM_FACTOR
    return (int(r * factor), int(g * factor), int(b * factor))