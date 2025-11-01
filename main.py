import machine
import network
import os
import ntptime
import pngdec
import time

from random import choice
from interstate75 import Interstate75, DISPLAY_INTERSTATE75_256X64 as DISPLAY_INTERSTATE75

# CONFIG

SCROLL_SPEED = 1
SCROLL_DELAY = 0.01

TIME_POSITION = (2, 2)
TIME_SHOW_SECONDS = False

DATE_POSITION = (2, 16)
DATE_SHOW_DAY = True
DATE_SHORT_MONTH = True

IMG_WIDTH = 256
IMG_HEIGHT = 64
IMG_SCALE = (1, 1)

# HARDWARE

i75 = Interstate75(display=DISPLAY_INTERSTATE75, stb_invert=False, panel_type=Interstate75.PANEL_GENERIC)
display = i75.display
display.set_thickness(1)
WIDTH, HEIGHT = display.get_bounds()
rtc = machine.RTC()

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
            
# Constants

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
IMAGES_PATH = "images"

C_BLACK = display.create_pen(0, 0, 0)
C_WHITE = display.create_pen(255, 255, 255)
C_ORANGE = display.create_pen(255, 117, 24)
OUTLINE_SHADOW, OUTLINE_FULL = 1, 2

# UI Helpers

def render_text(text, position, pen=C_WHITE, font="bitmap6", scale=1, outline=None, outline_pen=C_BLACK):
    display.set_font(font)
    x, y = position
    for ox in (-1, 0, 1):
        for oy in (-1, 0, 1):
            if outline == OUTLINE_FULL or (outline == OUTLINE_SHADOW and ox == 1 and oy == 1):
                display.set_pen(outline_pen)
                display.text(text, x + ox, y + oy, scale=scale)
    display.set_pen(pen)
    display.text(text, x, y, scale=scale)
    
# Init

sync_time()
png_decoder = pngdec.PNG(display)
image_filename = choice(os.listdir(IMAGES_PATH))
image_path = f"{IMAGES_PATH}/{image_filename}"
png_decoder.open_file(image_path)

# Main Loop

print("Main loop starting...")

x_pos = 0

while True:
    
    now = rtc.datetime()
    now_year, now_month, now_day, now_dow = now[0:4]
    now_hours, now_mins, now_secs = now[4:7]
    day_name = DAYS[now_dow]
    
    month_name = MONTHS[now_month]
    if DATE_SHORT_MONTH:
        month_name = month_name[:3]
    if DATE_SHOW_DAY:
        date_str = "{} {:02d} {} {:04d}".format(day_name, now_day, month_name, now_year)
    else:
        date_str = "{:02d} {} {:04d}".format(now_day, month_name, now_year)

    if TIME_SHOW_SECONDS:
        time_str = "{:02d}:{:02d}:{:02d}".format(now_hours, now_mins, now_secs)
    else:
        time_str = "{:02d}:{:02d}".format(now_hours, now_mins)
    if x_pos < -WIDTH:
        x_pos = 0
 
    x_pos -= SCROLL_SPEED
    
    display.set_pen(0)
    display.clear()

    png_decoder.decode(x_pos, 0, scale=IMG_SCALE)
    
    if x_pos < IMG_WIDTH:
       png_decoder.decode(x_pos + IMG_WIDTH, 0, scale=IMG_SCALE)

    render_text(time_str, TIME_POSITION, scale=2, outline=OUTLINE_FULL)
    render_text(date_str, DATE_POSITION, C_ORANGE, outline=OUTLINE_FULL)

    i75.update()
    time.sleep(SCROLL_DELAY)

