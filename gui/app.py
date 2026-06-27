"""FileBrain 图形界面 —— 6层质感设计: 毛玻璃+渐变+阴影"""

import os
import time
import threading
import logging
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk

# ── 主题 ──
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("dark-blue")

# ── 6层设计配色 ──
COLOR_PAGE_BG = "#f3efe8"          # 基底: 暖白米色
COLOR_GLASS_BG = "#faf8f5"         # 毛玻璃层: 半透白
COLOR_TEXTURE_1 = "#e8e0d4"        # 质感层1: 灰米
COLOR_TEXTURE_2 = "#dcd2c2"        # 质感层2: 深米
COLOR_SHADOW = "rgba(60,40,20,0.08)"  # 阴影色
COLOR_CARD = "#ffffff"             # 卡片面
COLOR_ACCENT = "#c97a3a"           # 强调色 琥珀
COLOR_ACCENT_DARK = "#a8612a"      # 强调暗
COLOR_TEXT = "#2c2418"             # 主文字
COLOR_MUTED = "#8a7e72"            # 辅助文字
COLOR_SUCCESS = "#5a8f5a"
COLOR_ERROR = "#b85450"
COLOR_BORDER_SUBTLE = "#e8e0d4"    # 极淡边框

FONT_TITLE = ("PingFang SC", 20, "bold")
FONT_SECTION = ("PingFang SC", 15, "bold")
FONT_BODY = ("PingFang SC", 13)
FONT_MONO = ("Menlo", 11)

logger = logging.getLogger("FileBrain")


