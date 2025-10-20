# PowerShell Script to Setup Periodic Update Monitoring
# This creates a Windows Task Scheduler task to check for updates daily

$ErrorActionPreference = "Stop"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  PERIODIC UPDATE MONITOR SETUP" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$TaskName = "TradingSystemUpdateMonitor"
$ScriptPath = Join-Path $PSScriptRoot "update_monitor.py"
$LogPath = Join-Path $PSScriptRoot "update_monitor_logs"
$CheckIntervalHours = 24

# Verify Python is available
Write-Host "[1/5] Verifying Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  - Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  - ERROR: Python not found in PATH" -ForegroundColor Red
    Write-Host "  Please install Python or add it to your PATH" -ForegroundColor Red
    exit 1
}

# Verify script exists
Write-Host "[2/5] Verifying update_monitor.py exists..." -ForegroundColor Yellow
if (-Not (Test-Path $ScriptPath)) {
    Write-Host "  - ERROR: update_monitor.py not found at: $ScriptPath" -ForegroundColor Red
    exit 1
}
Write-Host "  - Script found" -ForegroundColor Green

# Create log directory
Write-Host "[3/5] Creating log directory..." -ForegroundColor Yellow
if (-Not (Test-Path $LogPath)) {
    New-Item -ItemType Directory -Path $LogPath | Out-Null
}
Write-Host "  - Log directory: $LogPath" -ForegroundColor Green

# Remove existing task if it exists
Write-Host "[4/5] Checking for existing scheduled task..." -ForegroundColor Yellow
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "  - Found existing task. Removing..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "  - Existing task removed" -ForegroundColor Green
}

# Create new scheduled task
Write-Host "[5/5] Creating scheduled task..." -ForegroundColor Yellow

# Task action - run Python script
$pythonExe = (Get-Command python).Source
$logFile = Join-Path $LogPath "last_run.log"
$actionArgs = "`"$ScriptPath`""
$action = New-ScheduledTaskAction -Execute $pythonExe -Argument $actionArgs -WorkingDirectory $PSScriptRoot

# Task trigger - daily at 6:00 AM
$trigger = New-ScheduledTaskTrigger -Daily -At 6:00AM

# Task settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable -MultipleInstances IgnoreNew

# Register the task
try {
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "Monitors trading system updates folder for changes" -User $env:USERNAME | Out-Null
    Write-Host "  - Scheduled task created successfully" -ForegroundColor Green
} catch {
    Write-Host "  - ERROR: Failed to create scheduled task" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Summary
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  SETUP COMPLETE!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Task Configuration:" -ForegroundColor Yellow
Write-Host "  - Task Name: $TaskName" -ForegroundColor White
Write-Host "  - Schedule: Daily at 6:00 AM" -ForegroundColor White
Write-Host "  - Script: $ScriptPath" -ForegroundColor White
Write-Host "  - Logs: $LogPath" -ForegroundColor White
Write-Host ""
Write-Host "Manual Commands:" -ForegroundColor Yellow
Write-Host "  - Run now: python update_monitor.py" -ForegroundColor Cyan
Write-Host "  - Check status: python update_monitor.py --status" -ForegroundColor Cyan
Write-Host "  - View in Task Scheduler" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. The system will check for updates daily at 6:00 AM" -ForegroundColor White
Write-Host "  2. Check logs in: $LogPath" -ForegroundColor White
Write-Host "  3. When updates are found, you will see a report" -ForegroundColor White
Write-Host "  4. Review the report and decide whether to implement" -ForegroundColor White
Write-Host ""
