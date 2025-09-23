"""
Processing Wrapper for V2PPT GUI
Enhanced processing functions with progress callback support
"""

import sys
import os
from pathlib import Path
from typing import Optional, Callable, Dict, Any
import logging

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))

try:
    from config.settings import VideoSettings, ImageSettings
    from src.utils import format_duration, format_file_size
    from src.video_processor import VideoProcessor
    from src.image_processor import ImageProcessor
    from src.ppt_generator import PPTGenerator
except ImportError as e:
    # Handle missing dependencies gracefully
    import warnings
    warnings.warn(f"Some dependencies are missing: {e}. GUI may have limited functionality.")

    # Create dummy classes for testing
    class VideoSettings:
        FRAME_INTERVAL = 5.0
        SKIP_START_SECONDS = 0.0
        SKIP_END_SECONDS = 0.0

    class ImageSettings:
        SIMILARITY_THRESHOLD = 0.8

    def format_duration(seconds):
        return f"{seconds:.1f}s"

    def format_file_size(size):
        return f"{size} bytes"


class ProgressCallback:
    """Progress callback wrapper for smooth progress updates"""

    def __init__(self, callback_func: Optional[Callable[[str, float, str, Optional[str]], None]] = None):
        self.callback_func = callback_func
        self.current_overall_progress = 0.0
        self.last_status = ""  # Track last status to avoid duplicate logs
    
    def update(self, overall_progress: float, status: str, details: Optional[str] = None, force_new_log: bool = False):
        """Update progress with direct overall percentage"""
        # Ensure progress only increases
        if overall_progress > self.current_overall_progress:
            self.current_overall_progress = overall_progress

        # Clamp to 0-100 range
        self.current_overall_progress = max(0.0, min(100.0, self.current_overall_progress))

        # Determine if this is a new step or update to current step
        # Extract the main operation from status (e.g., "正在提取视频帧", "正在过滤PPT内容")
        def extract_operation(status_text):
            if "正在提取视频帧" in status_text:
                return "提取视频帧"
            elif "正在过滤PPT内容" in status_text:
                return "过滤PPT内容"
            elif "正在计算图像哈希值" in status_text:
                return "计算图像哈希值"
            elif "正在检测重复图像" in status_text:
                return "检测重复图像"
            elif "正在增强图像质量" in status_text:
                return "增强图像质量"
            else:
                # For other messages, use the first few words
                words = status_text.split()
                return " ".join(words[:3]) if len(words) >= 3 else status_text

        current_operation = extract_operation(status)
        last_operation = extract_operation(self.last_status) if self.last_status else ""
        is_same_step = current_operation == last_operation

        if self.callback_func:
            self.callback_func("处理中", self.current_overall_progress, status, details, not is_same_step or force_new_log)

        self.last_status = status

    def finish(self):
        """Mark as finished"""
        self.current_overall_progress = 100.0
        if self.callback_func:
            self.callback_func("完成", 100.0, "处理完成！", None)


