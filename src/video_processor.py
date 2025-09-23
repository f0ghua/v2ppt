"""
Video processing module for extracting frames from video files
"""
import cv2
import numpy as np
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Generator
import time

from config.settings import VideoSettings
from src.utils import ProgressTracker, format_duration

logger = logging.getLogger('v2ppt.video')

class VideoProcessor:
    """
    Video processor for extracting frames from video files
    """
    
    def __init__(self, video_path: str):
        """
        Initialize video processor
        
        Args:
            video_path: Path to the video file
        """
        self.video_path = Path(video_path)
        self.cap = None
        self.video_info = {}
        
        # Validate video file
        if not self.video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Initialize video capture
        self._initialize_video()
    
    def _initialize_video(self):
        """Initialize video capture and get video information"""
        self.cap = cv2.VideoCapture(str(self.video_path))
        
        if not self.cap.isOpened():
            raise ValueError(f"Cannot open video file: {self.video_path}")
        
        # Get video properties
        self.video_info = {
            'fps': self.cap.get(cv2.CAP_PROP_FPS),
            'frame_count': int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'duration': 0  # Will be calculated
        }
        
        # Calculate duration
        if self.video_info['fps'] > 0:
            self.video_info['duration'] = self.video_info['frame_count'] / self.video_info['fps']
        
        logger.info(f"Video loaded: {self.video_path.name}")
        logger.info(f"Resolution: {self.video_info['width']}x{self.video_info['height']}")
        logger.info(f"FPS: {self.video_info['fps']:.2f}")
        logger.info(f"Duration: {format_duration(self.video_info['duration'])}")
        logger.info(f"Total frames: {self.video_info['frame_count']}")
    
    def get_video_info(self) -> dict:
        """
        Get video information
        
        Returns:
            Dictionary containing video properties
        """
        return self.video_info.copy()
    
    def extract_frames(self, output_dir: Path,
                      frame_interval: Optional[float] = None,
                      frame_step: Optional[int] = None,
                      skip_start: float = 0,
                      skip_end: float = 0,
                      progress_callback: Optional[callable] = None) -> List[Path]:
        """
        Extract frames from video

        Args:
            output_dir: Directory to save extracted frames
            frame_interval: Time interval between frames (seconds)
            frame_step: Frame step (alternative to time interval)
            skip_start: Skip frames at the beginning (seconds)
            skip_end: Skip frames at the end (seconds)
            progress_callback: Optional callback function for progress updates (current, total)

        Returns:
            List of paths to extracted frame images
        """
        # Use default settings if not provided
        if frame_interval is None:
            frame_interval = VideoSettings.FRAME_INTERVAL
        if frame_step is None:
            frame_step = VideoSettings.FRAME_STEP
        if skip_start == 0:
            skip_start = VideoSettings.SKIP_START_SECONDS
        if skip_end == 0:
            skip_end = VideoSettings.SKIP_END_SECONDS
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Calculate frame extraction parameters
        fps = self.video_info['fps']
        total_frames = self.video_info['frame_count']
        duration = self.video_info['duration']
        
        # Calculate start and end frames
        start_frame = int(skip_start * fps)
        end_frame = total_frames - int(skip_end * fps)
        
        if start_frame >= end_frame:
            raise ValueError("Skip parameters result in no frames to extract")
        
        # Determine extraction method
        if frame_step is not None:
            # Extract every N frames
            frame_indices = list(range(start_frame, end_frame, frame_step))
        else:
            # Extract based on time interval
            frame_interval_frames = int(frame_interval * fps)
            if frame_interval_frames < 1:
                frame_interval_frames = 1
            frame_indices = list(range(start_frame, end_frame, frame_interval_frames))
        
        logger.info(f"Extracting {len(frame_indices)} frames from video")
        logger.info(f"Frame range: {start_frame} to {end_frame}")
        
        # Extract frames
        extracted_frames = []
        progress = ProgressTracker(len(frame_indices), "Extracting frames")

        for i, frame_index in enumerate(frame_indices):
            # Set video position
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)

            # Read frame
            ret, frame = self.cap.read()
            if not ret:
                logger.warning(f"Failed to read frame at index {frame_index}")
                continue

            # Check frame quality
            if not self._is_frame_valid(frame):
                logger.debug(f"Skipping invalid frame at index {frame_index}")
                continue

            # Generate filename
            timestamp = frame_index / fps
            filename = f"frame_{i:06d}_{timestamp:.2f}s.png"
            frame_path = output_dir / filename

            # Save frame
            success = cv2.imwrite(str(frame_path), frame)
            if success:
                extracted_frames.append(frame_path)
                logger.debug(f"Saved frame: {filename}")
            else:
                logger.warning(f"Failed to save frame: {filename}")

            progress.update()

            # Call external progress callback if provided
            if progress_callback:
                progress_callback(i + 1, len(frame_indices))
        
        logger.info(f"Successfully extracted {len(extracted_frames)} frames")
        return extracted_frames
    
    def _is_frame_valid(self, frame: np.ndarray) -> bool:
        """
        Check if frame meets quality requirements
        
        Args:
            frame: Frame image as numpy array
            
        Returns:
            True if frame is valid
        """
        if frame is None or frame.size == 0:
            return False
        
        height, width = frame.shape[:2]
        
        # Check minimum dimensions
        if width < VideoSettings.MIN_FRAME_WIDTH or height < VideoSettings.MIN_FRAME_HEIGHT:
            return False
        
        # Check if frame is not completely black or white
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        
        # Skip frames that are too dark or too bright
        if mean_brightness < 10 or mean_brightness > 245:
            return False
        
        return True
    
    def extract_frame_at_time(self, timestamp: float, output_path: Path) -> bool:
        """
        Extract a single frame at specific timestamp
        
        Args:
            timestamp: Time in seconds
            output_path: Path to save the frame
            
        Returns:
            True if successful
        """
        if timestamp < 0 or timestamp > self.video_info['duration']:
            raise ValueError(f"Timestamp {timestamp} is out of range")
        
        # Set video position
        self.cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
        
        # Read frame
        ret, frame = self.cap.read()
        if not ret:
            return False
        
        # Save frame
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return cv2.imwrite(str(output_path), frame)
    
    def get_frame_generator(self, start_frame: int = 0, 
                           end_frame: Optional[int] = None,
                           step: int = 1) -> Generator[Tuple[int, np.ndarray], None, None]:
        """
        Generator for iterating through video frames
        
        Args:
            start_frame: Starting frame index
            end_frame: Ending frame index (None for end of video)
            step: Frame step
            
        Yields:
            Tuple of (frame_index, frame_image)
        """
        if end_frame is None:
            end_frame = self.video_info['frame_count']
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        current_frame = start_frame
        while current_frame < end_frame:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            yield current_frame, frame
            
            # Skip frames according to step
            if step > 1:
                for _ in range(step - 1):
                    ret, _ = self.cap.read()
                    if not ret:
                        return
            
            current_frame += step
    
    def close(self):
        """Release video capture resources"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    def __del__(self):
        """Destructor"""
        self.close()
