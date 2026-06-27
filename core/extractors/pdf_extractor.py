"""PDF 内容提取器

支持：
- 文本型 PDF（直接提取）
- 扫描型 PDF（自动降级为 OCR，需要安装 Tesseract）
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PDFExtractor:
    """PDF 文件内容提取"""

    def __init__(self):
        self._fitz = None
        self._have_ocr = False
        self._pytesseract = None
        self._PIL_Image = None

    def _lazy_import(self):
        if self._fitz is not None:
            return
        try:
            import fitz  # PyMuPDF
            self._fitz = fitz
        except ImportError:
            logger.warning("PyMuPDF 未安装，PDF 提取不可用")
            self._fitz = False

        try:
            import pytesseract
            self._pytesseract = pytesseract
            from PIL import Image
            self._PIL_Image = Image
            # 快速检查 tesseract 是否可用
            import subprocess
            subprocess.run(["tesseract", "--version"],
                           capture_output=True, check=True)
            self._have_ocr = True
        except Exception:
            logger.warning("Tesseract OCR 未安装，扫描件 PDF 将无法识别")
            self._have_ocr = False

    def extract(self, file_path: str) -> dict:
        """提取 PDF 内容，返回 {text, title, success}"""
        self._lazy_import()
        path = Path(file_path)
        if not path.exists():
            return {"text": "", "title": "", "success": False,
                    "error": "文件不存在"}

        if not self._fitz:
            return {"text": "", "title": "", "success": False,
                    "error": "PyMuPDF 未安装，请 pip install PyMuPDF"}

        try:
            doc = self._fitz.open(file_path)
            full_text = ""
            first_page_text = ""

            # 提取元数据
            meta = doc.metadata
            meta_title = meta.get("title", "") or ""
            meta_author = meta.get("author", "") or ""

            for page_num in range(min(len(doc), 10)):  # 最多读 10 页
                page = doc[page_num]
                text = page.get_text().strip()
                if page_num == 0:
                    first_page_text = text
                full_text += text + "\n"

            # 判断是否有足够文本（非扫描件）
            if len(full_text.strip()) < 20 and len(doc) > 0:
                # 可能是扫描件，降级到 OCR
                logger.info("PDF 文本不足，尝试 OCR ...")
                full_text = self._ocr_pdf(doc)

            doc.close()

            # 提取标题
            title = self._extract_title(full_text, meta_title)

            return {
                "text": full_text.strip(),
                "title": title,
                "author": meta_author,
                "success": True,
                "ocr_fallback": len(full_text.strip()) > 0 and len(meta_title) < 3,
            }

        except Exception as e:
            logger.error(f"PDF 提取失败: {e}")
            return {"text": "", "title": "", "success": False,
                    "error": str(e)}

    def _ocr_pdf(self, doc) -> str:
        """对扫描件 PDF 进行 OCR 识别（300 DPI + 灰度增强）"""
        if not self._have_ocr:
            return ""
        text_parts = []
        total = min(len(doc), 20)
        for i in range(total):
            page = doc[i]
            pix = page.get_pixmap(dpi=300)
            from io import BytesIO
            img = self._PIL_Image.open(BytesIO(pix.tobytes("png")))
            img = img.convert("L")  # 灰度提高识别率
            try:
                txt = self._pytesseract.image_to_string(
                    img, lang="chi_sim+eng", config="--psm 6"
                )
                text_parts.append(txt.strip())
            except Exception as e:
                logger.warning(f"OCR 第 {i+1} 页失败: {e}")
        return "\n".join(text_parts)

    def _extract_title(self, text: str, meta_title: str) -> str:
        """从文本中提取最适合做标题的句子"""
        # 优先使用元数据中的标题
        if meta_title and len(meta_title) > 2:
            return meta_title

        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if not lines:
            return ""

        # 取第一个有意义的短句（不是页码/页眉页脚）
        for line in lines:
            clean = line.strip()
            # 过滤掉常见的页眉页脚
            if len(clean) < 3:
                continue
            if clean.isdigit():
                continue
            if len(clean) > 10 and len(clean) < 80:
                return clean

        # 回退：取第一段的前半段
        first = lines[0] if lines else ""
        return first[:60] if len(first) > 10 else ""
