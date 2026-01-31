import os
import sys
import logging
from datetime import datetime
from collections import deque
from typing import Optional, TextIO
import threading

class ProgressLogger:
    """
    Centralized logging system for Marvel Mega Cut processing.
    Handles FFmpeg output redirection, log file management, and recent output tracking.
    """
    
    def __init__(self, log_file: str = "mega_cut.log", max_recent_chars: int = 120):
        self.log_file = log_file
        self.max_recent_chars = max_recent_chars
        self.recent_output = deque(maxlen=500)  # Keep last 500 lines for recent output
        self.lock = threading.Lock()
        
        # Set up logging
        self.logger = logging.getLogger('mega_cut')
        self.logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Custom formatter with timestamps
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Initialize log file
        self.logger.info("=== Marvel Mega Cut Processing Started ===")
        
    def log_info(self, message: str):
        """Log an info message."""
        with self.lock:
            self.logger.info(message)
            self.recent_output.append(f"INFO: {message}")
    
    def log_warning(self, message: str):
        """Log a warning message."""
        with self.lock:
            self.logger.warning(message)
            self.recent_output.append(f"WARN: {message}")
    
    def log_error(self, message: str):
        """Log an error message."""
        with self.lock:
            self.logger.error(message)
            self.recent_output.append(f"ERROR: {message}")
    
    def log_ffmpeg_output(self, output: str):
        """Log FFmpeg output (usually verbose technical details)."""
        with self.lock:
            # Split into lines and log each
            for line in output.strip().split('\n'):
                if line.strip():
                    self.logger.info(f"FFMPEG: {line.strip()}")
                    self.recent_output.append(line.strip())
    
    def get_recent_output(self) -> str:
        """Get the last max_recent_chars characters from recent output."""
        with self.lock:
            # Join recent lines and get last N characters
            recent_text = ' '.join(self.recent_output)
            if len(recent_text) <= self.max_recent_chars:
                return recent_text
            return '...' + recent_text[-self.max_recent_chars:]
    
    def get_log_file_size(self) -> str:
        """Get formatted log file size."""
        try:
            size_bytes = os.path.getsize(self.log_file)
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            else:
                return f"{size_bytes / (1024 * 1024):.1f} MB"
        except OSError:
            return "0 B"
    
    def close(self):
        """Close the logger and clean up handlers."""
        with self.lock:
            self.logger.info("=== Marvel Mega Cut Processing Completed ===")
            for handler in self.logger.handlers:
                handler.close()
            self.logger.handlers.clear()


class OutputRedirector:
    """
    Context manager to redirect stdout/stderr to the logger.
    Used to capture MoviePy and FFmpeg output.
    """
    
    def __init__(self, logger: ProgressLogger, stream_name: str = "stdout"):
        self.logger = logger
        self.stream_name = stream_name
        self.original_stream = None
        self.redirected_output = []
    
    def write(self, text: str):
        """Capture written text."""
        if text.strip():
            self.redirected_output.append(text)
            # Log FFmpeg-like output
            if any(keyword in text.lower() for keyword in ['input #', 'stream #', 'codec', 'duration:', 'bitrate:']):
                self.logger.log_ffmpeg_output(text)
    
    def flush(self):
        """Flush method required for file-like object."""
        pass
    
    def __enter__(self):
        """Enter context manager."""
        if self.stream_name == "stdout":
            self.original_stream = sys.stdout
            sys.stdout = self
        elif self.stream_name == "stderr":
            self.original_stream = sys.stderr
            sys.stderr = self
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if self.stream_name == "stdout":
            sys.stdout = self.original_stream
        elif self.stream_name == "stderr":
            sys.stderr = self.original_stream 