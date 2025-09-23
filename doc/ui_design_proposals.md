# V2PPT 用户界面设计方案

## 项目概述

为 v2ppt（视频转PPT工具）设计简单易用的图形用户界面，满足以下需求：
1. **简单性**：最小依赖，易于安装和使用
2. **配置性**：支持输入文件和输出目录配置
3. **可视化**：显示执行过程和进度信息

## 方案对比

### 方案一：Tkinter GUI（推荐）

**技术栈**：
- `tkinter`（Python 内置，无需额外依赖）
- `threading`（后台处理，避免界面冻结）

**优势**：
- ✅ 零额外依赖，Python 内置
- ✅ 跨平台兼容性好
- ✅ 开发简单，维护成本低
- ✅ 打包后体积小

**界面设计**：
```
┌─────────────────────────────────────────────────────────┐
│                    V2PPT - 视频转PPT工具                    │
├─────────────────────────────────────────────────────────┤
│ 输入设置                                                  │
│ 视频文件: [选择文件...] [/path/to/video.mp4        ]      │
│ 输出目录: [选择目录...] [/path/to/output/          ]      │
│                                                         │
│ 处理模式                                                  │
│ ○ 标准模式    ○ 保守模式    ○ 非常保守    ○ 自定义        │
│                                                         │
│ 高级设置 [展开/收起]                                      │
│ ├ 相似度阈值: [0.8    ] (0.0-1.0)                       │
│ ├ 帧间隔(秒): [5.0    ]                                 │
│ ├ □ 图像增强  □ 去重  □ PPT内容过滤                      │
│ └ 演示标题: [可选标题                    ]                │
│                                                         │
│ [开始处理] [停止] [重置] [查看日志]                        │
│                                                         │
│ 进度信息                                                  │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 当前步骤: 正在提取视频帧...                           │ │
│ │ 进度: ████████████░░░░░░░░░░ 50%                    │ │
│ │ 已处理: 125/250 帧                                   │ │
│ │ 预计剩余: 2分30秒                                     │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ 状态: 就绪                                               │
└─────────────────────────────────────────────────────────┘
```

**实现特点**：
- 文件/目录选择对话框
- 实时进度条和状态更新
- 可展开的高级设置面板
- 后台线程处理，界面响应流畅
- 简洁的日志查看窗口

---

### 方案二：Web界面（Flask）

**技术栈**：
- `flask`（轻量级Web框架）
- `flask-socketio`（实时通信）
- 基础HTML/CSS/JavaScript

**优势**：
- ✅ 现代化界面体验
- ✅ 支持远程访问
- ✅ 响应式设计
- ✅ 实时进度更新

**劣势**：
- ❌ 需要额外依赖
- ❌ 部署相对复杂
- ❌ 需要浏览器环境

**界面预览**：
```html
<!DOCTYPE html>
<html>
<head>
    <title>V2PPT - 视频转PPT工具</title>
    <style>
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; }
        .progress-bar { width: 100%; height: 20px; background: #f0f0f0; }
        .progress-fill { height: 100%; background: #4CAF50; transition: width 0.3s; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 V2PPT - 视频转PPT工具</h1>
        
        <div class="upload-area" id="dropZone">
            <p>拖拽视频文件到此处，或点击选择文件</p>
            <input type="file" id="videoFile" accept="video/*" style="display:none">
            <button onclick="document.getElementById('videoFile').click()">选择视频文件</button>
        </div>
        
        <div class="settings">
            <h3>处理设置</h3>
            <label>
                <input type="radio" name="mode" value="standard" checked> 标准模式
            </label>
            <label>
                <input type="radio" name="mode" value="conservative"> 保守模式
            </label>
            <!-- 更多设置... -->
        </div>
        
        <button id="startBtn" onclick="startProcessing()">开始处理</button>
        
        <div id="progressSection" style="display:none">
            <h3>处理进度</h3>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill" style="width: 0%"></div>
            </div>
            <p id="statusText">准备中...</p>
            <p id="progressText">0%</p>
        </div>
    </div>
    
    <script src="/static/socket.io.js"></script>
    <script>
        const socket = io();
        
        socket.on('progress', function(data) {
            document.getElementById('progressFill').style.width = data.percentage + '%';
            document.getElementById('statusText').textContent = data.status;
            document.getElementById('progressText').textContent = data.percentage + '%';
        });
        
        function startProcessing() {
            // 发送处理请求到后端
            socket.emit('start_processing', {
                video_file: document.getElementById('videoFile').files[0],
                settings: getSettings()
            });
        }
    </script>
</body>
</html>
```

---

### 方案三：命令行TUI（Rich）

**技术栈**：
- `rich`（终端UI库）
- `textual`（可选，更高级的TUI）

**优势**：
- ✅ 轻量级依赖
- ✅ 现代化终端界面
- ✅ 丰富的进度显示
- ✅ 适合服务器环境

**劣势**：
- ❌ 需要终端环境
- ❌ 文件选择不够直观

