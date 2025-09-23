#!/usr/bin/env python3
"""
V2PPT 自动化打包脚本
使用 uv + PyInstaller 打包 v2ppt 项目
"""

import subprocess
import sys
import os
from pathlib import Path
import shutil

def run_command(cmd, description=""):
    """运行命令并处理错误"""
    print(f"\n[INFO] {description}")
    print(f"执行命令: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"OK {description} 成功")
        if result.stdout:
            print(f"输出: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR {description} 失败")
        print(f"错误: {e.stderr}")
        return False

def check_environment():
    """检查环境和依赖"""
    print("检查环境...")
    
    # 检查 uv 是否可用
    if not run_command("uv --version", "检查 uv"):
        print("ERROR uv 未安装或不可用")
        return False
    
    # 检查项目文件
    required_files = [
        "gui_main.py",
        "main.py", 
        "improved_processing.py",
        "src/__init__.py",
        "src/video_processor.py",
        "src/image_processor.py",
        "src/ppt_generator.py",
        "src/utils.py",
        "config/__init__.py",
        "config/settings.py",
        "ui/__init__.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("ERROR 缺少必要文件:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False

    print("OK 环境检查通过")
    return True

def install_build_dependencies():
    """安装打包依赖"""
    print("\n安装打包依赖...")
    
    # 同步环境
    if not run_command("uv sync", "同步 uv 环境"):
        return False
    
    # 安装 PyInstaller
    if not run_command("uv add --group build pyinstaller", "安装 PyInstaller"):
        return False
    
    return True

def test_dependencies():
    """测试依赖是否正常"""
    print("\n测试依赖...")

    # 测试所有必需的依赖 - 使用ASCII字符避免编码问题
    test_cmd = 'uv run python -c "import cv2, numpy, PIL, pptx; print(\'All dependencies OK\')"'
    return run_command(test_cmd, "测试依赖导入")

def build_gui_version():
    """打包GUI版本"""
    print("\n打包GUI版本...")
    
    # 清理之前的构建
    if Path("dist").exists():
        shutil.rmtree("dist")
    if Path("build").exists():
        shutil.rmtree("build")
    
    # 使用spec文件打包（如果存在）
    if Path("v2ppt-gui.spec").exists():
        cmd = "uv run pyinstaller v2ppt-gui.spec"
        if run_command(cmd, "使用spec文件打包GUI版本"):
            return True
    
    # 使用完整命令打包
    cmd = '''uv run pyinstaller --onefile --console \
--add-data "src;src" \
--add-data "config;config" \
--add-data "ui;ui" \
--add-data "main.py;." \
--add-data "improved_processing.py;." \
--hidden-import cv2 \
--hidden-import numpy \
--hidden-import PIL \
--hidden-import pptx \
--name v2ppt-gui gui_main.py'''
    
    return run_command(cmd, "打包GUI版本")

def build_cli_versions():
    """打包命令行版本"""
    print("\n打包命令行版本...")

    # 打包主程序
    cmd1 = "uv run pyinstaller --onefile --console --name v2ppt main.py"
    success1 = run_command(cmd1, "打包主程序")

    # 打包改进版本
    cmd2 = "uv run pyinstaller --onefile --console --name v2ppt-improved improved_processing.py"
    success2 = run_command(cmd2, "打包改进版本")
    
    return success1 and success2

def test_executables():
    """测试生成的可执行文件"""
    print("\n测试可执行文件...")

    dist_dir = Path("dist")
    if not dist_dir.exists():
        print("ERROR dist 目录不存在")
        return False

    # 列出生成的文件
    exe_files = list(dist_dir.glob("*.exe"))
    if not exe_files:
        print("ERROR 没有找到生成的exe文件")
        return False

    print("OK 生成的文件:")
    for exe_file in exe_files:
        print(f"   - {exe_file.name} ({exe_file.stat().st_size / 1024 / 1024:.1f} MB)")

    # 测试GUI版本
    gui_exe = dist_dir / "v2ppt-gui.exe"
    if gui_exe.exists():
        print("\n测试GUI版本...")
        print("请手动运行以下命令测试GUI:")
        print(f"   {gui_exe.absolute()}")
    
    # 测试命令行版本
    cli_exe = dist_dir / "v2ppt.exe"
    if cli_exe.exists():
        cmd = f'"{cli_exe}" --help'
        run_command(cmd, "测试命令行版本")
    
    return True

def main():
    """主函数"""
    print("V2PPT 自动化打包脚本")
    print("=" * 50)

    # 检查环境
    if not check_environment():
        sys.exit(1)

    # 安装依赖
    if not install_build_dependencies():
        sys.exit(1)

    # 测试依赖
    if not test_dependencies():
        sys.exit(1)

    # 打包GUI版本
    if not build_gui_version():
        print("ERROR GUI版本打包失败")
        sys.exit(1)

    # 打包命令行版本
    if not build_cli_versions():
        print("WARNING 命令行版本打包失败，但GUI版本可能成功")

    # 测试可执行文件
    if not test_executables():
        print("WARNING 可执行文件测试失败")

    print("\n打包完成！")
    print("生成的文件在 dist/ 目录中")
    print("\n下一步:")
    print("1. 测试 dist/v2ppt-gui.exe")
    print("2. 测试 dist/v2ppt.exe --help")
    print("3. 如果有问题，查看 BUILD_GUIDE.md 中的故障排除部分")

if __name__ == "__main__":
    main()