def process_video_to_ppt_with_progress(
    video_path: Path,
    output_path: Path,
    frame_interval: float = VideoSettings.FRAME_INTERVAL,
    frame_step: Optional[int] = None,
    skip_start: float = VideoSettings.SKIP_START_SECONDS,
    skip_end: float = VideoSettings.SKIP_END_SECONDS,
    similarity_threshold: float = ImageSettings.SIMILARITY_THRESHOLD,
    enhance_images: bool = True,
    remove_duplicates: bool = True,
    filter_ppt_content: bool = True,
    presentation_title: Optional[str] = None,
    presentation_author: Optional[str] = None,
    add_slide_titles: bool = False,
    template_path: Optional[str] = None,
    progress_callback: Optional[Callable[[str, float, str, Optional[str]], None]] = None,
    stop_event: Optional[object] = None
) -> bool:
    """
    Process video to PPT with progress callbacks
    
    Args:
        video_path: Path to input video file
        output_path: Path to output PPT file
        ... (other parameters same as original function)
        progress_callback: Callback function for progress updates
        stop_event: Threading event to check for stop requests
        
    Returns:
        True if successful
    """
    logger = logging.getLogger('v2ppt')
    progress = ProgressCallback(progress_callback)

    def check_stop():
        """Check if processing should stop"""
        return stop_event and stop_event.is_set()

    try:
        # 初始化 (0-5%)
        progress.update(1, "正在验证视频文件...")

        if check_stop():
            return False

        # Validate video file
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        progress.update(3, "正在初始化视频处理器...")

        if check_stop():
            return False

        progress.update(5, "初始化完成，开始提取视频帧...", force_new_log=True)

        # 提取视频帧 (5-40%)
        progress.update(7, "正在读取视频信息...")
        
        # Force reload of VideoProcessor to get latest version
        import importlib
        import src.video_processor
        importlib.reload(src.video_processor)
        from src.video_processor import VideoProcessor as ReloadedVideoProcessor

        with ReloadedVideoProcessor(str(video_path)) as video_processor:
            # Get video info
            progress.update(10, "正在读取视频信息...")
            video_info = video_processor.get_video_info()
            duration_str = format_duration(video_info['duration'])

            progress.update(15, f"视频时长: {duration_str}")
            logger.info(f"Video duration: {duration_str}")

            if check_stop():
                return False

            # Extract frames with progress tracking
            frames_dir = Path("output/frames") / video_path.stem
            frames_dir.mkdir(parents=True, exist_ok=True)

            progress.update(20, "正在创建输出目录...")

            # Calculate expected frame count for progress tracking
            fps = video_info['fps']
            duration = video_info['duration']
            if frame_interval:
                expected_frames = int((duration - skip_start - skip_end) / frame_interval)
            else:
                expected_frames = int((duration - skip_start - skip_end) * fps / (frame_step or 1))

            progress.update(25, f"开始提取视频帧，预计提取 {expected_frames} 帧...")

            # Create progress callback for frame extraction
            def frame_progress_callback(current, total):
                if total > 0:
                    # Map frame extraction progress to 25-40% range
                    frame_progress = 25 + (current / total) * 15  # 15% range for frame extraction
                    percentage = int((current / total) * 100)
                    progress.update(frame_progress, f"正在提取视频帧 {current}/{total} ({percentage}%)")

            extracted_frames = video_processor.extract_frames(
                output_dir=frames_dir,
                frame_interval=frame_interval,
                frame_step=frame_step,
                skip_start=skip_start,
                skip_end=skip_end,
                progress_callback=frame_progress_callback
            )

            progress.update(40, f"帧提取完成，共提取 {len(extracted_frames)} 帧")
        
        if not extracted_frames:
            logger.error("No frames were extracted from the video")
            return False
        
        if check_stop():
            return False
        
        # 过滤PPT内容 (40-55%)
        image_processor = ImageProcessor()

        if filter_ppt_content:
            progress.update(42, f"开始过滤 {len(extracted_frames)} 张图像...", force_new_log=True)

            if check_stop():
                return False

            # Create progress callback for PPT filtering
            def filter_progress_callback(current, total):
                if total > 0:
                    # Map filtering progress to 42-55% range
                    filter_progress = 42 + (current / total) * 13  # 13% range for filtering
                    percentage = int((current / total) * 100)
                    progress.update(filter_progress, f"正在过滤PPT内容 {current}/{total} ({percentage}%)")

            filtered_images = image_processor.filter_ppt_images(extracted_frames, filter_progress_callback)

            progress.update(55, f"过滤完成，保留 {len(filtered_images)} 张PPT相关图像")
        else:
            filtered_images = extracted_frames
            progress.update(55, "跳过PPT内容过滤")

        if check_stop():
            return False

        # 检测重复图像 (55-70%)
        if remove_duplicates:
            progress.update(57, f"开始检测 {len(filtered_images)} 张图像的重复...", force_new_log=True)

            if check_stop():
                return False

            progress.update(60, f"使用相似度阈值: {similarity_threshold}")

            # Create progress callback for duplicate detection
            def duplicate_progress_callback(current_progress, total_progress):
                # Map duplicate detection progress to 60-70% range
                duplicate_progress = 60 + current_progress * 10  # 10% range for duplicate detection
                percentage = int(current_progress * 100)

                if current_progress < 0.5:
                    progress.update(duplicate_progress, f"正在计算图像哈希值 ({percentage}%)")
                else:
                    progress.update(duplicate_progress, f"正在检测重复图像 ({percentage}%)")

            if similarity_threshold != ImageSettings.SIMILARITY_THRESHOLD:
                # Custom similarity threshold
                unique_images = image_processor.remove_duplicates(filtered_images, similarity_threshold, duplicate_progress_callback)
            else:
                # Default processing
                unique_images = image_processor.remove_duplicates(filtered_images, progress_callback=duplicate_progress_callback)

            progress.update(70, f"去重完成，保留 {len(unique_images)} 张唯一图像")
        else:
            unique_images = filtered_images
            progress.update(70, "跳过重复检测")

        # Image enhancement (if needed)
        processed_images = []
        if enhance_images:
            for i, img_path in enumerate(unique_images):
                enhanced_image_path = frames_dir / "processed" / f"processed_{i:06d}_{img_path.name}"
                enhanced_path = image_processor.enhance_image(img_path, enhanced_image_path)
                processed_images.append(enhanced_path)
                # Update progress during enhancement
                enhancement_progress = 72 + (i + 1) / len(unique_images) * 8  # 72-80%
                percentage = int(((i + 1) / len(unique_images)) * 100)
                progress.update(enhancement_progress, f"正在增强图像质量 {i+1}/{len(unique_images)} ({percentage}%)")
        else:
            processed_images = unique_images
            progress.update(80, "跳过图像增强")

        if not processed_images:
            logger.error("No images remained after processing")
            return False
        
        if check_stop():
            return False

        # 创建幻灯片 (80-95%)
        progress.update(82, "正在初始化PPT生成器...", force_new_log=True)

        template_path_obj = Path(template_path) if template_path else None
        ppt_generator = PPTGenerator(template_path=template_path_obj)

        progress.update(85, "正在设置演示文稿属性...")

        # Set presentation properties
        if presentation_title or presentation_author:
            ppt_generator.set_presentation_properties(
                title=presentation_title or f"从视频提取: {video_path.name}",
                author=presentation_author,
                subject="视频帧提取",
                comments=f"使用 v2ppt 从 {video_path.name} 生成"
            )

        if check_stop():
            return False

        progress.update(88, f"正在创建 {len(processed_images)} 张幻灯片...")

        # Create presentation with progress tracking
        progress.update(92, "正在添加幻灯片到演示文稿...")

        success = ppt_generator.create_presentation_from_images(
            image_paths=processed_images,
            output_path=output_path,
            add_titles=add_slide_titles,
            title_prefix="幻灯片"
        )

        progress.update(95, "幻灯片创建完成")

        if check_stop():
            return False

        # 保存文件 (95-100%)
        progress.update(97, "正在保存PPT文件...")

        if success:
            # Get file size info
            if output_path.exists():
                file_size = output_path.stat().st_size
                size_str = format_file_size(file_size)
                progress.update(100, f"PPT文件已保存 ({size_str})")

                logger.info(f"Successfully created PPT: {output_path.name}")
                logger.info(f"Full path: {output_path}")
                logger.info(f"File size: {size_str}")
                logger.info(f"Total slides: {len(processed_images)}")
            else:
                progress.update(100, "PPT文件已保存")

            progress.finish()
            return True
        else:
            logger.error("Failed to create PPT file")
            return False
    
    except Exception as e:
        logger.error(f"Error in processing pipeline: {e}", exc_info=True)
        if progress_callback:
            progress_callback("错误", 0, f"处理失败: {str(e)}", None)
        return False


