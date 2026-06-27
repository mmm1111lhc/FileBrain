"""全文检索索引 —— 对所有扫描过的文件建立内容索引，支持快速搜索"""

import json
import logging
import re
from pathlib import Path

from config import STATE_DIR_NAME

logger = logging.getLogger(__name__)

INDEX_FILE = "search_index.json"


class SearchIndex:
    """文件内容全文检索索引"""

    def __init__(self, watch_dir: str):
        self.watch_dir = Path(watch_dir)
        self.state_dir = self.watch_dir / STATE_DIR_NAME
        self.index_file = self.state_dir / INDEX_FILE
        self._index: list[dict] = []
        self._load()

    def _ensure_dir(self):
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _load(self):
        if self.index_file.exists():
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    self._index = json.load(f)
            except Exception as e:
                logger.warning(f"读取搜索索引失败: {e}")
                self._index = []
        else:
            self._index = []

    def _save(self):
        self._ensure_dir()
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(self._index, f,
                          ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存搜索索引失败: {e}")

    def add(self, file_path: str, new_name: str, extracted: dict):
        """将文件内容加入索引（自动修复OCR中文间空格）"""
        path = Path(file_path)
        abs_path = str(path.absolute())

        # 删除旧记录（如果有）
        self._index = [r for r in self._index
                       if r.get("path") != abs_path]

        # 修复OCR中文间空格："年 创 收" → "年创收"
        def fix_cn_spaces(t):
            return re.sub(r"([\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", r"\1", t)
        raw_text = extracted.get("text", "")
        raw_title = extracted.get("title", "")
        fixed_text = fix_cn_spaces(raw_text)
        fixed_title = fix_cn_spaces(raw_title)

        entry = {
            "path": abs_path,
            "file_name": path.name,
            "new_name": new_name,
            "extracted_title": fixed_title,
            "text_snippet": fixed_text[:200],
            "full_text_hash": hash(fixed_text),
            "indexed_at": __import__("time").time(),
        }
        self._index.append(entry)
        self._save()

    def remove(self, file_path: str):
        """从索引中移除文件"""
        abs_path = str(Path(file_path).absolute())
        self._index = [r for r in self._index
                       if r.get("path") != abs_path]
        self._save()

    def search(self, query: str, max_results: int = 30) -> list[dict]:
        """
        全文检索，返回匹配的文件列表

        返回 [{path, file_name, new_name, title, snippet, score}]
        """
        if not query.strip():
            return []

        query_lower = query.lower()
        # 同时搜索"年创收"和"年 创 收"（兼容OCR空格问题）
        query_flex = re.sub(r"([\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", r"\1", query_lower)
        query_spaced = re.sub(r"(?<=[\u4e00-\u9fff])(?=[\u4e00-\u9fff])", " ", query_lower)
        results = []

        for entry in self._index:
            score = 0
            title = entry.get("extracted_title", "")
            snippet = entry.get("text_snippet", "")
            fname = entry.get("file_name", "")
            new_name = entry.get("new_name", "")

            # 文件名匹配（权重高）
            if query_flex in fname.lower():
                score += 10
            if query_flex in new_name.lower():
                score += 8

            # 标题匹配（兼容OCR空格）
            if query_flex in title.lower() or query_lower in title.lower():
                score += 5
            if query_spaced in title.lower():
                score += 3

            # 内容匹配（兼容OCR空格）
            if query_flex in snippet.lower() or query_lower in snippet.lower():
                score += 3
            if query_spaced in snippet.lower():
                score += 2

            if score > 0:
                # 高亮上下文：找到匹配位置并截取周围文本
                context = self._find_context(snippet, query)
                results.append({
                    "path": entry.get("path", ""),
                    "file_name": fname,
                    "new_name": new_name,
                    "title": title,
                    "snippet": snippet[:300],
                    "context": context,
                    "score": score,
                })

        # 按相关度排序
        results.sort(key=lambda r: -r["score"])
        return results[:max_results]

    def _find_context(self, text: str, query: str) -> str:
        """在文本中找到 query 的上下文片段"""
        idx = text.lower().find(query.lower())
        if idx == -1:
            return text[:100]

        start = max(0, idx - 30)
        end = min(len(text), idx + len(query) + 30)

        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(text) else ""
        return f"{prefix}{text[start:end]}{suffix}"

    def all_indexed(self) -> list[dict]:
        """返回所有已索引文件列表"""
        return sorted(self._index,
                      key=lambda r: -r.get("indexed_at", 0))

    def count(self) -> int:
        return len(self._index)
