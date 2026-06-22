"""FileBrain 图形界面 —— tkinter 桌面应用"""

import os
import threading
import logging
from pathlib import Path
from tkinter import (
    Tk, ttk, Frame, Label, Button, Entry,
    Text, Scrollbar, Checkbutton, IntVar,
    StringVar, BooleanVar, filedialog, messagebox,
    Toplevel, END, NORMAL, DISABLED, WORD,
)
from tkinter.ttk import Combobox

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("FileBrain")

# 颜色方案
COLORS = {
    "bg": "#f5f2ed",
    "fg": "#2c2c2c",
    "accent": "#c97a3a",
    "accent_light": "#e8d5c0",
    "success": "#5a8f5a",
    "warn": "#c97a3a",
    "error": "#b85450",
    "card_bg": "#ffffff",
    "border": "#d4cfc8",
    "text_secondary": "#888888",
}

FONTS = {
    "title": ("PingFang SC", 16, "bold"),
    "heading": ("PingFang SC", 13, "bold"),
    "body": ("PingFang SC", 11),
    "small": ("PingFang SC", 9),
    "mono": ("Menlo", 10),
}


class FileBrainApp:
    """FileBrain 主窗口"""

    def __init__(self):
        self.root = Tk()
        self.root.title("FileBrain · 文件大脑")
        self.root.geometry("820x640")
        self.root.minsize(700, 520)
        self.root.configure(bg=COLORS["bg"])

        # 应用图标（可选）
        try:
            self.root.iconbitmap(default="")
        except Exception:
            pass

        # 核心组件引用（延迟初始化）
        self.watcher = None
        self.version_mgr = None
        self.search_index = None
        self.send_journal = None
        self.watch_dir = StringVar(value=os.path.expanduser("~/Desktop"))

        # 配置变量
        self.auto_rename = BooleanVar(value=True)
        self.auto_version = BooleanVar(value=True)
        self.include_author = BooleanVar(value=True)
        self.author_name = StringVar(value=os.environ.get("USER", "unknown"))
        self.monitor_pdf = BooleanVar(value=True)
        self.monitor_word = BooleanVar(value=True)
        self.monitor_excel = BooleanVar(value=True)
        self.monitor_image = BooleanVar(value=True)

        # 搜索相关
        self.search_results = []
        self.selected_file_path = StringVar()

        # 构建界面
        self._build_ui()

        # 窗口关闭处理
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ==================== UI 构建 ====================

    def _build_ui(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        main_frame = Frame(self.root, bg=COLORS["bg"])
        main_frame.grid(row=0, column=0, sticky="nsew", padx=12, pady=8)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # 顶栏
        self._build_header(main_frame)

        # Tab 控制
        self._build_tabs(main_frame)

    def _build_header(self, parent):
        header = Frame(parent, bg=COLORS["bg"])
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        header.grid_columnconfigure(1, weight=1)

        Label(header, text="🧠 FileBrain",
              font=FONTS["title"],
              bg=COLORS["bg"], fg=COLORS["fg"]
              ).grid(row=0, column=0, sticky="w")

        Label(header, text="文件大脑 · 自动识别 · 智能命名 · 全文检索",
              font=FONTS["body"],
              bg=COLORS["bg"], fg=COLORS["text_secondary"]
              ).grid(row=0, column=1, sticky="w", padx=(8, 0))

        # 状态指示器 + 品牌来源
        right_frame = Frame(header, bg=COLORS["bg"])
        right_frame.grid(row=0, column=2, sticky="e")
        right_frame.grid_columnconfigure(0, weight=1)

        self.status_label = Label(right_frame,
                                  text="⏸ 未启动",
                                  font=FONTS["body"],
                                  bg=COLORS["accent_light"],
                                  fg=COLORS["accent"],
                                  padx=10, pady=2)
        self.status_label.grid(row=0, column=0, sticky="e")

        # 品牌来源标注 — 科普视频推广
        Label(right_frame,
              text="⬇ GitHub 开源 · 免费下载",
              font=("PingFang SC", 8),
              bg=COLORS["bg"],
              fg="#aaaaaa",
              cursor="hand2"
              ).grid(row=1, column=0, sticky="e", pady=(1, 0))

    def _build_tabs(self, parent):
        # Notebook (tab 控件)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=COLORS["bg"],
                        borderwidth=0)
        style.configure("TNotebook.Tab",
                        font=FONTS["body"],
                        padding=[12, 4])
        style.map("TNotebook.Tab",
                  background=[("selected", COLORS["card_bg"])])

        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=1, column=0, sticky="nsew")

        # 各标签页
        self._build_monitor_tab()
        self._build_search_tab()
        self._build_journal_tab()
        self._build_settings_tab()

    # ---------- 标签页 1: 文件监控 ----------

    def _build_monitor_tab(self):
        frame = Frame(self.notebook, bg=COLORS["card_bg"])
        self.notebook.add(frame, text="📁 文件监控")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(3, weight=1)

        # 目录选择
        dir_frame = Frame(frame, bg=COLORS["card_bg"])
        dir_frame.grid(row=0, column=0, sticky="ew",
                       padx=12, pady=(12, 4))
        dir_frame.grid_columnconfigure(1, weight=1)

        Label(dir_frame, text="监控目录：",
              font=FONTS["body"], bg=COLORS["card_bg"]
              ).grid(row=0, column=0, sticky="w")

        Entry(dir_frame, textvariable=self.watch_dir,
              font=FONTS["body"], relief="flat",
              bg="#f0ede8"
              ).grid(row=0, column=1, sticky="ew", padx=6)

        Button(dir_frame,
               text="📂 选择",
               font=FONTS["small"],
               command=self._select_dir,
               bg=COLORS["accent_light"],
               relief="flat", padx=8
               ).grid(row=0, column=2, sticky="e")

        # 控制按钮
        ctrl_frame = Frame(frame, bg=COLORS["card_bg"])
        ctrl_frame.grid(row=1, column=0, sticky="ew",
                        padx=12, pady=4)

        self.btn_start = Button(ctrl_frame,
                                text="▶ 开始监控",
                                font=FONTS["body"],
                                command=self._toggle_monitor,
                                bg=COLORS["success"],
                                fg="white",
                                relief="flat", padx=16, pady=4)
        self.btn_start.grid(row=0, column=0, sticky="w")

        Button(ctrl_frame,
               text="🔄 扫描已有文件",
               font=FONTS["body"],
               command=self._scan_existing,
               bg=COLORS["accent"],
               fg="white",
               relief="flat", padx=12, pady=4
               ).grid(row=0, column=1, sticky="w", padx=(8, 0))

        # 文件类型选择
        type_frame = Frame(frame, bg=COLORS["card_bg"])
        type_frame.grid(row=2, column=0, sticky="ew",
                        padx=12, pady=4)

        Label(type_frame, text="识别类型：",
              font=FONTS["body"], bg=COLORS["card_bg"]
              ).grid(row=0, column=0, sticky="w")

        Checkbutton(type_frame, text="PDF (含扫描件)",
                    variable=self.monitor_pdf,
                    bg=COLORS["card_bg"],
                    font=FONTS["body"]
                    ).grid(row=0, column=1, padx=4)
        Checkbutton(type_frame, text="Word",
                    variable=self.monitor_word,
                    bg=COLORS["card_bg"],
                    font=FONTS["body"]
                    ).grid(row=0, column=2, padx=4)
        Checkbutton(type_frame, text="Excel",
                    variable=self.monitor_excel,
                    bg=COLORS["card_bg"],
                    font=FONTS["body"]
                    ).grid(row=0, column=3, padx=4)
        Checkbutton(type_frame, text="图片 (OCR)",
                    variable=self.monitor_image,
                    bg=COLORS["card_bg"],
                    font=FONTS["body"]
                    ).grid(row=0, column=4, padx=4)

        # 活动日志
        log_label = Label(frame, text="📋 活动日志",
                          font=FONTS["heading"],
                          bg=COLORS["card_bg"])
        log_label.grid(row=3, column=0, sticky="nw",
                       padx=12, pady=(8, 2))

        log_frame = Frame(frame, bg=COLORS["card_bg"])
        log_frame.grid(row=3, column=0, sticky="nsew",
                       padx=12, pady=(0, 12))
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self.log_text = Text(log_frame,
                             font=FONTS["mono"],
                             wrap=WORD,
                             relief="flat",
                             bg="#f8f6f2",
                             fg=COLORS["fg"],
                             height=8,
                             state=NORMAL)
        self.log_text.grid(row=0, column=0, sticky="nsew")

        scroll = Scrollbar(log_frame, command=self.log_text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=scroll.set)

    # ---------- 标签页 2: 全文检索 ----------

    def _build_search_tab(self):
        frame = Frame(self.notebook, bg=COLORS["card_bg"])
        self.notebook.add(frame, text="🔍 全文检索")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        # 搜索栏
        search_frame = Frame(frame, bg=COLORS["card_bg"])
        search_frame.grid(row=0, column=0, sticky="ew",
                          padx=12, pady=(12, 4))
        search_frame.grid_columnconfigure(1, weight=1)

        Label(search_frame, text="搜索内容：",
              font=FONTS["body"], bg=COLORS["card_bg"]
              ).grid(row=0, column=0, sticky="w")

        self.search_entry = Entry(search_frame,
                                  font=FONTS["body"],
                                  relief="flat",
                                  bg="#f0ede8")
        self.search_entry.grid(row=0, column=1, sticky="ew",
                               padx=6)
        self.search_entry.bind("<Return>",
                               lambda e: self._do_search())

        Button(search_frame,
               text="🔍 搜索",
               font=FONTS["body"],
               command=self._do_search,
               bg=COLORS["accent"],
               fg="white",
               relief="flat", padx=12
               ).grid(row=0, column=2, sticky="e")

        # 搜索统计
        self.search_count_label = Label(
            frame, text="",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"]
        )
        self.search_count_label.grid(row=1, column=0,
                                     sticky="ew",
                                     padx=12, pady=2)

        # 搜索结果
        result_frame = Frame(frame, bg=COLORS["card_bg"])
        result_frame.grid(row=2, column=0, sticky="nsew",
                          padx=12, pady=(0, 12))
        result_frame.grid_rowconfigure(0, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)

        # 结果列表（Treeview）
        columns = ("file", "title", "context", "score")
        self.result_tree = ttk.Treeview(
            result_frame, columns=columns,
            show="headings", height=12,
            selectmode="browse"
        )
        self.result_tree.heading("file", text="文件名")
        self.result_tree.heading("title", text="标题")
        self.result_tree.heading("context", text="匹配上下文")
        self.result_tree.heading("score", text="相关度")
        self.result_tree.column("file", width=180)
        self.result_tree.column("title", width=120)
        self.result_tree.column("context", width=300)
        self.result_tree.column("score", width=60, anchor="center")
        self.result_tree.grid(row=0, column=0, sticky="nsew")

        scroll_y = Scrollbar(result_frame,
                             command=self.result_tree.yview)
        scroll_y.grid(row=0, column=1, sticky="ns")
        self.result_tree.config(yscrollcommand=scroll_y.set)

        self.result_tree.bind("<<TreeviewSelect>>",
                              self._on_result_select)

        # 操作按钮
        action_frame = Frame(frame, bg=COLORS["card_bg"])
        action_frame.grid(row=3, column=0, sticky="ew",
                          padx=12, pady=(0, 12))

        Button(action_frame,
               text="📂 打开文件位置",
               font=FONTS["body"],
               command=self._open_file_location,
               bg=COLORS["accent_light"],
               relief="flat", padx=10
               ).grid(row=0, column=0, sticky="w")

        Button(action_frame,
               text="📤 记录发送",
               font=FONTS["body"],
               command=self._show_send_dialog,
               bg=COLORS["accent"],
               fg="white",
               relief="flat", padx=10
               ).grid(row=0, column=1, sticky="w", padx=(6, 0))

        # 发送记录预览
        self.send_preview = Label(
            action_frame,
            text="",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"]
        )
        self.send_preview.grid(row=0, column=2, sticky="w",
                               padx=(12, 0))

    # ---------- 标签页 3: 发送留痕 ----------

    def _build_journal_tab(self):
        frame = Frame(self.notebook, bg=COLORS["card_bg"])
        self.notebook.add(frame, text="📤 发送留痕")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        # 搜索栏
        jsearch_frame = Frame(frame, bg=COLORS["card_bg"])
        jsearch_frame.grid(row=0, column=0, sticky="ew",
                           padx=12, pady=(12, 4))
        jsearch_frame.grid_columnconfigure(1, weight=1)

        Label(jsearch_frame, text="搜索发送记录：",
              font=FONTS["body"], bg=COLORS["card_bg"]
              ).grid(row=0, column=0, sticky="w")

        self.journal_search_entry = Entry(
            jsearch_frame, font=FONTS["body"],
            relief="flat", bg="#f0ede8"
        )
        self.journal_search_entry.grid(row=0, column=1,
                                       sticky="ew", padx=6)
        self.journal_search_entry.bind(
            "<Return>", lambda e: self._search_journal()
        )

        Button(jsearch_frame,
               text="🔍 搜索",
               font=FONTS["body"],
               command=self._search_journal,
               bg=COLORS["accent"],
               fg="white",
               relief="flat", padx=8
               ).grid(row=0, column=2, sticky="e")

        # 记录列表
        jlist_frame = Frame(frame, bg=COLORS["card_bg"])
        jlist_frame.grid(row=2, column=0, sticky="nsew",
                         padx=12, pady=(0, 12))
        jlist_frame.grid_rowconfigure(0, weight=1)
        jlist_frame.grid_columnconfigure(0, weight=1)

        jcolumns = ("time", "file", "recipient", "method", "notes")
        self.journal_tree = ttk.Treeview(
            jlist_frame, columns=jcolumns,
            show="headings", height=12,
            selectmode="browse"
        )
        self.journal_tree.heading("time", text="发送时间")
        self.journal_tree.heading("file", text="文件名")
        self.journal_tree.heading("recipient", text="接收人")
        self.journal_tree.heading("method", text="方式")
        self.journal_tree.heading("notes", text="备注")
        self.journal_tree.column("time", width=130)
        self.journal_tree.column("file", width=200)
        self.journal_tree.column("recipient", width=120)
        self.journal_tree.column("method", width=100)
        self.journal_tree.column("notes", width=150)
        self.journal_tree.grid(row=0, column=0, sticky="nsew")

        jscroll_y = Scrollbar(jlist_frame,
                              command=self.journal_tree.yview)
        jscroll_y.grid(row=0, column=1, sticky="ns")
        self.journal_tree.config(yscrollcommand=jscroll_y.set)

        # 操作按钮
        jaction_frame = Frame(frame, bg=COLORS["card_bg"])
        jaction_frame.grid(row=3, column=0, sticky="ew",
                           padx=12, pady=(0, 12))

        Button(jaction_frame,
               text="🗑 删除选中记录",
               font=FONTS["body"],
               command=self._delete_journal_record,
               bg=COLORS["error"],
               fg="white",
               relief="flat", padx=10
               ).grid(row=0, column=0, sticky="w")

        Button(jaction_frame,
               text="🔄 刷新",
               font=FONTS["body"],
               command=self._refresh_journal,
               bg=COLORS["accent_light"],
               relief="flat", padx=10
               ).grid(row=0, column=1, sticky="w", padx=(6, 0))

    # ---------- 标签页 4: 设置 ----------

    def _build_settings_tab(self):
        frame = Frame(self.notebook, bg=COLORS["card_bg"])
        self.notebook.add(frame, text="⚙️ 设置")
        frame.grid_columnconfigure(0, weight=1)

        # 命名设置
        Label(frame,
              text="智能命名设置",
              font=FONTS["heading"],
              bg=COLORS["card_bg"]
              ).grid(row=0, column=0, sticky="w",
                     padx=16, pady=(16, 8))

        Checkbutton(frame,
                    text="自动重命名文件（内容摘要 + 日期 + 版本号）",
                    variable=self.auto_rename,
                    bg=COLORS["card_bg"],
                    font=FONTS["body"]
                    ).grid(row=1, column=0, sticky="w",
                           padx=16, pady=2)

        Checkbutton(frame,
                    text="按最后修改时间自动标注版本号",
                    variable=self.auto_version,
                    bg=COLORS["card_bg"],
                    font=FONTS["body"]
                    ).grid(row=2, column=0, sticky="w",
                           padx=16, pady=2)

        # 作者标注设置
        author_frame = Frame(frame, bg=COLORS["card_bg"])
        author_frame.grid(row=3, column=0, sticky="ew",
                          padx=16, pady=(6, 2))
        author_frame.grid_columnconfigure(2, weight=1)

        Checkbutton(author_frame,
                    text="文件名标注作者/来源：",
                    variable=self.include_author,
                    bg=COLORS["card_bg"],
                    font=FONTS["body"]
                    ).grid(row=0, column=0, sticky="w")

        Entry(author_frame,
              textvariable=self.author_name,
              font=FONTS["body"],
              relief="flat",
              bg="#f0ede8",
              width=16
              ).grid(row=0, column=1, sticky="w", padx=(4, 0))

        Label(author_frame,
              text="→ 文件名效果: 摘要_日期_作者_v1.0.pdf",
              font=FONTS["small"],
              bg=COLORS["card_bg"],
              fg=COLORS["text_secondary"]
              ).grid(row=0, column=2, sticky="w", padx=(8, 0))

        # ── 来源信息（推广用）──
        source_frame = Frame(frame, bg=COLORS["accent_light"],
                             highlightbackground=COLORS["accent"],
                             highlightthickness=1)
        source_frame.grid(row=4, column=0, sticky="ew",
                          padx=16, pady=(16, 4))
        source_frame.grid_columnconfigure(0, weight=1)

        Label(source_frame,
              text="⬇ 免费开源工具 · 欢迎下载使用 ⬇",
              font=("PingFang SC", 11, "bold"),
              bg=COLORS["accent_light"],
              fg=COLORS["accent"]
              ).grid(row=0, column=0, pady=(6, 0))

        Label(source_frame,
              text="GitHub 搜索「FileBrain」或访问下方链接下载",
              font=FONTS["body"],
              bg=COLORS["accent_light"],
              fg=COLORS["fg"]
              ).grid(row=1, column=0, pady=(0, 4))

        Label(source_frame,
              text="🔗 github.com/mmm1111lhc/FileBrain",
              font=("Menlo", 10),
              bg=COLORS["accent_light"],
              fg=COLORS["accent"],
              cursor="hand2"
              ).grid(row=2, column=0, pady=(0, 6))

        # 关于
        Label(frame,
              text="\n关于 FileBrain v1.0",
              font=FONTS["heading"],
              bg=COLORS["card_bg"]
              ).grid(row=5, column=0, sticky="w",
                     padx=16, pady=(12, 4))

        about_text = (
            "桌面文件智能整理工具\n\n"
            "功能：\n"
            "  • 自动扫描文件，识别内容\n"
            "  • 智能重命名：内容摘要 + 日期 + 版本号\n"
            "  • 支持 PDF（含扫描件OCR）、Word、Excel、图片\n"
            "  • 全文检索，快速定位文件\n"
            "  • 发送留痕，记录文件发给谁\n"
            "\n"
            "依赖：\n"
            "  • PyMuPDF / python-docx / openpyxl\n"
            "  • Tesseract OCR (brew install tesseract)\n"
            "  • Pillow / pytesseract\n"
        )
        Label(frame,
              text=about_text,
              font=FONTS["body"],
              bg=COLORS["card_bg"],
              fg=COLORS["text_secondary"],
              justify="left"
              ).grid(row=5, column=0, sticky="w",
                     padx=16, pady=2)

    # ==================== 核心逻辑 ====================

    def _select_dir(self):
        """选择监控目录"""
        d = filedialog.askdirectory(
            title="选择要监控的文件夹",
            initialdir=self.watch_dir.get()
        )
        if d:
            self.watch_dir.set(d)

    def _toggle_monitor(self):
        """启动/停止监控"""
        from core.watcher import Watcher

        if self.watcher and self.watcher.is_running():
            # 停止
            threading.Thread(target=self.watcher.stop,
                             daemon=True).start()
            self.watcher = None
            self.btn_start.config(text="▶ 开始监控",
                                  bg=COLORS["success"])
            self.status_label.config(text="⏸ 已停止",
                                     bg=COLORS["accent_light"])
            self._log("监控已停止")
        else:
            # 启动
            watch_dir = self.watch_dir.get()
            if not os.path.isdir(watch_dir):
                messagebox.showerror("错误", f"目录不存在：{watch_dir}")
                return

            self.watcher = Watcher(
                watch_dir,
                on_processed=self._on_file_processed
            )

            def start_watcher():
                self.watcher.start()
                self.root.after(0, self._on_monitor_started)

            threading.Thread(target=start_watcher,
                             daemon=True).start()
            self._log(f"正在启动监控: {watch_dir}")

    def _on_monitor_started(self):
        self.btn_start.config(text="⏹ 停止监控",
                              bg=COLORS["error"])
        self.status_label.config(text="🟢 监控中",
                                 bg=COLORS["success"])

    def _on_file_processed(self, status, old_name,
                           new_name, version, date):
        """文件处理完成回调"""
        msg = f"[{status}] {old_name} → {new_name}  (v{version})"
        self.root.after(0, self._log, msg)

    def _scan_existing(self):
        """扫描已有文件"""
        if not self.watcher or not self.watcher.is_running():
            messagebox.showinfo("提示",
                                "请先点击「开始监控」")
            return

        threading.Thread(
            target=self.watcher.handler.scan_existing,
            daemon=True
        ).start()
        self._log("开始扫描已有文件...")

    def _log(self, message: str):
        """在日志区添加一条消息"""
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(END, f"[{ts}] {message}\n")
        self.log_text.see(END)

    # ---------- 搜索 ----------

    def _do_search(self):
        """执行全文检索"""
        query = self.search_entry.get().strip()
        if not query:
            return

        # 清除旧结果
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

        if not self.watcher:
            messagebox.showinfo("提示", "请先启动文件监控")
            return

        results = self.watcher.search_index.search(query)

        if not results:
            self.search_count_label.config(
                text="未找到匹配结果"
            )
            return

        self.search_count_label.config(
            text=f"找到 {len(results)} 个匹配文件"
        )

        for r in results:
            self.result_tree.insert("", END,
                values=(
                    r.get("new_name", r.get("file_name", "")),
                    r.get("title", "")[:30],
                    r.get("context", "")[:60],
                    r.get("score", 0),
                ),
                tags=(r.get("path", ""),)
            )

    def _on_result_select(self, event):
        """搜索结果选中事件"""
        sel = self.result_tree.selection()
        if not sel:
            return

        item = self.result_tree.item(sel[0])
        file_path = item.get("tags", [""])[0]
        self.selected_file_path.set(file_path)

        # 预览发送记录
        if self.watcher and file_path:
            records = self.watcher.send_journal.get_records_for_file(
                file_path
            )
            if records:
                latest = records[0]
                self.send_preview.config(
                    text=f"📤 最近发送: {latest.get('recipient','?')} "
                         f"于 {latest.get('sent_at_str','')}"
                )
            else:
                self.send_preview.config(text="")

    def _open_file_location(self):
        """在 Finder 中打开文件所在位置"""
        file_path = self.selected_file_path.get()
        if not file_path:
            messagebox.showinfo("提示", "请先在搜索结果中选择一个文件")
            return
        os.system(f'open -R "{file_path}"')

    # ---------- 发送留痕 ----------

    def _show_send_dialog(self):
        """弹出发送记录对话框"""
        file_path = self.selected_file_path.get()
        if not file_path:
            messagebox.showinfo("提示", "请先在搜索结果中选择一个文件")
            return

        dialog = SendDialog(self.root, file_path,
                            self.watcher.send_journal,
                            self._on_send_recorded)
        self.root.wait_window(dialog.top)

    def _on_send_recorded(self):
        """发送记录已添加"""
        self._refresh_journal()
        self._log("✅ 发送记录已保存")

    def _search_journal(self):
        """搜索发送记录"""
        query = self.journal_search_entry.get().strip()

        for item in self.journal_tree.get_children():
            self.journal_tree.delete(item)

        if not self.watcher:
            return

        if query:
            records = self.watcher.send_journal.search(query)
        else:
            records = self.watcher.send_journal.get_recent()

        for r in records:
            self.journal_tree.insert("", END, values=(
                r.get("sent_at_str", ""),
                r.get("file_name", ""),
                r.get("recipient", ""),
                r.get("method", ""),
                r.get("notes", ""),
            ), tags=(r.get("id", 0),))

    def _delete_journal_record(self):
        """删除选中的发送记录"""
        sel = self.journal_tree.selection()
        if not sel:
            return

        record_id = self.journal_tree.item(sel[0]).get("tags", [0])[0]
        if messagebox.askyesno("确认删除",
                                "确定删除这条发送记录吗？"):
            if self.watcher:
                self.watcher.send_journal.delete_record(record_id)
            self._refresh_journal()
            self._log("🗑 发送记录已删除")

    def _refresh_journal(self):
        """刷新发送记录列表"""
        self.journal_search_entry.delete(0, END)
        self._search_journal()

    # ---------- 生命周期 ----------

    def _on_close(self):
        """窗口关闭时停止监控"""
        if self.watcher and self.watcher.is_running():
            self.watcher.stop()
        self.root.destroy()

    def run(self):
        """启动应用"""
        self.root.mainloop()


