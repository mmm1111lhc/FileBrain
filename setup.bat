@echo off
chcp 65001
echo 🧠 FileBrain · 文件大脑 安装中...

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 未安装！
    echo 请到 https://www.python.org/downloads/ 下载 Python 3
    pause
    exit /b
)

echo 正在安装依赖...
pip install -r requirements.txt
echo ✅ 安装完成！
echo 双击 start.bat 即可启动
pause
