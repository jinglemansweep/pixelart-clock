"""
Time utilities for display mode scheduling, formatting, and timezone/DST handling
"""
import time as _time
import os

import config


def _last_sunday_of_month(year, month):
    """Returns the day of the month (1-31) of the last Sunday in the given month."""
    if month == 12:
        ny, nm = year + 1, 1
    else:
        ny, nm = year, month + 1

    next_midnight = _time.mktime((ny, nm, 1, 0, 0, 0, 0, 0))
    last_epoch = next_midnight - 86400
    last = _time.localtime(last_epoch)
    last_day = last[2]
    last_dow = last[6]
    return last_day - ((last_dow + 1) % 7)


def _nth_sunday_of_month(year, month, n):
    """Returns the day of the month (1-31) of the nth Sunday in the given month."""
    ep = _time.mktime((year, month, 1, 0, 0, 0, 0, 0))
    first_dow = _time.localtime(ep)[6]
    if first_dow == 6:
        days_to_first = 0
    else:
        days_to_first = 6 - first_dow
    return 1 + days_to_first + (n - 1) * 7


def _is_dst_active(rtc):
    """
    Determine whether DST is currently active based on the configured rules.

    Evaluates the DST transition window against the current RTC time (which is
    stored as UTC). EU transitions are at fixed UTC times (01:00). US
    transitions are at 02:00 local time, converted to UTC using the configured
    offset.

    Returns:
        bool: True if DST is currently in effect.
    """
    dst_cfg = config.DST_CONFIG
    if dst_cfg is None:
        return False

    now = rtc.datetime()
    year, month, day, _, hour, minute, second, _ = now
    now_t = (year, month, day, hour, minute, second, 0, 0)
    now_epoch = _time.mktime(now_t)

    base = config.TIMEZONE_OFFSET

    if dst_cfg == "eu":
        start_day = _last_sunday_of_month(year, 3)
        end_day = _last_sunday_of_month(year, 10)
        start_epoch = _time.mktime((year, 3, start_day, 0, 0, 0, 0, 0)) + 3600
        end_epoch = _time.mktime((year, 10, end_day, 0, 0, 0, 0, 0)) + 3600
        return start_epoch <= now_epoch < end_epoch

    elif dst_cfg == "us":
        start_day = _nth_sunday_of_month(year, 3, 2)
        end_day = _nth_sunday_of_month(year, 11, 1)
        dst_offset = config.DST_OFFSET
        start_epoch = (
            _time.mktime((year, 3, start_day, 0, 0, 0, 0, 0))
            + int((2.0 - base) * 3600)
        )
        end_epoch = (
            _time.mktime((year, 11, end_day, 0, 0, 0, 0, 0))
            + int((2.0 - (base + dst_offset)) * 3600)
        )
        return start_epoch <= now_epoch < end_epoch

    return False


def get_local_datetime(rtc):
    """
    Convert the RTC's UTC datetime to local time using the configured
    timezone offset and DST rules.

    The returned tuple follows the same format as time.localtime():
        (year, month, mday, hour, minute, second, weekday, yearday)
    where weekday is 0=Monday … 6=Sunday.

    When TIMEZONE_OFFSET is 0 and DST_CONFIG is None the conversion is a
    fast no-op (the RTC datetime tuple is simply reshaped to the localtime
    format).
    """
    base = config.TIMEZONE_OFFSET

    if base == 0 and config.DST_CONFIG is None:
        now = rtc.datetime()
        return (now[0], now[1], now[2], now[4], now[5], now[6], now[3], 0)

    total_offset = float(base)
    if _is_dst_active(rtc):
        total_offset += config.DST_OFFSET

    now = rtc.datetime()
    utc_t = (now[0], now[1], now[2], now[4], now[5], now[6], 0, 0)
    utc_epoch = _time.mktime(utc_t)
    local_epoch = utc_epoch + int(total_offset * 3600)
    return _time.localtime(local_epoch)


def get_current_hour(rtc):
    """Get the current hour (0-23) adjusted for timezone and DST."""
    local = get_local_datetime(rtc)
    return local[3]


def get_current_mode(rtc, mode_schedule):
    """
    Get the current display mode based on the hour and mode schedule.

    The mode_schedule is a dict mapping hour (0-23) to mode ("normal", "night", "off").
    Only specify hours where mode changes; the mode persists until the next change.

    Example: {9: "normal", 18: "night", 1: "off"} means:
        - 1am-8:59am: off
        - 9am-5:59pm: normal
        - 6pm-12:59am: night

    Args:
        rtc: RTC object to get current time from
        mode_schedule (dict): Dict mapping hour (int) to mode (str)

    Returns:
        str: Current mode ("normal", "night", or "off")
    """
    if not mode_schedule:
        return "normal"  # Default to normal if no schedule

    current_hour = get_current_hour(rtc)

    # Sort schedule hours to find the most recent mode change
    sorted_hours = sorted(mode_schedule.keys())

    # Find the most recent hour that has passed
    current_mode = None
    for hour in sorted_hours:
        if current_hour >= hour:
            current_mode = mode_schedule[hour]
        else:
            break

    # If no mode found (current hour is before first scheduled hour),
    # wrap around and use the last scheduled mode from previous day
    if current_mode is None:
        current_mode = mode_schedule[sorted_hours[-1]]

    return current_mode


