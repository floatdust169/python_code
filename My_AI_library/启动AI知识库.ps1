# AI智能知识库检索系统启动器
# PowerShell版本

# 设置控制台编码为UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$host.ui.RawUI.WindowTitle = "AI智能知识库检索系统"

Write-Host ""
Write-Host "====================================================" -ForegroundColor Green
Write-Host "        🚀 AI智能知识库检索系统启动器" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Green
Write-Host ""

# 检查Python是否安装
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "🐍 检测到的Python版本：$pythonVersion" -ForegroundColor Yellow
    } else {
        throw "Python未安装"
    }
} catch {
    Write-Host "❌ 错误：未找到Python，请先安装Python 3.8或更高版本" -ForegroundColor Red
    Write-Host "📥 下载地址：https://www.python.org/downloads/" -ForegroundColor Blue
    Write-Host ""
    Read-Host "按任意键退出"
    exit 1
}

# 切换到脚本所在目录
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# 检查依赖包
Write-Host ""
Write-Host "📦 检查依赖包..." -ForegroundColor Yellow

try {
    pip show flask | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  缺少必要依赖，正在安装..." -ForegroundColor Yellow
        pip install flask flask-cors python-docx PyPDF2 jieba volcengine-python-sdk
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 依赖安装完成" -ForegroundColor Green
        } else {
            throw "依赖安装失败"
        }
    } else {
        Write-Host "✅ 依赖包检查完成" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ 依赖安装失败，请检查网络连接" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

# 启动服务
Write-Host ""
Write-Host "🌐 正在启动AI知识库服务器..." -ForegroundColor Cyan
Write-Host ""

try {
    python start.py
} catch {
    Write-Host "❌ 启动失败：$_" -ForegroundColor Red
} finally {
    Write-Host ""
    Read-Host "按任意键退出"
}
