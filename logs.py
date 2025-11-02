"""
Logging System for Trading Bot
"""

import logging
import sys
from datetime import datetime
from functools import wraps
import traceback

# Import config later to avoid circular imports
try:
    import config
    MAX_LOG_LINES = config.MAX_LOG_LINES
    LOG_LEVEL = config.LOG_LEVEL
    LOG_FILE = config.LOG_FILE
except:
    MAX_LOG_LINES = 1000
    LOG_LEVEL = "INFO"
    LOG_FILE = "bot_logs.txt"

class BotLogger:
    def __init__(self):
        """Initialize logger"""
        self.log_lines = []
        self.max_lines = MAX_LOG_LINES
        
        # Setup logging
        self.logger = logging.getLogger('MidStrategyBot')
        self.logger.setLevel(getattr(logging, LOG_LEVEL))
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setLevel(logging.DEBUG)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def info(self, message):
        """Log info message"""
        self.logger.info(message)
        self._add_to_memory(f"ℹ️ {message}")
    
    def error(self, message):
        """Log error message"""
        self.logger.error(message)
        self._add_to_memory(f"❌ {message}")
    
    def warning(self, message):
        """Log warning message"""
        self.logger.warning(message)
        self._add_to_memory(f"⚠️ {message}")
    
    def debug(self, message):
        """Log debug message"""
        self.logger.debug(message)
    
    def _add_to_memory(self, message):
        """Add log to memory for /logs command"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_lines.append(f"`{timestamp}` {message}")
        
        # Keep only last N lines
        if len(self.log_lines) > self.max_lines:
            self.log_lines = self.log_lines[-self.max_lines:]
    
    def get_recent_logs(self, count=20):
        """Get recent logs for display"""
        return self.log_lines[-count:]


class PerformanceTracker:
    def __init__(self):
        """Track bot performance metrics"""
        self.scans_completed = 0
        self.total_signals = 0
        self.total_api_calls = 0
        self.total_errors = 0
        self.scan_times = []
        self.max_scan_times = 100
    
    def increment_scans(self):
        self.scans_completed += 1
    
    def increment_signals(self):
        self.total_signals += 1
    
    def increment_api_calls(self):
        self.total_api_calls += 1
    
    def increment_errors(self):
        self.total_errors += 1
    
    def record_scan_time(self, duration):
        """Record scan duration"""
        self.scan_times.append(duration)
        self.scans_completed += 1
        
        # Keep only last N scan times
        if len(self.scan_times) > self.max_scan_times:
            self.scan_times = self.scan_times[-self.max_scan_times:]
    
    def get_stats(self):
        """Get performance statistics"""
        avg_scan_time = sum(self.scan_times) / len(self.scan_times) if self.scan_times else 0
        
        return {
            'scans_completed': self.scans_completed,
            'total_signals': self.total_signals,
            'total_api_calls': self.total_api_calls,
            'total_errors': self.total_errors,
            'avg_scan_time': avg_scan_time
        }


# Decorator for exception handling
def log_exceptions(func):
    """Decorator to log exceptions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Exception in {func.__name__}: {str(e)}")
            logger.debug(traceback.format_exc())
            return None
    return wrapper


# Global instances
logger = BotLogger()
performance_tracker = PerformanceTracker()
