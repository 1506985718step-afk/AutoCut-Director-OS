# AutoCut Director 启动脚本

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "AutoCut Director - 启动服务" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan

# 1. 设置 Resolve 环境
Write-Host "`n[1] 设置 Resolve 环境..." -ForegroundColor Yellow
.\scripts\set_resolve_env.ps1

# 2. 启动 FastAPI 服务
Write-Host "`n[2] 启动 FastAPI 服务..." -ForegroundColor Yellow
Write-Host "服务地址: http://localhost:8787" -ForegroundColor Cyan
Write-Host "API 文档: http://localhost:8787/docs" -ForegroundColor Cyan
Write-Host "`n按 Ctrl+C 停止服务`n" -ForegroundColor Gray

uvicorn app.main:app --host 0.0.0.0 --port 8787 --reload
