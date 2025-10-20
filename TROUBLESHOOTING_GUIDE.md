# 🔧 Deep Backtesting System - Troubleshooting Guide

## 🚨 Quick Fixes

### Installation Issues

#### 1. PowerShell Execution Policy Error
**Error**: `Execution of scripts is disabled on this system`

**Solution**:
```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# Then run the installer again
```

#### 2. Python Installation Failed
**Error**: `Python installation failed`

**Solutions**:
- Download Python 3.11.7 manually from [python.org](https://python.org)
- Install with "Add to PATH" and "Install for all users" checked
- Restart command prompt after installation
- Run installer again

#### 3. Antivirus Blocking Installation
**Error**: Files being deleted or blocked

**Solutions**:
- Add `C:\DeepBacktesting` to antivirus exclusions
- Temporarily disable real-time protection
- Whitelist the installer files

#### 4. Network/Download Issues
**Error**: `Failed to download` or `Connection timeout`

**Solutions**:
- Check internet connection
- Disable VPN temporarily
- Use different DNS servers (8.8.8.8, 8.8.4.4)
- Try installing during off-peak hours

### Runtime Issues

#### 1. Import Errors
**Error**: `ModuleNotFoundError: No module named 'xxx'`

**Solutions**:
```bash
# Activate virtual environment
cd C:\DeepBacktesting
venv\Scripts\activate

# Install missing package
pip install package_name

# Or reinstall all requirements
pip install -r requirements_enhanced.txt
```

#### 2. GPU Not Detected
**Error**: `CUDA not available` or `GPU not found`

**Solutions**:
```bash
# Check NVIDIA drivers
nvidia-smi

# Update drivers from nvidia.com
# Install CUDA Toolkit 11.8
# Reinstall PyTorch with CUDA
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### 3. Memory Issues
**Error**: `Out of memory` or system slowdown

**Solutions**:
- Close unnecessary applications
- Increase virtual memory (System Properties > Advanced > Performance Settings)
- Use smaller datasets for testing
- Reduce batch sizes in configuration

#### 4. Data Loading Errors
**Error**: `File not found` or `Invalid data format`

**Solutions**:
```bash
# Check data directory
ls data/historical/

# Verify file format
python -c "import pandas as pd; print(pd.read_csv('data/historical/eur_usd_1h.csv', nrows=5))"

# Re-download data if needed
```

## 🔍 Diagnostic Commands

### System Check
```bash
# Check Python version
python --version

# Check pip version
pip --version

# Check virtual environment
where python

# Check installed packages
pip list
```

### GPU Check
```python
# Run in Python
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
print(f"GPU count: {torch.cuda.device_count()}")
if torch.cuda.is_available():
    print(f"GPU name: {torch.cuda.get_device_name(0)}")
```

### Data Check
```python
# Check data files
import os
import pandas as pd

data_dir = "data/historical"
files = os.listdir(data_dir)
print(f"Data files: {files}")

# Check file format
for file in files[:3]:  # Check first 3 files
    df = pd.read_csv(f"{data_dir}/{file}", nrows=5)
    print(f"{file}: {list(df.columns)}")
```

### Performance Check
```python
# CPU performance test
import time
import numpy as np

start = time.time()
a = np.random.rand(1000, 1000)
b = np.random.rand(1000, 1000)
c = np.dot(a, b)
print(f"CPU test: {time.time() - start:.2f}s")

# Memory test
import psutil
print(f"RAM usage: {psutil.virtual_memory().percent}%")
print(f"Available RAM: {psutil.virtual_memory().available / (1024**3):.1f}GB")
```

## 🛠️ Advanced Troubleshooting

### Complete Reinstallation
If nothing else works:

1. **Uninstall everything**:
```bash
# Remove installation directory
rmdir /s C:\DeepBacktesting

# Uninstall Python (Control Panel > Programs)
# Remove virtual environment
```

2. **Clean system**:
```bash
# Clear pip cache
pip cache purge

# Clear temp files
del /q /s %temp%\*
```

3. **Fresh installation**:
```bash
# Download fresh copy
# Run installer as Administrator
# Follow installation guide step by step
```

### Manual Package Installation
If automatic installation fails:

```bash
# Core packages
pip install numpy pandas fastapi uvicorn
pip install matplotlib seaborn plotly
pip install scikit-learn scipy

# Financial packages
pip install yfinance ccxt ta-lib
pip install alpha-vantage fredapi

# GPU packages
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Development packages
pip install jupyter pytest black flake8
```

### Configuration Issues

#### 1. YAML Configuration Errors
**Error**: `YAML parsing error`

**Solution**:
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('experiments.yaml'))"
```

#### 2. Path Issues
**Error**: `File not found` or `Import error`

**Solution**:
```bash
# Check current directory
pwd

# Check Python path
python -c "import sys; print(sys.path)"

# Add to Python path if needed
export PYTHONPATH="${PYTHONPATH}:C:\DeepBacktesting"
```

## 📊 Performance Optimization

### For RTX 3080
```python
# Optimize PyTorch for your GPU
import torch
torch.backends.cudnn.benchmark = True
torch.backends.cudnn.deterministic = False

# Use mixed precision
from torch.cuda.amp import autocast, GradScaler
scaler = GradScaler()

# Optimize memory usage
torch.cuda.empty_cache()
```

### For 64GB RAM
```python
# Increase batch sizes
BATCH_SIZE = 1024  # Instead of 256

# Use larger datasets
MAX_DATA_POINTS = 1000000  # Instead of 100000

# Enable parallel processing
NUM_WORKERS = 16  # Instead of 4
```

### System Optimization
```bash
# Windows Performance Settings
# System Properties > Advanced > Performance Settings
# - Adjust for best performance
# - Increase virtual memory
# - Disable unnecessary startup programs

# Power Settings
# - Set to High Performance
# - Disable USB selective suspend
# - Disable hard disk sleep
```

## 🚨 Emergency Recovery

### If System Won't Start
1. **Check logs**:
```bash
type C:\DeepBacktesting\install.log
type C:\DeepBacktesting\logs\*.log
```

2. **Run verification**:
```bash
cd C:\DeepBacktesting
python SYSTEM_VERIFICATION.py
```

3. **Quick test**:
```bash
python quick_test.py
```

### If Data is Corrupted
1. **Backup results**:
```bash
copy results\*.* backup\
```

2. **Re-download data**:
```bash
# Use data acquisition scripts
python data_acquisition_script.py
```

3. **Validate data**:
```bash
python data_pipeline_validator.py
```

### If Strategies Won't Load
1. **Check imports**:
```python
# Test each strategy individually
import strategies.ultra_strict_v3_strategy
import strategies.enhanced_optimized_strategy
```

2. **Fix dependencies**:
```bash
pip install -r requirements_enhanced.txt --force-reinstall
```

3. **Update strategies**:
```bash
# Pull latest strategy files
git pull origin main
```

## 📞 Getting Help

### Before Asking for Help
1. **Run diagnostics**:
```bash
python SYSTEM_VERIFICATION.py > diagnostic_report.txt
```

2. **Collect information**:
- System specs (CPU, RAM, GPU)
- Python version
- Error messages
- Log files
- Configuration files

3. **Try solutions**:
- Check this troubleshooting guide
- Search for similar issues online
- Try different approaches

### Useful Resources
- **Official Documentation**: README.md and INSTALLATION_GUIDE.md
- **Python Documentation**: [docs.python.org](https://docs.python.org)
- **PyTorch Documentation**: [pytorch.org/docs](https://pytorch.org/docs)
- **NVIDIA CUDA**: [developer.nvidia.com/cuda](https://developer.nvidia.com/cuda)

### Log Files Location
```
C:\DeepBacktesting\
├── install.log              # Installation log
├── logs\                    # Runtime logs
│   ├── controller.log       # Main controller log
│   ├── backtesting.log      # Backtesting log
│   └── error.log           # Error log
├── verification_report.json # System verification
└── diagnostic_report.txt    # Diagnostic output
```

## ✅ Success Checklist

Your system is working correctly when:
- [ ] All verification tests pass
- [ ] GPU is detected and working
- [ ] Strategies can be imported
- [ ] Data files are accessible
- [ ] Quick test completes successfully
- [ ] Jupyter notebook opens
- [ ] Desktop shortcut works
- [ ] No error messages in logs

## 🔄 Maintenance Schedule

### Daily
- Check system status
- Monitor disk space
- Review error logs

### Weekly
- Run verification tests
- Update dependencies
- Clean up old results

### Monthly
- Full system check
- Performance optimization
- Backup important data

### Quarterly
- Review and update strategies
- Analyze performance trends
- Plan system upgrades

---

**💡 Remember: Most issues can be resolved by running the verification script and following the diagnostic steps above.**
