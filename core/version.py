"""版本管理器 —— 根据文件修改时间分配版本号

策略：
- 首次遇到文件 → v1.0
- 文件修改时间更新 → v1.1, v1.2 ...
- 跨天 → v2.0, v3.0 ...
"""

import json
import os
import time
import logging
from datetime import datetime
from pathlib import Path

from config import STATE_DIR_NAME, VERSION_INCREMENT_MINUTES

logger = logging.getLogger(__name__)

# 状态文件（存放在监控目录的 .filebrain/ 下）
STATE_FILE = "version_state.json"


class VersionManager:
    """版本管理器"""

    def __init__(self, watch_dir: str):
        self.watch_dir = Path(watch_dir)
        self.state_dir = self.watch_dir / STATE_DIR_NAME
        self.state_file = self.state_dir / STATE_FILE
        self._state: dict = {}
        self._load_state()

    def _ensure_state_dir(self):
        """确保 .filebrain/ 目录存在"""
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _load_state(self):
        """加载持久化的状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    self._state = json.load(f)
            except Exception as e:
                logger.warning(f"读取版本状态失败: {e}")
                self._state = {}
        else:
            self._state = {}

    def _save_state(self):
        """持久化状态"""
        self._ensure_state_dir()
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self._state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存版本状态失败: {e}")

    def get_version(self, file_path: str) -> str:
        """
        根据文件路径和修改时间，计算版本号

        首次遇到返回空字符串（不加版本号），
        文件修改后才开始标 v1.0、v1.1...

        返回格式: "" | "v1.0" | "v1.1"
        """
        path = Path(file_path)
        if not path.exists():
            return ""

        mtime = path.stat().st_mtime
        mtime_dt = datetime.fromtimestamp(mtime)
        date_key = mtime_dt.strftime("%Y%m%d")
        abs_path = str(path.absolute())

        record = self._state.get(abs_path)

        if record is None:
            # 首次遇到 —— 记录状态但不标版本号
            self._state[abs_path] = {
                "major": 0,
                "minor": 0,
                "version_count": 0,      # 记录修改次数
                "last_mtime": mtime,
                "last_date": date_key,
            }
            self._save_state()
            return ""

        last_mtime = record.get("last_mtime", 0)
        last_date = record.get("last_date", date_key)
        version_count = record.get("version_count", 0)

        # 判断是否修改
        if abs(mtime - last_mtime) < 1:
            # 时间没变
            if version_count == 0:
                return ""
            major = record.get("major", 0)
            minor = record.get("minor", 0)
            return f"v{major}.{minor}"

        # 文件有修改，开始计算版本号
        version_count += 1
        time_diff_minutes = abs(mtime - last_mtime) / 60

        if date_key != last_date:
            # 跨天 → 大版本+1
            major = (version_count + 1) // 2
            minor = 0
        elif time_diff_minutes > VERSION_INCREMENT_MINUTES:
            # 超过间隔 → 次版本+1
            major = (version_count + 1) // 2
            minor = (version_count - 1) % 2
        else:
            # 短时间内多次修改 → 次版本
            major = (version_count + 1) // 2
            minor = (version_count - 1) % 2

        # 更新记录
        self._state[abs_path] = {
            "major": major,
            "minor": minor,
            "version_count": version_count,
            "last_mtime": mtime,
            "last_date": date_key,
        }
        self._save_state()
        self._save_state()
        return f"v{major}.{minor}"

    def skip_file(self, file_path: str):
        """标记文件已处理（但不需要版本追踪）"""
        abs_path = str(Path(file_path).absolute())
        if abs_path not in self._state:
            self._state[abs_path] = {
                "major": 0,
                "minor": 0,
                "last_mtime": 0,
                "last_date": "",
            }
            self._save_state()

    def delete_record(self, file_path: str):
        """删除文件的状态记录（文件被删除时调用）"""
        abs_path = str(Path(file_path).absolute())
        if abs_path in self._state:
            del self._state[abs_path]
            self._save_state()

    def cleanup_missing(self):
        """清理已不存在的文件记录"""
        to_delete = []
        for abs_path in self._state:
            if not Path(abs_path).exists():
                to_delete.append(abs_path)
        for p in to_delete:
            del self._state[p]
        if to_delete:
            self._save_state()
