"""FileBrain 全局配置"""

import os

# 默认监控目录（桌面）
DEFAULT_WATCH_DIR = os.path.expanduser("~/Desktop")

# 状态数据库存放目录（在监控目录下创建 .filebrain/）
STATE_DIR_NAME = ".filebrain"

# 文件类型配置 —— 扩展名全小写
SUPPORTED_EXTENSIONS = {
    # PDF
    ".pdf",
    # Word
    ".docx", ".doc",
    # Excel
    ".xlsx", ".xls",
    # 图片（OCR）
    ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif",
}

# 命名配置
SUMMARY_MAX_LENGTH = 50          # 文件名摘要最大字符数
SUMMARY_MIN_LENGTH = 6           # 文件名摘要最小字符数
DATE_FORMAT = "%Y%m%d"           # 日期格式
VERSION_SEPARATOR = "v"          # 版本号前缀（如 v1.0）

# 作者标注
DEFAULT_AUTHOR = os.environ.get("USER", "unknown")  # 默认使用系统用户名
AUTHOR_ENABLED = True            # 是否在文件名中标注作者
AUTHOR_MAX_LENGTH = 12           # 作者名最大长度

# 文件名非法字符替换
FILENAME_BAD_CHARS = r'[\\/:*?"<>|]'
FILENAME_REPLACE_CHAR = "_"

# 版本管理
VERSION_INCREMENT_MINUTES = 5    # 两次修改间隔超过此分钟数 → 升次版本号

# OCR 语言（Tesseract），中文+英文
OCR_LANG = "chi_sim+eng"

# 延迟等待（秒）- 文件创建后等待写入完成
FILE_WRITE_WAIT_SECONDS = 2
WATCHER_INTERVAL = 3             # 轮询间隔（秒）
