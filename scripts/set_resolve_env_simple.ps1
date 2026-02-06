# scripts/set_resolve_env_simple.ps1
# 简化版：直接设置路径

$env:RESOLVE_SCRIPT_DIR = "C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
$env:PYTHONPATH = "$env:RESOLVE_SCRIPT_DIR;$env:PYTHONPATH"

Write-Host "RESOLVE_SCRIPT_DIR=$env:RESOLVE_SCRIPT_DIR"
Write-Host "PYTHONPATH=$env:PYTHONPATH"

python -c "import sys; print('PYTHONPATH OK'); print(sys.path[0:5])"
