"""
Time utilities for display mode scheduling and formatting
"""
import os

def get_current_hour(rtc):
    """Get the current hour (0-23) from RTC"""
    now = rtc.datetime()
    return now[4]  # Hour is at index 4 in datetime tuple

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
    # In off mode, no scenes are active
    if mode == "off":
        return False

    # No preference means active in all non-off modes
    if scene_preference is None:
        return True

    # Check scene preference against mode
    if scene_preference == "day":
        return mode == "normal"
    elif scene_preference == "night":
        return mode == "night"

    # Unknown preference, default to active
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

    Examples:
        >>> resolve_image_path_for_mode("images/bg1.png", "night")
        "images/bg1_night.png"  # if file exists
        >>> resolve_image_path_for_mode("images/bg1.png", "normal")
        "images/bg1.png"
    """
    # Only check for night variant in night mode
    if mode != "night" or not image_path:
        return image_path

    # Split path into base and extension
    if '.' in image_path:
        base_path, ext = image_path.rsplit('.', 1)
        night_variant_path = f"{base_path}_night.{ext}"
    else:
        # No extension (unlikely for image files, but handle it)
        night_variant_path = f"{image_path}_night"

    # Check if night variant exists
    try:
        # Try to stat the file to see if it exists
        os.stat(night_variant_path)
        print(f"Using night variant: {night_variant_path}")
        return night_variant_path
    except OSError:
        # Night variant doesn't exist, use original
        return image_path

def format_time(rtc, format_string):
    """
    Format time using a custom format string.

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
    now = rtc.datetime()
    hour = now[4]
    minute = now[5]
    second = now[6]

    # Calculate 12-hour format
    hour_12 = hour % 12
    if hour_12 == 0:
        hour_12 = 12
    am_pm = "AM" if hour < 12 else "PM"
    a_p = "A" if hour < 12 else "P"

    # Use placeholders to avoid conflicts during replacement
    # Replace longer tokens first, using unique placeholders
    replacements = [
        ("HH", "\x01"),  # Placeholder for 24-hour with zero
        ("hh", "\x02"),  # Placeholder for 12-hour with zero
        ("MM", "\x03"),  # Placeholder for minutes with zero
        ("SS", "\x04"),  # Placeholder for seconds with zero
        ("AP", "\x05"),  # Placeholder for AM/PM
        ("H", "\x06"),   # Placeholder for 24-hour no zero
        ("h", "\x07"),   # Placeholder for 12-hour no zero
        ("M", "\x08"),   # Placeholder for minutes no zero
        ("S", "\x09"),   # Placeholder for seconds no zero
        ("A", "\x0A"),   # Placeholder for A/P
    ]

    result = format_string

    # First pass: replace tokens with placeholders
    for token, placeholder in replacements:
        result = result.replace(token, placeholder)

    # Second pass: replace placeholders with actual values
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
    Format date using a custom format string.

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

    now = rtc.datetime()
    year = now[0]
    month = now[1]
    day = now[2]
    dow = now[3]  # Day of week (0-6)

    # Use placeholders to avoid conflicts during replacement
    # Replace longer tokens first, using unique placeholders
    replacements = [
        ("DDDD", "\x01"),  # Placeholder for full day name
        ("DDD", "\x02"),   # Placeholder for short day name
        ("MMMM", "\x03"),  # Placeholder for full month name
        ("MMM", "\x04"),   # Placeholder for short month name
        ("YYYY", "\x05"),  # Placeholder for 4-digit year
        ("YY", "\x06"),    # Placeholder for 2-digit year
        ("DD", "\x07"),    # Placeholder for day with zero
        ("D", "\x08"),     # Placeholder for day no zero
        ("MM", "\x09"),    # Placeholder for month with zero
        ("M", "\x0A"),     # Placeholder for month no zero
    ]

    result = format_string

    # First pass: replace tokens with placeholders
    for token, placeholder in replacements:
        result = result.replace(token, placeholder)

    # Second pass: replace placeholders with actual values
    result = result.replace("\x01", DAYS_LONG[dow])
    result = result.replace("\x02", DAYS_SHORT[dow])
    result = result.replace("\x03", MONTHS_LONG[month - 1])  # month is 1-12
    result = result.replace("\x04", MONTHS_SHORT[month - 1])
    result = result.replace("\x05", str(year))
    result = result.replace("\x06", "{:02d}".format(year % 100))
    result = result.replace("\x07", "{:02d}".format(day))
    result = result.replace("\x08", str(day))
    result = result.replace("\x09", "{:02d}".format(month))
    result = result.replace("\x0A", str(month))

    return result