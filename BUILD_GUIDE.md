# v2ppt EXE 打包指南

将v2ppt项目打包成可执行文件(.exe)，方便朋友使用。支持命令行版本和GUI版本。

## 📋 准备工作

### 1. 安装打包工具

```bash
# 使用 uv 安装 PyInstaller
uv add --group build pyinstaller

# 或使用 pip
pip install pyinstaller
```

### 2. 安装所有依赖

```bash
# 确保所有依赖都已安装
uv sync

# 或手动安装核心依赖
uv add opencv-python python-pptx pillow numpy
```

### 3. 验证环境

```bash
# 测试GUI版本是否正常运行
uv run python gui_main.py

# 测试命令行版本
uv run python main.py --help
```

## 🔧 打包配置

### 方法一：GUI版本打包（推荐）

使用专门的spec文件打包GUI版本，确保所有依赖和资源文件都被正确包含：

```bash
# 使用 uv 调用 PyInstaller 打包GUI版本
uv run pyinstaller v2ppt-gui.spec

# 或者直接使用简单命令（可能缺少文件）
uv run pyinstaller --onefile --console --name v2ppt-gui gui_main.py
```

**重要**：推荐使用 `v2ppt-gui.spec` 文件，因为它包含了完整的项目结构和依赖配置。

### 方法二：命令行版本打包

```bash
# 打包命令行版本
uv run pyinstaller --onefile --console --name v2ppt main.py
uv run pyinstaller --onefile --console --name v2ppt-improved improved_processing.py
```

### 方法三：高级打包配置

如果需要自定义配置，可以修改 `v2ppt-gui.spec` 文件：

```python
# 在 v2ppt-gui.spec 中可以配置：
# - 包含的数据文件
# - 隐藏导入的模块
# - 排除的模块
# - 图标和版本信息
```

## 📦 打包步骤

### Step 1: 准备打包环境

```bash
# 确保环境同步
uv sync

# 验证所有依赖
uv run python -c "import cv2, numpy, PIL, pptx, imagehash, skimage; print('✅ 所有依赖检查通过')"
```

### Step 2: 执行GUI版本打包

```bash
# 使用spec文件打包（推荐）
uv run pyinstaller v2ppt-gui.spec

# 或使用简单命令
uv run pyinstaller --onefile --console --name v2ppt-gui gui_main.py
```

### Step 3: 执行命令行版本打包

```bash
# 打包主程序
uv run pyinstaller --onefile --console --name v2ppt main.py

# 打包改进版本
uv run pyinstaller --onefile --console --name v2ppt-improved improved_processing.py
```

### Step 4: 测试可执行文件

```bash
# 测试GUI版本
dist/v2ppt-gui.exe

# 测试命令行版本
dist/v2ppt.exe --help
dist/v2ppt-improved.exe --help
```

## 📁 打包后的文件结构

```
v2ppt-release/
├── v2ppt.exe                    # 主程序
├── v2ppt-improved.exe           # 改进版本
├── v2ppt-diagnose.exe           # 诊断工具
├── README-用户指南.txt           # 用户使用说明
├── examples/                    # 示例文件
│   ├── sample_video.mp4
│   └── template.pptx
└── output/                      # 输出目录
    ├── frames/
    └── ppt/
```

## 🎯 用户使用指南

### 基本使用

```cmd
# 基本转换
v2ppt.exe video.mp4

# 保守模式（推荐）
v2ppt-improved.exe video.mp4 --conservative

# 诊断问题
v2ppt-diagnose.exe video.mp4 --analyze-duplicates
```

### 常见问题解决

1. **缺少页面**：使用 `v2ppt-improved.exe video.mp4 --very-conservative`
2. **处理太慢**：使用 `v2ppt.exe video.mp4 --interval 8`
3. **分析问题**：使用 `v2ppt-diagnose.exe video.mp4`

## 🚀 分发准备

### 创建安装包

1. 将所有exe文件和说明文档打包成zip
2. 创建简单的批处理文件方便使用
3. 提供详细的用户指南

### 系统要求

- Windows 10/11 (64位)
- 至少 4GB 内存
- 1GB 可用磁盘空间

## ⚠️ 注意事项

1. **文件路径**：避免中文路径和空格
2. **权限问题**：可能需要管理员权限
3. **防病毒软件**：可能误报，需要添加信任
4. **依赖问题**：确保所有依赖都已打包

## 🔍 故障排除

### 常见错误及解决方案

#### 1. "项目文件不完整，缺少以下文件" 错误

**问题**：PyInstaller 没有正确包含项目源文件

**解决方案**：
```bash
# 方法1：使用专门的spec文件（推荐）
uv run pyinstaller v2ppt-gui.spec

# 方法2：手动指定包含路径
uv run pyinstaller --onefile --console \
  --add-data "src;src" \
  --add-data "config;config" \
  --add-data "ui;ui" \
  --add-data "main.py;." \
  --add-data "improved_processing.py;." \
  --name v2ppt-gui gui_main.py
```

#### 2. ModuleNotFoundError 错误

**问题**：某些模块未被自动检测到

**解决方案**：
```bash
# 添加隐藏导入
uv run pyinstaller --onefile --console \
  --hidden-import cv2 \
  --hidden-import numpy \
  --hidden-import PIL \
  --hidden-import pptx \
  --name v2ppt-gui gui_main.py
```

