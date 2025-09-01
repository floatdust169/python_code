@echo off
chcp 65001 > nul
title AI智能知识库检索系统

echo.
echo ====================================================
echo         🚀 AI智能知识库检索系统启动器
echo ====================================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到Python，请先安装Python 3.8或更高版本
    echo 📥 下载地址：https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: 显示Python版本
echo 🐍 检测到的Python版本：
python --version

:: 切换到脚本所在目录
cd /d "%~dp0"

:: 检查依赖包
echo.
echo 📦 检查依赖包...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo ⚠️  缺少Flask依赖，正在安装...
    pip install flask flask-cors python-docx PyPDF2 jieba volcengine-python-sdk
    if errorlevel 1 (
        echo ❌ 依赖安装失败，请检查网络连接
        pause
        exit /b 1
    )
    echo ✅ 依赖安装完成
)

:: 启动服务
echo.
echo 🌐 正在启动AI知识库服务器...
echo.
python start.py

pause
