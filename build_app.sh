#!/bin/bash
# ⚙️ FileBrain Mac 应用构建脚本
# 在项目目录运行: bash build_app.sh
# 会在桌面上生成 FileBrain.app（真正的 Mac 应用）

cd "$(dirname "$0")"
DIR="$(pwd)"
APP_NAME="FileBrain"
APP_PATH="$HOME/Desktop/$APP_NAME.app"

echo "🔨 构建 $APP_NAME.app ..."

# 删除旧的
rm -rf "$APP_PATH"

# 创建 .app 目录结构
mkdir -p "$APP_PATH/Contents/MacOS"

# 创建启动脚本
cat > "$APP_PATH/Contents/MacOS/FileBrain" << 'SCRIPT'
#!/bin/bash
# 获取 .app 包所在目录
APP_PATH="$0"
while [ -L "$APP_PATH" ]; do
    APP_PATH="$(readlink "$APP_PATH")"
done
APP_DIR="$(dirname "$APP_PATH")"
# .app/Contents/MacOS → .app
APP_BUNDLE="$(cd "$APP_DIR/.." && pwd)"
# 项目代码在 .app 旁边的 FileBrain 文件夹
PROJECT_DIR="$(cd "$APP_BUNDLE/../FileBrain" && pwd)"

if [ ! -f "$PROJECT_DIR/main.py" ]; then
    # 回退：包内 Resources 目录
    PROJECT_DIR="$APP_BUNDLE/Contents/Resources"
fi

cd "$PROJECT_DIR"

# 检查依赖
python3 -c "import fitz" 2>/dev/null
if [ $? -ne 0 ]; then
    INSTALL=$(osascript -e 'button returned of (display dialog "📦 FileBrain 首次运行需要安装依赖包\n点击「安装」开始自动安装（需要网络）。" buttons {"取消","安装"} default button 2 with title "FileBrain" with icon note)' 2>/dev/null)
    if [ "$INSTALL" = "安装" ]; then
        pip3 install --break-system-packages PyMuPDF python-docx openpyxl pytesseract Pillow watchdog 2>&1
        osascript -e 'display dialog "✅ 依赖安装完成！" buttons {"打开 FileBrain"} default button 1 with title "FileBrain" with icon note' 2>/dev/null
    else
        exit 1
    fi
fi

python3 main.py
SCRIPT

chmod +x "$APP_PATH/Contents/MacOS/FileBrain"

# 创建 Info.plist
cat > "$APP_PATH/Contents/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>FileBrain</string>
    <key>CFBundleIdentifier</key>
    <string>com.filebrain.app</string>
    <key>CFBundleName</key>
    <string>FileBrain · 文件大脑</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</PLIST>
PLIST

# 复制项目代码到 .app 内部（自包含）
mkdir -p "$APP_PATH/Contents/Resources"
cp -R "$DIR" "$APP_PATH/Contents/Resources/FileBrain"

echo ""
echo "========================================"
echo "  ✅ 构建完成！"
echo "========================================"
echo ""
echo "  📱 $APP_PATH"
echo ""
echo "  使用方式："
echo "  1. 把 FileBrain.app 拖到「应用程序」文件夹"
echo "  2. 双击运行"
echo "  3. 首次打开会提示「来自互联网」，点「打开」即可"
echo ""
echo "  或保持它在桌面，双击就能用"
echo ""

# 直接试试打开
open "$APP_PATH"
