# Ollama 本地视觉模型快速安装脚本
# 适用于 Windows PowerShell

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Ollama 本地视觉模型快速安装" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 检查 Ollama 是否已安装
Write-Host "[1/4] 检查 Ollama 安装..." -ForegroundColor Yellow
$ollamaInstalled = Get-Command ollama -ErrorAction SilentlyContinue

if ($ollamaInstalled) {
    Write-Host "  ✓ Ollama 已安装" -ForegroundColor Green
    ollama --version
} else {
    Write-Host "  ✗ Ollama 未安装" -ForegroundColor Red
    Write-Host "`n请先安装 Ollama:" -ForegroundColor Yellow
    Write-Host "  1. 访问: https://ollama.com/download/windows" -ForegroundColor White
    Write-Host "  2. 下载并安装 OllamaSetup.exe" -ForegroundColor White
    Write-Host "  3. 重新运行此脚本`n" -ForegroundColor White
    exit 1
}

# 检查 Ollama 服务
Write-Host "`n[2/4] 检查 Ollama 服务..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "  ✓ Ollama 服务正在运行" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Ollama 服务未运行" -ForegroundColor Red
    Write-Host "`n正在启动 Ollama 服务..." -ForegroundColor Yellow
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
    Write-Host "  ✓ Ollama 服务已启动" -ForegroundColor Green
}

# 下载 Moondream 模型
Write-Host "`n[3/4] 下载 Moondream 模型 (1.5GB)..." -ForegroundColor Yellow
Write-Host "  这可能需要几分钟，请耐心等待..." -ForegroundColor Gray

$moondreamExists = ollama list | Select-String "moondream"

if ($moondreamExists) {
    Write-Host "  ✓ Moondream 已安装，跳过下载" -ForegroundColor Green
} else {
    Write-Host "  正在下载..." -ForegroundColor Gray
    ollama pull moondream
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Moondream 下载完成" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Moondream 下载失败" -ForegroundColor Red
        exit 1
    }
}

# 询问是否下载 LLaVA-Phi3
Write-Host "`n[4/4] 下载 LLaVA-Phi3 模型 (2.5GB)..." -ForegroundColor Yellow
$downloadLlava = Read-Host "  是否下载 LLaVA-Phi3？(y/n，推荐 n)"

if ($downloadLlava -eq "y" -or $downloadLlava -eq "Y") {
    $llavaExists = ollama list | Select-String "llava-phi3"
    
    if ($llavaExists) {
        Write-Host "  ✓ LLaVA-Phi3 已安装，跳过下载" -ForegroundColor Green
    } else {
        Write-Host "  正在下载..." -ForegroundColor Gray
        ollama pull llava-phi3
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ LLaVA-Phi3 下载完成" -ForegroundColor Green
        } else {
            Write-Host "  ✗ LLaVA-Phi3 下载失败" -ForegroundColor Red
        }
    }
} else {
    Write-Host "  ⏭  跳过 LLaVA-Phi3 下载" -ForegroundColor Gray
}

# 显示已安装的模型
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "已安装的模型:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
ollama list

# 更新 .env 配置
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "配置 AutoCut Director" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$envFile = ".env"
$envExample = ".env.example"

if (Test-Path $envFile) {
    Write-Host "  检查 .env 配置..." -ForegroundColor Yellow
    
    $envContent = Get-Content $envFile -Raw
    
    if ($envContent -notmatch "USE_LOCAL_VISION") {
        Write-Host "  添加本地视觉模型配置..." -ForegroundColor Yellow
        
        $localConfig = @"

# 本地视觉模型配置（Ollama）
USE_LOCAL_VISION=True
LOCAL_VISION_MODEL=moondream
OLLAMA_HOST=http://localhost:11434
"@
        
        Add-Content -Path $envFile -Value $localConfig
        Write-Host "  ✓ 配置已添加" -ForegroundColor Green
    } else {
        Write-Host "  ✓ 配置已存在" -ForegroundColor Green
    }
} else {
    Write-Host "  创建 .env 文件..." -ForegroundColor Yellow
    Copy-Item $envExample $envFile
    Write-Host "  ✓ .env 文件已创建" -ForegroundColor Green
    Write-Host "  ⚠  请编辑 .env 文件，填写必要的配置" -ForegroundColor Yellow
}

# 运行测试
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "运行测试" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$runTest = Read-Host "是否运行测试？(y/n)"

if ($runTest -eq "y" -or $runTest -eq "Y") {
    Write-Host "`n正在运行测试..." -ForegroundColor Yellow
    python test_ollama_vision.py
} else {
    Write-Host "  ⏭  跳过测试" -ForegroundColor Gray
}

# 完成
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "安装完成！" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "下一步:" -ForegroundColor Yellow
Write-Host "  1. 确保 .env 中 USE_LOCAL_VISION=True" -ForegroundColor White
Write-Host "  2. 运行测试: python test_ollama_vision.py" -ForegroundColor White
Write-Host "  3. 启动服务: python run_server.py" -ForegroundColor White
Write-Host "  4. 查看文档: OLLAMA_SETUP_GUIDE.md`n" -ForegroundColor White

Write-Host "享受零成本的本地视觉分析！🎉`n" -ForegroundColor Green
