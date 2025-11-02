import machine
import network
import ntptime
import pngdec
import time

from interstate75 import Interstate75, DISPLAY_INTERSTATE75_256X64 as DISPLAY_INTERSTATE75

# Import new modular components
import config
from hud import HUD
from scene_manager import create_default_scene_manager

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
scene_manager = create_default_scene_manager(display, png_decoder)

# Main Loop

print("Main loop starting...")
print(f"Scene duration: {config.SCENE_DURATION} seconds")
print(f"Scene selection: {config.SCENE_SELECTION}")

while True:
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

