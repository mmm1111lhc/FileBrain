#!/bin/bash
# ⚙️ FileBrain Mac 应用构建脚本
# 在项目目录运行: bash build_app.sh
# 会在桌面上生成 FileBrain.app（真正的 Mac 应用，双击即可运行）

cd "$(dirname "$0")"
DIR="$(pwd)"
APP_NAME="FileBrain"
APP_PATH="$HOME/Desktop/$APP_NAME.app"

echo "🔨 构建 $APP_NAME.app ..."

# 创建 .app 目录结构
mkdir -p "$APP_PATH/Contents/MacOS"

# 创建启动脚本
cat > "$APP_PATH/Contents/MacOS/FileBrain" << 'SCRIPT'
#!/bin/bash
DIR="$(dirname "$0")"
PROJECT_DIR="$DIR/../../../"

# 如果是从 Desktop/FileBrain.app 运行的，项目在 App 包旁边
# 否则从项目目录运行
if [ -f "$PROJECT_DIR/main.py" ]; then
    cd "$PROJECT_DIR"
else
    cd "$(pwd)"
fi

# 检查依赖
python3 -c "import fitz" 2>/dev/null
if [ $? -ne 0 ]; then
    osascript -e 'display dialog "首次运行需要安装依赖，点击确定开始安装。" buttons {"取消","安装"} default button 2' 2>/dev/null
    if [ $? -eq 0 ]; then
        pip3 install --break-system-packages PyMuPDF python-docx openpyxl pytesseract Pillow watchdog 2>&1
        osascript -e 'display dialog "✅ 依赖安装完成！点击确定启动 FileBrain。" buttons {"确定"}' 2>/dev/null
    fi
fi

python3 -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    osascript -e 'display dialog "需要安装 tkinter，请运行: brew install python-tk" buttons {"知道了"}' 2>/dev/null
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
</dict>
</plist>
PLIST

# 复制项目代码到 App 包内（可选，也可以引用外部路径）
# 这里用软链接方式引用原项目
ln -sf "$DIR" "$APP_PATH/Contents/Resources" 2>/dev/null

echo "✅ 已生成: $APP_PATH"
echo "   双击此图标即可运行 FileBrain"
