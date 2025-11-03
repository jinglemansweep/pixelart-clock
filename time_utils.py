"""
Time utilities for display mode scheduling
"""

def get_current_hour(rtc):
    """Get the current hour (0-23) from RTC"""
    now = rtc.datetime()
    return now[4]  # Hour is at index 4 in datetime tuple

def get_current_mode(rtc, mode_schedule):
    """
    Get the current display mode based on the hour and mode schedule.

    The mode_schedule is a dict mapping hour (0-23) to mode ("normal", "dark", "off").
    Only specify hours where mode changes; the mode persists until the next change.

    Example: {9: "normal", 18: "dark", 1: "off"} means:
        - 1am-8:59am: off
        - 9am-5:59pm: normal
        - 6pm-12:59am: dark

    Args:
        rtc: RTC object to get current time from
        mode_schedule (dict): Dict mapping hour (int) to mode (str)

    Returns:
        str: Current mode ("normal", "dark", or "off")
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
            - "night": active only in dark mode
            - None: active in both normal and dark modes
        mode (str): Current display mode ("normal", "dark", or "off")

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
        return mode == "dark"

    # Unknown preference, default to active
    return True