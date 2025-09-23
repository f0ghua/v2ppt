"""
Worker Thread for V2PPT GUI
Handles background processing tasks with progress callbacks
"""

import threading
import sys
import os
from pathlib import Path
from typing import Dict, Any, Callable, Optional
import logging
import traceback

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))


class WorkerThread(threading.Thread):
    """Background worker thread for video processing"""
    
    def __init__(self, processing_args: Dict[str, Any], 
                 progress_callback: Callable[[str, float, str, Optional[str]], None],
                 completion_callback: Callable[[bool, str, Optional[str]], None]):
        """
        Initialize worker thread
        
        Args:
            processing_args: Arguments for processing function
            progress_callback: Callback for progress updates (step, percentage, status, details)
            completion_callback: Callback for completion (success, message, output_path)
        """
        super().__init__(daemon=True)
        
        self.processing_args = processing_args
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        
        # Thread control
        self.stop_event = threading.Event()
        self.is_running = False
        
        # Progress tracking
        self.current_step = ""
        self.total_steps = 4  # video -> frames -> images -> ppt
        self.step_progress = 0
        
        # Setup logging to capture processing logs
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging to capture processing messages"""
        # Create a custom log handler that forwards to progress callback
        class ProgressLogHandler(logging.Handler):
            def __init__(self, worker_thread):
                super().__init__()
                self.worker = worker_thread
                
            def emit(self, record):
                if self.worker.progress_callback:
                    message = self.format(record)
                    # Don't update progress percentage, just log the message
                    self.worker.progress_callback(
                        self.worker.current_step, 
                        self.worker.get_current_percentage(), 
                        message, 
                        None
                    )
        
        # Add our handler to the v2ppt logger
        logger = logging.getLogger('v2ppt')
        if not any(isinstance(h, ProgressLogHandler) for h in logger.handlers):
            handler = ProgressLogHandler(self)
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    
    def run(self):
        """Main thread execution"""
        self.is_running = True
        
        try:
            self.update_progress("初始化", 0, "正在初始化处理...")

            # Import enhanced processing modules
            from .processing_wrapper import process_flexible_with_progress

            # Ensure output directory exists
            output_path = self.processing_args['output_path']
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Start processing with progress tracking
            # Extract output_path separately to avoid parameter conflicts
            processing_args = self.processing_args.copy()
            output_path = processing_args.pop('output_path')

            success = process_flexible_with_progress(
                start_from='video',
                output_path=output_path,
                progress_callback=self.progress_callback,
                stop_event=self.stop_event,
                **processing_args
            )

            if success:
                self.completion_callback(True, "处理完成！", str(output_path))
            else:
                self.completion_callback(False, "处理失败", None)
                
        except Exception as e:
            error_msg = f"处理过程中发生错误: {str(e)}"
            self.completion_callback(False, error_msg, None)
            
            # Log full traceback for debugging
            if self.progress_callback:
                self.progress_callback("错误", 0, f"详细错误信息: {traceback.format_exc()}", None)
        
        finally:
            self.is_running = False
            # Reset stop event for potential reuse
            self.stop_event.clear()
    
    def process_with_progress(self) -> bool:
        """Process video with progress tracking (deprecated - now handled by processing_wrapper)"""
        # This method is no longer used as processing is handled by processing_wrapper
        # Kept for compatibility
        return True
    
    def update_progress(self, step: str, percentage: float, status: str, details: Optional[str] = None):
        """Update progress information"""
        if self.stop_event.is_set():
            return
            
        self.current_step = step
        
        if self.progress_callback:
            self.progress_callback(step, percentage, status, details)
    
    def get_current_percentage(self) -> float:
        """Get current progress percentage"""
        base_percentage = (self.step_progress / self.total_steps) * 100
        return min(base_percentage, 100.0)
    
    def stop(self):
        """Stop the processing thread"""
        self.stop_event.set()
        
        if self.progress_callback:
            self.progress_callback("停止中", 0, "正在停止处理...", None)


class EnhancedWorkerThread(WorkerThread):
    """Enhanced worker thread with detailed progress tracking"""
    
    def __init__(self, processing_args: Dict[str, Any], 
                 progress_callback: Callable[[str, float, str, Optional[str]], None],
                 completion_callback: Callable[[bool, str, Optional[str]], None]):
        super().__init__(processing_args, progress_callback, completion_callback)
        
        # Enhanced progress tracking
        self.detailed_steps = [
            ("视频分析", "正在分析视频文件属性..."),
            ("帧提取", "正在从视频中提取关键帧..."),
            ("图像处理", "正在处理和优化图像..."),
            ("重复检测", "正在检测和移除重复图像..."),
            ("内容过滤", "正在过滤PPT相关内容..."),
            ("PPT生成", "正在生成PowerPoint文件..."),
            ("完成", "处理完成！")
        ]
        self.current_step_index = 0
    
    def process_with_progress(self) -> bool:
        """Enhanced processing with detailed progress tracking"""
        
        try:
            # Step 1: Video Analysis
            self.advance_step("正在分析视频文件...")
            if self.stop_event.is_set():
                return False
            
            # Import processing modules
            from main import process_video_to_ppt_flexible
            
            # Get video info for progress estimation
            video_path = self.processing_args['video_path']
            
            # Step 2: Frame Extraction
            self.advance_step("正在提取视频帧...")
            if self.stop_event.is_set():
                return False
            
            # Step 3: Image Processing
            self.advance_step("正在处理图像...")
            if self.stop_event.is_set():
                return False
            
            # Step 4: Duplicate Detection
            if self.processing_args.get('remove_duplicates', True):
                self.advance_step("正在检测重复图像...")
                if self.stop_event.is_set():
                    return False
            
            # Step 5: Content Filtering
            if self.processing_args.get('filter_ppt_content', True):
                self.advance_step("正在过滤PPT内容...")
                if self.stop_event.is_set():
                    return False
            
            # Step 6: PPT Generation
            self.advance_step("正在生成PPT文件...")
            if self.stop_event.is_set():
                return False
            
            # Call the main processing function
            success = process_video_to_ppt_flexible(
                start_from='video',
                **self.processing_args
            )
            
            if success:
                self.advance_step("处理完成！")
            
            return success
            
        except Exception as e:
            self.update_progress("错误", 0, f"处理失败: {str(e)}", traceback.format_exc())
            return False
    
    def advance_step(self, status_message: str):
        """Advance to next processing step"""
        if self.current_step_index < len(self.detailed_steps):
            step_name, default_message = self.detailed_steps[self.current_step_index]
            message = status_message or default_message
            
            # Calculate progress percentage
            percentage = (self.current_step_index / (len(self.detailed_steps) - 1)) * 100
            
            self.update_progress(step_name, percentage, message)
            self.current_step_index += 1
        
        # Small delay to make progress visible
        import time
        time.sleep(0.1)


# Factory function to create appropriate worker thread
def create_worker_thread(processing_args: Dict[str, Any], 
                        progress_callback: Callable[[str, float, str, Optional[str]], None],
                        completion_callback: Callable[[bool, str, Optional[str]], None],
                        enhanced: bool = True) -> WorkerThread:
    """
    Create a worker thread
    
    Args:
        processing_args: Processing arguments
        progress_callback: Progress callback function
        completion_callback: Completion callback function
        enhanced: Whether to use enhanced progress tracking
        
    Returns:
        WorkerThread instance
    """
    if enhanced:
        return EnhancedWorkerThread(processing_args, progress_callback, completion_callback)
    else:
        return WorkerThread(processing_args, progress_callback, completion_callback)
