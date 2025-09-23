"""
Utility functions for Video to PPT converter
"""
import os
import logging
import hashlib
from pathlib import Path
from typing import List, Optional, Tuple
import time

def setup_logging(log_level: str = "INFO", log_file: Optional[Path] = None, verbose: bool = False):
    """
    Setup logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file (optional)
        verbose: Enable verbose console output
    """
    # Create logger
    logger = logging.getLogger('v2ppt')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_format = logging.Formatter(
        '%(levelname)s: %(message)s' if not verbose 
        else '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    
    return logger

def validate_file_path(file_path: str, supported_formats: List[str]) -> Path:
    """
    Validate file path and format
    
    Args:
        file_path: Path to the file
        supported_formats: List of supported file extensions
        
    Returns:
        Path object if valid
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is not supported
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    if path.suffix.lower() not in [fmt.lower() for fmt in supported_formats]:
        raise ValueError(f"Unsupported file format: {path.suffix}. "
                        f"Supported formats: {', '.join(supported_formats)}")
    
    return path

def generate_output_filename(input_path: Path, suffix: str = "", extension: str = ".pptx") -> str:
    """
    Generate output filename based on input file
    
    Args:
        input_path: Input file path
        suffix: Additional suffix to add
        extension: Output file extension
        
    Returns:
        Generated filename
    """
    base_name = input_path.stem
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    if suffix:
        return f"{base_name}_{suffix}_{timestamp}{extension}"
    else:
        return f"{base_name}_extracted_{timestamp}{extension}"

def calculate_file_hash(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Calculate MD5 hash of a file
    
    Args:
        file_path: Path to the file
        chunk_size: Size of chunks to read
        
    Returns:
        MD5 hash string
    """
    hash_md5 = hashlib.md5()
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hash_md5.update(chunk)
    
    return hash_md5.hexdigest()

def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string (e.g., "1h 23m 45s")
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in bytes to human-readable string
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"

def clean_filename(filename: str) -> str:
    """
    Clean filename by removing invalid characters
    
    Args:
        filename: Original filename
        
    Returns:
        Cleaned filename
    """
    # Characters not allowed in filenames
    invalid_chars = '<>:"/\\|?*'
    
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove multiple consecutive underscores
    while '__' in filename:
        filename = filename.replace('__', '_')
    
    # Remove leading/trailing underscores and spaces
    filename = filename.strip('_ ')
    
    return filename

class ProgressTracker:
    """Simple progress tracker for console output"""
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()
    
    def update(self, increment: int = 1):
        """Update progress"""
        self.current += increment
        self._display_progress()
    
    def _display_progress(self):
        """Display progress bar"""
        if self.total == 0:
            return
        
        percentage = (self.current / self.total) * 100
        elapsed_time = time.time() - self.start_time
        
        # Estimate remaining time
        if self.current > 0:
            eta = (elapsed_time / self.current) * (self.total - self.current)
            eta_str = format_duration(eta)
        else:
            eta_str = "Unknown"
        
        # Create progress bar
        bar_length = 30
        filled_length = int(bar_length * self.current // self.total)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        
        print(f'\r{self.description}: |{bar}| {self.current}/{self.total} '
              f'({percentage:.1f}%) ETA: {eta_str}', end='', flush=True)
        
        if self.current >= self.total:
            print()  # New line when complete

def ensure_directory(path: Path) -> Path:
    """
    Ensure directory exists, create if it doesn't
    
    Args:
        path: Directory path
        
    Returns:
        Path object
    """
    path.mkdir(parents=True, exist_ok=True)
    return path
