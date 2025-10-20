#!/bin/bash
# Monte Carlo Pattern Analysis - Setup Script
# Installs required dependencies for MC pattern analysis

echo "============================================================"
echo "Monte Carlo Pattern Analysis - Setup"
echo "============================================================"
echo ""

echo "Installing required Python packages..."
echo ""

pip install scipy>=1.7.0
pip install statsmodels>=0.13.0
pip install scikit-learn>=1.0.0
pip install psutil>=5.9.0

echo ""
echo "============================================================"
echo "Installation Complete!"
echo "============================================================"
echo ""
echo "You can now run Monte Carlo pattern analysis:"
echo ""
echo "  python mc_pattern_runner.py --file your_results.json"
echo "  python mc_pattern_runner.py --dir backtesting_output"
echo ""
echo "For help:"
echo "  python mc_pattern_runner.py --help"
echo ""
echo "Documentation:"
echo "  MONTE_CARLO_PATTERNS_README.md"
echo "  MONTE_CARLO_QUICK_START.md"
echo ""
echo "============================================================"




