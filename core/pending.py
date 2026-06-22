"""待处理队列 —— 文件检测后先进入队列，用户确认后再处理"""

import time
import threading
from pathlib import Path
from typing import Callable, Optional


class PendingFile:
    """一个待用户确认的文件"""

    def __init__(self, file_path: str, extracted: dict):
        self.file_path = file_path
        self.file_name = Path(file_path).name
        self.ext = Path(file_path).suffix.lower()
        self.extracted = extracted
        self.detected_at = time.time()
        self.status = "pending"  # pending | approved | skipped
        self.user_version = ""   # 用户选择的版本号
        self.summary = extracted.get("title", "") or Path(file_path).stem

    @property
    def time_str(self) -> str:
        return time.strftime("%H:%M:%S", time.localtime(self.detected_at))


class PendingQueue:
    """待处理队列"""

    def __init__(self, on_updated: Optional[Callable] = None):
        self._items: list[PendingFile] = []
        self._lock = threading.Lock()
        self.on_updated = on_updated  # 队列变化时通知 GUI

    def add(self, file_path: str, extracted: dict) -> PendingFile:
        """将文件加入待处理队列"""
        pf = PendingFile(file_path, extracted)
        with self._lock:
            # 去重：相同路径替换
            self._items = [i for i in self._items
                           if i.file_path != file_path]
            self._items.append(pf)
        if self.on_updated:
            self.on_updated()
        return pf

    def approve(self, file_path: str, version_label: str = "") -> Optional[PendingFile]:
        """标记文件为已批准，可指定版本标签"""
        with self._lock:
            for item in self._items:
                if item.file_path == file_path and item.status == "pending":
                    item.status = "approved"
                    item.user_version = version_label
                    return item
        if self.on_updated:
            self.on_updated()
        return None

    def skip(self, file_path: str) -> bool:
        """标记文件为跳过"""
        with self._lock:
            for item in self._items:
                if item.file_path == file_path and item.status == "pending":
                    item.status = "skipped"
                    return True
        if self.on_updated:
            self.on_updated()
        return False

    def approve_all(self, version_label: str = ""):
        """全部批准"""
        with self._lock:
            for item in self._items:
                if item.status == "pending":
                    item.status = "approved"
                    item.user_version = version_label
        if self.on_updated:
            self.on_updated()

    def get_pending(self) -> list[PendingFile]:
        """获取所有待处理文件"""
        with self._lock:
            return [i for i in self._items if i.status == "pending"]

    def get_approved(self) -> list[PendingFile]:
        """获取已批准但尚未处理完的文件"""
        with self._lock:
            return [i for i in self._items if i.status == "approved"]

    def remove_processed(self, file_path: str):
        """处理完成后从队列移除"""
        with self._lock:
            self._items = [i for i in self._items
                           if i.file_path != file_path]
        if self.on_updated:
            self.on_updated()

    def count(self) -> int:
        with self._lock:
            return sum(1 for i in self._items if i.status == "pending")

    def clear(self):
        with self._lock:
            self._items.clear()
        if self.on_updated:
            self.on_updated()
