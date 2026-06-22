"""图片内容提取器（OCR 识别）

需要安装 Tesseract：
  macOS: brew install tesseract tesseract-lang
  Linux: sudo apt install tesseract-ocr tesseract-ocr-chi-sim
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ImageExtractor:
    """图片文件 OCR 提取"""

    def __init__(self):
        self._PIL = None
        self._pytesseract = None
        self._available = False

    def _lazy_import(self):
        if self._available:
            return
        if self._pytesseract is not None and not self._available:
            return

        try:
            from PIL import Image
            self._PIL = Image
        except ImportError:
            logger.warning("Pillow 未安装")
            self._pytesseract = False
            return

        try:
            import pytesseract
            self._pytesseract = pytesseract
            # 验证 Tesseract 是否可用
            import subprocess
            subprocess.run(["tesseract", "--version"],
                           capture_output=True, check=True)
            self._available = True
        except Exception:
            logger.warning("Tesseract 不可用，OCR 功能将受限。"
                           "请安装: brew install tesseract tesseract-lang")
            self._available = False

    def extract(self, file_path: str) -> dict:
        """OCR 提取图片中的文字"""
        self._lazy_import()
        path = Path(file_path)
        if not path.exists():
            return {"text": "", "title": "", "success": False,
                    "error": "文件不存在"}

        if not self._available:
            return {"text": "", "title": "", "success": False,
                    "error": "Tesseract 不可用"}

        try:
            img = self._PIL.open(file_path)
            # 尝试中文+英文识别
            text = self._pytesseract.image_to_string(
                img, lang="chi_sim+eng"
            )
            lines = [l.strip() for l in text.split("\n") if l.strip()]

            # 取第一行有意义的文本作为标题
            title = ""
            for line in lines:
                if len(line) > 5 and len(line) < 80:
                    title = line
                    break
            if not title and lines:
                title = lines[0][:60]

            return {
                "text": "\n".join(lines),
                "title": title,
                "success": True,
            }

        except Exception as e:
            logger.error(f"图片 OCR 失败: {e}")
            return {"text": "", "title": "", "success": False,
                    "error": str(e)}
