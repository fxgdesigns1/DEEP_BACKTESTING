#Requires -Version 5.1
<#
.SYNOPSIS
    One-Click Windows 11 Installer for Deep Backtesting System
.DESCRIPTION
    This script provides a complete one-click installation for the professional
    backtesting system on Windows 11 with automatic verification and setup.
    
    Features:
    - Automatic Python 3.11+ installation
    - Complete dependency management
    - System verification and health checks
    - GPU acceleration setup (NVIDIA RTX 3080)
    - Professional backtesting environment
    - Self-verification and testing
    
.PARAMETER InstallPath
    Installation directory (default: C:\DeepBacktesting)
.PARAMETER PythonVersion
    Python version to install (default: 3.11.7)
.PARAMETER SkipGPU
    Skip GPU acceleration setup
.PARAMETER ForceReinstall
    Force reinstall even if system exists
.EXAMPLE
    .\INSTALL_WINDOWS.ps1
    Standard installation with default settings
.EXAMPLE
    .\INSTALL_WINDOWS.ps1 -InstallPath "D:\Trading\Backtesting" -PythonVersion "3.12.0"
    Custom installation path and Python version
#>

param(
    [string]$InstallPath = "C:\DeepBacktesting",
    [string]$PythonVersion = "3.11.7",
    [switch]$SkipGPU = $false,
    [switch]$ForceReinstall = $false
)

# Set execution policy and error handling
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Global variables
$Global:LogFile = "$InstallPath\install.log"
$Global:StartTime = Get-Date
$Global:InstallSuccess = $false

# Color functions for better output
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
    Add-Content -Path $Global:LogFile -Value "[$timestamp] $Message"
}

function Write-Success { param([string]$Message) Write-ColorOutput "✅ $Message" "Green" }
function Write-Info { param([string]$Message) Write-ColorOutput "ℹ️  $Message" "Cyan" }
function Write-Warning { param([string]$Message) Write-ColorOutput "⚠️  $Message" "Yellow" }
function Write-Error { param([string]$Message) Write-ColorOutput "❌ $Message" "Red" }
function Write-Header { param([string]$Message) Write-ColorOutput "`n🎯 $Message" "Magenta" }

