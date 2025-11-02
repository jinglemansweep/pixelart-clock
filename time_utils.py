"""
Time utilities for scene scheduling
"""

def get_current_hour(rtc):
    """Get the current hour (0-23) from RTC"""
    now = rtc.datetime()
    return now[4]  # Hour is at index 4 in datetime tuple

def is_time_in_range(current_hour, hour_start, hour_end):
    """
    Check if current hour is within the specified range.
    Handles cross-midnight ranges (e.g., 21-9 means 9pm to 9am next day).
    
    Args:
        current_hour (int): Current hour (0-23)
        hour_start (int): Start hour (0-23)
        hour_end (int): End hour (0-23)
    
    Returns:
        bool: True if current hour is in range
    """
    if hour_start <= hour_end:
        # Same day range (e.g., 9-17 means 9am to 5pm)
        return hour_start <= current_hour < hour_end
    else:
        # Cross-midnight range (e.g., 21-9 means 9pm to 9am next day)
        return current_hour >= hour_start or current_hour < hour_end

def is_scene_scheduled(schedule, current_hour):
    """
    Check if a scene should be active based on its schedule and current time.
    
    Args:
        schedule (dict or None): Schedule configuration with 'hour_start' and 'hour_end' keys
        current_hour (int): Current hour (0-23)
    
    Returns:
        bool: True if scene should be active
    """
    # No schedule means always active
    if not schedule:
        return True
    
    # Extract schedule parameters with defaults
    hour_start = schedule.get("hour_start", 0)
    hour_end = schedule.get("hour_end", 23)
    
    # Validate hour ranges
    if not (0 <= hour_start <= 23) or not (0 <= hour_end <= 23):
        print(f"Warning: Invalid schedule hours: start={hour_start}, end={hour_end}")
        return True  # Default to active if invalid schedule
    
    return is_time_in_range(current_hour, hour_start, hour_end)

def validate_schedule(schedule):
    """
    Validate a schedule configuration.
    
    Args:
        schedule (dict or None): Schedule to validate
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not schedule:
        return True, None
    
    if not isinstance(schedule, dict):
        return False, "Schedule must be a dictionary"
    
    hour_start = schedule.get("hour_start")
    hour_end = schedule.get("hour_end")
    
    if hour_start is None or hour_end is None:
        return False, "Schedule must have both 'hour_start' and 'hour_end'"
    
    if not isinstance(hour_start, int) or not isinstance(hour_end, int):
        return False, "Schedule hours must be integers"
    
    if not (0 <= hour_start <= 23) or not (0 <= hour_end <= 23):
        return False, "Schedule hours must be between 0 and 23"
    
    return True, None

def format_schedule_description(schedule):
    """
    Format a human-readable description of a schedule.
    
    Args:
        schedule (dict or None): Schedule to describe
    
    Returns:
        str: Human-readable schedule description
    """
    if not schedule:
        return "Always active"
    
    hour_start = schedule.get("hour_start", 0)
    hour_end = schedule.get("hour_end", 23)
    
    # Format hours as HH:00
    start_str = f"{hour_start:02d}:00"
    end_str = f"{hour_end:02d}:00"
    
    if hour_start <= hour_end:
        return f"Active {start_str}-{end_str}"
    else:
        return f"Active {start_str}-{end_str} (next day)"