class SendDialog:
    """发送记录录入对话框"""

    def __init__(self, parent, file_path, journal, callback):
        self.journal = journal
        self.file_path = file_path
        self.callback = callback

        self.top = Toplevel(parent)
        self.top.title("📤 记录文件发送")
        self.top.geometry("420x380")
        self.top.configure(bg=COLORS["card_bg"])
        self.top.resizable(False, False)

        # 文件信息
        Label(self.top,
              text=f"文件: {Path(file_path).name}",
              font=FONTS["body"],
              bg=COLORS["card_bg"],
              wraplength=380
              ).pack(padx=16, pady=(16, 8), anchor="w")

        # 接收人
        Label(self.top, text="接收人 *",
              font=FONTS["body"],
              bg=COLORS["card_bg"]
              ).pack(padx=16, pady=(8, 2), anchor="w")
        self.recipient_entry = Entry(self.top,
                                     font=FONTS["body"],
                                     relief="flat",
                                     bg="#f0ede8")
        self.recipient_entry.pack(padx=16, fill="x", ipady=4)

        # 发送方式
        Label(self.top, text="发送方式 *",
              font=FONTS["body"],
              bg=COLORS["card_bg"]
              ).pack(padx=16, pady=(8, 2), anchor="w")
        self.method_combo = Combobox(
            self.top,
            values=self.journal.METHODS,
            font=FONTS["body"],
            state="normal"
        )
        self.method_combo.set("微信 WeChat")
        self.method_combo.pack(padx=16, fill="x", ipady=2)

        # 备注
        Label(self.top, text="备注",
              font=FONTS["body"],
              bg=COLORS["card_bg"]
              ).pack(padx=16, pady=(8, 2), anchor="w")
        self.notes_entry = Entry(self.top,
                                 font=FONTS["body"],
                                 relief="flat",
                                 bg="#f0ede8")
        self.notes_entry.pack(padx=16, fill="x", ipady=4)

        # 按钮
        btn_frame = Frame(self.top, bg=COLORS["card_bg"])
        btn_frame.pack(padx=16, pady=(16, 12), fill="x")

        Button(btn_frame,
               text="取消",
               font=FONTS["body"],
               command=self.top.destroy,
               bg=COLORS["accent_light"],
               relief="flat", padx=16
               ).pack(side="left")

        Button(btn_frame,
               text="✅ 保存记录",
               font=FONTS["body"],
               command=self._save,
               bg=COLORS["success"],
               fg="white",
               relief="flat", padx=16
               ).pack(side="right")

    def _save(self):
        recipient = self.recipient_entry.get().strip()
        method = self.method_combo.get().strip()

        if not recipient:
            messagebox.showwarning("提示", "请填写接收人",
                                   parent=self.top)
            return

        notes = self.notes_entry.get().strip()
        file_name = Path(self.file_path).name

        self.journal.add_record(
            self.file_path, file_name,
            recipient, method, notes
        )
        self.callback()
        self.top.destroy()


def main():
    """启动 FileBrain GUI"""
    app = FileBrainApp()
    app.run()


if __name__ == "__main__":
    main()
