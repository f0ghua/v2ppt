# Video to PPT Converter (v2ppt)

一个用于从录制视频中提取PPT画面并生成PowerPoint文件的Python工具。

## 功能特性

- 🎥 **视频帧提取**: 从多种视频格式中智能提取关键帧
- 🖼️ **图像处理**: 自动增强图像质量（亮度、对比度、锐化）
- 🔍 **重复检测**: 使用感知哈希算法去除重复和相似的画面
- 📊 **PPT内容识别**: 智能识别包含PPT内容的画面
- 📄 **PPT生成**: 自动创建包含提取画面的PowerPoint文件
- ⚙️ **灵活配置**: 支持多种参数调整和自定义设置

## 安装依赖

使用 uv 安装项目依赖：

```bash
uv sync
```

或者手动安装依赖包：

```bash
uv add opencv-python python-pptx pillow numpy
```

## 使用方法

### 基本用法

```bash
python main.py video.mp4
```

### 高级用法

```bash
# 指定输出文件
python main.py video.mp4 -o my_presentation.pptx

# 调整帧提取间隔（每10秒提取一帧）
python main.py video.mp4 --interval 10

# 跳过视频开头和结尾
python main.py video.mp4 --skip-start 30 --skip-end 10

# 设置相似度阈值（0-1，越高越严格）
python main.py video.mp4 --similarity 0.9

# 禁用图像增强
python main.py video.mp4 --no-enhance

# 添加演示文稿信息
python main.py video.mp4 --title "我的演示" --author "张三"

# 为幻灯片添加标题
python main.py video.mp4 --add-titles

# 使用模板文件
python main.py video.mp4 --template template.pptx

# 启用详细输出
python main.py video.mp4 --verbose
```

### 分步处理功能

程序支持从任意步骤开始处理，适用于以下场景：

**1. 从已提取的帧开始处理**
```bash
# 如果你已经有了提取的帧图片
python main.py dummy.mp4 --start-from frames --frames-dir path/to/frames/
```

**2. 从已处理的图片开始创建PPT**
```bash
# 如果你已经有了处理好的图片
python main.py dummy.mp4 --start-from images --images-dir path/to/processed/images/
```

**3. 跳过所有处理步骤**
```bash
# 仅用于测试配置，不进行实际处理
python main.py dummy.mp4 --start-from ppt
```

**4. 完整的分步处理示例**
```bash
# 第一步：仅提取帧
python main.py video.mp4 --interval 5 --output-dir my_project

# 第二步：处理提取的帧
python main.py dummy.mp4 --start-from frames --frames-dir my_project/frames/video/ --similarity 0.9

# 第三步：从处理好的图片创建PPT
python main.py dummy.mp4 --start-from images --images-dir my_project/frames/video/processed/ --title "我的演示"
```

## 🔧 解决PPT页面丢失问题

如果发现生成的PPT缺少原视频中的页面，可以使用以下方法：

### 1. 使用改进的处理脚本

```bash
# 保守模式：保留更多幻灯片
python improved_processing.py video.mp4 --conservative

# 非常保守模式：最大程度保留幻灯片
python improved_processing.py video.mp4 --very-conservative

# 自定义参数：降低相似度阈值，增加提取频率
python improved_processing.py video.mp4 --similarity 0.6 --interval 3 --no-filter
```

### 2. 诊断工具分析

```bash
# 分析为什么某些页面被过滤
python diagnose_ppt_detection.py video.mp4 --verbose --analyze-duplicates

# 分析现有图片目录
python diagnose_ppt_detection.py path/to/images/ --analyze-duplicates --threshold 0.75
```

### 3. 手动调整参数

```bash
# 降低相似度阈值（减少误判为重复）
python main.py video.mp4 --similarity 0.6

# 禁用PPT内容过滤
python main.py video.mp4 --no-filter

# 增加帧提取频率
python main.py video.mp4 --interval 2

# 组合使用
python main.py video.mp4 --similarity 0.65 --interval 3 --no-filter --verbose
```

