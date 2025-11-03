# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a MicroPython-based pixel art clock designed for the Interstate 75W display board. The clock displays various scenes (including scrolling background images or vector art effects) with overlaid date and time and in future other metrics/statistics.

The application runs on a 2 x HUB75 LED 128x64px display modules, laid out horizontally providing a full resolution 256px wide x 64px hight. It should always display date, time and other HUD information on top of scene content.

The background should be controlled by a scene. A typical scene would be to display a static image or slowly scroll it infinitely. Another scene could be an animation (e.g. pacman navigating a maze) or a geometric metric art effect. Scenes should be changeable after a configurable period of time (e.g. 1m, 1h, 6h, 1d.)

## Hardware Requirements

- Interstate 75W board with 256x64 pixel display
- MicroPython firmware
- WiFi connectivity for NTP time synchronization

## Hardware Configuration

* Display: 256px wide x 64px tall (2 x 128x64 panels arranged horizontally)
* Input: No physical (GPIO) buttons present

## Resources

* [Getting Started with Interstate 75W](https://learn.pimoroni.com/article/getting-started-with-interstate-75)
* [Animated GIFs with Interstate 75W](https://learn.pimoroni.com/article/gifs-and-interstate-75-w)
* [Pico Graphics MicroPython module](https://github.com/pimoroni/pimoroni-pico/blob/main/micropython/modules/picographics/README.md)

## Development Commands

### Running the Clock
```bash
# Deploy to Interstate 75W (requires MicroPython REPL or IDE like Thonny)
python main.py
```

### Adding Background Images
- Place PNG images (256x64 pixels) in the `images/` directory
- The application randomly selects one image at startup
- Images scroll horizontally behind the clock display

## Architecture

The application uses a modular scene-based architecture that separates scene rendering from HUD overlay functionality.

### Core Components

#### Configuration System (`config.py`)
- Centralized configuration for display, scenes, and HUD settings
- `SCENE_DURATION`: How long each scene runs (default: 60 seconds)
- `SCENE_SELECTION`: Scene transition mode ("sequential" or "random")
- Display constants: scroll speed, image dimensions, positions, colors
- **Display Modes**: Global display mode scheduling (Normal/Dark/Off) by hour
- **Scene Preferences**: Scenes specify day/night preference for mode filtering
- **Night Mode Dimming**: `NIGHT_MODE_DIM_FACTOR` controls color dimming (default: 0.3)
- **Color Utilities**: `dim_color(r, g, b, factor)` dims RGB values for night mode
- **Date/Time Formats**: `TIME_FORMAT` and `DATE_FORMAT` define custom display formats

#### Scene System (`scenes.py`)
- **Base Scene Class**: Interface with `update()`, `render()`, and `cleanup()` methods
- **ScrollingImageScene**: Horizontally scrolling background images
- **StaticImageScene**: Static background image display
- **CubeScene**: 3D rotating wireframe cubes with color cycling
- **TetrisScene**: Automated Tetris simulation with falling pieces and line clearing
- Memory-efficient design using shared PNG decoder
- Vector scenes support day/night color dimming

#### HUD System (`hud.py`)
- **HUD Class**: Renders time, date, and future overlay information
- Separated from scene logic for clean overlay rendering
- Configurable positioning and styling with shadow effects
- Supports custom date/time formats with flexible token-based formatting
- Automatically dims colors in dark mode

#### Scene Management (`scene_manager.py`)
- **SceneManager Class**: Handles scene transitions and timing
- Supports sequential or random scene selection
- Automatic scene switching based on configurable duration
- Proper resource cleanup during transitions

#### Hardware Initialization (`main.py:14-23`)
- Configures Interstate75 display with 256x64 resolution
- Sets up RTC for timekeeping
- Initializes display colors and modular components

#### Network Management (`main.py:25-69`)
- Requires `secrets.py` file with `WIFI_SSID` and `WIFI_PASSWORD` constants
- `network_connect()`: Handles WiFi connection with power saving disabled for compatibility
- `sync_time()`: Synchronizes clock via NTP when WiFi is available

#### Main Loop (`main.py:88-102`)
- Clean separation: scene update → scene render → HUD render → display update
- Maintains 60fps performance with 0.01s frame timing
- Simple 4-step render cycle

### Scene Architecture Benefits

- **Extensibility**: Easy to add new scene types (animations, vector graphics, effects)
- **Memory Efficiency**: Single PNG decoder shared across scenes
- **Clean Separation**: HUD overlay independent of scene content
- **Configurable**: Runtime control of scene duration and selection
- **Maintainable**: Modular design with clear responsibilities

## Dependencies

### MicroPython Libraries
- `machine`: Hardware RTC access
- `network`: WiFi connectivity
- `ntptime`: Network time synchronization
- `pngdec`: PNG image decoding
- `interstate75`: Hardware-specific display driver

### Required Files
- `secrets.py`: Must contain `WIFI_SSID` and `WIFI_PASSWORD` string constants
- `images/*.png`: Background images (256x64 pixels recommended)

### Application Modules
- `main.py`: Main application entry point and hardware initialization
- `config.py`: Centralized configuration settings
- `scenes.py`: Scene classes and base scene interface
- `hud.py`: HUD overlay rendering system
- `scene_manager.py`: Scene transition and timing management

## Image Requirements

Background images should be:
- PNG format
- 256x64 pixels (matches display resolution)
- Placed in the `images/` directory
- Optimized for LED matrix display (high contrast works best)

## Error Handling

The application includes error handling for:
- Missing `secrets.py` file
- Empty WiFi credentials
- Network connection failures
- NTP synchronization failures

WiFi connection failures are handled gracefully - the clock will continue to run with the internal RTC time even if network sync fails.

## Display Modes and Scene Scheduling

The application supports global display mode scheduling with scene filtering based on day/night preferences.

### Display Modes

Three display modes are available:
- **Normal**: Day mode, shows "day" scenes
- **Dark**: Night mode, shows "night" scenes and night image variants
- **Off**: Display turned off, no scenes active

### Mode Scheduling Configuration

Configure display modes by hour in `config.py`:

```python
# MODE_SCHEDULE maps hour (0-23) to mode ("normal", "dark", "off")
# Only specify hours where mode changes - mode persists until next change
MODE_SCHEDULE = {
    9: "normal",   # 9am: switch to normal mode
    18: "dark",    # 6pm: switch to dark mode
    1: "off"       # 1am: turn display off
}
```

**How it works:**
- At 1am: Display turns off (mode: "off")
- At 9am: Display turns on in normal mode (mode: "normal")
- At 6pm: Display switches to dark mode (mode: "dark")
- Mode persists until the next scheduled change

### Scene Configuration Format

Scenes can include an optional 4th element specifying time preference:

```python
SCENES = [
    # Format: (scene_class, args, kwargs, preference)
    ("CubeScene", (), {"num_cubes": 3}, "night"),  # Only in dark mode
    ("ScrollingImageScene", ("images/bg1.png",), {"scroll_speed": 1}, None),  # Both modes
    ("ScrollingImageScene", ("images/bg2.png",), {"scroll_speed": 1}),  # Both modes (4th element omitted)
    ("ScrollingImageScene", ("images/bg3.png",), {"scroll_speed": 1}, "day"),  # Only in normal mode
]
```

### Scene Time Preferences

- **"day"**: Scene active only in **normal** mode
- **"night"**: Scene active only in **dark** mode
- **None** (or omit 4th element): Scene active in **both normal and dark** modes
- In **off** mode, no scenes are active regardless of preference

### Mode Behavior

**Normal Mode:**
- Shows scenes with preference "day" or None
- Uses standard image files
- HUD displays normally

**Dark Mode:**
- Shows scenes with preference "night" or None
- Automatically uses "_night.png" image variants when available (falls back to standard images)
- HUD colors are dimmed (configurable via `NIGHT_MODE_DIM_FACTOR`)
- Vector scene colors are dimmed (e.g., CubeScene)

**Off Mode:**
- Display cleared to black
- No scene updates (saves CPU/power)
- No HUD rendering
- Loop continues to check for mode transitions

### Night Mode Dimming

**Hardware Note:** The Interstate 75W does not support hardware brightness control. To achieve darker visuals in night mode, the application uses two complementary approaches:

#### 1. Night Image Variants (for image-based scenes)

**How it works:**
- When in dark mode, image scenes automatically look for images with a "_night" suffix
- If `images/bg1_night.png` exists, it will be used instead of `images/bg1.png` in dark mode
- If no night variant exists, the original image is used
- This allows you to create dimmed or color-adjusted versions of images for nighttime viewing

**Creating night variants:**
```bash
# Create a dimmed version using ImageMagick (30% brightness)
convert images/bg1.png -modulate 30 images/bg1_night.png

# Create with slight desaturation for a more natural night look
convert images/bg1.png -modulate 40,80,100 images/bg1_night.png
```

**Example image organization:**
```
images/
  bg1.png         # Day version (used in normal mode)
  bg1_night.png   # Night version (used in dark mode)
  bg2.png         # Used in both modes (no night variant)
  stars.png       # Night-only scene
```

#### 2. Color Dimming (for HUD and vector scenes)

**How it works:**
- The HUD (time/date display) automatically dims its colors in dark mode
- Vector scenes (like CubeScene) dim their generated colors in dark mode
- Dimming is controlled by `NIGHT_MODE_DIM_FACTOR` config setting (default: 0.3 = 30% brightness)

**Configuration:**
```python
# In config.py
NIGHT_MODE_DIM_FACTOR = 0.3  # Range: 0.0-1.0 (0.3 = 30% brightness)
```

**Implementation:**
- The `dim_color(r, g, b, factor)` utility function multiplies RGB values by the dim factor
- HUD creates dimmed versions of white and orange text colors in dark mode
- Vector scenes apply dimming to their dynamically generated colors
- This ensures all visual elements (images, text, graphics) are dimmer at night

## Built-in Scenes

The application includes several built-in scene types for different visual effects.

### Image-Based Scenes

**ScrollingImageScene:**
- Horizontally scrolling background images
- Configurable scroll speed
- Supports night mode image variants (`_night.png` suffix)
- Example: `("ScrollingImageScene", ("images/bg.png",), {"scroll_speed": 1})`

**StaticImageScene:**
- Static background image display
- Supports night mode image variants (`_night.png` suffix)
- Example: `("StaticImageScene", ("images/bg.png",), {})`

### Vector Scenes

**CubeScene:**
- 3D rotating wireframe cubes
- Color cycling animation
- Configurable number of cubes
- Automatically dims colors in dark mode
- Example: `("CubeScene", (), {"num_cubes": 3}, "night")`

**TetrisScene:**
- Automated Tetris simulation
- Falling pieces with random colors and rotations
- Random horizontal movement and rotation while falling
- No line clearing - blocks continuously stack up
- Grid resets after configurable interval (default: 60 seconds)
- Automatically dims colors in dark mode
- Configurable fall speed (default: 0.01 seconds per row)
- Configurable reset interval (default: 60 seconds)
- Example: `("TetrisScene", (), {"fall_speed": 0.01, "reset_interval": 60.0}, "night")`

**Features:**
- 7 classic Tetris shapes (I, O, T, S, Z, J, L)
- Random piece colors, spawn positions, and initial rotations
- 30% chance of horizontal movement per step (left or right)
- 20% chance of rotation per step
- Continuous piece spawning - never stops
- Configurable grid dimensions (default: 64 wide × 16 tall visible)
- Block size automatically scaled to fit display
- Periodic grid reset to keep scene dynamic

## Date and Time Formatting

The HUD supports flexible, customizable date and time formats using token-based format strings.

### Configuration

Configure formats in `config.py`:

```python
# Time format (default: "HH:MM:SS")
TIME_FORMAT = "HH:MM:SS"  # 24-hour with seconds
# TIME_FORMAT = "HH:MM"      # 24-hour without seconds
# TIME_FORMAT = "hh:MM AP"   # 12-hour with AM/PM

# Date format (default: "DDD DD/MM/YYYY")
DATE_FORMAT = "DDD DD/MM/YYYY"  # Short day, numeric date
# DATE_FORMAT = "DDDD, MMMM D, YYYY"  # Long format
# DATE_FORMAT = "DD-MMM-YY"           # Short format with month name
```

### Time Format Tokens

| Token | Description | Example |
|-------|-------------|---------|
| `HH` | 24-hour with leading zero | 00-23 |
| `H` | 24-hour without leading zero | 0-23 |
| `hh` | 12-hour with leading zero | 01-12 |
| `h` | 12-hour without leading zero | 1-12 |
| `MM` | Minutes with leading zero | 00-59 |
| `M` | Minutes without leading zero | 0-59 |
| `SS` | Seconds with leading zero | 00-59 |
| `S` | Seconds without leading zero | 0-59 |
| `AP` | AM/PM indicator | AM, PM |
| `A` | A/P indicator | A, P |

### Date Format Tokens

| Token | Description | Example |
|-------|-------------|---------|
| `DDDD` | Full day name | Monday |
| `DDD` | Short day name | Mon |
| `DD` | Day with leading zero | 01-31 |
| `D` | Day without leading zero | 1-31 |
| `MMMM` | Full month name | January |
| `MMM` | Short month name | Jan |
| `MM` | Month number with leading zero | 01-12 |
| `M` | Month number without leading zero | 1-12 |
| `YYYY` | 4-digit year | 2024 |
| `YY` | 2-digit year | 24 |

### Format Examples

**Time formats:**
- `"HH:MM:SS"` → `14:35:22`
- `"HH:MM"` → `14:35`
- `"hh:MM AP"` → `02:35 PM`
- `"h:MM A"` → `2:35 P`

**Date formats:**
- `"DDD DD/MM/YYYY"` → `Mon 15/01/2024`
- `"DDDD, MMMM D, YYYY"` → `Monday, January 15, 2024`
- `"DD-MMM-YY"` → `15-Jan-24`
- `"D MMM YYYY"` → `15 Jan 2024`
- `"MM/DD/YYYY"` → `01/15/2024` (US format)

### Example Use Cases

```python
# Morning/daytime scenes (9am-6pm in normal mode)
("ScrollingImageScene", ("images/daytime.png",), {}, "day"),
("StaticImageScene", ("images/work.png",), {}, "day"),

# Evening/night scenes (6pm-1am in dark mode)
("CubeScene", (), {"num_cubes": 3}, "night"),
("TetrisScene", (), {"fall_speed": 0.01, "reset_interval": 60.0}, "night"),
("ScrollingImageScene", ("images/stars.png",), {"scroll_speed": 0.3}, "night"),

# Always available (shown in both normal and dark modes)
("ScrollingImageScene", ("images/clouds.png",), {}),
("StaticImageScene", ("images/abstract.png",), {}, None),
```

### Time Utilities (`time_utils.py`)

**Display mode functions:**
- `get_current_hour(rtc)`: Extract current hour (0-23) from RTC
- `get_current_mode(rtc, mode_schedule)`: Determine current display mode from hour and schedule
- `is_scene_active_in_mode(scene_preference, mode)`: Check if scene should be active in given mode
- `resolve_image_path_for_mode(image_path, mode)`: Resolve image path to night variant if in dark mode

**Date/time formatting functions:**
- `format_time(rtc, format_string)`: Format time using custom format string with tokens (HH, MM, SS, etc.)
- `format_date(rtc, format_string)`: Format date using custom format string with tokens (DD, MMM, YYYY, etc.)

### Mode Transitions

- **Immediate Switching**: When mode changes, scenes are re-evaluated immediately
- **Scene Filtering**: Only scenes matching the current mode are available for rotation
- **Automatic Updates**: Scene manager detects mode changes and switches scenes if needed

## Extending with New Scenes

To add new scene types:

1. **Create Scene Class**: Inherit from `Scene` base class in `scenes.py`
   ```python
   class CustomScene(Scene):
       def __init__(self, display, png_decoder, *args, display_mode=None):
           super().__init__(display, png_decoder)
           self.display_mode = display_mode if display_mode is not None else "normal"
           # Custom initialization

       def update(self, delta_time):
           # Update scene state/animation
           pass

       def render(self):
           # Render scene content
           # For vector/generated graphics, dim colors in dark mode:
           # if self.display_mode == "dark":
           #     r, g, b = config.dim_color(r, g, b)
           pass

       def cleanup(self):
           # Clean up resources
           pass
   ```

2. **Register Scene**: Add to scene manager in `main.py` or modify `create_default_scene_manager()`
   ```python
   scene_manager.add_scene_class(CustomScene, arg1, arg2)
   ```

3. **Configuration**: Add scene-specific settings to `config.py` if needed

### Scene Development Tips
- Keep memory usage minimal - MicroPython has limited RAM
- Use the shared PNG decoder efficiently
- Implement proper cleanup to avoid memory leaks
- Test scene transitions to ensure smooth operation
- Consider frame timing - aim for consistent 60fps performance
- **Night Mode Support**:
  - For image scenes: create "_night.png" variants of your images
  - For vector/generated graphics: use `config.dim_color()` to dim RGB values in dark mode
  - Accept `display_mode` parameter in `__init__()` to enable mode-aware rendering