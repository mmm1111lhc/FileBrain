#!/bin/bash
# 🧠 FileBrain · 文件大脑 —— 双击直接启动

cd "$(dirname "$0")"
echo "========================================"
echo "  🧠 FileBrain · 文件大脑"
echo "  正在启动..."
echo "========================================"
echo ""

# 检查依赖
MISSING=""
python3 -c "import fitz" 2>/dev/null || MISSING="$MISSING PyMuPDF"
python3 -c "import docx" 2>/dev/null || MISSING="$MISSING python-docx"
python3 -c "import openpyxl" 2>/dev/null || MISSING="$MISSING openpyxl"
python3 -c "import PIL" 2>/dev/null || MISSING="$MISSING Pillow"

if [ -n "$MISSING" ]; then
    echo "⚠️  缺少依赖包: $MISSING"
    echo "双击「setup.command」安装后即可使用"
    echo ""
    read -p "按回车退出..."
    exit 1
fi

python3 main.py

echo ""
echo "FileBrain 已退出"
read -p "按回车关闭此窗口..."
