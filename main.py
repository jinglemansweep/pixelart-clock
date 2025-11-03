import machine
import network
import ntptime
import pngdec
import time

from interstate75 import Interstate75, DISPLAY_INTERSTATE75_256X64 as DISPLAY_INTERSTATE75

# Import new modular components
import config
import time_utils
from hud import HUD
from scene_manager import create_scene_manager_from_config

# HARDWARE

i75 = Interstate75(display=DISPLAY_INTERSTATE75, stb_invert=False, panel_type=Interstate75.PANEL_GENERIC)
display = i75.display
display.set_thickness(1)
WIDTH, HEIGHT = display.get_bounds()
rtc = machine.RTC()

# Initialize display colors
config.init_colors(display)

# NETWORK

try:
    from secrets import WIFI_PASSWORD, WIFI_SSID
    if WIFI_SSID == "":
        raise ValueError("WIFI_SSID in 'secrets.py' is empty!")
    if WIFI_PASSWORD == "":
        raise ValueError("WIFI_PASSWORD in 'secrets.py' is empty!")
except ImportError:
    raise ImportError("'secrets.py' is missing")
except ValueError as e:
    print(e)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

def network_connect(SSID, PSK):
    max_wait = 5
    print("WiFi connecting...")
    wlan.config(pm=0xa11140) # Turn WiFi power saving off for some slow APs
    wlan.connect(SSID, PSK)

    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('Waiting for connection...')
        time.sleep(1)

    if wlan.status() != 3:
        print("WiFi connection failed, retrying")
        
    print("WiFi connected")
          
def sync_time():
    try:
        network_connect(WIFI_SSID, WIFI_PASSWORD)
    except NameError:
        print("Create secrets.py with your WiFi credentials")
    if wlan.status() < 0 or wlan.status() >= 3:
        try:
            ntptime.settime()
            print("NTP clock set")
        except OSError:
            print("NTP sync failed")
            
# Initialize modular components

# Init

sync_time()
png_decoder = pngdec.PNG(display)

# Initialize HUD and Scene Manager
hud = HUD(display, rtc)
scene_manager = create_scene_manager_from_config(display, png_decoder, rtc)

# Main Loop

print("Main loop starting...")
print(f"Scene duration: {config.SCENE_DURATION} seconds")
print(f"Scene selection: {config.SCENE_SELECTION}")

# Track display mode for brightness control
current_display_mode = None

while True:
    # Get current display mode
    display_mode = time_utils.get_current_mode(rtc, config.MODE_SCHEDULE)

    # Check if mode changed
    if display_mode != current_display_mode:
        current_display_mode = display_mode
        print(f"Display mode: {display_mode}")

        # Apply brightness for dark mode
        # Note: Interstate75/PicoGraphics may not support brightness control
        # If available, use display.set_backlight() or i75.set_brightness()
        if hasattr(i75, 'set_brightness'):
            if display_mode == "dark":
                i75.set_brightness(config.DARK_MODE_BRIGHTNESS)
            elif display_mode == "normal":
                i75.set_brightness(1.0)

    # Skip rendering in off mode
    if display_mode == "off":
        # Clear display to black
        display.set_pen(0)
        display.clear()
        i75.update()
        time.sleep(config.SCROLL_DELAY)
        continue

    # Clear display
    display.set_pen(0)
    display.clear()

    # Update and render current scene
    scene_manager.update(config.SCROLL_DELAY)
    scene_manager.render()

    # Render HUD overlay
    hud.render()

    # Update display and sleep
    i75.update()
    time.sleep(config.SCROLL_DELAY)

