"""目录监控器 —— 监视文件夹变化，自动提取内容并重命名"""

import os
import time
import logging
from pathlib import Path
from threading import Event

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

logger = logging.getLogger(__name__)


class FileBrainHandler(FileSystemEventHandler):
    """文件系统事件处理器"""

    def __init__(self, watch_dir: str,
                 version_mgr: VersionManager,
                 search_index: SearchIndex,
                 on_processed=None):
        self.watch_dir = Path(watch_dir)
        self.version_mgr = version_mgr
        self.search_index = search_index
        self.on_processed = on_processed  # 回调函数
        self._pending = set()             # 去重
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

        # 去重
        if file_path in self._pending:
            return
        self._pending.add(file_path)

        try:
            # 等待文件写入完成
            time.sleep(FILE_WRITE_WAIT_SECONDS)
            self._process_file(file_path)
        finally:
            self._pending.discard(file_path)

    def _process_file(self, file_path: str):
        """处理单个文件：提取 → 命名 → 版本 → 重命名 → 索引"""
        path = Path(file_path)
        ext = path.suffix.lower()

        if not path.exists():
            return

        logger.info(f"检测到文件: {path.name}")

        # 1. 获取合适的提取器
        extractor_cls = EXTRACTORS.get(ext)
        if not extractor_cls:
            return

        # 提取之前重命名，记录旧文件名
        old_full_path = str(path.absolute())
        old_name = path.name

        # 2. 提取内容
        extractor = extractor_cls()
        extracted = extractor.extract(file_path)

        if not extracted.get("success"):
            logger.warning(f"内容提取失败: {old_name} - "
                           f"{extracted.get('error', '未知错误')}")
            if self.on_processed:
                self.on_processed("提取失败", old_name, "", "", "")
            return

        # 3. 获取版本号
        version_str = self.version_mgr.get_version(file_path)

        # 4. 获取日期
        mtime = path.stat().st_mtime
        date_str = time.strftime("%Y%m%d",
                                 time.localtime(mtime))

        # 5. 生成新文件名
        new_name = build_new_filename(old_name, extracted,
                                      version_str, date_str)

        # 如果新旧文件名一样则跳过
        if new_name == old_name:
            logger.info(f"文件名无需变更: {old_name}")
        else:
            # 6. 执行重命名
            new_path = path.parent / new_name
            try:
                # 如果目标文件已存在，加时间戳避免覆盖
                if new_path.exists():
                    stem = Path(new_name).stem
                    ts = time.strftime("%H%M%S")
                    new_name = f"{stem}_{ts}{ext}"
                    new_path = path.parent / new_name

                path.rename(new_path)
                logger.info(f"重命名: {old_name} → {new_name}")
            except Exception as e:
                logger.error(f"重命名失败: {e}")
                if self.on_processed:
                    self.on_processed("重命名失败", old_name,
                                      new_name, version_str, date_str)
                return

        final_name = new_name
        final_path = str((path.parent / final_name).absolute())

        # 7. 加入搜索索引（用最终的文件名）
        self.search_index.add(
            final_path, final_name, extracted
        )

        # 8. 回调通知 GUI
        if self.on_processed:
            self.on_processed("已完成", old_name, final_name,
                              version_str, date_str)

    def scan_existing(self):
        """扫描目录中已有的文件"""
        logger.info("扫描已有文件...")
        for ext in SUPPORTED_EXTENSIONS:
            for f in self.watch_dir.glob(f"*{ext}"):
                self._handle_file(str(f))
            for f in self.watch_dir.glob(f"*{ext.upper()}"):
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