def _make_gradient(w=900, h=700):
    """快速渐变背景（小图拉伸，减少像素量）"""
    sw, sh = max(4, w//64), max(4, h//64)
    img = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for y in range(sh):
        p = y / sh
        r = int(243 - p * 10)
        g = int(239 - p * 12)
        b = int(232 - p * 10)
        draw.line([(0, y), (sw, y)], fill=(r, g, b, 255))
    return img.resize((w, h), Image.NEAREST)


class FileBrainApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("FileBrain · 文件大脑")
        self.root.geometry("900x700")
        self.root.minsize(760, 560)
        self.root.configure(fg_color=COLOR_PAGE_BG)

        # 背景质感纹理（用渐变图片）
        self._set_bg_texture()

        self.watcher = None
        self.watch_dir = ctk.StringVar(value=os.path.expanduser("~/Desktop"))
        self.selected_file_path = ""

        # ── 主体容器 ──
        self.main_glass = ctk.CTkFrame(self.root, fg_color=COLOR_GLASS_BG,
                                       corner_radius=16, border_width=0)
        self.main_glass.pack(fill="both", expand=True, padx=16, pady=16)

        # 纹理分隔条
        ctk.CTkFrame(self.main_glass, fg_color=COLOR_TEXTURE_1,
                     height=2, corner_radius=0).pack(fill="x")

        # 标题区
        header = ctk.CTkFrame(self.main_glass, fg_color="transparent", height=52)
        header.pack(fill="x", padx=20, pady=(8, 2))
        header.pack_propagate(False)

        # Logo + 标题（内阴影感用双色文字叠加模拟）
        logo_frame = ctk.CTkFrame(header, fg_color="transparent")
        logo_frame.pack(side="left")
        ctk.CTkLabel(logo_frame, text="🧠", font=("", 26)
                     ).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(logo_frame, text="FileBrain",
                     font=FONT_TITLE, text_color=COLOR_ACCENT_DARK
                     ).pack(side="left")
        ctk.CTkLabel(logo_frame, text=" · 文件大脑",
                     font=FONT_TITLE, text_color=COLOR_TEXT
                     ).pack(side="left")
        ctk.CTkLabel(logo_frame, text="  文件扔桌面，自动整理好",
                     font=("", 12), text_color=COLOR_MUTED
                     ).pack(side="left", padx=(12, 0), pady=(4, 0))

        # 分隔线（质感层2）
        sep = ctk.CTkFrame(self.main_glass, fg_color=COLOR_TEXTURE_2,
                           height=1, corner_radius=0)
        sep.pack(fill="x", padx=20, pady=0)

        # ── Tab 控件 ──
        self.tab = ctk.CTkTabview(
            self.main_glass,
            fg_color="transparent",
            segmented_button_fg_color=COLOR_TEXTURE_1,
            segmented_button_selected_color=COLOR_ACCENT,
            segmented_button_selected_hover_color=COLOR_ACCENT_DARK,
            segmented_button_unselected_color=COLOR_GLASS_BG,
            text_color=COLOR_TEXT,
            text_color_disabled=COLOR_MUTED,
            corner_radius=10,
        )
        self.tab.pack(fill="both", expand=True, padx=16, pady=(8, 12))

        t1 = self.tab.add("📁 自动整理")
        self._build_organize(t1)

        t2 = self.tab.add("🔍 全文检索")
        self._build_search(t2)

        t3 = self.tab.add("📤 发送留痕")
        self._build_journal(t3)

        t4 = self.tab.add("⚙️ 设置")
        self._build_settings(t4)

        # 底部阴影条
        bottom_shadow = ctk.CTkFrame(self.main_glass, fg_color=COLOR_TEXTURE_2,
                                     height=1, corner_radius=0)
        bottom_shadow.pack(fill="x", padx=20, side="bottom", pady=(0, 0))

        # 图标
        try:
            img = Image.open("images/app_icon.png")
            self.root.iconphoto(True, ImageTk.PhotoImage(img))
        except Exception:
            pass

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _set_bg_texture(self):
        """快速渐变背景"""
        img = _make_gradient(900, 700)
        bg_img = ctk.CTkImage(light_image=img, dark_image=img, size=(900, 700))
        lbl = ctk.CTkLabel(self.root, image=bg_img, text="")
        lbl.place(x=0, y=0, relwidth=1, relheight=1)
        lbl.lower()  # 推到最底层，不遮挡其他控件
        self.root.configure(fg_color=COLOR_PAGE_BG)

    # ═══════════════ 自动整理 ═══════════════

    def _build_organize(self, f):
        f.grid_columnconfigure(0, weight=1)
        f.grid_rowconfigure(4, weight=1)

        # 路径行
        p = ctk.CTkFrame(f, fg_color=COLOR_CARD, corner_radius=12,
                         border_width=1, border_color=COLOR_BORDER_SUBTLE)
        p.grid(row=0, column=0, sticky="ew", pady=3)
        p.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(p, text="📂 管理文件夹",
                     font=FONT_BODY, text_color=COLOR_TEXT
                     ).grid(row=0, column=0, padx=(16, 4), pady=10)
        e = ctk.CTkEntry(p, textvariable=self.watch_dir,
                         font=FONT_BODY, height=34,
                         fg_color="#f0ede8", border_width=0,
                         corner_radius=6)
        e.grid(row=0, column=1, sticky="ew", padx=4, pady=10)
        ctk.CTkButton(p, text="选择",
                      command=self._select_dir,
                      fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_DARK,
                      height=34, width=70, corner_radius=8,
                      text_color="white", font=("", 12, "bold")
                      ).grid(row=0, column=2, padx=(4, 16), pady=10)

        # 按钮行
        b = ctk.CTkFrame(f, fg_color="transparent")
        b.grid(row=1, column=0, sticky="ew", pady=(4, 2))
        b.grid_columnconfigure(2, weight=1)
        self.btn_start = ctk.CTkButton(
            b, text="▶  开始整理",
            font=("", 14, "bold"), text_color="white",
            height=40, width=150,
            command=self._toggle_monitor,
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_DARK,
            corner_radius=10,
        )
        self.btn_start.grid(row=0, column=0, sticky="w")
        ctk.CTkButton(
            b, text="🔄 扫描现有文件",
            command=self._scan_existing,
            fg_color="transparent",
            text_color=COLOR_ACCENT,
            hover_color=COLOR_TEXTURE_1,
            height=38, width=130, corner_radius=8,
            border_width=1, border_color=COLOR_ACCENT,
            font=FONT_BODY
        ).grid(row=0, column=1, padx=(8, 0))
        self.status_label = ctk.CTkLabel(
            b, text="⏸ 就绪", font=("", 12), text_color=COLOR_MUTED
        )
        self.status_label.grid(row=0, column=2, sticky="e", padx=(12, 0))

        # 类型行
        t = ctk.CTkFrame(f, fg_color=COLOR_CARD, corner_radius=10,
                         border_width=1, border_color=COLOR_BORDER_SUBTLE)
        t.grid(row=2, column=0, sticky="ew", pady=3)
        ctk.CTkLabel(t, text="识别类型：",
                     font=FONT_BODY, text_color=COLOR_TEXT
                     ).pack(side="left", padx=(16, 4), pady=8)
        self.pdf = ctk.BooleanVar(value=True)
        self.word = ctk.BooleanVar(value=True)
        self.excel = ctk.BooleanVar(value=True)
        self.img = ctk.BooleanVar(value=True)
        for txt, var in [("PDF (含扫描件)", self.pdf), ("Word", self.word),
                         ("Excel", self.excel), ("图片 (OCR)", self.img)]:
            ctk.CTkCheckBox(t, text=txt, variable=var,
                            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_DARK,
                            font=FONT_BODY
                            ).pack(side="left", padx=6, pady=8)

        # 日志标题
        ctk.CTkLabel(f, text="📋 活动日志",
                     font=FONT_SECTION, text_color=COLOR_TEXT
                     ).grid(row=3, column=0, sticky="nw", pady=(6, 2))

        # 日志框（简化：单层卡片）
        self.log = ctk.CTkTextbox(
            f, font=FONT_MONO,
            fg_color=COLOR_CARD, corner_radius=10,
            border_width=1, border_color=COLOR_BORDER_SUBTLE,
            height=130, text_color=COLOR_TEXT
        )
        self.log.grid(row=4, column=0, sticky="nsew", pady=(0, 2))

    # ═══════════════ 全文检索 ═══════════════

    def _build_search(self, f):
        f.grid_columnconfigure(0, weight=1)
        f.grid_rowconfigure(2, weight=1)

        # 搜索栏 —— 卡片+阴影感
        bar = ctk.CTkFrame(f, fg_color=COLOR_CARD, corner_radius=12,
                           border_width=1, border_color=COLOR_BORDER_SUBTLE)
        bar.grid(row=0, column=0, sticky="ew", pady=4)
        bar.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(bar, text="🔍 搜索",
                     font=FONT_SECTION, text_color=COLOR_TEXT
                     ).grid(row=0, column=0, padx=(16, 4), pady=10)
        self.se = ctk.CTkEntry(bar, font=FONT_BODY, height=34,
                               fg_color="#f0ede8", border_width=0,
                               corner_radius=6)
        self.se.grid(row=0, column=1, sticky="ew", padx=4, pady=10)
        self.se.bind("<Return>", lambda e: self._do_search())
        ctk.CTkButton(bar, text="搜索",
                      command=self._do_search,
                      fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_DARK,
                      height=34, width=80, corner_radius=8,
                      text_color="white", font=("", 12, "bold")
                      ).grid(row=0, column=2, padx=(4, 16), pady=10)

        # 搜索计数
        self.sc = ctk.CTkLabel(f, text="", font=FONT_BODY,
                               text_color=COLOR_MUTED)
        self.sc.grid(row=1, column=0, sticky="w", padx=4)

        # 结果区
        rf = ctk.CTkFrame(f, fg_color=COLOR_CARD, corner_radius=12,
                          border_width=1, border_color=COLOR_BORDER_SUBTLE)
        rf.grid(row=2, column=0, sticky="nsew", pady=2)
        rf.grid_columnconfigure(0, weight=1)
        rf.grid_rowconfigure(0, weight=1)
        self.rl = ctk.CTkScrollableFrame(rf, fg_color="transparent",
                                          corner_radius=0,
                                          scrollbar_button_color=COLOR_TEXTURE_2)
        self.rl.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        # 操作按钮
        ab = ctk.CTkFrame(f, fg_color="transparent")
        ab.grid(row=3, column=0, sticky="ew", pady=(6, 2))
        ab.grid_columnconfigure(2, weight=1)
        for i, (txt, cmd) in enumerate([
            ("📂 打开文件位置", self._open_file),
            ("📤 记录发送", self._send_dialog),
        ]):
            ctk.CTkButton(ab, text=txt, command=cmd,
                          fg_color="transparent",
                          text_color=COLOR_ACCENT,
                          hover_color=COLOR_TEXTURE_1,
                          height=34, corner_radius=8,
                          border_width=1, border_color=COLOR_ACCENT,
                          font=FONT_BODY
                          ).grid(row=0, column=i, padx=(0, 6))
        self.sp = ctk.CTkLabel(ab, text="", font=FONT_BODY,
                               text_color=COLOR_MUTED)
        self.sp.grid(row=0, column=2, sticky="e")

    # ═══════════════ 发送留痕 ═══════════════

    def _build_journal(self, f):
        f.grid_columnconfigure(0, weight=1)
        f.grid_rowconfigure(2, weight=1)

        bar = ctk.CTkFrame(f, fg_color=COLOR_CARD, corner_radius=12,
                           border_width=1, border_color=COLOR_BORDER_SUBTLE)
        bar.grid(row=0, column=0, sticky="ew", pady=4)
        bar.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(bar, text="📤 发送留痕",
                     font=FONT_SECTION, text_color=COLOR_TEXT
                     ).grid(row=0, column=0, padx=(16, 4), pady=10)
        self.je = ctk.CTkEntry(bar, font=FONT_BODY, height=34,
                               fg_color="#f0ede8", border_width=0,
                               corner_radius=6)
        self.je.grid(row=0, column=1, sticky="ew", padx=4, pady=10)
        self.je.bind("<Return>", lambda e: self._j_search())
        ctk.CTkButton(bar, text="搜索",
                      command=self._j_search,
                      fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_DARK,
                      height=34, width=80, corner_radius=8,
                      text_color="white", font=("", 12, "bold")
                      ).grid(row=0, column=2, padx=(4, 16), pady=10)

        jf = ctk.CTkFrame(f, fg_color=COLOR_CARD, corner_radius=12,
                          border_width=1, border_color=COLOR_BORDER_SUBTLE)
        jf.grid(row=2, column=0, sticky="nsew", pady=2)
        jf.grid_columnconfigure(0, weight=1)
        jf.grid_rowconfigure(0, weight=1)
        self.jl = ctk.CTkScrollableFrame(jf, fg_color="transparent",
                                          corner_radius=0,
                                          scrollbar_button_color=COLOR_TEXTURE_2)
        self.jl.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        ab = ctk.CTkFrame(f, fg_color="transparent")
        ab.grid(row=3, column=0, sticky="ew", pady=(6, 2))
        ctk.CTkButton(ab, text="🔄 刷新",
                      command=self._j_refresh,
                      fg_color="transparent",
                      text_color=COLOR_ACCENT,
                      hover_color=COLOR_TEXTURE_1,
                      height=34, corner_radius=8,
                      border_width=1, border_color=COLOR_ACCENT,
                      font=FONT_BODY
                      ).grid(row=0, column=0, sticky="w")

    # ═══════════════ 设置 ═══════════════

    def _build_settings(self, f):
        f.grid_columnconfigure(0, weight=1)

        # 设置卡片
        c1 = ctk.CTkFrame(f, fg_color=COLOR_CARD, corner_radius=12,
                          border_width=1, border_color=COLOR_BORDER_SUBTLE)
        c1.grid(row=0, column=0, sticky="ew", pady=4, padx=0)
        ctk.CTkLabel(c1, text="📐 智能命名",
                     font=FONT_SECTION, text_color=COLOR_TEXT
                     ).pack(anchor="w", padx=20, pady=(14, 6))
        self.ar = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(c1, text="自动重命名文件（内容摘要 · 日期 · 作者）",
                        variable=self.ar, font=FONT_BODY,
                        fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_DARK
                        ).pack(anchor="w", padx=20, pady=2)
        self.av = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(c1, text="文件修改后自动标注版本号 (v1.0)",
                        variable=self.av, font=FONT_BODY,
                        fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_DARK
                        ).pack(anchor="w", padx=20, pady=2)
        ctk.CTkLabel(c1, text="格式: 内容摘要 · 2026.06.22 · 作者 · v1.0.pdf",
                     font=FONT_MONO, text_color=COLOR_MUTED
                     ).pack(anchor="w", padx=20, pady=(4, 14))

        # 开源卡片 —— 质感背景
        s = ctk.CTkFrame(f, fg_color=COLOR_TEXTURE_1, corner_radius=12,
                         border_width=0)
        s.grid(row=1, column=0, sticky="ew", pady=(8, 4))
        # 底部阴影内边框
        inner_shadow = ctk.CTkFrame(s, fg_color=COLOR_GLASS_BG,
                                    corner_radius=10, height=60)
        inner_shadow.pack(fill="x", padx=2, pady=2)
        ctk.CTkLabel(inner_shadow, text="⬇ 免费开源 · 欢迎下载 ⬇",
                     font=("", 14, "bold"), text_color=COLOR_ACCENT
                     ).pack(pady=(8, 0))
        ctk.CTkLabel(inner_shadow, text="github.com/mmm1111lhc/FileBrain",
                     font=FONT_MONO, text_color=COLOR_ACCENT_DARK
                     ).pack(pady=(0, 8))

        # 关于
        c2 = ctk.CTkFrame(f, fg_color=COLOR_CARD, corner_radius=12,
                          border_width=1, border_color=COLOR_BORDER_SUBTLE)
        c2.grid(row=2, column=0, sticky="ew", pady=4)
        ctk.CTkLabel(c2, text="ℹ️ 关于",
                     font=FONT_SECTION, text_color=COLOR_TEXT
                     ).pack(anchor="w", padx=20, pady=(14, 4))
        info = ("FileBrain · 文件大脑 v1.0\n\n"
                "🔒 纯本地 · 不过云\n"
                "所有文件在本地处理，数据不上传云端\n\n"
                "📄 支持 PDF(含OCR) · Word · Excel · 图片")
        ctk.CTkLabel(c2, text=info, font=FONT_BODY,
                     justify="left", text_color=COLOR_TEXT
                     ).pack(anchor="w", padx=20, pady=(0, 14))

    # ═══════════════ 核心逻辑（保持不变） ═══════════════

    def _select_dir(self):
        d = filedialog.askdirectory(initialdir=self.watch_dir.get())
        if d:
            self.watch_dir.set(d)

    def _toggle_monitor(self):
        from core.watcher import Watcher
        if self.watcher and self.watcher.is_running():
            threading.Thread(target=self.watcher.stop, daemon=True).start()
            self.watcher = None
            self.btn_start.configure(text="▶  开始整理", fg_color=COLOR_ACCENT)
            self.status_label.configure(text="⏸ 已暂停", text_color=COLOR_MUTED)
            self._log("自动整理已停止")
        else:
            wd = self.watch_dir.get()
            if not os.path.isdir(wd):
                messagebox.showerror("错误", f"目录不存在：{wd}")
                return
            self.watcher = Watcher(wd, on_processed=self._on_proc)
            threading.Thread(target=self._start_w, daemon=True).start()
            self._log(f"正在启动: {wd}")

    def _start_w(self):
        """先更新UI状态再开始扫描（扫描在后台执行）"""
        self.root.after(0, self._started)
        self.watcher.start()
        self.root.after(0, self._log, "✅ 扫描完成，正在监控文件变化")

    def _started(self):
        self.btn_start.configure(text="⏹  停止整理", fg_color=COLOR_ERROR, state="normal")
        self.status_label.configure(text="🟢 整理中", text_color=COLOR_SUCCESS)

    def _on_proc(self, status, old, new, ver, date):
        self.root.after(0, self._log, f"[{status}] {old} → {new}")

    def _scan_existing(self):
        if not self.watcher or not self.watcher.is_running():
            messagebox.showinfo("提示", "请先点击「开始整理」")
            return
        threading.Thread(target=self.watcher.handler.scan_existing,
                         daemon=True).start()
        self._log("开始扫描现有文件...")

    def _log(self, msg):
        self.log.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log.see("end")

    def _do_search(self):
        q = self.se.get().strip()
        if not q:
            return
        for w in self.rl.winfo_children():
            w.destroy()
        if not self.watcher:
            messagebox.showinfo("提示", "请先启动自动整理")
            return
        rs = self.watcher.search_index.search(q)
        self.sc.configure(text=f"找到 {len(rs)} 个结果")
        for r in rs:
            c = ctk.CTkFrame(self.rl, fg_color="#f8f6f2",
                             corner_radius=8, height=38)
            c.pack(fill="x", pady=2)
            fn = ctk.CTkLabel(c, text=f"📄 {r.get('new_name', r.get('file_name',''))}",
                              font=FONT_BODY, anchor="w")
            fn.pack(side="left", padx=8)
            cx = r.get("context", "")[:40]
            ctk.CTkLabel(c, text=cx, font=FONT_BODY,
                         text_color=COLOR_MUTED).pack(side="left", padx=4)
            ctk.CTkLabel(c, text=f"相关度 {r.get('score',0)}",
                         font=FONT_BODY, text_color=COLOR_MUTED,
                         anchor="e", width=70
                         ).pack(side="right", padx=8)
            c.bind("<Button-1>", lambda e, p=r["path"]: setattr(
                self, "selected_file_path", p))

    def _open_file(self):
        p = self.selected_file_path
        if not p:
            messagebox.showinfo("提示", "请先在搜索结果中选择文件")
            return
        os.system(f'open -R "{p}"')

    def _send_dialog(self):
        p = self.selected_file_path
        if not p:
            messagebox.showinfo("提示", "请先选择文件")
            return
        if not self.watcher:
            return
        d = SendDialog(self.root, p, self.watcher.send_journal, self._on_sent)
        self.root.wait_window(d.top)

    def _on_sent(self):
        self._j_refresh()
        self._log("✅ 发送记录已保存")

    def _j_search(self):
        q = self.je.get().strip()
        for w in self.jl.winfo_children():
            w.destroy()
        if not self.watcher:
            return
        rs = (self.watcher.send_journal.search(q)
              if q else self.watcher.send_journal.get_recent(30))
        for r in rs:
            c = ctk.CTkFrame(self.jl, fg_color="#f8f6f2",
                             corner_radius=8, height=36)
            c.pack(fill="x", pady=2)
            ctk.CTkLabel(c, text=r.get("sent_at_str", ""),
                         font=FONT_MONO, width=110, anchor="w"
                         ).pack(side="left", padx=6)
            ctk.CTkLabel(c, text=Path(r.get("file_name", "")).name,
                         font=FONT_BODY).pack(side="left", padx=4, fill="x", expand=True)
            ctk.CTkLabel(c, text=f"→ {r.get('recipient', '')}",
                         font=FONT_BODY, text_color=COLOR_ACCENT
                         ).pack(side="left", padx=4)
            ctk.CTkLabel(c, text=f"({r.get('method', '')})",
                         font=FONT_BODY, text_color=COLOR_MUTED
                         ).pack(side="right", padx=8)

    def _j_refresh(self):
        self.je.delete(0, "end")
        self._j_search()

    def _on_close(self):
        if self.watcher and self.watcher.is_running():
            self.watcher.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


class SendDialog:
    METHODS = ["微信 WeChat", "邮件 Email", "AirDrop", "钉钉 DingTalk",
               "企业微信 WeCom", "飞书 Feishu", "USB 拷贝", "其他"]

    def __init__(self, parent, path, journal, cb):
        self.j = journal
        self.fp = path
        self.cb = cb
        self.top = ctk.CTkToplevel(parent)
        self.top.title("📤 记录发送")
        self.top.geometry("420x320")
        self.top.resizable(False, False)
        self.top.configure(fg_color=COLOR_GLASS_BG)

        ctk.CTkLabel(self.top, text=f"📄 {Path(path).name}",
                     font=FONT_SECTION, text_color=COLOR_TEXT
                     ).pack(padx=20, pady=(16, 12), anchor="w")

        ctk.CTkLabel(self.top, text="接收人 *", font=FONT_BODY,
                     text_color=COLOR_TEXT
                     ).pack(padx=20, pady=(4, 2), anchor="w")
        self.r = ctk.CTkEntry(self.top, font=FONT_BODY, height=34,
                              fg_color="#f0ede8", border_width=0,
                              corner_radius=6)
        self.r.pack(padx=20, fill="x")

        ctk.CTkLabel(self.top, text="发送方式", font=FONT_BODY,
                     text_color=COLOR_TEXT
                     ).pack(padx=20, pady=(8, 2), anchor="w")
        self.m = ctk.CTkComboBox(self.top, values=self.METHODS,
                                 font=FONT_BODY, height=34,
                                 fg_color="#f0ede8", border_width=0,
                                 corner_radius=6)
        self.m.set("微信 WeChat")
        self.m.pack(padx=20, fill="x")

        bf = ctk.CTkFrame(self.top, fg_color="transparent")
        bf.pack(padx=20, pady=(18, 14), fill="x")
        ctk.CTkButton(bf, text="取消", command=self.top.destroy,
                      fg_color="transparent",
                      text_color=COLOR_MUTED,
                      height=36, corner_radius=8,
                      border_width=1, border_color=COLOR_TEXTURE_2,
                      font=FONT_BODY
                      ).pack(side="left")
        ctk.CTkButton(bf, text="✅ 保存", command=self._save,
                      fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_DARK,
                      height=36, corner_radius=8,
                      text_color="white", font=("", 13, "bold")
                      ).pack(side="right")

    def _save(self):
        r = self.r.get().strip()
        if not r:
            messagebox.showwarning("提示", "请填写接收人", parent=self.top)
            return
        self.j.add_record(self.fp, Path(self.fp).name,
                          r, self.m.get(), "")
        self.cb()
        self.top.destroy()


def main():
    ctk.set_appearance_mode("light")
    app = FileBrainApp()
    app.run()


if __name__ == "__main__":
    main()
