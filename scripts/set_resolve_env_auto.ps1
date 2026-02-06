# scripts/set_resolve_env_auto.ps1
# 自动检测版：搜索 Resolve 安装路径

Write-Host "正在搜索 DaVinci Resolve 脚本 API..." -ForegroundColor Cyan

# 搜索可能的路径
$searchPaths = @(
    "C:\ProgramData\Blackmagic Design",
    "C:\Program Files\Blackmagic Design",
    "D:\",
    "E:\"
)

$foundPath = $null

foreach ($basePath in $searchPaths) {
    if (Test-Path $basePath) {
        $result = Get-ChildItem -Path $basePath -Recurse -Filter "DaVinciResolveScript.py" -ErrorAction SilentlyContinue | Select-Object -First 1
        
        if ($result) {
            $foundPath = $result.DirectoryName
            break
        }
    }
}

if ($foundPath) {
    Write-Host "✓ 找到: $foundPath" -ForegroundColor Green
    
    $env:RESOLVE_SCRIPT_DIR = $foundPath
    $env:PYTHONPATH = "$env:RESOLVE_SCRIPT_DIR;$env:PYTHONPATH"
    
    Write-Host "`nRESOLVE_SCRIPT_DIR=$env:RESOLVE_SCRIPT_DIR" -ForegroundColor Cyan
    Write-Host "PYTHONPATH=$env:PYTHONPATH" -ForegroundColor Cyan
    
    Write-Host "`n验证 Python 配置:" -ForegroundColor Green
    python -c "import sys; print('PYTHONPATH OK'); print(sys.path[0:5])"
    
    Write-Host "`n测试导入:" -ForegroundColor Green
    python -c "import DaVinciResolveScript; print('✓ 导入成功')"
    
} else {
    Write-Host "✗ 未找到 DaVinciResolveScript.py" -ForegroundColor Red
    Write-Host "请手动设置 RESOLVE_SCRIPT_DIR 环境变量" -ForegroundColor Yellow
}
