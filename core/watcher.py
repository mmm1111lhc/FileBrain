"""目录监控器 —— 监视文件夹变化，自动提取内容并重命名"""

import os
import time
import logging
from pathlib import Path
from threading import Event
from collections import deque

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from config import (
    SUPPORTED_EXTENSIONS,
    FILE_WRITE_WAIT_SECONDS,
    WATCHER_INTERVAL,
)
from core.extractors import EXTRACTORS
from core.namer import build_new_filename
from core.version import VersionManager
from core.search_index import SearchIndex
from core.pending import PendingQueue
from core.journal import SendJournal

logger = logging.getLogger(__name__)


class FileBrainHandler(FileSystemEventHandler):
    """文件系统事件处理器"""

    def __init__(self, watch_dir: str,
                 version_mgr: VersionManager,
                 search_index: SearchIndex,
                 pending_queue: PendingQueue = None,
                 on_processed=None,
                 auto_mode: bool = True):
        self.watch_dir = Path(watch_dir)
        self.version_mgr = version_mgr
        self.search_index = search_index
        self.pending_queue = pending_queue or PendingQueue()
        self.on_processed = on_processed  # 回调函数
        self.auto_mode = auto_mode        # True=自动处理, False=用户确认
        self._dedup = set()               # 去重
        self._dedup_max = 500             # 去重上限，防内存泄漏
        self._observer = None

    def on_created(self, event):
        if event.is_directory:
            return
        self._handle_file(event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return
        self._handle_file(event.src_path)

    def on_moved(self, event):
        if event.is_directory:
            return
        self._handle_file(event.dest_path)

    def _handle_file(self, file_path: str):
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext not in SUPPORTED_EXTENSIONS:
            return

        # 去重 + 防内存泄漏
        if file_path in self._dedup:
            return
        if len(self._dedup) > self._dedup_max:
            self._dedup.clear()
        self._dedup.add(file_path)

        try:
            # 等待文件写入完成
            time.sleep(FILE_WRITE_WAIT_SECONDS)
            if not path.exists():
                return
            self._process_or_queue(file_path)
        finally:
            self._dedup.discard(file_path)

    def _process_or_queue(self, file_path: str):
        """提取内容，然后根据模式决定是自动处理还是加入待处理队列"""
        path = Path(file_path)
        ext = path.suffix.lower()

        extractor_cls = EXTRACTORS.get(ext)
        if not extractor_cls:
            return

        extractor = extractor_cls()
        extracted = extractor.extract(file_path)

        if not extracted.get("success"):
            logger.warning(f"内容提取失败: {path.name}")
            return

        if self.auto_mode:
            # 自动模式：直接处理
            self._process_file(file_path, extracted)
        else:
            # 交互模式：加入待处理队列
            self.pending_queue.add(file_path, extracted)
            logger.info(f"已加入待处理: {path.name}")
            if self.on_processed:
                self.on_processed("待处理", path.name, "", "", "")
            else:
                # 没有 GUI 回调时，打印提示
                print(f"\n📋 待处理: {path.name}")

    def _process_file(self, file_path: str, extracted: dict = None,
                      user_version: str = ""):
        """处理单个文件：命名 → 版本 → 重命名 → 索引

        Args:
            file_path: 文件路径
            extracted: 已提取的内容（如果为 None 则重新提取）
            user_version: 用户手动指定的版本标签（如 "v1", "v2"）
        """
        path = Path(file_path)
        ext = path.suffix.lower()

        if not path.exists():
            return

        logger.info(f"处理文件: {path.name}")

        old_full_path = str(path.absolute())
        old_name = path.name

        # 提取内容（如未提供）
        if extracted is None:
            extractor_cls = EXTRACTORS.get(ext)
            if not extractor_cls:
                return
            extractor = extractor_cls()
            extracted = extractor.extract(file_path)

        if not extracted.get("success"):
            logger.warning(f"内容提取失败: {old_name} - "
                           f"{extracted.get('error', '未知错误')}")
            if self.on_processed:
                self.on_processed("提取失败", old_name, "", "", "")
            return

        # 获取版本号（用户指定优先）
        if user_version:
            version_str = user_version
        else:
            version_str = self.version_mgr.get_version(file_path)

        # 4. 获取日期
        mtime = path.stat().st_mtime
        date_str = time.strftime("%Y%m%d",
                                 time.localtime(mtime))

        # 5. 生成新文件名
        new_name = build_new_filename(old_name, extracted,
                                      version_str, date_str)

        # 6. 归类到子文件夹
        category_dir = self._get_category_dir(ext)
        target_dir = path.parent / category_dir if category_dir else path.parent
        target_dir.mkdir(exist_ok=True)

        # 如果文件名不变且已在正确文件夹，跳过
        already_categorized = (
            new_name == old_name
            and path.parent == target_dir
        )
        if already_categorized:
            final_name = new_name
            final_path = str(path.absolute())
        else:
            new_path = target_dir / new_name
            try:
                # 如果目标文件已存在，加时间戳避免覆盖
                if new_path.exists():
                    stem = Path(new_name).stem
                    ts = time.strftime("%H%M%S")
                    new_name = f"{stem}_{ts}{ext}"
                    new_path = target_dir / new_name

                path.rename(new_path)
                location = f"{category_dir}/" if category_dir else ""
                logger.info(f"→ {location}{new_name}")
            except Exception as e:
                logger.error(f"处理失败: {e}")
                if self.on_processed:
                    self.on_processed("处理失败", old_name,
                                      new_name, version_str, date_str)
                return
            final_name = new_name
            final_path = str(new_path.absolute())

        # 7. 加入搜索索引（用最终的文件名）
        self.search_index.add(
            final_path, final_name, extracted
        )

        # 8. 回调通知 GUI
        if self.on_processed:
            self.on_processed("已完成", old_name, final_name,
                              version_str, date_str)

    def process_pending_file(self, file_path: str,
                              version_label: str = ""):
        """处理一个待队列中的文件"""
        pending = self.pending_queue.approve(file_path, version_label)
        if not pending:
            logger.warning(f"待处理文件不存在: {file_path}")
            return False

        self._process_file(file_path, pending.extracted,
                           user_version=version_label)
        self.pending_queue.remove_processed(file_path)
        return True

    def process_all_pending(self, version_label: str = ""):
        """处理所有待处理文件"""
        pending_items = self.pending_queue.get_pending()
        for item in pending_items:
            self.process_pending_file(item.file_path, version_label)

    def _get_category_dir(self, ext: str) -> str:
        """根据文件扩展名返回归类文件夹名称（不用 emoji 保证跨平台兼容）"""
        pdf_exts = {".pdf"}
        word_exts = {".doc", ".docx"}
        excel_exts = {".xls", ".xlsx"}
        image_exts = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}

        if ext in pdf_exts:
            return "PDF文档"
        elif ext in word_exts:
            return "Word文档"
        elif ext in excel_exts:
            return "Excel表格"
        elif ext in image_exts:
            return "图片"
        return ""

    def scan_existing(self):
        """扫描目录中已有的文件（含子目录）"""
        logger.info("扫描已有文件...")
        for ext in SUPPORTED_EXTENSIONS:
            for f in self.watch_dir.rglob(f"*{ext}"):
                if f.is_file():
                    self._handle_file(str(f))
        # 也处理大写扩展名
        for ext in list(SUPPORTED_EXTENSIONS):
            upper_ext = ext.upper()
            if upper_ext != ext:
                for f in self.watch_dir.rglob(f"*{upper_ext}"):
                    if f.is_file():
                        self._handle_file(str(f))
        logger.info("已有文件扫描完成")


class Watcher:
    """目录监控器"""

    def __init__(self, watch_dir: str,
                 on_processed=None):
        self.watch_dir = watch_dir
        self.version_mgr = VersionManager(watch_dir)
        self.search_index = SearchIndex(watch_dir)
        self.handler = FileBrainHandler(
            watch_dir, self.version_mgr,
            self.search_index, on_processed
        )
        self.send_journal = SendJournal(watch_dir)
        self._observer = Observer()
        self._running = False

    def start(self):
        """开始监控"""
        if self._running:
            return

        # 先扫描已有文件
        self.handler.scan_existing()

        # 启动监控
        self._observer.schedule(
            self.handler, self.watch_dir, recursive=False
        )
        self._observer.start()
        self._running = True
        logger.info(f"FileBrain 已开始监控: {self.watch_dir}")

    def stop(self):
        """停止监控"""
        if not self._running:
            return
        self._observer.stop()
        self._observer.join()
        self._running = False
        logger.info("FileBrain 已停止监控")

    def is_running(self) -> bool:
        return self._running