def is_scene_active_in_mode(scene_preference, mode):
    """
    Check if a scene should be active in the given display mode.

    Args:
        scene_preference (str or None): Scene time preference
            - "day": active only in normal mode
            - "night": active only in night mode
            - None: active in both normal and night modes
        mode (str): Current display mode ("normal", "night", or "off")

    Returns:
        bool: True if scene should be active in this mode
    """
    if mode == "off":
        return False

    if scene_preference is None:
        return True

    if scene_preference == "day":
        return mode == "normal"
    elif scene_preference == "night":
        return mode == "night"

    return True


def resolve_image_path_for_mode(image_path, mode):
    """
    Resolve image path based on display mode, checking for night mode variants.

    If mode is "night", checks if an image with "_night" suffix exists
    (e.g., "image_night.png" for "image.png"). If it exists, returns the night
    variant path. Otherwise, returns the original path.

    Args:
        image_path (str): Original image path (e.g., "images/bg1.png")
        mode (str): Current display mode ("normal", "night", or "off")

    Returns:
        str: Resolved image path (night variant if available in night mode, otherwise original)
    """
    if mode != "night" or not image_path:
        return image_path

    if '.' in image_path:
        base_path, ext = image_path.rsplit('.', 1)
        night_variant_path = f"{base_path}_night.{ext}"
    else:
        night_variant_path = f"{image_path}_night"

    try:
        os.stat(night_variant_path)
        print(f"Using night variant: {night_variant_path}")
        return night_variant_path
    except OSError:
        return image_path


def format_time(rtc, format_string):
    """
    Format time using a custom format string. Applies timezone/DST offset.

    Supported tokens:
        HH - 24-hour with leading zero (00-23)
        H  - 24-hour without leading zero (0-23)
        hh - 12-hour with leading zero (01-12)
        h  - 12-hour without leading zero (1-12)
        MM - Minutes with leading zero (00-59)
        M  - Minutes without leading zero (0-59)
        SS - Seconds with leading zero (00-59)
        S  - Seconds without leading zero (0-59)
        AP - AM/PM
        A  - A/P

    Args:
        rtc: RTC object
        format_string: Format string (e.g., "HH:MM:SS", "hh:MM AP")

    Returns:
        str: Formatted time string
    """
    local = get_local_datetime(rtc)
    hour = local[3]
    minute = local[4]
    second = local[5]

    hour_12 = hour % 12
    if hour_12 == 0:
        hour_12 = 12
    am_pm = "AM" if hour < 12 else "PM"
    a_p = "A" if hour < 12 else "P"

    replacements = [
        ("HH", "\x01"),
        ("hh", "\x02"),
        ("MM", "\x03"),
        ("SS", "\x04"),
        ("AP", "\x05"),
        ("H", "\x06"),
        ("h", "\x07"),
        ("M", "\x08"),
        ("S", "\x09"),
        ("A", "\x0A"),
    ]

    result = format_string
    for token, placeholder in replacements:
        result = result.replace(token, placeholder)

    result = result.replace("\x01", "{:02d}".format(hour))
    result = result.replace("\x02", "{:02d}".format(hour_12))
    result = result.replace("\x03", "{:02d}".format(minute))
    result = result.replace("\x04", "{:02d}".format(second))
    result = result.replace("\x05", am_pm)
    result = result.replace("\x06", str(hour))
    result = result.replace("\x07", str(hour_12))
    result = result.replace("\x08", str(minute))
    result = result.replace("\x09", str(second))
    result = result.replace("\x0A", a_p)

    return result


def format_date(rtc, format_string):
    """
    Format date using a custom format string. Applies timezone/DST offset.

    Supported tokens:
        DDDD - Full day name (Monday)
        DDD  - Short day name (Mon)
        DD   - Day with leading zero (01-31)
        D    - Day without leading zero (1-31)
        MMMM - Full month name (January)
        MMM  - Short month name (Jan)
        MM   - Month number with leading zero (01-12)
        M    - Month number without leading zero (1-12)
        YYYY - 4-digit year (2024)
        YY   - 2-digit year (24)

    Args:
        rtc: RTC object
        format_string: Format string (e.g., "DDD DD/MM/YYYY", "DDDD, MMMM D, YYYY")

    Returns:
        str: Formatted date string
    """
    from config import DAYS_SHORT, DAYS_LONG, MONTHS_SHORT, MONTHS_LONG

    local = get_local_datetime(rtc)
    year = local[0]
    month = local[1]
    day = local[2]
    dow = local[6]

    replacements = [
        ("DDDD", "\x01"),
        ("DDD", "\x02"),
        ("MMMM", "\x03"),
        ("MMM", "\x04"),
        ("YYYY", "\x05"),
        ("YY", "\x06"),
        ("DD", "\x07"),
        ("D", "\x08"),
        ("MM", "\x09"),
        ("M", "\x0A"),
    ]

    result = format_string
    for token, placeholder in replacements:
        result = result.replace(token, placeholder)

    result = result.replace("\x01", DAYS_LONG[dow])
    result = result.replace("\x02", DAYS_SHORT[dow])
    result = result.replace("\x03", MONTHS_LONG[month - 1])
    result = result.replace("\x04", MONTHS_SHORT[month - 1])
    result = result.replace("\x05", str(year))
    result = result.replace("\x06", "{:02d}".format(year % 100))
    result = result.replace("\x07", "{:02d}".format(day))
    result = result.replace("\x08", str(day))
    result = result.replace("\x09", "{:02d}".format(month))
    result = result.replace("\x0A", str(month))

    return result
