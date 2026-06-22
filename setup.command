#!/bin/bash
# ⚙️ FileBrain 安装脚本 —— 一键安装依赖 + 创建桌面快捷方式

cd "$(dirname "$0")"
DIR="$(pwd)"
echo "========================================"
echo "  🧠 FileBrain · 文件大脑  一键安装"
echo "========================================"
echo ""

# 检查 Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ 未检测到 Python3，请先安装:"
    echo "   https://www.python.org/downloads/"
    read -p "按回车退出..."
    exit 1
fi

echo "✅ Python3 已安装"

# 安装依赖
echo ""
echo "📦 安装依赖包..."
pip3 install --break-system-packages PyMuPDF python-docx openpyxl pytesseract Pillow watchdog 2>&1 | tail -3
echo "✅ 依赖安装完成"

# 检测并安装 Tesseract OCR
if ! command -v tesseract &> /dev/null; then
    echo ""
    echo "🖼️  检测到未安装 Tesseract OCR（用于图片/扫描件识别）"
    echo "   建议安装: brew install tesseract tesseract-lang"
    echo "   跳过不影响核心功能（PDF文字版仍可用）"
fi

# 创建桌面快捷方式
DESKTOP="$HOME/Desktop"
LAUNCHER="$DESKTOP/FileBrain启动器.command"

cat > "$LAUNCHER" << EOF
#!/bin/bash
cd "$DIR"
python3 main.py
EOF

chmod +x "$LAUNCHER"

echo ""
echo "========================================"
echo "  ✅ 安装完成！"
echo "========================================"
echo ""
echo "📌 桌面上已创建「FileBrain启动器」"
echo "   双击它就能运行 🧠 FileBrain"
echo ""
echo "⚠️  首次运行如果系统提示无法验证开发者："
echo "   系统设置 → 隐私与安全性 → 仍要打开"
echo ""

read -p "按回车启动 FileBrain..."
python3 main.py
