"""
Main Window for V2PPT GUI
Implements the primary user interface with file selection, parameter configuration, and controls
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import sys
import os

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from .config_manager import ConfigManager, ProcessingConfig
from .progress_monitor import ProgressMonitor
from .worker_thread import WorkerThread


class MainWindow:
    """Main application window"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        
        # Configuration management
        self.config_manager = ConfigManager()
        self.current_config = self.config_manager.load_config()
        
        # Worker thread
        self.worker_thread = None
        
        # Setup UI
        self.setup_ui()
        self.setup_bindings()
        self.load_config_to_ui()
        
        # Window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_window(self):
        """Setup main window properties"""
        self.root.title("🎬 V2PPT - 视频转PPT工具")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.root.winfo_screenheight() // 2) - (700 // 2)
        self.root.geometry(f"900x700+{x}+{y}")
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')  # Modern theme
    
    def setup_ui(self):
        """Setup user interface"""
        
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill='x', pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="🎬 V2PPT - 视频转PPT工具", 
                               font=('Arial', 16, 'bold'))
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame, text="将视频中的PPT页面提取并生成PowerPoint文件", 
                                  font=('Arial', 10), foreground='gray')
        subtitle_label.pack(pady=(2, 0))
        
        # Main content area
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill='both', expand=True)
        
        # Left panel - Input and Settings
        left_panel = ttk.Frame(content_frame)
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        self.create_input_section(left_panel)
        self.create_settings_section(left_panel)
        self.create_control_section(left_panel)
        
        # Right panel - Progress and Log
        right_panel = ttk.Frame(content_frame)
        right_panel.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # Progress monitor
        self.progress_monitor = ProgressMonitor(right_panel)
        
        # Status bar
        self.create_status_bar(main_container)
    
    def create_input_section(self, parent):
        """Create input file selection section"""
        
        input_frame = ttk.LabelFrame(parent, text="📁 输入设置", padding=10)
        input_frame.pack(fill='x', pady=(0, 10))
        
        # Video file selection
        video_frame = ttk.Frame(input_frame)
        video_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(video_frame, text="视频文件:", width=10).pack(side='left')
        
        self.video_path_var = tk.StringVar()
        video_entry = ttk.Entry(video_frame, textvariable=self.video_path_var, width=35)
        video_entry.pack(side='left', fill='x', expand=True, padx=(5, 5))
        
        ttk.Button(video_frame, text="浏览...", width=8,
                  command=self.select_video_file).pack(side='right')
        
        # Output directory selection
        output_frame = ttk.Frame(input_frame)
        output_frame.pack(fill='x')
        
        ttk.Label(output_frame, text="输出目录:", width=10).pack(side='left')
        
        self.output_dir_var = tk.StringVar()
        output_entry = ttk.Entry(output_frame, textvariable=self.output_dir_var, width=35)
        output_entry.pack(side='left', fill='x', expand=True, padx=(5, 5))
        
        ttk.Button(output_frame, text="浏览...", width=8,
                  command=self.select_output_dir).pack(side='right')
    
    def create_settings_section(self, parent):
        """Create settings configuration section"""
        
        settings_frame = ttk.LabelFrame(parent, text="⚙️ 处理设置", padding=10)
        settings_frame.pack(fill='x', pady=(0, 10))
        
        # Processing mode
        mode_frame = ttk.Frame(settings_frame)
        mode_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(mode_frame, text="处理模式:", font=('Arial', 9, 'bold')).pack(anchor='w')
        
        self.mode_var = tk.StringVar()
        mode_buttons_frame = ttk.Frame(mode_frame)
        mode_buttons_frame.pack(fill='x', pady=(5, 0))
        
        modes = [
            ("标准模式", "standard", "平衡的处理效果"),
            ("保守模式", "conservative", "保留更多幻灯片"),
            ("非常保守", "very_conservative", "最大程度保留"),
            ("自定义", "custom", "手动调整参数")
        ]
        
        for i, (text, value, tooltip) in enumerate(modes):
            btn = ttk.Radiobutton(mode_buttons_frame, text=text, variable=self.mode_var, 
                                 value=value, command=self.on_mode_change)
            btn.pack(side='left', padx=(0, 10))
            # TODO: Add tooltip
        
        # Advanced settings (collapsible)
        self.advanced_visible = tk.BooleanVar(value=False)
        advanced_toggle = ttk.Checkbutton(settings_frame, text="显示高级设置", 
                                         variable=self.advanced_visible,
                                         command=self.toggle_advanced_settings)
        advanced_toggle.pack(anchor='w', pady=(5, 0))
        
        # Advanced settings panel
        self.advanced_frame = ttk.Frame(settings_frame)
        
        self.create_advanced_settings()
    
    def create_advanced_settings(self):
        """Create advanced settings panel"""
        
        # Similarity threshold
        similarity_frame = ttk.Frame(self.advanced_frame)
        similarity_frame.pack(fill='x', pady=2)
        
        ttk.Label(similarity_frame, text="相似度阈值:", width=12).pack(side='left')
        
        self.similarity_var = tk.DoubleVar()
        similarity_scale = ttk.Scale(similarity_frame, from_=0.0, to=1.0, 
                                    variable=self.similarity_var, orient='horizontal')
        similarity_scale.pack(side='left', fill='x', expand=True, padx=(5, 5))
        
        self.similarity_label = ttk.Label(similarity_frame, text="0.8", width=5)
        self.similarity_label.pack(side='right')
        similarity_scale.configure(command=self.update_similarity_label)
        
        # Frame interval
        interval_frame = ttk.Frame(self.advanced_frame)
        interval_frame.pack(fill='x', pady=2)
        
        ttk.Label(interval_frame, text="帧间隔(秒):", width=12).pack(side='left')
        
        self.interval_var = tk.DoubleVar()
        interval_spinbox = ttk.Spinbox(interval_frame, from_=1.0, to=30.0, increment=0.5,
                                      textvariable=self.interval_var, width=8)
        interval_spinbox.pack(side='left', padx=(5, 0))
        
        # Skip settings
        skip_frame = ttk.Frame(self.advanced_frame)
        skip_frame.pack(fill='x', pady=2)
        
        ttk.Label(skip_frame, text="跳过开始:", width=8).pack(side='left')
        self.skip_start_var = tk.DoubleVar()
        ttk.Spinbox(skip_frame, from_=0.0, to=300.0, increment=1.0,
                   textvariable=self.skip_start_var, width=6).pack(side='left', padx=(2, 10))
        
        ttk.Label(skip_frame, text="跳过结束:", width=8).pack(side='left')
        self.skip_end_var = tk.DoubleVar()
        ttk.Spinbox(skip_frame, from_=0.0, to=300.0, increment=1.0,
                   textvariable=self.skip_end_var, width=6).pack(side='left', padx=(2, 0))
        
        # Processing options
        options_frame = ttk.Frame(self.advanced_frame)
        options_frame.pack(fill='x', pady=5)
        
        self.enhance_var = tk.BooleanVar()
        self.dedup_var = tk.BooleanVar()
        self.filter_var = tk.BooleanVar()
        
        ttk.Checkbutton(options_frame, text="图像增强", 
                       variable=self.enhance_var).pack(side='left')
        ttk.Checkbutton(options_frame, text="去除重复", 
                       variable=self.dedup_var).pack(side='left', padx=(10, 0))
        ttk.Checkbutton(options_frame, text="PPT内容过滤", 
                       variable=self.filter_var).pack(side='left', padx=(10, 0))
        
        # PPT settings
        ppt_frame = ttk.LabelFrame(self.advanced_frame, text="PPT设置", padding=5)
        ppt_frame.pack(fill='x', pady=(10, 0))
        
        # Title and author
        title_frame = ttk.Frame(ppt_frame)
        title_frame.pack(fill='x', pady=2)
        
        ttk.Label(title_frame, text="标题:", width=8).pack(side='left')
        self.title_var = tk.StringVar()
        ttk.Entry(title_frame, textvariable=self.title_var, width=20).pack(side='left', padx=(2, 10))
        
        ttk.Label(title_frame, text="作者:", width=8).pack(side='left')
        self.author_var = tk.StringVar()
        ttk.Entry(title_frame, textvariable=self.author_var, width=15).pack(side='left', padx=(2, 0))
        
        # Additional options
        ppt_options_frame = ttk.Frame(ppt_frame)
        ppt_options_frame.pack(fill='x', pady=2)
        
        self.add_titles_var = tk.BooleanVar()
        ttk.Checkbutton(ppt_options_frame, text="添加幻灯片标题", 
                       variable=self.add_titles_var).pack(side='left')
    
    def create_control_section(self, parent):
        """Create control buttons section"""
        
        control_frame = ttk.LabelFrame(parent, text="🎮 控制", padding=10)
        control_frame.pack(fill='x', pady=(0, 10))
        
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill='x')
        
        # Start button
        self.start_button = ttk.Button(button_frame, text="▶️ 开始处理", 
                                      command=self.start_processing,
                                      style='Accent.TButton')
        self.start_button.pack(side='left', padx=(0, 5))
        
        # Stop button
        self.stop_button = ttk.Button(button_frame, text="⏹️ 停止", 
                                     command=self.stop_processing,
                                     state='disabled')
        self.stop_button.pack(side='left', padx=(0, 5))
        
        # Reset button
        self.reset_button = ttk.Button(button_frame, text="🔄 重置", 
                                      command=self.reset_settings)
        self.reset_button.pack(side='left', padx=(0, 5))
        
        # Help button
        ttk.Button(button_frame, text="❓ 帮助", 
                  command=self.show_help).pack(side='right')
    
    def create_status_bar(self, parent):
        """Create status bar"""
        
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill='x', pady=(5, 0))
        
        ttk.Separator(status_frame, orient='horizontal').pack(fill='x', pady=(0, 2))
        
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                font=('Arial', 9))
        status_label.pack(side='left')
        
        # Version info
        version_label = ttk.Label(status_frame, text="v1.0.0", 
                                 font=('Arial', 8), foreground='gray')
        version_label.pack(side='right')
    
    def setup_bindings(self):
        """Setup event bindings"""
        
        # Drag and drop for video file (simplified)
        self.root.bind('<Button-1>', self.on_click)
        
        # Keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self.select_video_file())
        self.root.bind('<F5>', lambda e: self.start_processing())
        self.root.bind('<Escape>', lambda e: self.stop_processing())
    
    def on_click(self, event):
        """Handle click events"""
        pass  # Placeholder for future drag-drop implementation

    # Event handlers
    def select_video_file(self):
        """Select video file"""
        filetypes = [
            ('视频文件', '*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.m4v'),
            ('MP4文件', '*.mp4'),
            ('AVI文件', '*.avi'),
            ('所有文件', '*.*')
        ]

        filename = filedialog.askopenfilename(
            title="选择视频文件",
            filetypes=filetypes
        )

        if filename:
            self.video_path_var.set(filename)
            # Auto-generate output filename
            video_name = Path(filename).stem
            current_output = self.output_dir_var.get()
            if not current_output or current_output == "output/ppt":
                self.output_dir_var.set("output/ppt")
            self.status_var.set(f"已选择视频: {Path(filename).name}")

    def select_output_dir(self):
        """Select output directory"""
        directory = filedialog.askdirectory(
            title="选择输出目录"
        )

        if directory:
            self.output_dir_var.set(directory)
            self.status_var.set(f"输出目录: {directory}")

    def on_mode_change(self):
        """Handle processing mode change"""
        mode = self.mode_var.get()

        # Apply preset if not custom
        if mode != "custom":
            self.current_config.mode = mode
            self.config_manager.apply_preset(self.current_config, mode)
            self.load_config_to_ui()
            self.status_var.set(f"已切换到{mode}模式")

        # Show/hide advanced settings for custom mode
        if mode == "custom":
            self.advanced_visible.set(True)
            self.toggle_advanced_settings()

    def toggle_advanced_settings(self):
        """Toggle advanced settings visibility"""
        if self.advanced_visible.get():
            self.advanced_frame.pack(fill='x', pady=(10, 0))
        else:
            self.advanced_frame.pack_forget()

    def update_similarity_label(self, value):
        """Update similarity threshold label"""
        self.similarity_label.config(text=f"{float(value):.2f}")

    def start_processing(self):
        """Start video processing"""
        try:
            # Save current UI state to config
            self.save_ui_to_config()

            # Validate configuration
            is_valid, error_msg = self.config_manager.validate_config(self.current_config)
            if not is_valid:
                messagebox.showerror("配置错误", error_msg)
                return

            # Save configuration
            self.config_manager.save_config(self.current_config)

            # Update UI state
            self.start_button.configure(state='disabled')
            self.stop_button.configure(state='normal')
            self.status_var.set("正在处理...")

            # Start progress monitoring
            self.progress_monitor.start_processing()

            # Get processing arguments
            processing_args = self.config_manager.get_processing_args(self.current_config)

            # Start worker thread
            from .worker_thread import WorkerThread
            self.worker_thread = WorkerThread(
                processing_args=processing_args,
                progress_callback=self.progress_callback,
                completion_callback=self.completion_callback
            )
            self.worker_thread.start()

        except Exception as e:
            messagebox.showerror("启动失败", f"无法启动处理: {str(e)}")
            self.reset_ui_state()

    def stop_processing(self):
        """Stop video processing"""
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.stop()
            self.status_var.set("正在停止...")
            self.progress_monitor.add_log("用户请求停止处理", "WARNING")

            # Schedule UI reset after a short delay to allow thread to finish
            self.root.after(1000, self._delayed_reset_ui)

    def reset_settings(self):
        """Reset all settings to default"""
        result = messagebox.askyesno("重置设置", "确定要重置所有设置到默认值吗？")
        if result:
            self.current_config = self.config_manager.get_default_config()
            self.load_config_to_ui()
            self.progress_monitor.reset()
            self.status_var.set("设置已重置")

    def show_help(self):
        """Show help dialog"""
        help_text = """
🎬 V2PPT - 视频转PPT工具 使用说明

📁 基本使用：
1. 选择要处理的视频文件
2. 选择输出目录
3. 选择处理模式
4. 点击"开始处理"

⚙️ 处理模式：
• 标准模式：平衡的处理效果，适合大多数情况
• 保守模式：保留更多幻灯片，降低相似度阈值
• 非常保守：最大程度保留幻灯片，关闭内容过滤
• 自定义：手动调整所有参数

🔧 高级设置：
• 相似度阈值：控制重复检测的严格程度（0.0-1.0）
• 帧间隔：视频帧提取的时间间隔（秒）
• 跳过设置：跳过视频开头和结尾的时间
• 处理选项：图像增强、去重、PPT内容过滤

⌨️ 快捷键：
• Ctrl+O：选择视频文件
• F5：开始处理
• Esc：停止处理

💡 提示：
如果生成的PPT缺少页面，尝试使用保守模式或降低相似度阈值。
        """

        help_window = tk.Toplevel(self.root)
        help_window.title("使用帮助")
        help_window.geometry("500x400")
        help_window.resizable(False, False)

        # Center help window
        help_window.transient(self.root)
        help_window.grab_set()

        text_widget = tk.Text(help_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill='both', expand=True)
        text_widget.insert(1.0, help_text)
        text_widget.configure(state='disabled')

        ttk.Button(help_window, text="关闭",
                  command=help_window.destroy).pack(pady=10)

    # Configuration management
    def load_config_to_ui(self):
        """Load configuration to UI elements"""
        config = self.current_config

        # Basic settings
        self.video_path_var.set(config.video_path)
        self.output_dir_var.set(config.output_dir)
        self.mode_var.set(config.mode)

        # Advanced settings
        self.similarity_var.set(config.similarity_threshold)
        self.update_similarity_label(config.similarity_threshold)
        self.interval_var.set(config.frame_interval)
        self.skip_start_var.set(config.skip_start)
        self.skip_end_var.set(config.skip_end)

        # Processing options
        self.enhance_var.set(config.enhance_images)
        self.dedup_var.set(config.remove_duplicates)
        self.filter_var.set(config.filter_ppt_content)

        # PPT settings
        self.title_var.set(config.presentation_title)
        self.author_var.set(config.presentation_author)
        self.add_titles_var.set(config.add_slide_titles)

    def save_ui_to_config(self):
        """Save UI state to configuration"""
        config = self.current_config

        # Basic settings
        config.video_path = self.video_path_var.get()
        config.output_dir = self.output_dir_var.get()
        config.mode = self.mode_var.get()

        # Advanced settings
        config.similarity_threshold = self.similarity_var.get()
        config.frame_interval = self.interval_var.get()
        config.skip_start = self.skip_start_var.get()
        config.skip_end = self.skip_end_var.get()

        # Processing options
        config.enhance_images = self.enhance_var.get()
        config.remove_duplicates = self.dedup_var.get()
        config.filter_ppt_content = self.filter_var.get()

        # PPT settings
        config.presentation_title = self.title_var.get()
        config.presentation_author = self.author_var.get()
        config.add_slide_titles = self.add_titles_var.get()

    # Callback functions
    def progress_callback(self, step: str, percentage: float, status: str, details: str = None, is_new_step: bool = True):
        """Progress callback from worker thread"""
        self.progress_monitor.update_progress(step, percentage, status, details, is_new_step)

    def completion_callback(self, success: bool, message: str, output_path: str = None):
        """Completion callback from worker thread"""
        # Schedule the UI update in the main thread to avoid thread issues
        self.root.after(0, self._handle_completion, success, message, output_path)

    def _handle_completion(self, success: bool, message: str, output_path: str = None):
        """Handle completion in the main thread"""
        self.progress_monitor.finish_processing(success, message)

        if success and output_path:
            self.status_var.set(f"完成！输出文件: {Path(output_path).name}")

            # Ask if user wants to open output directory
            result = messagebox.askyesno("处理完成",
                                       f"处理完成！\n\n输出文件: {output_path}\n\n是否打开输出目录？")
            if result:
                self.open_output_directory(output_path)
        else:
            self.status_var.set("处理失败")

        self.reset_ui_state()

    def reset_ui_state(self):
        """Reset UI to ready state"""
        self.start_button.configure(state='normal')
        self.stop_button.configure(state='disabled')

        # Schedule thread cleanup in the main thread to avoid "cannot join current thread" error
        if self.worker_thread:
            # Don't try to join from within the worker thread itself
            # Just mark it for cleanup and let it finish naturally
            self.worker_thread = None

    def _delayed_reset_ui(self):
        """Delayed UI reset for manual stop operations"""
        if self.worker_thread and not self.worker_thread.is_alive():
            self.reset_ui_state()

    def open_output_directory(self, file_path: str):
        """Open output directory in file explorer"""
        try:
            import subprocess
            import platform

            directory = str(Path(file_path).parent)

            if platform.system() == "Windows":
                subprocess.run(f'explorer "{directory}"', shell=True)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", directory])
            else:  # Linux
                subprocess.run(["xdg-open", directory])

        except Exception as e:
            self.progress_monitor.add_log(f"无法打开目录: {e}", "WARNING")

    def on_closing(self):
        """Handle window closing"""
        if self.worker_thread and self.worker_thread.is_alive():
            result = messagebox.askyesno("确认退出", "正在处理中，确定要退出吗？")
            if result:
                self.worker_thread.stop()
                self.worker_thread.join(timeout=2)  # Wait up to 2 seconds
            else:
                return

        # Save current configuration
        try:
            self.save_ui_to_config()
            self.config_manager.save_config(self.current_config)
        except Exception:
            pass  # Ignore save errors on exit

        self.root.destroy()

    def run(self):
        """Start the GUI application"""
        self.root.mainloop()


def main():
    """Main entry point for GUI application"""
    try:
        app = MainWindow()
        app.run()
    except Exception as e:
        print(f"Failed to start GUI: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
