# AutoCut Director 启动脚本（带达芬奇检查）

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AutoCut Director 启动检查" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查达芬奇是否运行
Write-Host "[1/3] 检查达芬奇状态..." -ForegroundColor Yellow

$resolve = Get-Process -Name "Resolve" -ErrorAction SilentlyContinue

if ($resolve) {
    Write-Host "  ✓ 达芬奇正在运行" -ForegroundColor Green
} else {
    Write-Host "  ✗ 达芬奇未运行" -ForegroundColor Red
    Write-Host ""
    Write-Host "  ⚠️  警告: 达芬奇未启动" -ForegroundColor Yellow
    Write-Host "  AutoCut Director 需要达芬奇运行才能执行剪辑操作" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  请先:" -ForegroundColor Cyan
    Write-Host "  1. 启动 DaVinci Resolve" -ForegroundColor White
    Write-Host "  2. 创建或打开一个项目" -ForegroundColor White
    Write-Host "  3. 然后重新运行此脚本" -ForegroundColor White
    Write-Host ""
    
    $choice = Read-Host "  是否继续启动 AutoCut Director? (y/n)"
    if ($choice -ne "y" -and $choice -ne "Y") {
        Write-Host ""
        Write-Host "  已取消启动" -ForegroundColor Gray
        exit 0
    }
}

Write-Host ""

# 2. 检查 Python 环境
Write-Host "[2/3] 检查 Python 环境..." -ForegroundColor Yellow

try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python 未安装或不在 PATH 中" -ForegroundColor Red
    Write-Host ""
    Write-Host "  请安装 Python 3.6-3.11" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# 3. 检查依赖
Write-Host "[3/3] 检查项目依赖..." -ForegroundColor Yellow

if (Test-Path "requirements.txt") {
    Write-Host "  ✓ requirements.txt 存在" -ForegroundColor Green
} else {
    Write-Host "  ✗ requirements.txt 不存在" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  启动 AutoCut Director" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 启动服务器
Write-Host "正在启动服务器..." -ForegroundColor Green
Write-Host "访问地址: http://localhost:8787" -ForegroundColor Cyan
Write-Host ""
Write-Host "按 Ctrl+C 停止服务器" -ForegroundColor Gray
Write-Host ""

python run_server.py
