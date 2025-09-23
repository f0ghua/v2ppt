#!/usr/bin/env python3
"""
V2PPT GUI Application Entry Point
Graphical user interface for video to PowerPoint conversion
"""

import sys
import os
from pathlib import Path

# Add project paths to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "config"))

def check_dependencies():
    """Check if all required dependencies are available"""
    missing_deps = []
    
    try:
        import tkinter
    except ImportError:
        missing_deps.append("tkinter (Python GUI library)")
    
    try:
        import cv2
    except ImportError:
        missing_deps.append("opencv-python")
    
    try:
        from pptx import Presentation
    except ImportError:
        missing_deps.append("python-pptx")
    
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")
    
    try:
        from PIL import Image
    except ImportError:
        missing_deps.append("pillow")
    
    if missing_deps:
        print("❌ 缺少必要的依赖包:")
        for dep in missing_deps:
            print(f"   • {dep}")
        print("\n请安装缺少的依赖包:")
        print("   uv add opencv-python python-pptx pillow numpy")
        print("   或者:")
        print("   pip install opencv-python python-pptx pillow numpy")
        return False
    
    return True

def check_project_structure():
    """Check if project structure is correct"""
    required_files = [
        "src/__init__.py",
        "src/video_processor.py", 
        "src/image_processor.py",
        "src/ppt_generator.py",
        "src/utils.py",
        "config/__init__.py",
        "config/settings.py",
        "main.py",
        "improved_processing.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not (project_root / file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ 项目文件不完整，缺少以下文件:")
        for file_path in missing_files:
            print(f"   • {file_path}")
        return False
    
    return True

def setup_logging():
    """Setup logging for GUI application"""
    import logging
    from datetime import datetime
    
    # Create logs directory
    logs_dir = project_root / "output" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup logging
    log_file = logs_dir / f"gui_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger('v2ppt.gui')
    logger.info("V2PPT GUI application starting...")
    logger.info(f"Project root: {project_root}")
    logger.info(f"Log file: {log_file}")
    
    return logger

def main():
    """Main entry point for GUI application"""
    
    print("🎬 V2PPT - 视频转PPT工具 (GUI版本)")
    print("=" * 50)
    
    # Check dependencies
    print("📦 检查依赖包...")
    if not check_dependencies():
        sys.exit(1)
    print("✅ 依赖包检查通过")
    
    # Check project structure
    print("📁 检查项目结构...")
    if not check_project_structure():
        print("\n💡 提示: 请确保在正确的项目目录中运行此脚本")
        sys.exit(1)
    print("✅ 项目结构检查通过")
    
    # Setup logging
    print("📝 初始化日志系统...")
    logger = setup_logging()
    print("✅ 日志系统初始化完成")
    
    # Create output directories
    print("📂 创建输出目录...")
    output_dirs = ["output/ppt", "output/frames", "output/logs"]
    for dir_path in output_dirs:
        (project_root / dir_path).mkdir(parents=True, exist_ok=True)
    print("✅ 输出目录创建完成")
    
    try:
        # Import and start GUI
        print("🚀 启动图形界面...")
        from ui.main_window import MainWindow
        
        # Create and run application
        app = MainWindow()
        logger.info("GUI application initialized successfully")
        
        print("✅ 图形界面已启动")
        print("\n💡 使用提示:")
        print("   • 选择视频文件和输出目录")
        print("   • 根据需要调整处理模式")
        print("   • 点击'开始处理'开始转换")
        print("   • 可以在日志区域查看详细进度")
        print("\n🎯 开始使用 V2PPT 吧！")
        
        # Start GUI main loop
        app.run()
        
    except ImportError as e:
        logger.error(f"Failed to import GUI modules: {e}")
        print(f"\n❌ 无法导入GUI模块: {e}")
        print("请检查项目文件是否完整")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\n❌ 启动GUI时发生错误: {e}")
        
        # Show error dialog if tkinter is available
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            root = tk.Tk()
            root.withdraw()  # Hide main window
            
            messagebox.showerror(
                "启动错误",
                f"无法启动V2PPT GUI:\n\n{str(e)}\n\n请查看日志文件获取详细信息。"
            )
            
        except Exception:
            pass  # If even tkinter fails, just print to console
        
        sys.exit(1)

def show_version():
    """Show version information"""
    print("🎬 V2PPT - 视频转PPT工具")
    print("版本: 1.0.0")
    print("作者: V2PPT Team")
    print("描述: 从视频中提取PPT页面并生成PowerPoint文件")
    print("\n支持的视频格式:")
    print("  • MP4, AVI, MOV, MKV, WMV, FLV, M4V")
    print("\n功能特性:")
    print("  • 智能帧提取和重复检测")
    print("  • 图像增强和PPT内容过滤")
    print("  • 多种处理模式（标准/保守/自定义）")
    print("  • 实时进度显示和日志记录")
    print("  • 简洁易用的图形界面")

if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-v", "--version"]:
            show_version()
            sys.exit(0)
        elif sys.argv[1] in ["-h", "--help"]:
            print("用法: python gui_main.py [选项]")
            print("\n选项:")
            print("  -h, --help     显示此帮助信息")
            print("  -v, --version  显示版本信息")
            print("\n启动GUI:")
            print("  python gui_main.py")
            print("\n命令行版本:")
            print("  python improved_processing.py video.mp4 [选项]")
            sys.exit(0)
    
    # Start GUI application
    main()
