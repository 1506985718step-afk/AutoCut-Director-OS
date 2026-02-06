# 简化启动脚本（假设环境已配置）

Write-Host "启动 AutoCut Director..." -ForegroundColor Green
Write-Host "服务地址: http://localhost:8787" -ForegroundColor Cyan
Write-Host "API 文档: http://localhost:8787/docs" -ForegroundColor Cyan

uvicorn app.main:app --host 0.0.0.0 --port 8787 --reload