### 命令行参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `video_path` | 输入视频文件路径 | 必需 |
| `-o, --output` | 输出PPT文件路径 | 自动生成 |
| **分步处理参数** | | |
| `--start-from` | 开始处理的步骤 | video |
| `--frames-dir` | 帧图片目录（start-from frames/images时需要） | None |
| `--images-dir` | 处理后图片目录（start-from images时需要） | None |
| **视频处理参数** | | |
| `--interval` | 帧提取间隔（秒） | 5.0 |
| `--frame-step` | 每N帧提取一次（覆盖interval） | None |
| `--skip-start` | 跳过开头时间（秒） | 0 |
| `--skip-end` | 跳过结尾时间（秒） | 0 |
| **图像处理参数** | | |
| `--similarity` | 相似度阈值（0-1） | 0.85 |
| `--no-enhance` | 跳过图像增强 | False |
| `--no-dedup` | 跳过重复检测 | False |
| `--no-filter` | 跳过PPT内容过滤 | False |
| **PPT生成参数** | | |
| `--title` | 演示文稿标题 | None |
| `--author` | 演示文稿作者 | None |
| `--add-titles` | 为幻灯片添加标题 | False |
| `--template` | PPT模板文件路径 | None |
| **日志参数** | | |
| `--verbose, -v` | 详细输出 | False |
| `--log-level` | 日志级别 | INFO |
| `--log-file` | 日志文件路径 | output/v2ppt.log |

#### 分步处理选项说明

`--start-from` 参数支持以下选项：

- `video`: 从视频文件开始完整处理（默认）
- `frames`: 从已提取的帧开始处理（需要 `--frames-dir`）
- `images`: 从已处理的图片开始创建PPT（需要 `--images-dir`）
- `ppt`: 跳过所有处理步骤（用于测试配置）

### 常见问题解决

#### 问题：生成的PPT缺少很多原视频中的页面

**原因分析：**
1. **相似度阈值过高** - 不同的PPT页面被误判为重复
2. **PPT内容检测过严** - 真正的PPT页面被过滤掉
3. **帧提取间隔过大** - 错过了快速切换的页面

**解决方案：**
```bash
# 方案1：使用保守模式
python improved_processing.py video.mp4 --conservative

# 方案2：手动调整参数
python main.py video.mp4 --similarity 0.6 --interval 2 --no-filter

# 方案3：先诊断再处理
python diagnose_ppt_detection.py video.mp4 --analyze-duplicates
```

#### 问题：处理速度太慢

**解决方案：**
```bash
# 增加帧间隔，启用并行处理
python main.py video.mp4 --interval 8 --no-enhance

# 或使用分步处理
python main.py video.mp4 --interval 6  # 先提取
python main.py dummy.mp4 --start-from frames --frames-dir output/frames/video/
```

## 项目结构

```
v2ppt/
├── main.py                 # 主程序入口
├── src/                    # 源代码目录
│   ├── __init__.py
│   ├── video_processor.py  # 视频处理模块
│   ├── image_processor.py  # 图像处理模块
│   ├── ppt_generator.py    # PPT生成模块
│   └── utils.py           # 工具函数
├── config/                 # 配置目录
│   ├── __init__.py
│   └── settings.py        # 配置文件
├── output/                 # 输出目录
│   ├── frames/            # 提取的帧图片
│   └── ppt/              # 生成的PPT文件
├── pyproject.toml         # 项目配置
└── README.md             # 说明文档
```

## 配置说明

可以通过修改 `config/settings.py` 文件来调整默认设置：

### 视频处理设置
- `FRAME_INTERVAL`: 帧提取间隔（秒）
- `MIN_FRAME_WIDTH/HEIGHT`: 最小帧尺寸
- `SKIP_START/END_SECONDS`: 跳过开头/结尾时间

### 图像处理设置
- `SIMILARITY_THRESHOLD`: 相似度阈值
- `ENHANCE_BRIGHTNESS/CONTRAST/SHARPNESS`: 图像增强参数
- `MAX_WIDTH/HEIGHT`: 最大图像尺寸