# System requirements check
function Test-SystemRequirements {
    Write-Header "SYSTEM REQUIREMENTS CHECK"
    
    $requirements = @{
        "OS Version" = @{
            "Required" = "Windows 10 1903+ or Windows 11"
            "Current" = (Get-WmiObject -Class Win32_OperatingSystem).Caption
            "Pass" = $false
        }
        "RAM" = @{
            "Required" = "16GB minimum, 32GB+ recommended"
            "Current" = "{0:N0}GB" -f ((Get-WmiObject -Class Win32_ComputerSystem).TotalPhysicalMemory / 1GB)
            "Pass" = $false
        }
        "Disk Space" = @{
            "Required" = "10GB free space"
            "Current" = "{0:N1}GB free" -f ((Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'").FreeSpace / 1GB)
            "Pass" = $false
        }
        "GPU" = @{
            "Required" = "NVIDIA RTX 3080 or better (optional)"
            "Current" = "Checking..."
            "Pass" = $false
        }
    }
    
    # Check OS version
    $osVersion = [System.Environment]::OSVersion.Version
    if ($osVersion.Major -ge 10 -and $osVersion.Build -ge 18362) {
        $requirements["OS Version"].Pass = $true
    }
    
    # Check RAM
    $ramGB = (Get-WmiObject -Class Win32_ComputerSystem).TotalPhysicalMemory / 1GB
    if ($ramGB -ge 16) {
        $requirements["RAM"].Pass = $true
    }
    
    # Check disk space
    $freeSpaceGB = (Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'").FreeSpace / 1GB
    if ($freeSpaceGB -ge 10) {
        $requirements["Disk Space"].Pass = $true
    }
    
    # Check GPU
    try {
        $gpu = Get-WmiObject -Class Win32_VideoController | Where-Object { $_.Name -like "*NVIDIA*" -and $_.Name -like "*RTX*" }
        if ($gpu) {
            $requirements["GPU"].Current = $gpu.Name
            $requirements["GPU"].Pass = $true
        } else {
            $requirements["GPU"].Current = "No NVIDIA RTX GPU detected"
        }
    } catch {
        $requirements["GPU"].Current = "GPU detection failed"
    }
    
    # Display results
    foreach ($req in $requirements.GetEnumerator()) {
        $status = if ($req.Value.Pass) { "✅ PASS" } else { "❌ FAIL" }
        Write-Info "$($req.Key): $($req.Value.Current) - $status"
        if (-not $req.Value.Pass -and $req.Key -ne "GPU") {
            Write-Error "System requirement not met: $($req.Key)"
            return $false
        }
    }
    
    Write-Success "System requirements check completed"
    return $true
}

# Create installation directory
function New-InstallationDirectory {
    Write-Header "CREATING INSTALLATION DIRECTORY"
    
    try {
        if (Test-Path $InstallPath) {
            if ($ForceReinstall) {
                Write-Warning "Removing existing installation..."
                Remove-Item -Path $InstallPath -Recurse -Force
            } else {
                Write-Error "Installation directory already exists. Use -ForceReinstall to overwrite."
                return $false
            }
        }
        
        New-Item -Path $InstallPath -ItemType Directory -Force | Out-Null
        Write-Success "Created installation directory: $InstallPath"
        return $true
    } catch {
        Write-Error "Failed to create installation directory: $_"
        return $false
    }
}

# Install Python
function Install-Python {
    Write-Header "INSTALLING PYTHON $PythonVersion"
    
    try {
        # Check if Python is already installed
        $pythonPath = Get-Command python -ErrorAction SilentlyContinue
        if ($pythonPath -and -not $ForceReinstall) {
            $version = & python --version 2>&1
            Write-Info "Python already installed: $version"
            return $true
        }
        
        # Download Python installer
        $pythonUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-amd64.exe"
        $pythonInstaller = "$env:TEMP\python-$PythonVersion-installer.exe"
        
        Write-Info "Downloading Python $PythonVersion..."
        Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller -UseBasicParsing
        
        # Install Python with silent options
        Write-Info "Installing Python $PythonVersion..."
        $installArgs = @(
            "/quiet",
            "InstallAllUsers=1",
            "PrependPath=1",
            "Include_test=0",
            "Include_pip=1",
            "Include_tcltk=1",
            "Include_launcher=1"
        )
        
        Start-Process -FilePath $pythonInstaller -ArgumentList $installArgs -Wait
        
        # Refresh PATH
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
        
        # Verify installation
        $pythonVersion = & python --version 2>&1
        if ($pythonVersion -like "*$PythonVersion*") {
            Write-Success "Python $PythonVersion installed successfully"
            Remove-Item $pythonInstaller -Force
            return $true
        } else {
            Write-Error "Python installation verification failed"
            return $false
        }
    } catch {
        Write-Error "Python installation failed: $_"
        return $false
    }
}

# Install system dependencies
function Install-SystemDependencies {
    Write-Header "INSTALLING SYSTEM DEPENDENCIES"
    
    try {
        # Install Visual C++ Redistributable
        Write-Info "Installing Visual C++ Redistributable..."
        $vcRedistUrl = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
        $vcRedistPath = "$env:TEMP\vc_redist.x64.exe"
        
        Invoke-WebRequest -Uri $vcRedistUrl -OutFile $vcRedistPath -UseBasicParsing
        Start-Process -FilePath $vcRedistPath -ArgumentList "/quiet", "/norestart" -Wait
        Remove-Item $vcRedistPath -Force
        
        # Install Git if not present
        $gitPath = Get-Command git -ErrorAction SilentlyContinue
        if (-not $gitPath) {
            Write-Info "Installing Git..."
            $gitUrl = "https://github.com/git-for-windows/git/releases/latest/download/Git-2.43.0-64-bit.exe"
            $gitInstaller = "$env:TEMP\git-installer.exe"
            
            Invoke-WebRequest -Uri $gitUrl -OutFile $gitInstaller -UseBasicParsing
            Start-Process -FilePath $gitInstaller -ArgumentList "/SILENT" -Wait
            Remove-Item $gitInstaller -Force
        }
        
        Write-Success "System dependencies installed"
        return $true
    } catch {
        Write-Error "System dependencies installation failed: $_"
        return $false
    }
}

# Setup Python environment
function Setup-PythonEnvironment {
    Write-Header "SETTING UP PYTHON ENVIRONMENT"
    
    try {
        # Upgrade pip
        Write-Info "Upgrading pip..."
        & python -m pip install --upgrade pip
        
        # Install wheel and setuptools
        Write-Info "Installing build tools..."
        & python -m pip install wheel setuptools
        
        # Create virtual environment
        Write-Info "Creating virtual environment..."
        & python -m venv "$InstallPath\venv"
        
        # Activate virtual environment
        $venvActivate = "$InstallPath\venv\Scripts\Activate.ps1"
        if (Test-Path $venvActivate) {
            & $venvActivate
            Write-Success "Virtual environment activated"
        } else {
            Write-Error "Failed to activate virtual environment"
            return $false
        }
        
        # Install PyTorch with CUDA support if GPU available
        if (-not $SkipGPU) {
            Write-Info "Installing PyTorch with CUDA support..."
            & python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
        } else {
            Write-Info "Installing PyTorch CPU version..."
            & python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
        }
        
        Write-Success "Python environment setup completed"
        return $true
    } catch {
        Write-Error "Python environment setup failed: $_"
        return $false
    }
}

# Install Python packages
function Install-PythonPackages {
    Write-Header "INSTALLING PYTHON PACKAGES"
    
    try {
        # Enhanced requirements with latest versions
        $requirements = @"
# Core backtesting and data analysis
fastapi==0.109.0
uvicorn==0.27.0
aiohttp==3.9.3
python-dotenv==1.0.0
pyyaml==6.0.1
requests==2.31.0
python-dateutil==2.8.2
pytz==2024.1
numpy==1.26.3
pandas==2.2.0

# Advanced data analysis and machine learning
scikit-learn==1.3.2
scipy==1.11.4
matplotlib==3.8.2
seaborn==0.13.0
plotly==5.17.0
ta-lib==0.4.28

# Financial data and APIs
yfinance==0.2.28
ccxt==4.1.77
alpha-vantage==2.3.1
fredapi==0.5.1

# Database and storage
sqlite3
sqlalchemy==2.0.23
redis==5.0.1

# Performance and optimization
numba==0.58.1
joblib==1.3.2
tqdm==4.66.1

# Testing and validation
pytest==7.4.3
pytest-cov==4.1.0
hypothesis==6.92.1

# Development tools
jupyter==1.0.0
ipykernel==6.26.0
black==23.11.0
flake8==6.1.0

# Additional utilities
psutil==5.9.6
schedule==1.2.0
python-telegram-bot==20.7
discord.py==2.3.2
"@
        
        # Write requirements file
        $requirementsPath = "$InstallPath\requirements.txt"
        $requirements | Out-File -FilePath $requirementsPath -Encoding UTF8
        
        # Install packages
        Write-Info "Installing Python packages (this may take several minutes)..."
        & python -m pip install -r $requirementsPath --no-cache-dir
        
        Write-Success "Python packages installed successfully"
        return $true
    } catch {
        Write-Error "Python packages installation failed: $_"
        return $false
    }
}

# Copy system files
function Copy-SystemFiles {
    Write-Header "COPYING SYSTEM FILES"
    
    try {
        # Get current script directory
        $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
        
        # Copy all files except installation script
        $excludePatterns = @("INSTALL_WINDOWS.ps1", "*.log", "venv", "__pycache__", "*.pyc")
        
        Write-Info "Copying system files..."
        Get-ChildItem -Path $scriptDir -Recurse | Where-Object {
            $item = $_
            $shouldExclude = $false
            foreach ($pattern in $excludePatterns) {
                if ($item.Name -like $pattern -or $item.FullName -like "*\$pattern") {
                    $shouldExclude = $true
                    break
                }
            }
            -not $shouldExclude
        } | ForEach-Object {
            $relativePath = $_.FullName.Substring($scriptDir.Length + 1)
            $targetPath = Join-Path $InstallPath $relativePath
            
            if ($_.PSIsContainer) {
                New-Item -Path $targetPath -ItemType Directory -Force | Out-Null
            } else {
                $targetDir = Split-Path $targetPath -Parent
                if (-not (Test-Path $targetDir)) {
                    New-Item -Path $targetDir -ItemType Directory -Force | Out-Null
                }
                Copy-Item -Path $_.FullName -Destination $targetPath -Force
            }
        }
        
        Write-Success "System files copied successfully"
        return $true
    } catch {
        Write-Error "System files copy failed: $_"
        return $false
    }
}

# Create launcher scripts
function New-LauncherScripts {
    Write-Header "CREATING LAUNCHER SCRIPTS"
    
    try {
        # Main launcher script
        $launcherScript = @"
@echo off
title Deep Backtesting System
echo.
echo ========================================
echo    DEEP BACKTESTING SYSTEM LAUNCHER
echo ========================================
echo.

cd /d "$InstallPath"

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Available commands:
echo 1. Run Quick Test
echo 2. Run Full Strategy Search
echo 3. Run Data Validation
echo 4. Open Jupyter Notebook
echo 5. View Results
echo 6. Exit
echo.

set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" (
    echo Running quick test...
    python quick_test.py
) else if "%choice%"=="2" (
    echo Running full strategy search...
    python controller.py --config experiments.yaml
) else if "%choice%"=="3" (
    echo Running data validation...
    python data_pipeline_validator.py
) else if "%choice%"=="4" (
    echo Opening Jupyter Notebook...
    jupyter notebook
) else if "%choice%"=="5" (
    echo Opening results directory...
    start results
) else if "%choice%"=="6" (
    echo Goodbye!
    exit /b 0
) else (
    echo Invalid choice. Please run the script again.
)

echo.
pause
"@
        
        $launcherPath = "$InstallPath\LAUNCH_BACKTESTING.bat"
        $launcherScript | Out-File -FilePath $launcherPath -Encoding ASCII
        
        # PowerShell launcher
        $psLauncherScript = @"
# Deep Backtesting System PowerShell Launcher
param(
    [string]`$Command = "menu"
)

Set-Location "$InstallPath"

# Activate virtual environment
& "venv\Scripts\Activate.ps1"

switch (`$Command.ToLower()) {
    "test" {
        Write-Host "Running quick test..." -ForegroundColor Green
        python quick_test.py
    }
    "search" {
        Write-Host "Running full strategy search..." -ForegroundColor Green
        python controller.py --config experiments.yaml
    }
    "validate" {
        Write-Host "Running data validation..." -ForegroundColor Green
        python data_pipeline_validator.py
    }
    "jupyter" {
        Write-Host "Opening Jupyter Notebook..." -ForegroundColor Green
        jupyter notebook
    }
    "results" {
        Write-Host "Opening results directory..." -ForegroundColor Green
        Invoke-Item "results"
    }
    "menu" {
        Write-Host "`n🎯 Deep Backtesting System" -ForegroundColor Magenta
        Write-Host "Available commands:" -ForegroundColor Cyan
        Write-Host "  .\LAUNCH_BACKTESTING.ps1 test     - Run quick test" -ForegroundColor White
        Write-Host "  .\LAUNCH_BACKTESTING.ps1 search   - Run full strategy search" -ForegroundColor White
        Write-Host "  .\LAUNCH_BACKTESTING.ps1 validate - Run data validation" -ForegroundColor White
        Write-Host "  .\LAUNCH_BACKTESTING.ps1 jupyter  - Open Jupyter Notebook" -ForegroundColor White
        Write-Host "  .\LAUNCH_BACKTESTING.ps1 results  - View results" -ForegroundColor White
    }
    default {
        Write-Host "Unknown command: `$Command" -ForegroundColor Red
        Write-Host "Use 'menu' to see available commands" -ForegroundColor Yellow
    }
}
"@
        
        $psLauncherPath = "$InstallPath\LAUNCH_BACKTESTING.ps1"
        $psLauncherScript | Out-File -FilePath $psLauncherPath -Encoding UTF8
        
        Write-Success "Launcher scripts created"
        return $true
    } catch {
        Write-Error "Launcher scripts creation failed: $_"
        return $false
    }
}

# System verification
function Test-SystemVerification {
    Write-Header "SYSTEM VERIFICATION"
    
    try {
        # Test Python installation
        Write-Info "Testing Python installation..."
        $pythonVersion = & python --version 2>&1
        if ($pythonVersion -like "*Python*") {
            Write-Success "Python: $pythonVersion"
        } else {
            Write-Error "Python verification failed"
            return $false
        }
        
        # Test virtual environment
        Write-Info "Testing virtual environment..."
        $venvActivate = "$InstallPath\venv\Scripts\Activate.ps1"
        if (Test-Path $venvActivate) {
            & $venvActivate
            Write-Success "Virtual environment activated"
        } else {
            Write-Error "Virtual environment not found"
            return $false
        }
        
        # Test key packages
        $keyPackages = @("numpy", "pandas", "fastapi", "torch")
        foreach ($package in $keyPackages) {
            Write-Info "Testing $package..."
            try {
                $result = & python -c "import $package; print('OK')" 2>&1
                if ($result -eq "OK") {
                    Write-Success "$package: OK"
                } else {
                    Write-Error "$package: FAILED"
                    return $false
                }
            } catch {
                Write-Error "$package: FAILED - $_"
                return $false
            }
        }
        
        # Test GPU availability
        if (-not $SkipGPU) {
            Write-Info "Testing GPU availability..."
            try {
                $gpuTest = & python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('GPU count:', torch.cuda.device_count())" 2>&1
                Write-Info "GPU Test: $gpuTest"
                if ($gpuTest -like "*True*") {
                    Write-Success "GPU acceleration available"
                } else {
                    Write-Warning "GPU acceleration not available (CPU mode will be used)"
                }
            } catch {
                Write-Warning "GPU test failed: $_"
            }
        }
        
        # Test system files
        Write-Info "Testing system files..."
        $requiredFiles = @("controller.py", "requirements.txt", "experiments.yaml")
        foreach ($file in $requiredFiles) {
            $filePath = "$InstallPath\$file"
            if (Test-Path $filePath) {
                Write-Success "Found: $file"
            } else {
                Write-Error "Missing: $file"
                return $false
            }
        }
        
        Write-Success "System verification completed successfully"
        return $true
    } catch {
        Write-Error "System verification failed: $_"
        return $false
    }
}

# Create desktop shortcut
function New-DesktopShortcut {
    Write-Header "CREATING DESKTOP SHORTCUT"
    
    try {
        $WshShell = New-Object -comObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Deep Backtesting.lnk")
        $Shortcut.TargetPath = "$InstallPath\LAUNCH_BACKTESTING.bat"
        $Shortcut.WorkingDirectory = $InstallPath
        $Shortcut.Description = "Deep Backtesting System"
        $Shortcut.Save()
        
        Write-Success "Desktop shortcut created"
        return $true
    } catch {
        Write-Warning "Failed to create desktop shortcut: $_"
        return $true  # Non-critical
    }
}

# Main installation function
function Start-Installation {
    Write-Header "DEEP BACKTESTING SYSTEM INSTALLER"
    Write-Info "Installation Path: $InstallPath"
    Write-Info "Python Version: $PythonVersion"
    Write-Info "GPU Support: $(if ($SkipGPU) { 'Disabled' } else { 'Enabled' })"
    Write-Info "Force Reinstall: $ForceReinstall"
    
    # Create log file
    New-Item -Path $Global:LogFile -ItemType File -Force | Out-Null
    
    try {
        # Run installation steps
        $steps = @(
            { Test-SystemRequirements },
            { New-InstallationDirectory },
            { Install-Python },
            { Install-SystemDependencies },
            { Setup-PythonEnvironment },
            { Install-PythonPackages },
            { Copy-SystemFiles },
            { New-LauncherScripts },
            { Test-SystemVerification },
            { New-DesktopShortcut }
        )
        
        foreach ($step in $steps) {
            if (-not (& $step)) {
                throw "Installation step failed"
            }
        }
        
        $Global:InstallSuccess = $true
        
    } catch {
        Write-Error "Installation failed: $_"
        $Global:InstallSuccess = $false
    }
}

# Installation summary
function Show-InstallationSummary {
    $duration = (Get-Date) - $Global:StartTime
    
    Write-Header "INSTALLATION SUMMARY"
    
    if ($Global:InstallSuccess) {
        Write-Success "Installation completed successfully!"
        Write-Info "Duration: $($duration.ToString('hh\:mm\:ss'))"
        Write-Info "Installation Path: $InstallPath"
        Write-Info "Log File: $Global:LogFile"
        
        Write-Host "`n🎯 NEXT STEPS:" -ForegroundColor Magenta
        Write-Host "1. Double-click 'Deep Backtesting' on your desktop" -ForegroundColor White
        Write-Host "2. Or run: $InstallPath\LAUNCH_BACKTESTING.bat" -ForegroundColor White
        Write-Host "3. Start with option 1 (Quick Test) to verify everything works" -ForegroundColor White
        Write-Host "4. Then run option 2 (Full Strategy Search) for comprehensive analysis" -ForegroundColor White
        
        Write-Host "`n📚 DOCUMENTATION:" -ForegroundColor Magenta
        Write-Host "- README.md: Complete system documentation" -ForegroundColor White
        Write-Host "- experiments.yaml: Configuration file" -ForegroundColor White
        Write-Host "- results/: All backtesting results" -ForegroundColor White
        
    } else {
        Write-Error "Installation failed!"
        Write-Info "Check the log file for details: $Global:LogFile"
        Write-Host "`n🔧 TROUBLESHOOTING:" -ForegroundColor Yellow
        Write-Host "1. Ensure you have administrator privileges" -ForegroundColor White
        Write-Host "2. Check Windows Defender/antivirus settings" -ForegroundColor White
        Write-Host "3. Ensure stable internet connection" -ForegroundColor White
        Write-Host "4. Try running with -ForceReinstall parameter" -ForegroundColor White
    }
}

# Run installation
Start-Installation
Show-InstallationSummary

# Keep window open if there was an error
if (-not $Global:InstallSuccess) {
    Write-Host "`nPress any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
