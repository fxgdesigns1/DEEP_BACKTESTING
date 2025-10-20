@echo off
title Deep Backtesting System - Windows Installer
color 0A

echo.
echo ========================================
echo    DEEP BACKTESTING SYSTEM INSTALLER
echo ========================================
echo.
echo This installer will set up the complete backtesting system
echo on your Windows 11 machine with RTX 3080 and 64GB RAM.
echo.
echo Features:
echo - Automatic Python 3.11+ installation
echo - Complete dependency management
echo - GPU acceleration setup
echo - Self-verification and testing
echo - Professional backtesting environment
echo.

set /p confirm="Do you want to continue? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo Installation cancelled.
    pause
    exit /b 0
)

echo.
echo Starting installation...
echo.

REM Check if PowerShell is available
powershell -Command "Get-Host" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: PowerShell is not available or not working properly.
    echo Please ensure PowerShell 5.1+ is installed and try again.
    pause
    exit /b 1
)

REM Run the PowerShell installer
echo Running PowerShell installer...
powershell -ExecutionPolicy Bypass -File "%~dp0INSTALL_WINDOWS.ps1"

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo    INSTALLATION COMPLETED SUCCESSFULLY!
    echo ========================================
    echo.
    echo Next steps:
    echo 1. Look for "Deep Backtesting" shortcut on your desktop
    echo 2. Double-click it to launch the system
    echo 3. Start with "Quick Test" to verify everything works
    echo 4. Then run "Full Strategy Search" for analysis
    echo.
    echo Installation log saved to: C:\DeepBacktesting\install.log
    echo.
) else (
    echo.
    echo ========================================
    echo    INSTALLATION FAILED!
    echo ========================================
    echo.
    echo Please check the error messages above and:
    echo 1. Ensure you have administrator privileges
    echo 2. Check Windows Defender/antivirus settings
    echo 3. Ensure stable internet connection
    echo 4. Try running as administrator
    echo.
    echo Installation log saved to: C:\DeepBacktesting\install.log
    echo.
)

echo Press any key to exit...
pause >nul