### PPT生成设置
- `SLIDE_WIDTH/HEIGHT`: 幻灯片尺寸
- `IMAGE_LEFT/TOP/WIDTH/HEIGHT`: 图像在幻灯片中的位置

## 支持的文件格式

### 视频格式
- MP4, AVI, MOV, MKV, WMV, FLV, WebM

### 图像格式
- JPG, JPEG, PNG, BMP, TIFF

## 工作流程

1. **视频分析**: 读取视频文件，获取基本信息
2. **帧提取**: 按设定间隔提取视频帧
3. **质量检查**: 过滤掉质量不佳的帧
4. **PPT内容识别**: 识别包含PPT内容的帧
5. **图像增强**: 优化图像质量
6. **重复检测**: 去除相似的重复帧
7. **PPT生成**: 创建包含所有帧的PowerPoint文件

## 注意事项

- 确保有足够的磁盘空间存储提取的帧图片
- 处理大视频文件时可能需要较长时间
- 建议先用较大的帧间隔测试，再调整到合适的值
- 相似度阈值设置过低可能保留太多重复帧，过高可能误删有用帧

## 故障排除

### 常见问题

1. **"Cannot open video file"**
   - 检查视频文件路径是否正确
   - 确认视频格式是否支持
   - 尝试用其他播放器播放视频

2. **"No frames were extracted"**
   - 检查视频是否损坏
   - 调整跳过时间参数
   - 降低最小帧尺寸要求

3. **"No images remained after processing"**
   - 降低相似度阈值
   - 禁用PPT内容过滤 (`--no-filter`)
   - 检查提取的原始帧

4. **内存不足**
   - 增加帧提取间隔
   - 减小最大图像尺寸
   - 分批处理大视频文件

## 测试

### 运行测试

项目包含完整的测试套件，支持单元测试和集成测试。

#### 安装测试依赖

```bash
# 使用 uv 安装测试依赖
uv add --group test pytest pytest-cov pytest-mock pytest-xdist

# 或使用 Makefile
make install
```

#### 运行测试的几种方式

**1. 使用测试运行脚本（推荐）**

```bash
# 运行所有测试
python run_tests.py

# 只运行单元测试
python run_tests.py --type unit

# 运行集成测试
python run_tests.py --type integration

# 生成覆盖率报告
python run_tests.py --coverage

# 并行运行测试
python run_tests.py --parallel 4

# 详细输出
python run_tests.py --verbose
```

**2. 使用 Makefile**

```bash
make test              # 运行所有测试
make test-unit         # 单元测试
make test-integration  # 集成测试
make test-coverage     # 覆盖率测试
make test-fast         # 并行测试
```

**3. 直接使用 pytest**

```bash
# 基本测试
pytest tests/

# 带覆盖率
pytest tests/ --cov=src --cov=config

# 并行测试
pytest tests/ -n auto

# 运行特定测试文件
pytest tests/test_utils.py
```

#### 手动测试示例

项目还提供了手动测试脚本，可以用实际参数测试功能：

```bash
# 创建测试视频并运行完整测试
python manual_test.py --create-video --duration 15

# 使用现有视频文件测试
python manual_test.py --video your_video.mp4

# 简单功能测试（无需视频文件）
python test_example.py
```

### 测试结构

```
tests/
├── conftest.py              # pytest配置和fixtures
├── test_utils.py           # 工具函数测试
├── test_video_processor.py # 视频处理测试
├── test_image_processor.py # 图像处理测试
├── test_ppt_generator.py   # PPT生成测试
├── test_config.py          # 配置测试
└── test_integration.py     # 集成测试
```

### 测试类型

- **单元测试**: 测试单个函数和类的功能
- **集成测试**: 测试模块间的协作和完整流程
- **性能测试**: 测试大量数据处理的性能
- **错误处理测试**: 测试异常情况的处理

### 测试覆盖率

运行覆盖率测试后，可以查看详细报告：

```bash
# 生成HTML覆盖率报告
make test-coverage

# 查看报告
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
```

## 许可证

本项目采用 MIT 许可证。