def process_flexible_with_progress(
    start_from: str,
    output_path: Path,
    video_path: Optional[Path] = None,
    frames_dir: Optional[Path] = None,
    images_dir: Optional[Path] = None,
    progress_callback: Optional[Callable[[str, float, str, Optional[str]], None]] = None,
    stop_event: Optional[object] = None,
    **kwargs
) -> bool:
    """
    Flexible processing pipeline with progress callbacks
    
    This is a wrapper around the original process_video_to_ppt_flexible
    that adds progress callback support for different starting points.
    """
    
    if start_from == 'video' and video_path:
        # Use our enhanced processing function
        return process_video_to_ppt_with_progress(
            video_path=video_path,
            output_path=output_path,
            progress_callback=progress_callback,
            stop_event=stop_event,
            **kwargs
        )
    else:
        # For other start points, use original function with basic progress tracking
        progress = ProgressCallback(progress_callback)
        
        try:
            progress.update(f"从{start_from}开始", 0, "正在初始化...")
            
            # Import and call original function
            from main import process_video_to_ppt_flexible
            
            success = process_video_to_ppt_flexible(
                start_from=start_from,
                output_path=output_path,
                video_path=video_path,
                frames_dir=frames_dir,
                images_dir=images_dir,
                **kwargs
            )
            
            if success:
                progress.finish()
            
            return success
            
        except Exception as e:
            if progress_callback:
                progress_callback("错误", 0, f"处理失败: {str(e)}", None)
            return False