#### 3. 依赖检查失败

**解决方案**：
```bash
# 重新安装依赖
uv sync

# 清理并重新打包
uv run pyinstaller --clean v2ppt-gui.spec

# 检查依赖
uv run python -c "import cv2, pptx, PIL, numpy; print('All dependencies OK')"
```

## 📦 完整的 uv + PyInstaller 打包流程

### Step 1: 环境准备

```bash
# 1. 确保 uv 环境同步
uv sync

# 2. 安装打包工具（如果还没有）
uv add --group build pyinstaller

# 3. 验证环境
uv run python gui_main.py  # 测试GUI是否正常
uv run python main.py --help  # 测试命令行是否正常
```

### Step 2: 使用 uv 执行打包

```bash
# 方法1：使用spec文件打包GUI版本（推荐）
uv run pyinstaller v2ppt-gui.spec

# 方法2：直接打包GUI版本
uv run pyinstaller --onefile --console --name v2ppt-gui gui_main.py

# 方法3：打包命令行版本
uv run pyinstaller --onefile --console --name v2ppt main.py
uv run pyinstaller --onefile --console --name v2ppt-improved improved_processing.py
```

### Step 3: 验证打包结果

```bash
# 检查生成的文件
ls dist/

# 测试GUI版本
dist/v2ppt-gui.exe

# 测试命令行版本
dist/v2ppt.exe --help
dist/v2ppt-improved.exe --help
```

### Step 4: 解决常见问题

如果遇到"项目文件不完整"错误：

```bash
# 使用完整的打包命令
uv run pyinstaller --onefile --console \
  --add-data "src;src" \
  --add-data "config;config" \
  --add-data "ui;ui" \
  --add-data "main.py;." \
  --add-data "improved_processing.py;." \
  --hidden-import cv2 \
  --hidden-import numpy \
  --hidden-import PIL \
  --hidden-import pptx \
  --name v2ppt-gui gui_main.py
```

### Step 4: 创建分发包

```bash
# 运行安装脚本
cd v2ppt-release
安装.bat

# 打包成ZIP文件
# 将整个 v2ppt-release 文件夹压缩成 v2ppt-v1.0.zip
```

## 🎯 给朋友的使用说明

### 安装步骤

1. **下载并解压** `v2ppt-v1.0.zip`
2. **运行安装** 双击 `安装.bat`
3. **开始使用** 双击 `快速开始.bat`

### 三种使用方式

#### 方式1：拖拽使用（最简单）
- 将视频文件直接拖拽到 `简单转换.bat` 上
- 等待处理完成，查看 `output/ppt` 文件夹

#### 方式2：交互式菜单
- 双击 `快速开始.bat`
- 按提示选择转换模式
- 输入视频文件路径

#### 方式3：命令行使用
```cmd
# 基本转换
v2ppt.exe video.mp4

# 保守模式（推荐）
v2ppt-improved.exe video.mp4 --conservative

# 诊断问题
v2ppt-diagnose.exe video.mp4 --analyze-duplicates
```

## 🔧 高级打包选项

### 创建单文件版本

```bash
# 创建单个exe文件（较大但更便携）
pyinstaller --onefile --name v2ppt-portable main.py
```

### 添加图标和版本信息

```bash
# 下载或创建图标文件 assets/icon.ico
# 修改 spec 文件中的 icon 参数
# 重新打包
pyinstaller v2ppt.spec
```

### 优化文件大小

```bash
# 使用 UPX 压缩（需要先安装 UPX）
pyinstaller --upx-dir=/path/to/upx v2ppt.spec

# 排除不需要的模块
# 在 spec 文件的 excludes 中添加更多模块
```

## 📋 分发清单

### 必需文件
- ✅ v2ppt.exe（主程序）
- ✅ v2ppt-improved.exe（改进版本）
- ✅ v2ppt-diagnose.exe（诊断工具）
- ✅ README-用户指南.txt
- ✅ 安装.bat

### 可选文件
- 📁 examples/（示例文件）
- 📁 user_scripts/（批处理脚本）
- 📄 BUILD_GUIDE.md（开发文档）

### 目录结构
```
v2ppt-release/
├── v2ppt.exe
├── v2ppt-improved.exe
├── v2ppt-diagnose.exe
├── 安装.bat
├── README-用户指南.txt
├── output/
│   ├── frames/
│   └── ppt/
├── examples/
│   └── sample_video.mp4
└── user_scripts/
    ├── 简单转换.bat
    ├── 保守转换.bat
    ├── 诊断分析.bat
    └── 快速开始.bat
```

## 🚀 自动化打包脚本

创建一键打包脚本：

```bash
# 运行完整打包流程
python full_build.py
```

这将自动执行：
1. 环境检查
2. 依赖安装
3. 代码打包
4. 用户脚本生成
5. 测试验证
6. 分发包创建

## 💡 最佳实践

1. **版本管理**：为每个版本创建标签
2. **测试充分**：在不同Windows版本上测试
3. **文档完善**：提供详细的用户指南
4. **错误处理**：包含详细的错误信息和解决方案
5. **用户反馈**：收集使用反馈并持续改进
