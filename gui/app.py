"""FileBrain 图形界面 —— CustomTkinter 现代UI"""

import os
import time
import threading
import logging
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

# ── 主题 ──
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("dark-blue")

COLOR_ACCENT = "#c97a3a"
COLOR_BG = "#f5f2ed"
COLOR_CARD = "#ffffff"
COLOR_SUCCESS = "#5a8f5a"
COLOR_ERROR = "#b85450"
COLOR_MUTED = "#888888"

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("FileBrain")


class FileBrainApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("FileBrain · 文件大脑")
        self.root.geometry("860x660")
        self.root.minsize(720, 520)
        self.root.configure(fg_color=COLOR_BG)

        self.watcher = None
        self.watch_dir = ctk.StringVar(value=os.path.expanduser("~/Desktop"))
        self.selected_file_path = ""

        self.tab = ctk.CTkTabview(self.root, fg_color=COLOR_BG)
        self.tab.pack(fill="both", expand=True, padx=10, pady=10)

        t1 = self.tab.add("📁 自动整理")
        self._build_organize(t1)

        t2 = self.tab.add("🔍 全文检索")
        self._build_search(t2)

        t3 = self.tab.add("📤 发送留痕")
        self._build_journal(t3)

        t4 = self.tab.add("⚙️ 设置")
        self._build_settings(t4)

        
        # 设置图标
        try:
            from PIL import Image, ImageTk
            img = Image.open("images/app_icon.png")
            self.root.iconphoto(True, ImageTk.PhotoImage(img))
        except Exception:
            pass

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ═══════════════ 自动整理 ═══════════════

    def _build_organize(self, f):
        f.grid_columnconfigure(0, weight=1)
        f.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(f, text="🧠 FileBrain",
                     font=("PingFang SC", 22, "bold"),
                     text_color=COLOR_ACCENT
                     ).grid(row=0, column=0, sticky="w", pady=(4, 0))
        ctk.CTkLabel(f, text="文件扔桌面，自动整理好",
                     font=("", 13), text_color=COLOR_MUTED
                     ).grid(row=1, column=0, sticky="w", pady=(0, 6))

        # 路径
        p = ctk.CTkFrame(f, fg_color=COLOR_CARD, corner_radius=8)
        p.grid(row=2, column=0, sticky="ew", pady=2)
        p.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(p, text="📂 管理文件夹",
                     font=("", 13)).grid(row=0, column=0, padx=(12, 4), pady=8)
        e = ctk.CTkEntry(p, textvariable=self.watch_dir,
                         font=("", 13), height=32,
                         fg_color="#f0ede8", border_width=0)
        e.grid(row=0, column=1, sticky="ew", padx=4, pady=8)
        ctk.CTkButton(p, text="选择",
                      command=self._select_dir,
                      fg_color="#2c2c2c", hover_color="#000000",
                      height=32, width=60, corner_radius=6
                      ).grid(row=0, column=2, padx=(4, 12), pady=8)

        # 按钮
        b = ctk.CTkFrame(f, fg_color="transparent")
        b.grid(row=3, column=0, sticky="ew", pady=4)
        b.grid_columnconfigure(2, weight=1)
        self.btn_start = ctk.CTkButton(b, text="▶ 开始整理", text_color='white',
                                       font=("", 14, "bold"),
                                       height=38, width=140,
                                       command=self._toggle_monitor,
                                       fg_color="#2c2c2c",
                                       hover_color="#4a7a4a", corner_radius=8)
        self.btn_start.grid(row=0, column=0, sticky="w")
        ctk.CTkButton(b, text="🔄 扫描现有文件",
                      command=self._scan_existing,
                      fg_color="#2c2c2c", hover_color="#000000",
                      height=38, width=120, corner_radius=8
                      ).grid(row=0, column=1, padx=(8, 0))
        self.status_label = ctk.CTkLabel(b, text="⏸ 未开始",
                                         font=("", 12), text_color=COLOR_MUTED)
        self.status_label.grid(row=0, column=2, sticky="e", padx=(12, 0))

        # 类型
        t = ctk.CTkFrame(f, fg_color="transparent")
        t.grid(row=4, column=0, sticky="ew", pady=2)
        ctk.CTkLabel(t, text="识别类型：",
                     font=("", 12)).grid(row=0, column=0)
        self.pdf = ctk.BooleanVar(value=True)
        self.word = ctk.BooleanVar(value=True)
        self.excel = ctk.BooleanVar(value=True)
        self.img = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(t, text="PDF (含扫描件)",
                        variable=self.pdf).grid(row=0, column=1, padx=4)
        ctk.CTkCheckBox(t, text="Word",
                        variable=self.word).grid(row=0, column=2, padx=4)
        ctk.CTkCheckBox(t, text="Excel",
                        variable=self.excel).grid(row=0, column=3, padx=4)
        ctk.CTkCheckBox(t, text="图片 (OCR)",
                        variable=self.img).grid(row=0, column=4, padx=4)

        # 日志
        ctk.CTkLabel(f, text="📋 活动日志",
                     font=("", 12, "bold")
                     ).grid(row=5, column=0, sticky="nw", pady=(8, 2))
        self.log = ctk.CTkTextbox(f, font=("Menlo", 11),
                                  fg_color=COLOR_CARD, corner_radius=8,
                                  height=160)
        self.log.grid(row=6, column=0, sticky="nsew", pady=(0, 4))

    # ═══════════════ 全文检索 ═══════════════

    def _build_search(self, f):
        f.grid_columnconfigure(0, weight=1)
        f.grid_rowconfigure(2, weight=1)

        bar = ctk.CTkFrame(f, fg_color=COLOR_CARD, corner_radius=8)
        bar.grid(row=0, column=0, sticky="ew", pady=(4, 6))
        bar.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(bar, text="🔍 搜索",
                     font=("", 15, "bold")
                     ).grid(row=0, column=0, padx=(12, 4), pady=8)
        self.se = ctk.CTkEntry(bar, font=("", 13), height=34,
                               fg_color="#f0ede8", border_width=0)
        self.se.grid(row=0, column=1, sticky="ew", padx=4, pady=8)
        self.se.bind("<Return>", lambda e: self._do_search())
        ctk.CTkButton(bar, text="搜索",
                      command=self._do_search,
                      fg_color="#2c2c2c", hover_color="#000000",
                      height=34, width=80, corner_radius=6
                      ).grid(row=0, column=2, padx=(4, 12), pady=8)

        self.sc = ctk.CTkLabel(f, text="", font=("", 12), text_color=COLOR_MUTED)
        self.sc.grid(row=1, column=0, sticky="w")

        rf = ctk.CTkFrame(f, fg_color=COLOR_CARD, corner_radius=8)
        rf.grid(row=2, column=0, sticky="nsew")
        rf.grid_columnconfigure(0, weight=1)
        rf.grid_rowconfigure(0, weight=1)
        self.rl = ctk.CTkScrollableFrame(rf, fg_color="transparent",
                                          corner_radius=0)
        self.rl.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        ab = ctk.CTkFrame(f, fg_color="transparent")
        ab.grid(row=3, column=0, sticky="ew", pady=4)
        ab.grid_columnconfigure(2, weight=1)
        ctk.CTkButton(ab, text="📂 打开文件位置",
                      command=self._open_file,
                      fg_color="#2c2c2c", hover_color="#000000",
                      height=34, corner_radius=6
                      ).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(ab, text="📤 记录发送",
                      command=self._send_dialog,
                      fg_color="#2c2c2c", hover_color="#000000",
                      height=34, corner_radius=6
                      ).grid(row=0, column=1, padx=(6, 0))
        self.sp = ctk.CTkLabel(ab, text="", font=("", 11), text_color=COLOR_MUTED)
        self.sp.grid(row=0, column=2, sticky="e")

    # ═══════════════ 发送留痕 ═══════════════

    def _build_journal(self, f):
        f.grid_columnconfigure(0, weight=1)
        f.grid_rowconfigure(2, weight=1)

        bar = ctk.CTkFrame(f, fg_color=COLOR_CARD, corner_radius=8)
        bar.grid(row=0, column=0, sticky="ew", pady=(4, 6))
        bar.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(bar, text="📤 发送留痕",
                     font=("", 15, "bold")
                     ).grid(row=0, column=0, padx=(12, 4), pady=8)
        self.je = ctk.CTkEntry(bar, font=("", 13), height=34,
                               fg_color="#f0ede8", border_width=0)
        self.je.grid(row=0, column=1, sticky="ew", padx=4, pady=8)
        self.je.bind("<Return>", lambda e: self._j_search())
        ctk.CTkButton(bar, text="搜索",
                      command=self._j_search,
                      fg_color="#2c2c2c", hover_color="#000000",
                      height=34, width=80, corner_radius=6
                      ).grid(row=0, column=2, padx=(4, 12), pady=8)

        jf = ctk.CTkFrame(f, fg_color=COLOR_CARD, corner_radius=8)
        jf.grid(row=2, column=0, sticky="nsew")
        jf.grid_columnconfigure(0, weight=1)
        jf.grid_rowconfigure(0, weight=1)
        self.jl = ctk.CTkScrollableFrame(jf, fg_color="transparent",
                                          corner_radius=0)
        self.jl.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        ab = ctk.CTkFrame(f, fg_color="transparent")
        ab.grid(row=3, column=0, sticky="ew", pady=4)
        ctk.CTkButton(ab, text="🔄 刷新",
                      command=self._j_refresh,
                      fg_color="#2c2c2c", hover_color="#000000",
                      height=34, corner_radius=6
                      ).grid(row=0, column=0, sticky="w")

    # ═══════════════ 设置 ═══════════════

    def _build_settings(self, f):
        f.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(f, text="⚙️ 设置",
                     font=("PingFang SC", 18, "bold")
                     ).grid(row=0, column=0, sticky="w", pady=(8, 12))

        c1 = ctk.CTkFrame(f, fg_color=COLOR_CARD, corner_radius=10)
        c1.grid(row=1, column=0, sticky="ew", pady=4)
        ctk.CTkLabel(c1, text="智能命名",
                     font=("", 14, "bold")
                     ).pack(anchor="w", padx=16, pady=(12, 4))
        self.ar = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(c1, text="自动重命名文件（内容摘要 · 日期 · 作者）",
                        variable=self.ar, font=("", 13)
                        ).pack(anchor="w", padx=16, pady=2)
        self.av = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(c1, text="文件修改后自动标注版本号 (v1.0)",
                        variable=self.av, font=("", 13)
                        ).pack(anchor="w", padx=16, pady=2)
        ctk.CTkLabel(c1, text="格式: 内容摘要 · 2026.06.22 · 作者 · v1.0.pdf",
                     font=("Menlo", 11), text_color=COLOR_MUTED
                     ).pack(anchor="w", padx=16, pady=(4, 12))

        s = ctk.CTkFrame(f, fg_color="#e8d5c0", corner_radius=10,
                         border_width=1, border_color=COLOR_ACCENT)
        s.grid(row=2, column=0, sticky="ew", pady=(12, 4))
        ctk.CTkLabel(s, text="⬇ 免费开源 · 欢迎下载 ⬇",
                     font=("", 15, "bold"), text_color=COLOR_ACCENT
                     ).pack(pady=(10, 2))
        ctk.CTkLabel(s, text="github.com/mmm1111lhc/FileBrain",
                     font=("Menlo", 12), text_color=COLOR_ACCENT
                     ).pack(pady=(0, 10))

        c2 = ctk.CTkFrame(f, fg_color=COLOR_CARD, corner_radius=10)
        c2.grid(row=3, column=0, sticky="ew", pady=4)
        ctk.CTkLabel(c2, text="关于", font=("", 14, "bold")
                     ).pack(anchor="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(c2,
                     text=("FileBrain · 文件大脑 v1.0\n\n"
                           "🔒 纯本地 · 不过云\n"
                           "所有文件在本地处理，数据不上传云端\n\n"
                           "📄 支持 PDF(含OCR) · Word · Excel · 图片"),
                     font=("", 12), justify="left"
                     ).pack(anchor="w", padx=16, pady=(0, 12))

    # ═══════════════ 核心逻辑 ═══════════════

    def _select_dir(self):
        d = filedialog.askdirectory(initialdir=self.watch_dir.get())
        if d:
            self.watch_dir.set(d)

    def _toggle_monitor(self):
        from core.watcher import Watcher
        if self.watcher and self.watcher.is_running():
            threading.Thread(target=self.watcher.stop, daemon=True).start()
            self.watcher = None
            self.btn_start.configure(text="▶ 开始整理", text_color='white', fg_color=COLOR_SUCCESS)
            self.status_label.configure(text="⏸ 已暂停")
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
        self.watcher.start()
        self.root.after(0, self._started)

    def _started(self):
        self.btn_start.configure(text="⏹ 停止整理", fg_color="#b85450")
        self.status_label.configure(text="🟢 整理中")

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
                             corner_radius=6, height=38)
            c.pack(fill="x", pady=2)
            fn = ctk.CTkLabel(c, text=f"📄 {r.get('new_name', r.get('file_name',''))}",
                              font=("", 12), anchor="w")
            fn.pack(side="left", padx=8)
            cx = r.get("context", "")[:40]
            ctk.CTkLabel(c, text=cx, font=("", 11),
                         text_color=COLOR_MUTED).pack(side="left", padx=4)
            ctk.CTkLabel(c, text=f"相关度 {r.get('score',0)}",
                         font=("", 11), text_color=COLOR_MUTED,
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
                             corner_radius=6, height=36)
            c.pack(fill="x", pady=2)
            ctk.CTkLabel(c, text=r.get("sent_at_str",""),
                         font=("Menlo", 11), width=110, anchor="w"
                         ).pack(side="left", padx=6)
            ctk.CTkLabel(c, text=Path(r.get("file_name","")).name,
                         font=("", 12)).pack(side="left", padx=4, fill="x", expand=True)
            ctk.CTkLabel(c, text=f"→ {r.get('recipient','')}",
                         font=("", 12), text_color=COLOR_ACCENT
                         ).pack(side="left", padx=4)
            ctk.CTkLabel(c, text=f"({r.get('method','')})",
                         font=("", 11), text_color=COLOR_MUTED
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
        self.top.geometry("400x300")
        self.top.resizable(False, False)

        ctk.CTkLabel(self.top, text=f"文件: {Path(path).name}",
                     font=("", 13), wraplength=380
                     ).pack(padx=16, pady=(14, 6), anchor="w")

        ctk.CTkLabel(self.top, text="接收人 *", font=("", 12)
                     ).pack(padx=16, pady=(6, 2), anchor="w")
        self.r = ctk.CTkEntry(self.top, font=("", 13), height=32,
                              fg_color="#f0ede8", border_width=0)
        self.r.pack(padx=16, fill="x")

        ctk.CTkLabel(self.top, text="发送方式", font=("", 12)
                     ).pack(padx=16, pady=(6, 2), anchor="w")
        self.m = ctk.CTkComboBox(self.top, values=self.METHODS,
                                  font=("", 13), height=32,
                                  fg_color="#f0ede8", border_width=0)
        self.m.set("微信 WeChat")
        self.m.pack(padx=16, fill="x")

        bf = ctk.CTkFrame(self.top, fg_color="transparent")
        bf.pack(padx=16, pady=(14, 12), fill="x")
        ctk.CTkButton(bf, text="取消", command=self.top.destroy,
                      fg_color="#2c2c2c", hover_color="#000000",
                      height=34, corner_radius=6
                      ).pack(side="left")
        ctk.CTkButton(bf, text="✅ 保存", command=self._save,
                      fg_color="#2c2c2c", hover_color="#000000",
                      height=34, corner_radius=6
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
