"""
Progress Monitor for V2PPT GUI
Handles real-time progress updates and log display
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Optional, Callable
import threading


class ProgressMonitor:
    """Monitors and displays processing progress"""
    
    def __init__(self, parent_frame: ttk.Frame):
        self.parent_frame = parent_frame
        self.setup_ui()
        
        # Progress tracking
        self.current_step = ""
        self.current_percentage = 0.0
        self.start_time = None
        self.is_processing = False
        
        # Thread safety
        self.update_lock = threading.Lock()
    
    def setup_ui(self):
        """Setup progress monitoring UI"""
        
        # Progress frame
        progress_frame = ttk.LabelFrame(self.parent_frame, text="📊 处理进度", padding=10)
        progress_frame.pack(fill='x', pady=(0, 10))
        
        # Current step
        step_frame = ttk.Frame(progress_frame)
        step_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(step_frame, text="当前步骤:", font=('Arial', 9)).pack(side='left')
        self.step_var = tk.StringVar(value="就绪")
        self.step_label = ttk.Label(step_frame, textvariable=self.step_var, 
                                   font=('Arial', 9, 'bold'), foreground='blue')
        self.step_label.pack(side='left', padx=(5, 0))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                          maximum=100, length=400, mode='determinate')
        self.progress_bar.pack(fill='x', pady=(0, 5))
        
        # Progress text
        progress_text_frame = ttk.Frame(progress_frame)
        progress_text_frame.pack(fill='x', pady=(0, 5))
        
        self.progress_text_var = tk.StringVar(value="0%")
        ttk.Label(progress_text_frame, textvariable=self.progress_text_var, 
                 font=('Arial', 9)).pack(side='left')
        
        self.time_var = tk.StringVar(value="")
        ttk.Label(progress_text_frame, textvariable=self.time_var, 
                 font=('Arial', 9)).pack(side='right')
        
        # Details
        self.details_var = tk.StringVar(value="")
        self.details_label = ttk.Label(progress_frame, textvariable=self.details_var, 
                                      font=('Arial', 8), foreground='gray')
        self.details_label.pack(anchor='w', pady=(0, 5))
        
        # Log section
        log_frame = ttk.LabelFrame(self.parent_frame, text="📝 处理日志", padding=10)
        log_frame.pack(fill='both', expand=True)
        
        # Log text with scrollbar
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill='both', expand=True)
        
        self.log_text = tk.Text(log_container, height=8, wrap=tk.WORD, 
                               font=('Consolas', 9), state='disabled')
        
        log_scrollbar = ttk.Scrollbar(log_container, orient='vertical', 
                                     command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side='left', fill='both', expand=True)
        log_scrollbar.pack(side='right', fill='y')
        
        # Log control buttons
        log_control_frame = ttk.Frame(log_frame)
        log_control_frame.pack(fill='x', pady=(5, 0))
        
        ttk.Button(log_control_frame, text="清空日志", 
                  command=self.clear_log).pack(side='left')
        ttk.Button(log_control_frame, text="保存日志", 
                  command=self.save_log).pack(side='left', padx=(5, 0))
        
        # Auto-scroll checkbox
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_control_frame, text="自动滚动", 
                       variable=self.auto_scroll_var).pack(side='right')
    
    def start_processing(self):
        """Start processing - initialize progress tracking"""
        with self.update_lock:
            self.is_processing = True
            self.start_time = datetime.now()
            self.current_percentage = 0.0
            self.progress_var.set(0)
            self.step_var.set("准备中...")
            self.progress_text_var.set("0%")
            self.time_var.set("")
            self.details_var.set("")
            
        self.add_log("开始处理", "INFO")
    
    def update_progress(self, step: str, percentage: float, status: str, details: Optional[str] = None, is_new_step: bool = True):
        """
        Update progress information

        Args:
            step: Current processing step
            percentage: Progress percentage (0-100)
            status: Status message
            details: Optional detailed information
            is_new_step: Whether this is a new step (add new log) or update to current step
        """
        with self.update_lock:
            self.current_step = step
            self.current_percentage = percentage

            # Add or update log based on is_new_step
            if is_new_step:
                self.add_log(status, "INFO")
            else:
                self.update_current_log(status, "INFO")

            # Update UI in main thread
            if hasattr(self, 'parent_frame') and self.parent_frame.winfo_exists():
                self.parent_frame.after(0, self._update_progress_ui, step, percentage, status, details)
    
    def _update_progress_ui(self, step: str, percentage: float, status: str, details: Optional[str]):
        """Update progress UI (called in main thread)"""
        try:
            # Update step
            self.step_var.set(step)
            
            # Update progress bar and text
            self.progress_var.set(percentage)
            self.progress_text_var.set(f"{percentage:.1f}%")
            
            # Update time information
            if self.start_time and self.is_processing:
                elapsed = datetime.now() - self.start_time
                elapsed_str = str(elapsed).split('.')[0]  # Remove microseconds
                
                if percentage > 0:
                    # Estimate remaining time
                    total_time = elapsed.total_seconds() / (percentage / 100)
                    remaining_seconds = total_time - elapsed.total_seconds()
                    
                    if remaining_seconds > 0:
                        remaining_time = str(datetime.fromtimestamp(remaining_seconds) - 
                                           datetime.fromtimestamp(0)).split('.')[0]
                        time_text = f"已用时: {elapsed_str} | 预计剩余: {remaining_time}"
                    else:
                        time_text = f"已用时: {elapsed_str}"
                else:
                    time_text = f"已用时: {elapsed_str}"
                
                self.time_var.set(time_text)
            
            # Update details
            if details:
                self.details_var.set(details)
            
        except Exception as e:
            print(f"Error updating progress UI: {e}")
    
    def finish_processing(self, success: bool, message: str):
        """Finish processing"""
        with self.update_lock:
            self.is_processing = False
            
            if success:
                self.step_var.set("完成")
                self.progress_var.set(100)
                self.progress_text_var.set("100%")
                self.add_log(f"✅ {message}", "SUCCESS")
            else:
                self.step_var.set("失败")
                self.add_log(f"❌ {message}", "ERROR")
            
            if self.start_time:
                elapsed = datetime.now() - self.start_time
                elapsed_str = str(elapsed).split('.')[0]
                self.time_var.set(f"总用时: {elapsed_str}")
    
    def add_log(self, message: str, level: str = "INFO"):
        """
        Add log message

        Args:
            message: Log message
            level: Log level (INFO, WARNING, ERROR, SUCCESS)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Color coding
        color_map = {
            "INFO": "black",
            "WARNING": "orange",
            "ERROR": "red",
            "SUCCESS": "green"
        }
        color = color_map.get(level, "black")

        # Format message
        log_entry = f"[{timestamp}] {message}\n"

        # Update log text in main thread
        if hasattr(self, 'log_text') and self.log_text.winfo_exists():
            self.log_text.after(0, self._add_log_ui, log_entry, color)

    def update_current_log(self, message: str, level: str = "INFO"):
        """
        Update the current (last) log line instead of adding a new one

        Args:
            message: Log message
            level: Log level (INFO, WARNING, ERROR, SUCCESS)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Color coding
        color_map = {
            "INFO": "black",
            "WARNING": "orange",
            "ERROR": "red",
            "SUCCESS": "green"
        }
        color = color_map.get(level, "black")

        # Format message
        log_entry = f"[{timestamp}] {message}"

        # Update log text in main thread
        if hasattr(self, 'log_text') and self.log_text.winfo_exists():
            self.log_text.after(0, self._update_current_log_ui, log_entry, color)
    
    def _add_log_ui(self, log_entry: str, color: str):
        """Add log entry to UI (called in main thread)"""
        try:
            self.log_text.configure(state='normal')
            
            # Insert text with color
            start_index = self.log_text.index(tk.END + "-1c")
            self.log_text.insert(tk.END, log_entry)
            end_index = self.log_text.index(tk.END + "-1c")
            
            # Apply color tag
            tag_name = f"color_{color}"
            self.log_text.tag_add(tag_name, start_index, end_index)
            self.log_text.tag_configure(tag_name, foreground=color)
            
            self.log_text.configure(state='disabled')
            
            # Auto-scroll if enabled
            if self.auto_scroll_var.get():
                self.log_text.see(tk.END)
                
        except Exception as e:
            print(f"Error adding log entry: {e}")

    def _update_current_log_ui(self, log_entry: str, color: str):
        """Update the current (last) log line instead of adding new one"""
        try:
            self.log_text.configure(state='normal')

            # Get the current line count
            line_count = int(self.log_text.index('end-1c').split('.')[0])

            # Check if there's content on the last line
            if line_count > 1:
                last_line_start = f"{line_count-1}.0"
                last_line_end = f"{line_count-1}.end"
                last_line_content = self.log_text.get(last_line_start, last_line_end)

                if last_line_content.strip():
                    # Delete the last line including the newline
                    self.log_text.delete(last_line_start, f"{line_count}.0")

            # Insert the new content
            self.log_text.insert("end", log_entry + "\n")

            # Apply color to the new line
            new_line_start = self.log_text.index("end-2c linestart")
            new_line_end = self.log_text.index("end-2c lineend")

            tag_name = f"color_{color}"
            self.log_text.tag_add(tag_name, new_line_start, new_line_end)
            self.log_text.tag_configure(tag_name, foreground=color)

            self.log_text.configure(state='disabled')

            # Auto-scroll if enabled
            if self.auto_scroll_var.get():
                self.log_text.see(tk.END)

        except Exception as e:
            print(f"Error updating current log entry: {e}")
            # Fallback to adding new log
            self._add_log_ui(log_entry, color)

    def clear_log(self):
        """Clear log text"""
        self.log_text.configure(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state='disabled')
        self.add_log("日志已清空", "INFO")
    
    def save_log(self):
        """Save log to file"""
        try:
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(
                title="保存日志",
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            
            if filename:
                log_content = self.log_text.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                self.add_log(f"日志已保存到: {filename}", "SUCCESS")
                
        except Exception as e:
            self.add_log(f"保存日志失败: {e}", "ERROR")
    
    def reset(self):
        """Reset progress monitor"""
        with self.update_lock:
            self.is_processing = False
            self.start_time = None
            self.current_step = ""
            self.current_percentage = 0.0
            
            self.step_var.set("就绪")
            self.progress_var.set(0)
            self.progress_text_var.set("0%")
            self.time_var.set("")
            self.details_var.set("")
