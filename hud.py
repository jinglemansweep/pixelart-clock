import config
import time_utils

class HUD:
    """Heads-Up Display for overlaying time, date, and other information on scenes"""

    def __init__(self, display, rtc):
        self.display = display
        self.rtc = rtc
    
    def render_text(self, text, position, pen=None, font="bitmap6", scale=1, shadow=False, outline=False):
        """Render text with optional shadow or full outline effect"""
        if pen is None:
            pen = config.C_WHITE
            
        self.display.set_font(font)
        x, y = position
        
        if outline:
            # Render full outline by drawing text at all 8 surrounding positions
            self.display.set_pen(config.C_BLACK)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx != 0 or dy != 0:  # Skip center position
                        self.display.text(text, x + dx, y + dy, scale=scale)
        elif shadow:
            # Simple shadow effect (bottom-right offset)
            self.display.set_pen(config.C_BLACK)
            self.display.text(text, x + 1, y + 1, scale=scale)
        
        # Render main text on top
        self.display.set_pen(pen)
        self.display.text(text, x, y, scale=scale)
    
    def format_time_date(self):
        """Format current time and date strings"""
        now = self.rtc.datetime()
        now_year, now_month, now_day, now_dow = now[0:4]
        now_hours, now_mins, now_secs = now[4:7]
        day_name = config.DAYS[now_dow]
        
        date_str = "{} {:02d}/{:02d}/{:04d}".format(day_name, now_day, now_month, now_year)
        time_str = "{:02d}:{:02d}:{:02d}".format(now_hours, now_mins, now_secs)
        
        return time_str, date_str
    
    def render(self):
        """Render all HUD elements"""
        time_str, date_str = self.format_time_date()

        # Get current display mode to determine if we should dim colors
        current_mode = time_utils.get_current_mode(self.rtc, config.MODE_SCHEDULE)

        # Use dimmed colors in dark mode
        if current_mode == "dark":
            # Create dimmed white and orange colors
            white_r, white_g, white_b = config.dim_color(255, 255, 255)
            orange_r, orange_g, orange_b = config.dim_color(255, 117, 24)
            white_pen = self.display.create_pen(white_r, white_g, white_b)
            orange_pen = self.display.create_pen(orange_r, orange_g, orange_b)
        else:
            # Use normal colors
            white_pen = config.C_WHITE
            orange_pen = config.C_ORANGE

        # Render time with configured text effects
        self.render_text(time_str, config.TIME_POSITION, pen=white_pen, scale=config.TIME_SCALE,
                        outline=config.USE_TEXT_OUTLINE, shadow=config.USE_TEXT_SHADOW)

        # Render date with configured text effects
        self.render_text(date_str, config.DATE_POSITION, pen=orange_pen, scale=config.DATE_SCALE,
                        outline=config.USE_TEXT_OUTLINE, shadow=config.USE_TEXT_SHADOW)