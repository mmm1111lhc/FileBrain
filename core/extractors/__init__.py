"""文件内容提取器"""

import os
import logging

from .pdf_extractor import PDFExtractor
from .word_extractor import WordExtractor
from .excel_extractor import ExcelExtractor
from .image_extractor import ImageExtractor

logger = logging.getLogger(__name__)

EXTRACTORS = {
    ".pdf": PDFExtractor,
    ".docx": WordExtractor,
    ".doc": WordExtractor,
    ".xlsx": ExcelExtractor,
    ".xls": ExcelExtractor,
    ".png": ImageExtractor,
    ".jpg": ImageExtractor,
    ".jpeg": ImageExtractor,
    ".bmp": ImageExtractor,
    ".tiff": ImageExtractor,
    ".tif": ImageExtractor,
}


def get_system_user() -> str:
    """获取当前系统用户名"""
    try:
        import getpass
        return getpass.getuser()
    except Exception:
        return os.environ.get("USER", "unknown")


def extract_author(file_path: str, extracted: dict,
                   ext: str) -> str:
    """
    从文件元数据中提取作者/来源信息

    优先级：
    1. PDF/Word 元数据中的作者字段
    2. 系统用户名
    """
    author = extracted.get("author", "").strip()
    if author:
        return author

    # 回退：系统用户名
    return get_system_user()
