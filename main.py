import machine
import network
import os
import ntptime
import pngdec
import time

from random import choice
from interstate75 import Interstate75, DISPLAY_INTERSTATE75_256X64 as DISPLAY_INTERSTATE75

# MACHINE

rtc = machine.RTC()

# DISPLAY

i75 = Interstate75(display=DISPLAY_INTERSTATE75, stb_invert=False, panel_type=Interstate75.PANEL_GENERIC)
display = i75.display

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
    print("connecting...")
    wlan.config(pm=0xa11140) # Turn WiFi power saving off for some slow APs
    wlan.connect(SSID, PSK)

    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        time.sleep(1)

    if wlan.status() != 3:
        print("Unable to connect. Attempting connection again")

def sync_time():
    try:
        network_connect(WIFI_SSID, WIFI_PASSWORD)
    except NameError:
        print("Create secrets.py with your WiFi credentials")
    if wlan.status() < 0 or wlan.status() >= 3:
        try:
            ntptime.settime()
        except OSError:
            print("Unable to sync with NTP server. Check network and try again.")

# Constants

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
C_WHITE = display.create_pen(255, 255, 255)
C_ORANGE = display.create_pen(255, 117, 24)
# Variables

WIDTH, HEIGHT = display.get_bounds()
SCROLL_SPEED = 1
SCROLL_DELAY = 0.1
IMG_WIDTH = 256
IMG_HEIGHT = 64
IMG_SCALE = (1, 1)

# Init

sync_time()
p = pngdec.PNG(display)
file = choice(os.listdir("covers"))
img = f"covers/{file}"
p.open_file(img)

x_pos = WIDTH

while True:
    
    now = rtc.datetime()
    now_year, now_month, now_day, now_dow = now[0:4]
    now_hours, now_mins, now_secs = now[4:7]
    
    day_name = DAYS[now_dow]
    
    date_str = "{} {:02d}/{:02d}/{:04d}".format(day_name, now_day, now_month, now_year)
    time_str = "{:02d}:{:02d}:{:02d}".format(now_hours, now_mins, now_secs)
    
    if x_pos < -WIDTH:
        x_pos = 0
 
    x_pos -= SCROLL_SPEED
    
    display.set_pen(0)
    display.clear()

    p.decode(x_pos, 0, scale=IMG_SCALE)
    
    if x_pos < 0:
       p.decode(x_pos + IMG_WIDTH, 0, scale=IMG_SCALE)

    display.set_font("bitmap8")
    display.set_pen(C_WHITE)
    display.text(time_str, 2, 2)
    
    display.set_font("bitmap6")
    display.set_pen(C_ORANGE)
    display.text(date_str, 2, 16)
    
    i75.update()
    time.sleep(SCROLL_DELAY)
