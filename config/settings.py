"""
Configuration settings for Video to PPT converter
"""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
FRAMES_DIR = OUTPUT_DIR / "frames"
PPT_DIR = OUTPUT_DIR / "ppt"

# Video processing settings
class VideoSettings:
    """Video processing configuration"""
    # Frame extraction interval (in seconds)
    FRAME_INTERVAL = 5.0
    
    # Alternative: extract every N frames instead of time-based
    FRAME_STEP = None  # If set, overrides FRAME_INTERVAL
    
    # Video quality settings
    MIN_FRAME_WIDTH = 640
    MIN_FRAME_HEIGHT = 480
    
    # Skip frames at the beginning and end (in seconds)
    SKIP_START_SECONDS = 0
    SKIP_END_SECONDS = 0

# Image processing settings
class ImageSettings:
    """Image processing configuration"""
    # Image similarity threshold for duplicate detection (0-1, higher = more strict)
    # Lowered from 0.85 to 0.75 to be less aggressive with PPT slides
    SIMILARITY_THRESHOLD = 0.75
    
    # Image enhancement settings
    ENHANCE_BRIGHTNESS = 1.1
    ENHANCE_CONTRAST = 1.2
    ENHANCE_SHARPNESS = 1.1
    
    # Output image format and quality
    OUTPUT_FORMAT = "PNG"
    JPEG_QUALITY = 95
    
    # Image resize settings
    MAX_WIDTH = 1920
    MAX_HEIGHT = 1080
    MAINTAIN_ASPECT_RATIO = True

# PPT generation settings
class PPTSettings:
    """PowerPoint generation configuration"""
    # Slide dimensions (in inches)
    SLIDE_WIDTH = 13.333  # 16:9 aspect ratio
    SLIDE_HEIGHT = 7.5
    
    # Image positioning on slide
    IMAGE_LEFT = 0.5  # inches from left
    IMAGE_TOP = 0.5   # inches from top
    IMAGE_WIDTH = 12.333  # inches
    IMAGE_HEIGHT = 6.5    # inches
    
    # PPT template settings
    TEMPLATE_PATH = None  # Path to template PPTX file (optional)
    
    # Output settings
    DEFAULT_OUTPUT_NAME = "extracted_presentation.pptx"

# Logging settings
class LogSettings:
    """Logging configuration"""
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = OUTPUT_DIR / "v2ppt.log"
    
    # Console output
    SHOW_PROGRESS = True
    VERBOSE = False

# Performance settings
class PerformanceSettings:
    """Performance optimization settings"""
    # Maximum number of frames to process (0 = no limit)
    MAX_FRAMES = 0
    
    # Parallel processing
    USE_MULTIPROCESSING = True
    MAX_WORKERS = None  # None = auto-detect CPU cores
    
    # Memory management
    BATCH_SIZE = 50  # Process frames in batches
    CLEAR_CACHE_INTERVAL = 100  # Clear cache every N frames

# File format support
SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']

# Create output directories if they don't exist
def ensure_directories():
    """Create necessary directories if they don't exist"""
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    PPT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Validate settings
def validate_settings():
    """Validate configuration settings"""
    errors = []
    
    if VideoSettings.FRAME_INTERVAL <= 0 and VideoSettings.FRAME_STEP is None:
        errors.append("FRAME_INTERVAL must be positive or FRAME_STEP must be set")
    
    if not (0 <= ImageSettings.SIMILARITY_THRESHOLD <= 1):
        errors.append("SIMILARITY_THRESHOLD must be between 0 and 1")
    
    if PPTSettings.SLIDE_WIDTH <= 0 or PPTSettings.SLIDE_HEIGHT <= 0:
        errors.append("Slide dimensions must be positive")
    
    if errors:
        raise ValueError("Configuration errors: " + "; ".join(errors))
    
    return True
