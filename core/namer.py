"""智能命名器 —— 从文件内容生成美观易读的文件名"""

import re
import logging
from pathlib import Path

from config import (
    SUMMARY_MAX_LENGTH,
    SUMMARY_MIN_LENGTH,
    FILENAME_BAD_CHARS,
    FILENAME_REPLACE_CHAR,
    AUTHOR_ENABLED,
    AUTHOR_MAX_LENGTH,
)
from core.extractors import extract_author

logger = logging.getLogger(__name__)

# 美观分隔符（中点 · 两边加空格，视觉清爽）
SEP = " · "


def sanitize_filename(text: str, max_len: int = SUMMARY_MAX_LENGTH) -> str:
    """清理文本，保留可读性"""
    # 修复 OCR 常见问题：中文汉字之间的空格 → 去掉
    # 如 "赚 钱 如 果" → "赚钱如果"
    text = re.sub(r"([一-鿿])\s+(?=[一-鿿])", r"\1", text)
    # 中文与英文之间的空格 → 保留一个空格
    text = re.sub(r"([一-鿿])\s+([a-zA-Z])", r"\1 \2", text)
    text = re.sub(r"([a-zA-Z])\s+([一-鿿])", r"\1 \2", text)

    safe = re.sub(FILENAME_BAD_CHARS, FILENAME_REPLACE_CHAR, text)
    # 合并连续空白为单个空格
    safe = re.sub(r"\s+", " ", safe)
    safe = safe.strip(" _.-")
    if len(safe) > max_len:
        safe = safe[:max_len].rstrip(" -")
    return safe


def format_date(date_str: str) -> str:
    """将 20260622 格式化为 2026.06.22"""
    if len(date_str) == 8:
        return f"{date_str[:4]}.{date_str[4:6]}.{date_str[6:]}"
    return date_str


def generate_summary(extracted: dict) -> str:
    """从提取的内容中生成文件名摘要"""
    title = extracted.get("title", "").strip()
    text = extracted.get("text", "").strip()

    candidates = []

    if title and len(title) >= SUMMARY_MIN_LENGTH:
        candidates.append(title)

    # 从正文中取第一段有意义的句子
    if text:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        for line in lines:
            if len(line) < SUMMARY_MIN_LENGTH:
                continue
            if line.isdigit():
                continue
            if re.match(r'^https?://', line):
                continue
            if re.search(r'[一-鿿]', line) or len(line) >= 8:
                candidates.append(line)
                break

        if not candidates and lines:
            candidates.append(lines[0])

    if not candidates:
        return "未命名"

    best = candidates[0]
    if len(best) > SUMMARY_MAX_LENGTH:
        best = best[:SUMMARY_MAX_LENGTH]

    return sanitize_filename(best)


def get_author_tag(file_path: str, extracted: dict, ext: str) -> str:
    """获取作者标签"""
    author = extract_author(file_path, extracted, ext)
    if not AUTHOR_ENABLED or not author:
        return ""
    return sanitize_filename(author, max_len=AUTHOR_MAX_LENGTH)


def build_new_filename(
    old_name: str,
    extracted: dict,
    version_str: str,
    date_str: str,
    template: str = None,
) -> str:
    """
    构建美观的文件名
    支持自定义模板: {summary} {date} {author} {version}
    """
    from config import NAMING_TEMPLATE
    ext = Path(old_name).suffix
    summary = generate_summary(extracted)

    if not summary or summary == "未命名":
        stem = Path(old_name).stem
        summary = sanitize_filename(stem)

    pretty_date = format_date(date_str)
    author = get_author_tag(old_name, extracted, ext)

    # 使用模板
    tpl = template or NAMING_TEMPLATE
    new_stem = tpl.replace("{summary}", summary or "未命名") \
                  .replace("{date}", pretty_date) \
                  .replace("{author}", author or "") \
                  .replace("{version}", version_str or "")
    # 清理多余字符
    new_stem = re.sub(r"·\s*·", "·", new_stem)
    new_stem = re.sub(r"[·\s]*$", "", new_stem)
    new_stem = re.sub(r"^[·\s]*", "", new_stem)
    new_stem = re.sub(r"\s{2,}", " ", new_stem)
    new_stem = new_stem.strip(" ·_-")
    if not new_stem:
        new_stem = summary or "未命名"
    return f"{new_stem}{ext}"
