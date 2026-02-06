# 启动 Ollama 服务并下载模型
# 使用方法: .\start_ollama_service.ps1

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "启动 Ollama 服务" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 查找 Ollama 可执行文件
$ollamaPath = "C:\Users\Administrator\AppData\Local\Programs\Ollama\ollama.exe"

if (-not (Test-Path $ollamaPath)) {
    Write-Host "❌ 未找到 Ollama: $ollamaPath" -ForegroundColor Red
    Write-Host "`n请检查 Ollama 安装路径" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ 找到 Ollama: $ollamaPath" -ForegroundColor Green

# 启动 Ollama 服务
Write-Host "`n正在启动 Ollama 服务..." -ForegroundColor Yellow
Start-Process -FilePath $ollamaPath -ArgumentList "serve" -WindowStyle Hidden

Write-Host "等待服务启动..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# 检查服务是否启动
Write-Host "`n检查服务状态..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5
    Write-Host "✓ Ollama 服务已启动" -ForegroundColor Green
} catch {
    Write-Host "⚠️  服务可能还在启动中，请稍等..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5
        Write-Host "✓ Ollama 服务已启动" -ForegroundColor Green
    } catch {
        Write-Host "❌ 服务启动失败" -ForegroundColor Red
        Write-Host "`n请手动启动:" -ForegroundColor Yellow
        Write-Host "  1. 打开命令提示符" -ForegroundColor White
        Write-Host "  2. 运行: $ollamaPath serve" -ForegroundColor White
        exit 1
    }
}

# 检查已安装的模型
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "检查已安装的模型" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get
    $models = $response.models
    
    if ($models.Count -gt 0) {
        Write-Host "已安装 $($models.Count) 个模型:" -ForegroundColor Green
        foreach ($model in $models) {
            $size = [math]::Round($model.size / 1GB, 1)
            Write-Host "  - $($model.name) ($size GB)" -ForegroundColor White
        }
        
        # 检查推荐模型
        $hasMonodream = $models | Where-Object { $_.name -like "*moondream*" }
        $hasLlava = $models | Where-Object { $_.name -like "*llava-phi3*" }
        
        if ($hasMonodream) {
            Write-Host "`n✓ Moondream 已安装（推荐）" -ForegroundColor Green
        } else {
            Write-Host "`n⚠️  Moondream 未安装" -ForegroundColor Yellow
        }
        
        if ($hasLlava) {
            Write-Host "✓ LLaVA-Phi3 已安装（备选）" -ForegroundColor Green
        } else {
            Write-Host "⚠️  LLaVA-Phi3 未安装" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️  未安装任何模型" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ 获取模型列表失败: $_" -ForegroundColor Red
}

# 询问是否下载模型
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "下载视觉模型" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$downloadMoondream = Read-Host "是否下载 Moondream (1.5GB)？推荐！(y/n)"

if ($downloadMoondream -eq "y" -or $downloadMoondream -eq "Y") {
    Write-Host "`n正在下载 Moondream..." -ForegroundColor Yellow
    Write-Host "这可能需要几分钟，请耐心等待..." -ForegroundColor Gray
    
    & $ollamaPath pull moondream
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✓ Moondream 下载完成" -ForegroundColor Green
    } else {
        Write-Host "`n❌ Moondream 下载失败" -ForegroundColor Red
    }
}

$downloadLlava = Read-Host "`n是否下载 LLaVA-Phi3 (2.5GB)？备选 (y/n)"

if ($downloadLlava -eq "y" -or $downloadLlava -eq "Y") {
    Write-Host "`n正在下载 LLaVA-Phi3..." -ForegroundColor Yellow
    Write-Host "这可能需要几分钟，请耐心等待..." -ForegroundColor Gray
    
    & $ollamaPath pull llava-phi3
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✓ LLaVA-Phi3 下载完成" -ForegroundColor Green
    } else {
        Write-Host "`n❌ LLaVA-Phi3 下载失败" -ForegroundColor Red
    }
}

# 最终检查
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "最终检查" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "运行诊断..." -ForegroundColor Yellow
python check_ollama.py

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "完成！" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "下一步:" -ForegroundColor Yellow
Write-Host "  1. 运行测试: python test_ollama_vision.py" -ForegroundColor White
Write-Host "  2. 启动服务: python run_server.py" -ForegroundColor White
Write-Host "  3. 开始使用本地视觉分析！`n" -ForegroundColor White
