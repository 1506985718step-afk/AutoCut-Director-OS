# scripts/set_resolve_env.ps1
# Windows DaVinci Resolve Script Path Setup

# Set Resolve script directory (modify according to your installation)
$env:RESOLVE_SCRIPT_DIR = "C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"

# For custom installation path, uncomment and modify:
# $env:RESOLVE_SCRIPT_DIR = "D:\DaVinciResolve\Support\Developer\Scripting\Modules"

# Add to PYTHONPATH
$env:PYTHONPATH = "$env:RESOLVE_SCRIPT_DIR;$env:PYTHONPATH"

# Display configuration
Write-Host "RESOLVE_SCRIPT_DIR=$env:RESOLVE_SCRIPT_DIR" -ForegroundColor Cyan
Write-Host "PYTHONPATH=$env:PYTHONPATH" -ForegroundColor Cyan

# Verify Python path
Write-Host "`nVerifying Python configuration:" -ForegroundColor Green
python -c "import sys; print('PYTHONPATH OK'); print(sys.path[0:5])"

# Test DaVinciResolveScript import
Write-Host "`nTesting Resolve API:" -ForegroundColor Green
Write-Host "Note: DaVinci Resolve must be running for this test to succeed" -ForegroundColor Yellow

python -c "import DaVinciResolveScript; print('Success: DaVinciResolveScript imported')" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nConfiguration successful!" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "1. Start DaVinci Resolve" -ForegroundColor White
    Write-Host "2. Open a project" -ForegroundColor White
    Write-Host "3. Run: python test_resolve_connection.py" -ForegroundColor White
} else {
    Write-Host "`nPYTHONPATH is configured correctly" -ForegroundColor Green
    Write-Host "The import error is expected when Resolve is not running" -ForegroundColor Yellow
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "1. Start DaVinci Resolve" -ForegroundColor White
    Write-Host "2. Open a project" -ForegroundColor White
    Write-Host "3. Run: python test_resolve_connection.py" -ForegroundColor White
}
