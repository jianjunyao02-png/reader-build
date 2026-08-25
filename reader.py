import tkinter as tk
import re
import os
import json
from tkinter import filedialog, messagebox

class FloatingReader:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.85)
        self.root.geometry('420x90+1000+600')
        self.root.configure(bg='#202040')

        # 状态变量
        self.lines = []
        self.current_line = 0
        self.file_name = ''
        self.chars_per_line = 30
        self.min_chars = 15
        self.max_chars = 80
        self.chapter_positions = []  # [(line_index, chapter_title), ...]
        self.current_chapter = ''

        # 数据文件路径（用户主目录下，避免程序目录只读问题）
        self.data_dir = os.path.join(os.path.expanduser('~'), '.floating_reader')
        os.makedirs(self.data_dir, exist_ok=True)
        self.book_file = os.path.join(self.data_dir, 'current_book.json')

        # 创建界面
        self.chapter_label = tk.Label(self.root, text='', font=('宋体', 9), fg='#a0a0c0', bg='#202040', anchor='w')
        self.chapter_label.pack(fill='x', padx=8, pady=(2,0))
        self.label = tk.Label(self.root, text='双击打开TXT文件', font=('宋体', 14), fg='white', bg='#202040', wraplength=400, justify='left')
        self.label.pack(fill='both', expand=True, padx=8, pady=(0,5))

        # 绑定事件
        self.label.bind('<Double-Button-1>', self.open_file)
        self.root.bind('<Button-1>', self.start_move)
        self.root.bind('<B1-Motion>', self.on_move)
        self.root.bind('<Button-3>', self.show_menu)
        self.root.bind('<MouseWheel>', self.on_wheel)
        self.root.bind('<Button-4>', self.on_wheel_linux)
        self.root.bind('<Button-5>', self.on_wheel_linux)
        self.root.bind('<Up>', lambda e: self.prev_line())
        self.root.bind('<Down>', lambda e: self.next_line())
        self.root.bind('<Left>', lambda e: self.prev_line())
        self.root.bind('<Right>', lambda e: self.next_line())
        self.root.bind('<Home>', lambda e: self.go_to_line(0))
        self.root.bind('<End>', lambda e: self.go_to_line(len(self.lines)-1))

        # 右键菜单
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label='打开TXT文件', command=self.open_file)
        self.menu.add_separator()
        self.menu.add_command(label='上一行', command=self.prev_line)
        self.menu.add_command(label='下一行', command=self.next_line)
        self.menu.add_separator()

        # 每行字数子菜单
        self.chars_menu = tk.Menu(self.menu, tearoff=0)
        for val in [15, 20, 25, 30, 35, 40, 50, 60, 80]:
            self.chars_menu.add_command(label=str(val), command=lambda v=val: self.set_chars_per_line(v))
        self.menu.add_cascade(label='每行字数', menu=self.chars_menu)

        # 字体大小子菜单
        self.font_menu = tk.Menu(self.menu, tearoff=0)
        for size in [10, 12, 14, 16, 18, 20, 24, 28, 32]:
            self.font_menu.add_command(label=str(size), command=lambda s=size: self.set_font_size(s))
        self.menu.add_cascade(label='字体大小', menu=self.font_menu)

        # 窗口宽度子菜单
        self.width_menu = tk.Menu(self.menu, tearoff=0)
        for w in [200, 250, 300, 350, 400, 450, 500, 600]:
            self.width_menu.add_command(label=str(w)+'px', command=lambda w=w: self.set_window_width(w))
        self.menu.add_cascade(label='窗口宽度', menu=self.width_menu)

        # 窗口高度子菜单
        self.height_menu = tk.Menu(self.menu, tearoff=0)
        for h in [40, 50, 60, 70, 80, 100, 120, 150]:
            self.height_menu.add_command(label=str(h)+'px', command=lambda h=h: self.set_window_height(h))
        self.menu.add_cascade(label='窗口高度', menu=self.height_menu)

        self.menu.add_separator()
        # 章节子菜单
        self.chapter_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label='跳转章节', menu=self.chapter_menu)

        self.menu.add_separator()
        self.menu.add_command(label='提高不透明度', command=lambda: self.change_alpha(0.1))
        self.menu.add_command(label='降低不透明度', command=lambda: self.change_alpha(-0.1))
        self.menu.add_command(label='置顶/取消置顶', command=self.toggle_topmost)
        self.menu.add_command(label='重置窗口位置', command=self.reset_position)
        self.menu.add_command(label='退出', command=self.root.quit)

        # 自动加载上次的书
        self.auto_load()

        self.root.mainloop()

    # ---------- 书籍保存/加载 ----------
    def save_book(self):
        """保存当前书籍内容和进度到本地"""
        if not self.lines:
            return
        data = {
            'file_name': self.file_name,
            'lines': self.lines,
            'current_line': self.current_line,
            'chars_per_line': self.chars_per_line,
            'chapter_positions': self.chapter_positions,
        }
        try:
            with open(self.book_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception:
            pass

    def auto_load(self):
        """启动时自动加载上次的书籍"""
        if os.path.exists(self.book_file):
            try:
                with open(self.book_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.file_name = data.get('file_name', '')
                self.lines = data.get('lines', [])
                self.current_line = data.get('current_line', 0)
                self.chars_per_line = data.get('chars_per_line', 30)
                self.chapter_positions = data.get('chapter_positions', [])
                if self.lines:
                    self.update_display()
                    self.chapter_label.config(text=self.file_name if self.file_name else '')
                    self.build_chapter_menu()
            except Exception:
                pass

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
        """加载文本并重新分行"""
        raw_lines = text.split('\n')
        self.lines = []
        self.chapter_positions = []
        chapter_pattern = re.compile(
            r'^(第[一二三四五六七八九十百千万\d]+[章节回卷集部篇][^\n]{0,50}|Chapter\s+\d+[^\n]{0,60}|CHAPTER\s+\d+[^\n]{0,60})'
        )
        for raw in raw_lines:
            raw = raw.strip()
            if not raw:
                continue
            if chapter_pattern.match(raw):
                self.chapter_positions.append((len(self.lines), raw[:30]))
            for i in range(0, len(raw), self.chars_per_line):
                self.lines.append(raw[i:i+self.chars_per_line])
        if not self.lines:
            self.lines = ['（空文件）']
            self.chapter_positions = []
        self.current_line = 0
        self.update_display()
        self.build_chapter_menu()
        self.save_book()

    def update_display(self):
        if not self.lines:
            return
        text = self.lines[self.current_line]
        self.label.config(text=text)
        # 更新当前章节名
        self.current_chapter = ''
        for line_idx, title in self.chapter_positions:
            if line_idx <= self.current_line:
                self.current_chapter = title
            else:
                break
        self.chapter_label.config(text=f'{self.file_name} | {self.current_chapter}' if self.current_chapter else self.file_name)
        self.save_book()

    def build_chapter_menu(self):
        """构建章节跳转菜单"""
        self.chapter_menu.delete(0, 'end')
        if not self.chapter_positions:
            self.chapter_menu.add_command(label='（未识别到章节）', state='disabled')
            return
        for idx, (line_idx, title) in enumerate(self.chapter_positions, 1):
            self.chapter_menu.add_command(label=f'{idx}. {title}', command=lambda li=line_idx: self.go_to_line(li))

    # ---------- 导航 ----------
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

    # ---------- 设置 ----------
    def set_chars_per_line(self, val):
        """重新设置每行字数并重新分行"""
        val = max(self.min_chars, min(val, self.max_chars))
        if val == self.chars_per_line:
            return
        self.chars_per_line = val
        if self.file_name:
            # 重新加载原始文本
            try:
                file_path = self.find_original_file()
                if file_path:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                    self.load_text(text)
                else:
                    # 如果原始文件找不到，尝试从现有行重新组合
                    full_text = ''.join(self.lines)
                    self.lines = []
                    for i in range(0, len(full_text), self.chars_per_line):
                        self.lines.append(full_text[i:i+self.chars_per_line])
                    self.update_display()
                    self.save_book()
            except Exception:
                pass
        else:
            self.update_display()
            self.save_book()

    def find_original_file(self):
        """尝试查找原始文件路径"""
        # 因为保存的是文件名，需要在常见位置查找
        search_paths = [
            os.path.expanduser('~'),
            os.path.expanduser('~/Desktop'),
            os.path.expanduser('~/Downloads'),
            os.path.expanduser('~/Documents'),
        ]
        for path in search_paths:
            full_path = os.path.join(path, self.file_name)
            if os.path.exists(full_path):
                return full_path
        return None

    def set_font_size(self, size):
        self.label.config(font=('宋体', size))
        self.chapter_label.config(font=('宋体', max(8, size-4)))
        self.root.geometry(f'{self.root.winfo_width()}x{size * 2 + 30}')

    def set_window_width(self, width):
        width = max(200, width)
        self.root.geometry(f'{width}x{self.root.winfo_height()}')
        self.label.config(wraplength=width - 20)

    def set_window_height(self, height):
        height = max(40, height)
        self.root.geometry(f'{self.root.winfo_width()}x{height}')

    def change_alpha(self, delta):
        current = self.root.attributes('-alpha')
        new_alpha = max(0.2, min(1.0, current + delta))
        self.root.attributes('-alpha', new_alpha)

    def toggle_topmost(self):
        current = self.root.attributes('-topmost')
        self.root.attributes('-topmost', not current)

    def reset_position(self):
        self.root.geometry('420x90+1000+600')

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
            self.build_chapter_menu()  # 刷新章节菜单
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

if __name__ == '__main__':
    app = FloatingReader()