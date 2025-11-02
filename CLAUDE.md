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

#### Scene System (`scenes.py`)
- **Base Scene Class**: Interface with `update()`, `render()`, and `cleanup()` methods
- **ScrollingImageScene**: Horizontally scrolling background images
- **StaticImageScene**: Static background image display
- Memory-efficient design using shared PNG decoder

#### HUD System (`hud.py`)
- **HUD Class**: Renders time, date, and future overlay information
- Separated from scene logic for clean overlay rendering
- Configurable positioning and styling with shadow effects

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

## Extending with New Scenes

To add new scene types:

1. **Create Scene Class**: Inherit from `Scene` base class in `scenes.py`
   ```python
   class CustomScene(Scene):
       def __init__(self, display, png_decoder, *args):
           super().__init__(display, png_decoder)
           # Custom initialization
       
       def update(self, delta_time):
           # Update scene state/animation
           pass
       
       def render(self):
           # Render scene content
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