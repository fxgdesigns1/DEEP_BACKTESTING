# GitHub Workflow Guide for Deep Backtesting System

## 🚀 Quick Start - Your First Push

Your repository is already configured at: `https://github.com/fxgdesigns1/DEEP_BACKTESTING.git`

### Initial Setup (Already Done ✓)
- ✓ Git initialized
- ✓ Remote repository connected
- ✓ `.gitignore` created to protect sensitive data

### Push Your Code to GitHub

```powershell
# 1. Check what will be committed (review changes)
git status

# 2. Stage all your code files
git add .

# 3. Commit with a meaningful message
git commit -m "Initial commit: Complete trading system with backtesting framework"

# 4. Push to GitHub
git push -u origin main
```

**Note**: If you get authentication errors, you'll need to set up GitHub credentials (see Authentication section below).

---

## 📋 Daily Workflow

### Making Changes

```powershell
# 1. Before starting work, get latest changes from GitHub
git pull

# 2. Make your code changes...

# 3. Check what changed
git status
git diff  # See line-by-line changes

# 4. Stage your changes
git add .
# Or add specific files:
git add strategies/new_strategy.py

# 5. Commit with descriptive message
git commit -m "Add: XAU/USD scalping strategy with 75% win rate"

# 6. Push to GitHub
git push
```

### Commit Message Best Practices

```powershell
# Good commit messages:
git commit -m "Add: Monte Carlo simulation for strategy validation"
git commit -m "Fix: Stop loss calculation in gold scalping strategy"
git commit -m "Update: Risk management parameters for prop firm rules"
git commit -m "Refactor: Optimize backtesting engine performance"
git commit -m "Remove: Deprecated data downloaders"

# Use prefixes: Add, Fix, Update, Refactor, Remove, Docs
```

---

## 🔒 Security - CRITICAL

### Protected by .gitignore

These are **automatically excluded** from GitHub:

- ✅ API keys and credentials (`config.yaml`, `settings.yaml`)
- ✅ Trading data files (`.csv` files)
- ✅ Logs and temporary files
- ✅ Python cache (`__pycache__/`)
- ✅ Large result files
- ✅ Backup directories

### Before Each Commit - Security Checklist

```powershell
# Always check what you're about to commit:
git status

# Review actual changes:
git diff

# If you see sensitive data, use:
git restore --staged <filename>  # Remove from staging
```

### What TO Commit ✅

- Python code (`.py` files)
- Strategy configurations (`.yaml` files in strategies/)
- Requirements and setup files
- Documentation (`.md` files)
- Small config templates (without real credentials)

### What NOT to Commit ❌

- API keys, passwords, tokens
- Large data files (CSV, JSON data)
- Log files
- Results that can be regenerated
- Credentials or secrets

---

## 🌿 Branching for Features

When working on major changes, use branches:

```powershell
# Create and switch to new branch
git checkout -b feature/new-ma-ribbon-strategy

# Make your changes and commit
git add .
git commit -m "Add: MA Ribbon strategy with dynamic filters"

# Push branch to GitHub
git push -u origin feature/new-ma-ribbon-strategy

# Switch back to main branch
git checkout main

# Merge your feature when ready
git merge feature/new-ma-ribbon-strategy
git push
```

---

## 🔄 Working from Multiple Machines

### On Machine A (e.g., Windows Desktop)

```powershell
# Make changes
git add .
git commit -m "Update: strategy parameters"
git push
```

### On Machine B (e.g., Cloud Server)

```powershell
# Get latest changes
git pull

# Continue working...
```

---

## 🔐 GitHub Authentication

### Option 1: Personal Access Token (Recommended)

1. Go to GitHub.com → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `repo` (full control of private repositories)
4. Copy the token
5. When prompted for password, use the **token** instead

### Option 2: SSH Keys (More Secure)

```powershell
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Add to GitHub: Settings → SSH and GPG keys → New SSH key

# Change remote to SSH
git remote set-url origin git@github.com:fxgdesigns1/DEEP_BACKTESTING.git
```

---

## 🛠️ Common Commands

```powershell
# View commit history
git log
git log --oneline  # Compact view

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Discard all local changes (CAREFUL!)
git reset --hard HEAD

# View all branches
git branch -a

# Delete local branch
git branch -d feature/old-branch

# Pull latest without merge conflicts
git stash  # Save local changes temporarily
git pull
git stash pop  # Restore local changes

# View what changed in a file
git log -p filename.py

# Compare with previous version
git diff HEAD~1 filename.py
```

---

## 📦 Repository Structure Best Practices

```
deep_backtesting/
├── strategies/          # Strategy code and configs
├── data/               # (gitignored) Local data
├── config/             # (gitignored) Real credentials
├── config_templates/   # Template configs (committed)
├── docs/               # Documentation
├── scripts/            # Utility scripts
├── tests/              # Test files
├── requirements.txt    # Python dependencies
├── README.md           # Project overview
└── .gitignore         # Exclusion rules
```

---

## 🐛 Troubleshooting

### "Permission denied" when pushing

```powershell
# Use personal access token as password
# Or set up SSH keys (see Authentication section)
```

### "Your branch is behind"

```powershell
git pull
# Resolve any conflicts
git push
```

### "Large files rejected"

```powershell
# Check .gitignore is working
git rm --cached large_file.csv
git commit -m "Remove large file"
git push
```

### Accidentally committed sensitive data

```powershell
# Remove from tracking
git rm --cached config/settings.yaml
git commit -m "Remove sensitive config"
git push

# IMPORTANT: The file is still in history!
# For complete removal, see:
# https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
```

### Merge conflicts

```powershell
git pull
# Edit conflicted files (look for <<<<<<< and >>>>>>>)
git add <resolved-file>
git commit -m "Resolve merge conflict"
git push
```

---

## 🎯 Workflow Summary

### Every Day
1. `git pull` - Get latest changes
2. Make changes to your code
3. `git add .` - Stage changes
4. `git commit -m "description"` - Commit changes
5. `git push` - Upload to GitHub

### Before Major Changes
1. Create a branch: `git checkout -b feature/name`
2. Work on the branch
3. Merge when complete

### Always Remember
- ✅ Review with `git status` before committing
- ✅ Check `.gitignore` is protecting sensitive files
- ✅ Write meaningful commit messages
- ✅ Pull before you push
- ❌ Never commit credentials or large data files

---

## 🌐 Viewing Your Code on GitHub

Visit: https://github.com/fxgdesigns1/DEEP_BACKTESTING

Here you can:
- Browse code online
- View commit history
- Create issues for bugs
- Review pull requests
- Access from anywhere

---

## 📚 Additional Resources

- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)
- [GitHub Docs](https://docs.github.com/)
- [Pro Git Book](https://git-scm.com/book/en/v2)

---

**Ready to push your first commit!** Run:
```powershell
git status
git add .
git commit -m "Initial commit: Deep backtesting trading system"
git push
```

