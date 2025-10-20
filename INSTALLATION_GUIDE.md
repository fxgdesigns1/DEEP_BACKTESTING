# 🎯 Deep Backtesting System - Windows 11 Installation Guide

## 🚀 One-Click Installation

### Quick Start (Recommended)

1. **Download the system** to your Windows 11 machine
2. **Right-click** on `INSTALL_WINDOWS.bat` and select **"Run as administrator"**
3. **Follow the prompts** - the installer will handle everything automatically
4. **Wait for completion** (typically 10-15 minutes)
5. **Double-click** the "Deep Backtesting" desktop shortcut to start

### What the Installer Does

The installer automatically:
- ✅ Checks system requirements (Windows 11, 64GB RAM, RTX 3080)
- ✅ Installs Python 3.11.7 with all dependencies
- ✅ Sets up virtual environment for isolation
- ✅ Installs PyTorch with CUDA support for GPU acceleration
- ✅ Copies all system files and configurations
- ✅ Creates launcher scripts and desktop shortcut
- ✅ Runs comprehensive verification tests
- ✅ Generates installation report

## 📋 System Requirements

### Minimum Requirements
- **OS**: Windows 10 1903+ or Windows 11
- **RAM**: 16GB minimum, 32GB+ recommended
- **Storage**: 10GB free space
- **CPU**: 8+ cores recommended
- **GPU**: NVIDIA RTX 3080 or better (optional but recommended)

### Your System (Optimized For)
- **OS**: Windows 11
- **RAM**: 64GB (Excellent!)
- **GPU**: RTX 3080 (Perfect for GPU acceleration!)
- **CPU**: AMD 5950X (16 cores - Excellent!)

## 🔧 Manual Installation (Alternative)

If the one-click installer doesn't work, you can install manually:

### Step 1: Install Python
```bash
# Download Python 3.11.7 from python.org
# Install with "Add to PATH" option checked
# Verify installation:
python --version
```

### Step 2: Install Dependencies
```bash
# Navigate to installation directory
cd C:\DeepBacktesting

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install packages
pip install -r requirements_enhanced.txt

# Install PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Step 3: Verify Installation
```bash
# Run verification
python SYSTEM_VERIFICATION.py

# Run quick test
python quick_test.py
```

## 🎮 GPU Setup (RTX 3080)

Your RTX 3080 will be automatically configured for:
- **CUDA 11.8** support
- **PyTorch GPU acceleration**
- **Parallel processing** for backtesting
- **Memory optimization** for large datasets

### Verify GPU Setup
```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU count: {torch.cuda.device_count()}")
print(f"GPU name: {torch.cuda.get_device_name(0)}")
```

## 🚀 Usage Guide

### Quick Start
1. **Launch**: Double-click "Deep Backtesting" desktop shortcut
2. **Test**: Choose option 1 (Quick Test) to verify everything works
3. **Run**: Choose option 2 (Full Strategy Search) for comprehensive analysis

### Available Commands

#### Batch Commands
```bash
# Launch main menu
LAUNCH_BACKTESTING.bat

# Quick test
python quick_test.py

# Full strategy search
python controller.py --config experiments.yaml

# Data validation
python data_pipeline_validator.py
```

#### PowerShell Commands
```powershell
# Launch with menu
.\LAUNCH_BACKTESTING.ps1

# Direct commands
.\LAUNCH_BACKTESTING.ps1 test     # Quick test
.\LAUNCH_BACKTESTING.ps1 search   # Full search
.\LAUNCH_BACKTESTING.ps1 validate # Data validation
.\LAUNCH_BACKTESTING.ps1 jupyter  # Jupyter notebook
.\LAUNCH_BACKTESTING.ps1 results  # View results
```

## 📊 System Verification

### Automatic Verification
The system includes comprehensive verification:
- **System requirements** check
- **Python environment** validation
- **Dependencies** verification
- **Data pipeline** testing
- **Strategy** import testing
- **Performance** benchmarking
- **GPU** availability check

### Manual Verification
```bash
# Run full verification
python SYSTEM_VERIFICATION.py

