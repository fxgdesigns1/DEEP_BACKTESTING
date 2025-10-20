# Configuration Templates

## 🔒 Security Notice

**NEVER commit real credentials to GitHub!**

This directory contains template configuration files with placeholder values.

## Setup Instructions

### 1. Copy Templates to Config Directory

```powershell
# Copy templates to config/ directory
Copy-Item config_templates/config.yaml.template config/config.yaml
Copy-Item config_templates/settings.yaml.template config/settings.yaml
```

### 2. Add Your Real Credentials

Edit the files in `config/` directory and replace all placeholder values:

**config/config.yaml:**
- `YOUR_TELEGRAM_BOT_TOKEN_HERE` → Your Telegram bot token
- `YOUR_TELEGRAM_CHAT_ID_HERE` → Your Telegram chat ID

**config/settings.yaml:**
- `YOUR_ALPHAVANTAGE_API_KEY_HERE` → Your Alpha Vantage API key
- `YOUR_OANDA_API_KEY_HERE` → Your OANDA API key
- `YOUR_OANDA_ACCOUNT_ID_HERE` → Your OANDA account ID
- `YOUR_MARKETAUX_API_KEY_HERE` → Your Marketaux API key
- `YOUR_NEWSDATA_API_KEY_HERE` → Your NewsData API key

### 3. Verify Protection

The `.gitignore` file ensures that `config/config.yaml` and `config/settings.yaml` are **never committed** to GitHub.

To verify:
```powershell
git status
# config/config.yaml and config/settings.yaml should NOT appear in the list
```

## Getting API Keys

### Alpha Vantage (Market Data)
- Free tier: https://www.alphavantage.co/support/#api-key
- Limits: 5 requests/minute, 500 requests/day

### OANDA (Trading)
- Practice account: https://www.oanda.com/account/register
- Get API key from account dashboard

### Marketaux (News)
- Free tier: https://www.marketaux.com/
- 100 requests/minute

### NewsData.io (Additional News)
- Free tier: https://newsdata.io/
- 10 requests/minute

## Configuration Files

- ✅ **config_templates/** - Template files (committed to GitHub)
- ❌ **config/** - Real credentials (NEVER committed to GitHub)

## Security Checklist

Before pushing to GitHub:

```powershell
# Check git status
git status

# Ensure these files are NOT listed:
# - config/config.yaml
# - config/settings.yaml
# - Any file with credentials

# If accidentally staged, remove them:
git restore --staged config/config.yaml
git restore --staged config/settings.yaml
```

## Environment Variables (Alternative)

For extra security, you can use environment variables instead of config files:

```powershell
# PowerShell
$env:TELEGRAM_TOKEN="your_token_here"
$env:ALPHAVANTAGE_API_KEY="your_key_here"

# Or create .env file (also gitignored)
```

Then modify your code to read from environment variables:

```python
import os
telegram_token = os.getenv('TELEGRAM_TOKEN')
```

