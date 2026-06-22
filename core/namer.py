"""智能命名器 —— 从文件内容生成可读的文件名"""

import re
import logging
from pathlib import Path

from config import (
    SUMMARY_MAX_LENGTH,
    SUMMARY_MIN_LENGTH,
    DATE_FORMAT,
    FILENAME_BAD_CHARS,
    FILENAME_REPLACE_CHAR,
    AUTHOR_ENABLED,
    AUTHOR_MAX_LENGTH,
)
from core.extractors import extract_author, get_system_user

logger = logging.getLogger(__name__)


def sanitize_filename(text: str, max_len: int = SUMMARY_MAX_LENGTH) -> str:
    """清理文本，使其适合作为文件名"""
    # 替换非法字符
    safe = re.sub(FILENAME_BAD_CHARS, FILENAME_REPLACE_CHAR, text)
    # 替换连续空白为单个下划线
    safe = re.sub(r"\s+", "_", safe)
    # 去掉首尾特殊字符
    safe = safe.strip("_ .-")
    if len(safe) > max_len:
        safe = safe[:max_len].rstrip("_ -")
    return safe


def generate_summary(extracted: dict) -> str:
    """从提取的内容中生成文件名摘要"""
    title = extracted.get("title", "").strip()
    text = extracted.get("text", "").strip()

    # 优先使用提取的标题
    candidates = []

    if title and len(title) >= SUMMARY_MIN_LENGTH:
        candidates.append(title)

    # 从正文中取第一段有意义的句子
    if text:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        for line in lines:
            # 跳过纯数字、太短的行、URL
            if len(line) < SUMMARY_MIN_LENGTH:
                continue
            if line.isdigit():
                continue
            if re.match(r'^https?://', line):
                continue
            # 检查是否包含中文或足够长的英文
            if re.search(r'[一-鿿]', line) or len(line) >= 8:
                candidates.append(line)
                break

        # 回退：取第一行
        if not candidates and lines:
            candidates.append(lines[0])

    if not candidates:
        return "未命名"

    # 取最佳候选
    best = candidates[0]
    # 截断到合理长度
    if len(best) > SUMMARY_MAX_LENGTH:
        best = best[:SUMMARY_MAX_LENGTH]

    return sanitize_filename(best)


def _get_author_tag(file_path: str, extracted: dict, ext: str) -> str:
    """获取作者标签"""
    author = extract_author(file_path, extracted, ext)
    if not AUTHOR_ENABLED:
        return ""
    clean = sanitize_filename(author, max_len=AUTHOR_MAX_LENGTH)
    return clean


def build_new_filename(
    old_name: str,
    extracted: dict,
    version_str: str,
    date_str: str,
) -> str:
    """
    构建新文件名

    首次处理:  内容摘要_日期[_作者]
    有修改后:  内容摘要_日期[_作者]_v1.0
    """
    ext = Path(old_name).suffix
    summary = generate_summary(extracted)

    # 如果摘要为空，回退使用原文件名（去扩展名）
    if not summary or summary == "未命名":
        stem = Path(old_name).stem
        summary = sanitize_filename(stem)

    # 作者标签
    author_tag = _get_author_tag(old_name, extracted, ext)

    # 拼接文件名（版本号只在有修改时加入）
    parts = [summary, date_str]
    if author_tag:
        parts.append(author_tag)
    if version_str:
        parts.append(version_str)

    new_stem = "_".join(parts)
    return f"{new_stem}{ext}"
