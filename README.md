# 🧠 FileBrain · 文件大脑

> 桌面文件智能整理工具 —— 自动识别文件内容、智能重命名、全文检索、发送留痕
> **🔒 纯本地 · 不过云** — 所有文件处理在本地电脑完成，数据不上传任何云端服务器

**适合人群：** 经常下载各类文档的办公人员、政务办事用户、科研工作者、知识管理爱好者

---

## ✨ 功能

| 功能 | 说明 |
|------|------|
| 🔍 **自动扫描** | 监控桌面（或任意文件夹），新文件出现自动处理 |
| 🏷️ **智能命名** | 提取文件内容 → 自动生成 `内容摘要_日期_作者_版本号` 文件名 |
| 📄 **多格式支持** | PDF（含扫描件 OCR）、Word、Excel、图片文字识别 |
| 🔎 **全文检索** | 搜索关键词，瞬间定位到是哪份文件 |
| 📤 **发送留痕** | 记录文件发给过谁、什么时间、通过什么方式 |
| 📌 **版本管理** | 按最后修改时间自动标注版本号（v1.0、v1.1、v2.0...） |
| 🔒 **纯本地 · 不过云** | 所有文件处理在本地完成，数据不上传任何云端 |

## 💡 典型场景

| 场景 | 效果 |
|------|------|
| 🏛️ **政务软件下载** | 浙里办、粤省事、随申办、北京通等各省政务 App → 申请表/回执单自动命名 |
| 💬 **办公通讯软件** | 钉钉、企业微信、飞书、WeChat → 下载的文档/表格自动整理 |
| 💼 **办公文档管理** | 合同/方案/报告 → 按内容摘要+版本号自动归档 |
| 📚 **学术资料整理** | 论文/扫描件 → OCR 识别 + 全文检索 |
| 🏠 **个人文件归档** | 身份证/证件扫描件 → 自动识别并命名 |

> **举个实际例子：** 从浙里办下载审批回执，原始文件名是 `20260622_12345678.pdf`，FileBrain 自动识别内容后重命名为 `建设工程规划许可证_20260622_张三_v1.0.pdf`。粤省事、随申办、钉钉、企微、飞书……任何地方下载的文件，放桌面就自动整理，再也不用一个一个手动改文件名。

## 🖥️ 界面

简洁的桌面 GUI，分四个标签页：

- **文件监控** — 选择目录，启动监控，实时日志
- **全文检索** — 搜索文件内容，打开文件位置，记录发送
- **发送留痕** — 查看/搜索/管理发送历史
- **设置** — 配置选项和关于信息

## 🚀 快速开始

### 1. 安装依赖

```bash
# Python 3.9+
pip install -r requirements.txt

# 安装 Tesseract OCR（用于图片和扫描件识别）
# macOS:
brew install tesseract tesseract-lang

# Ubuntu:
sudo apt install tesseract-ocr tesseract-ocr-chi-sim

# Windows:
# https://github.com/UB-Mannheim/tesseract/wiki
```

### 2. 启动

```bash
python main.py
```

其他用法：

```bash
python main.py                      # 启动图形界面
python main.py --scan ~/Documents   # 扫描指定目录
python main.py --cli                # 命令行模式
python main.py --version            # 查看版本
```

## 📁 工作方式

1. 选择要监控的文件夹（默认桌面）
2. 点击「开始监控」，FileBrain 自动扫描已有文件
3. **新文件出现**或**已有文件被修改**时：
   - 提取文件内容（文本 / OCR）
   - 生成内容摘要作为文件名
   - 根据修改时间分配版本号
   - 重命名文件
   - 加入搜索索引
4. 在「全文检索」标签页搜索关键词，直接定位文件
5. 分享文件后，在「发送留痕」标签页记录发送信息

## ⚙️ 技术栈

- **Python 3** — tkinter 桌面 GUI
- **PyMuPDF** — PDF 解析
- **python-docx** — Word 文档
- **openpyxl** — Excel 文件
- **Tesseract OCR** — 图片和扫描件文字识别
- **watchdog** — 文件系统监控

## 📦 项目结构

```
FileBrain/
├── main.py                  # 启动入口
├── config.py                # 全局配置
├── requirements.txt         # 依赖清单
├── README.md                # 本文件
├── core/
│   ├── watcher.py           # 目录监控
│   ├── namer.py             # 智能命名
│   ├── version.py           # 版本管理
│   ├── search_index.py      # 全文检索索引
│   ├── journal.py           # 发送留痕
│   └── extractors/
│       ├── pdf_extractor.py    # PDF 提取
│       ├── word_extractor.py   # Word 提取
│       ├── excel_extractor.py  # Excel 提取
│       └── image_extractor.py  # 图片 OCR
└── gui/
    └── app.py               # tkinter 桌面界面
```

## 🗺️ 路线图

- [ ] 打包为 macOS .app / Windows .exe
- [ ] 集成 EasyOCR 提升识别准确率
- [ ] 批量导出/导入索引
- [ ] 文件相似度检测
- [ ] 自定义命名模板

## 📄 开源协议

MIT License

---

**FileBrain · 文件大脑** — 免费开源桌面工具

如果这个工具对你有帮助，欢迎 ⭐ Star 收藏！