# View verification report
type verification_report.json
```

## 🔍 Troubleshooting

### Common Issues

#### 1. PowerShell Execution Policy
```powershell
# Fix: Set execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 2. Antivirus Blocking
- Add `C:\DeepBacktesting` to antivirus exclusions
- Temporarily disable real-time protection during installation

#### 3. Python Installation Issues
```bash
# Reinstall Python with these options:
# - Add to PATH
# - Install for all users
# - Include pip
# - Include tkinter
```

#### 4. GPU Not Detected
```bash
# Update NVIDIA drivers
# Install CUDA Toolkit 11.8
# Reinstall PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### 5. Memory Issues
```bash
# Close other applications
# Increase virtual memory
# Use smaller datasets for testing
```

### Performance Optimization

#### For RTX 3080 (Your Setup)
```python
# Optimize for your GPU
torch.backends.cudnn.benchmark = True
torch.backends.cudnn.deterministic = False

# Use mixed precision
torch.cuda.amp.autocast()
```

#### For 64GB RAM
```python
# Increase batch sizes
# Use larger datasets
# Enable parallel processing
```

## 📁 Directory Structure

After installation:
```
C:\DeepBacktesting\
├── venv\                    # Virtual environment
├── data\                    # Historical data
│   └── historical\         # CSV data files
├── strategies\             # Strategy implementations
├── results\                # Backtesting results
├── logs\                   # System logs
├── config\                 # Configuration files
├── LAUNCH_BACKTESTING.bat  # Main launcher
├── LAUNCH_BACKTESTING.ps1  # PowerShell launcher
├── quick_test.py           # Quick verification
├── SYSTEM_VERIFICATION.py  # Full verification
├── controller.py           # Main controller
├── experiments.yaml        # Configuration
└── requirements_enhanced.txt # Dependencies
```

## 🎯 Next Steps

### 1. First Run
```bash
# Run quick test
python quick_test.py

# Expected output: All tests should pass
```

### 2. Explore the System
```bash
# Open Jupyter notebook
jupyter notebook

# View available strategies
ls strategies/

# Check data files
ls data/historical/
```

### 3. Run Your First Backtest
```bash
# Quick backtest
python controller.py --config experiments.yaml

# Monitor progress in logs/
# View results in results/
```

### 4. Customize Configuration
```yaml
# Edit experiments.yaml
# Adjust parameters for your needs
# Add new currency pairs
# Modify risk settings
```

## 📞 Support

### Getting Help
1. **Check logs**: `logs/` directory for error details
2. **Run verification**: `python SYSTEM_VERIFICATION.py`
3. **Check documentation**: `README.md` and this guide
4. **Review configuration**: `experiments.yaml`

### Performance Tips
- **Use GPU**: Ensure CUDA is working for faster processing
- **Optimize RAM**: Close unnecessary applications
- **Batch processing**: Run multiple timeframes in parallel
- **Data quality**: Ensure clean, complete historical data

## 🎉 Success Indicators

You'll know the installation was successful when:
- ✅ All verification tests pass
- ✅ GPU is detected and working
- ✅ Strategies can be imported
- ✅ Data files are accessible
- ✅ Quick test completes successfully
- ✅ Desktop shortcut works
- ✅ Jupyter notebook opens

## 🔄 Updates and Maintenance

### Updating the System
```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements_enhanced.txt --upgrade

# Re-run verification
python SYSTEM_VERIFICATION.py
```

### Regular Maintenance
- **Weekly**: Run verification tests
- **Monthly**: Update dependencies
- **Quarterly**: Review and optimize strategies
- **As needed**: Clean up old results and logs

---

**🎯 Ready to start backtesting? Double-click the "Deep Backtesting" shortcut on your desktop!**
