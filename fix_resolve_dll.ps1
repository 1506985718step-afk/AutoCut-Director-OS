# 修复达芬奇 DLL 加载问题

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  达芬奇 DLL 路径修复" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检测达芬奇安装路径
Write-Host "[1/4] 检测达芬奇安装路径..." -ForegroundColor Yellow

$resolveProcess = Get-Process -Name "Resolve" -ErrorAction SilentlyContinue

if ($resolveProcess) {
    $resolvePath = Split-Path $resolveProcess.Path
    Write-Host "  ✓ 达芬奇路径: $resolvePath" -ForegroundColor Green
} else {
    Write-Host "  ✗ 达芬奇未运行" -ForegroundColor Red
    Write-Host ""
    Write-Host "  请先启动达芬奇，然后重新运行此脚本" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# 2. 添加达芬奇路径到 PATH
Write-Host "[2/4] 添加达芬奇路径到 PATH..." -ForegroundColor Yellow

$env:PATH = "$resolvePath;$env:PATH"
Write-Host "  ✓ 已添加到当前会话 PATH" -ForegroundColor Green

Write-Host ""

# 3. 设置 Python 路径
Write-Host "[3/4] 设置 Python 模块路径..." -ForegroundColor Yellow

$scriptModules = "C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
$env:PYTHONPATH = "$scriptModules;$env:PYTHONPATH"
Write-Host "  ✓ PYTHONPATH 已设置" -ForegroundColor Green

Write-Host ""

# 4. 测试连接
Write-Host "[4/4] 测试达芬奇连接..." -ForegroundColor Yellow
Write-Host ""

python test_resolve_quick.py

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  修复完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
