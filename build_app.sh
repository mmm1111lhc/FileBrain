#!/bin/bash
# FileBrain Mac 应用构建脚本
# bash build_app.sh  →  桌面生成 FileBrain.app

cd "$(dirname "$0")"
DIR="$(pwd)"
APP_PATH="$HOME/Desktop/FileBrain.app"

echo "构建 FileBrain.app ..."
rm -rf "$APP_PATH"
mkdir -p "$APP_PATH/Contents/MacOS"
mkdir -p "$APP_PATH/Contents/Resources"

# 启动脚本
LAUNCHER="$APP_PATH/Contents/MacOS/FileBrain"
cat > "$LAUNCHER" << SCRIPT
#!/bin/bash
cd "\$(dirname "\$0")/../Resources/FileBrain"
python3 -c "import fitz,docx,openpyxl,PIL" 2>/dev/null || pip3 install --break-system-packages PyMuPDF python-docx openpyxl pytesseract Pillow watchdog >/dev/null 2>&1
python3 main.py 2>/tmp/filebrain_error.log
SCRIPT
chmod +x "$LAUNCHER"

# Info.plist（带图标配置）
cat > "$APP_PATH/Contents/Info.plist" << END
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
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
    <key>CFBundleIconFile</key>
    <string>app_icon</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
END

# 复制项目代码 + 图标
cp -R "$DIR" "$APP_PATH/Contents/Resources/FileBrain"
cp "$DIR/images/app_icon.icns" "$APP_PATH/Contents/Resources/app_icon.icns"

# 更新图标缓存
touch "$APP_PATH"

echo ""
echo "✅ 已生成: $APP_PATH"
echo "   图标: app_icon.icns（已配置）"
echo "   双击即可运行"
echo ""
open "$APP_PATH"
