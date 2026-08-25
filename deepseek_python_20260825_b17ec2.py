import tkinter as tk
import re
import os
import json
from tkinter import filedialog, messagebox

class FloatingReader:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)          # 无边框
        self.root.attributes('-topmost', True)    # 置顶
        self.root.attributes('-alpha', 0.85)      # 透明度
        self.root.geometry('380x70+1000+600')     # 初始位置和大小

        # 状态变量
        self.lines = []
        self.current_line = 0
        self.file_name = ''
        self.chars_per_line = 30
        self.progress_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reading_progress.json')
        self.progress_data = self.load_progress()

        # 创建标签显示文字
        self.label = tk.Label(self.root, text='双击打开TXT文件', font=('宋体', 14), fg='white', bg='#202040', wraplength=360)
        self.label.pack(fill='both', expand=True, padx=10, pady=5)

        # 绑定事件
        self.label.bind('<Double-Button-1>', self.open_file)
        self.root.bind('<Button-1>', self.start_move)
        self.root.bind('<B1-Motion>', self.on_move)
        self.root.bind('<Button-3>', self.show_menu)
        self.root.bind('<MouseWheel>', self.on_wheel)      # Windows滚轮
        self.root.bind('<Button-4>', self.on_wheel_linux)  # Linux向上滚动
        self.root.bind('<Button-5>', self.on_wheel_linux)  # Linux向下滚动
        self.root.bind('<Up>', lambda e: self.prev_line())
        self.root.bind('<Down>', lambda e: self.next_line())
        self.root.bind('<Left>', lambda e: self.prev_line())
        self.root.bind('<Right>', lambda e: self.next_line())

        # 右键菜单
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label='打开TXT文件', command=self.open_file)
        self.menu.add_command(label='上一行', command=self.prev_line)
        self.menu.add_command(label='下一行', command=self.next_line)
        self.menu.add_separator()
        self.menu.add_command(label='增大字号', command=lambda: self.change_font(2))
        self.menu.add_command(label='减小字号', command=lambda: self.change_font(-2))
        self.menu.add_command(label='增加宽度', command=lambda: self.change_width(50))
        self.menu.add_command(label='减少宽度', command=lambda: self.change_width(-50))
        self.menu.add_separator()
        self.menu.add_command(label='提高不透明度', command=lambda: self.change_alpha(0.1))
        self.menu.add_command(label='降低不透明度', command=lambda: self.change_alpha(-0.1))
        self.menu.add_separator()
        self.menu.add_command(label='置顶/取消置顶', command=self.toggle_topmost)
        self.menu.add_command(label='重置窗口位置', command=self.reset_position)
        self.menu.add_command(label='退出', command=self.root.quit)

        # 启动
        self.root.mainloop()

    # ---------- 文件处理 ----------
    def open_file(self, event=None):
        file_path = filedialog.askopenfilename(filetypes=[('文本文件', '*.txt'), ('所有文件', '*.*')])
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                self.file_name = os.path.basename(file_path)
                self.load_text(text)
            except UnicodeDecodeError:
                try:
                    with open(file_path, 'r', encoding='gbk') as f:
                        text = f.read()
                    self.file_name = os.path.basename(file_path)
                    self.load_text(text)
                except Exception as e:
                    messagebox.showerror('错误', f'文件编码无法识别：{e}')
            except Exception as e:
                messagebox.showerror('错误', f'读取失败：{e}')

    def load_text(self, text):
        # 按每行chars_per_line切分
        raw_lines = text.split('\n')
        self.lines = []
        self.chapter_positions = []  # 存储 (行索引, 标题)
        for raw in raw_lines:
            raw = raw.strip()
            if not raw:
                continue
            # 检查章节
            if re.match(r'^(第[一二三四五六七八九十百千万\d]+[章节回卷集部篇]|Chapter\s+\d+)', raw):
                self.chapter_positions.append((len(self.lines), raw[:30]))
            # 切分
            for i in range(0, len(raw), self.chars_per_line):
                self.lines.append(raw[i:i+self.chars_per_line])

        if not self.lines:
            self.lines = ['（空文件）']
            self.chapter_positions = []

        # 恢复进度
        self.current_line = 0
        if self.file_name in self.progress_data:
            saved_line = self.progress_data[self.file_name]
            if 0 <= saved_line < len(self.lines):
                self.current_line = saved_line
        self.update_display()

    def update_display(self):
        if self.lines:
            self.label.config(text=self.lines[self.current_line])
        # 保存进度
        if self.file_name:
            self.progress_data[self.file_name] = self.current_line
            self.save_progress()

    def save_progress(self):
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress_data, f)
        except:
            pass

    def load_progress(self):
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}

    # ---------- 行导航 ----------
    def next_line(self):
        if self.lines and self.current_line < len(self.lines) - 1:
            self.current_line += 1
            self.update_display()

    def prev_line(self):
        if self.lines and self.current_line > 0:
            self.current_line -= 1
            self.update_display()

    def go_to_line(self, line_idx):
        if self.lines and 0 <= line_idx < len(self.lines):
            self.current_line = line_idx
            self.update_display()

    # ---------- 事件处理 ----------
    def on_wheel(self, event):
        if event.delta > 0:
            self.prev_line()
        else:
            self.next_line()

    def on_wheel_linux(self, event):
        if event.num == 4:
            self.prev_line()
        elif event.num == 5:
            self.next_line()

    def start_move(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def on_move(self, event):
        x = self.root.winfo_x() + event.x - self.drag_start_x
        y = self.root.winfo_y() + event.y - self.drag_start_y
        self.root.geometry(f'+{x}+{y}')

    def show_menu(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    # ---------- 设置调整 ----------
    def change_font(self, delta):
        current_size = self.label.cget('font').split()[-1]
        new_size = max(8, int(current_size) + delta)
        self.label.config(font=('宋体', new_size))
        # 调整窗口高度以适应字体
        self.root.geometry(f'{self.root.winfo_width()}x{new_size * 2 + 20}')

    def change_width(self, delta):
        current_w = self.root.winfo_width()
        new_w = max(200, current_w + delta)
        self.root.geometry(f'{new_w}x{self.root.winfo_height()}')
        self.label.config(wraplength=new_w - 20)

    def change_alpha(self, delta):
        current = self.root.attributes('-alpha')
        new_alpha = max(0.2, min(1.0, current + delta))
        self.root.attributes('-alpha', new_alpha)

    def toggle_topmost(self):
        current = self.root.attributes('-topmost')
        self.root.attributes('-topmost', not current)

    def reset_position(self):
        self.root.geometry('380x70+1000+600')

    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    app = FloatingReader()