**界面效果**：
```
╭─────────────────────────────────────────────────────────────────╮
│                        🎬 V2PPT 视频转PPT工具                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 📁 输入文件: /path/to/video.mp4                                   │
│ 📂 输出目录: /path/to/output/                                     │
│                                                                 │
│ ⚙️  处理模式: [●] 标准  [ ] 保守  [ ] 非常保守  [ ] 自定义          │
│                                                                 │
│ 🔧 高级设置:                                                      │
│    相似度阈值: 0.8  │  帧间隔: 5.0秒  │  [✓] 图像增强             │
│                                                                 │
│ ▶️  [开始处理]  ⏹️  [停止]  🔄 [重置]                              │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ 📊 处理进度                                                       │
│                                                                 │
│ 当前步骤: 正在提取视频帧...                                        │
│ ████████████████████████████████████████████████████████ 100%   │
│ 已完成: 250/250 帧 │ 用时: 1分30秒 │ 速度: 2.8帧/秒              │
│                                                                 │
│ 📝 最近日志:                                                      │
│ [14:30:25] INFO  - 开始提取视频帧                                 │
│ [14:30:26] INFO  - 视频时长: 5分30秒, FPS: 30                     │
│ [14:31:55] INFO  - 帧提取完成: 250帧                              │
│ [14:31:55] INFO  - 开始图像处理...                                │
│                                                                 │
╰─────────────────────────────────────────────────────────────────╯
```

## 推荐方案详细设计

### 选择方案一：Tkinter GUI

**理由**：
1. **零依赖**：Python 内置，符合"最小依赖"要求
2. **简单易用**：图形界面直观，用户友好
3. **开发效率**：快速实现，维护简单
4. **兼容性好**：Windows/Linux/macOS 全平台支持

**核心功能模块**：

1. **主界面类** (`ui/main_window.py`)
   - 文件选择组件
   - 参数配置面板
   - 进度显示区域
   - 控制按钮组

2. **进度监控类** (`ui/progress_monitor.py`)
   - 实时进度更新
   - 状态信息显示
   - 日志输出捕获

3. **配置管理类** (`ui/config_manager.py`)
   - 参数验证
   - 设置保存/加载
   - 预设模式管理

4. **后台处理类** (`ui/worker_thread.py`)
   - 异步任务执行
   - 进度回调机制
   - 错误处理

**依赖需求**：
```toml
# pyproject.toml 新增依赖
[project.optional-dependencies]
gui = [
    # 无需额外依赖，tkinter 是 Python 内置模块
]
```

**文件结构**：
```
v2ppt/
├── ui/
│   ├── __init__.py
│   ├── main_window.py      # 主窗口界面
│   ├── progress_monitor.py # 进度监控
│   ├── config_manager.py   # 配置管理
│   ├── worker_thread.py    # 后台处理线程
│   └── widgets/            # 自定义组件
│       ├── __init__.py
│       ├── file_selector.py
│       ├── progress_bar.py
│       └── settings_panel.py
├── gui_main.py             # GUI 启动入口
└── ...
```

**启动方式**：
```bash
# 命令行模式（现有）
python improved_processing.py video.mp4 --conservative

# GUI 模式（新增）
python gui_main.py

# 或者通过参数启动
python improved_processing.py --gui
```

## 方案对比总结

| 特性 | Tkinter GUI | Web界面 (Flask) | 命令行TUI (Rich) |
|------|-------------|----------------|------------------|
| **依赖复杂度** | ⭐⭐⭐⭐⭐ 零依赖 | ⭐⭐⭐ 需要Flask等 | ⭐⭐⭐⭐ 仅需Rich |
| **开发难度** | ⭐⭐⭐⭐ 简单 | ⭐⭐⭐ 中等 | ⭐⭐⭐⭐ 简单 |
| **用户体验** | ⭐⭐⭐⭐ 直观易用 | ⭐⭐⭐⭐⭐ 现代化 | ⭐⭐⭐ 需要终端 |
| **部署便利性** | ⭐⭐⭐⭐⭐ 打包简单 | ⭐⭐ 需要服务器 | ⭐⭐⭐⭐ 命令行工具 |
| **跨平台性** | ⭐⭐⭐⭐⭐ 全平台 | ⭐⭐⭐⭐⭐ 浏览器 | ⭐⭐⭐⭐ 终端环境 |
| **文件操作** | ⭐⭐⭐⭐⭐ 原生对话框 | ⭐⭐⭐ 上传下载 | ⭐⭐ 手动输入路径 |
| **进度显示** | ⭐⭐⭐⭐ 实时更新 | ⭐⭐⭐⭐⭐ WebSocket | ⭐⭐⭐⭐⭐ 丰富样式 |
| **维护成本** | ⭐⭐⭐⭐⭐ 低 | ⭐⭐⭐ 中等 | ⭐⭐⭐⭐ 低 |

## 推荐理由

**强烈推荐 Tkinter GUI 方案**，原因：

1. ✅ **完美符合需求**：简单、最小依赖、易配置、可视化进度
2. ✅ **零学习成本**：用户熟悉的桌面应用界面
3. ✅ **开发效率高**：Python 内置，无需额外配置
4. ✅ **部署简单**：可直接打包成单文件可执行程序
5. ✅ **维护成本低**：代码简洁，依赖稳定

## 下一步计划

1. **确认方案**：请您确认选择哪个方案
2. **详细设计**：制定具体的实现计划
3. **原型开发**：创建基础界面框架
4. **功能集成**：集成现有处理逻辑
5. **测试优化**：界面测试和用户体验优化

**建议选择 Tkinter GUI 方案**，我已经准备好了详细的实现计划（见 `doc/tkinter_implementation_plan.md`）。

请告诉我您的选择，我将立即开始实现！
