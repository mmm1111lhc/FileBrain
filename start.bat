@echo off
chcp 65001
echo 🧠 FileBrain · 文件大脑
echo 正在启动...

REM 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未检测到 Python，请先安装 Python 3
    pause
    exit /b
)

REM 安装依赖
pip install -r requirements.txt

REM 启动
python main.py
pause
