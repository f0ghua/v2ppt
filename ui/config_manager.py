"""
Configuration Manager for V2PPT GUI
Handles parameter validation, settings save/load, and preset mode management
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class ProcessingConfig:
    """Processing configuration data class"""
    
    # Input/Output
    video_path: str = ""
    output_dir: str = "output/ppt"
    
    # Processing mode
    mode: str = "standard"  # standard, conservative, very_conservative, custom
    
    # Advanced settings
    similarity_threshold: float = 0.8
    frame_interval: float = 5.0
    skip_start: float = 0.0
    skip_end: float = 0.0
    
    # Processing options
    enhance_images: bool = True
    remove_duplicates: bool = True
    filter_ppt_content: bool = True
    
    # PPT settings
    presentation_title: str = ""
    presentation_author: str = ""
    add_slide_titles: bool = False
    template_path: str = ""


class ConfigManager:
    """Manages configuration settings for the GUI"""
    
    def __init__(self, config_file: str = "config/gui_settings.json"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Preset configurations
        self.presets = {
            "standard": {
                "similarity_threshold": 0.8,
                "frame_interval": 5.0,
                "enhance_images": True,
                "remove_duplicates": True,
                "filter_ppt_content": True
            },
            "conservative": {
                "similarity_threshold": 0.7,
                "frame_interval": 4.0,
                "enhance_images": True,
                "remove_duplicates": True,
                "filter_ppt_content": True
            },
            "very_conservative": {
                "similarity_threshold": 0.6,
                "frame_interval": 3.0,
                "enhance_images": True,
                "remove_duplicates": True,
                "filter_ppt_content": False
            }
        }
    
    def get_default_config(self) -> ProcessingConfig:
        """Get default configuration"""
        return ProcessingConfig()
    
    def apply_preset(self, config: ProcessingConfig, preset_name: str) -> ProcessingConfig:
        """Apply preset configuration"""
        if preset_name in self.presets:
            preset = self.presets[preset_name]
            for key, value in preset.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        return config
    
    def validate_config(self, config: ProcessingConfig) -> tuple[bool, str]:
        """
        Validate configuration
        
        Returns:
            (is_valid, error_message)
        """
        # Check video file
        if not config.video_path:
            return False, "请选择视频文件"
        
        video_path = Path(config.video_path)
        if not video_path.exists():
            return False, f"视频文件不存在: {config.video_path}"
        
        # Check video format
        supported_formats = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.m4v'}
        if video_path.suffix.lower() not in supported_formats:
            return False, f"不支持的视频格式: {video_path.suffix}"
        
        # Check output directory
        if not config.output_dir:
            return False, "请选择输出目录"
        
        # Validate numeric parameters
        if not (0.0 <= config.similarity_threshold <= 1.0):
            return False, "相似度阈值必须在 0.0 到 1.0 之间"
        
        if config.frame_interval <= 0:
            return False, "帧间隔必须大于 0"
        
        if config.skip_start < 0:
            return False, "跳过开始时间不能为负数"
        
        if config.skip_end < 0:
            return False, "跳过结束时间不能为负数"
        
        return True, ""
    
    def save_config(self, config: ProcessingConfig) -> bool:
        """Save configuration to file"""
        try:
            config_dict = asdict(config)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Failed to save config: {e}")
            return False
    
    def load_config(self) -> ProcessingConfig:
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_dict = json.load(f)
                return ProcessingConfig(**config_dict)
        except Exception as e:
            print(f"Failed to load config: {e}")
        
        return self.get_default_config()
    
    def get_processing_args(self, config: ProcessingConfig) -> Dict[str, Any]:
        """Convert config to processing arguments"""
        # Ensure output directory exists
        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate output filename with timestamp to avoid conflicts
        from time import strftime
        timestamp = strftime("%Y%m%d_%H%M%S")
        video_name = Path(config.video_path).stem if config.video_path else "presentation"
        output_filename = f"{video_name}_{timestamp}.pptx"

        return {
            'video_path': Path(config.video_path),
            'output_path': output_dir / output_filename,
            'frame_interval': config.frame_interval,
            'skip_start': config.skip_start,
            'skip_end': config.skip_end,
            'similarity_threshold': config.similarity_threshold,
            'enhance_images': config.enhance_images,
            'remove_duplicates': config.remove_duplicates,
            'filter_ppt_content': config.filter_ppt_content,
            'presentation_title': config.presentation_title or None,
            'presentation_author': config.presentation_author or None,
            'add_slide_titles': config.add_slide_titles,
            'template_path': config.template_path or None
        }
