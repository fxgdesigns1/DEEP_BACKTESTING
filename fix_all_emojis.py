"""
Remove all emojis from Python scripts to avoid Windows console encoding issues
"""

import re
from pathlib import Path

def remove_emojis(text):
    """Remove all emojis and special unicode characters"""
    # Remove emoji ranges
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    
    text = emoji_pattern.sub('', text)
    
    # Replace common emojis with text
    replacements = {
        '✅': '[OK]',
        '❌': '[ERROR]',
        '⚠️': '[WARNING]',
        '⏱️': '[TIME]',
        '📊': '[DATA]',
        '💾': '[SAVE]',
        '🎯': '[TARGET]',
        '📁': '[FOLDER]',
        '📄': '[FILE]',
        '⏰': '[CLOCK]',
        '🚀': '[LAUNCH]',
        '🌙': '[NIGHT]',
        '💤': '[SLEEP]',
        '🎉': '[COMPLETE]',
        '✨': '[STAR]',
        '→': '->',
        '←': '<-',
        '↑': '^',
        '↓': 'v',
    }
    
    for emoji, replacement in replacements.items():
        text = text.replace(emoji, replacement)
    
    return text

# Fix all Python files
files_to_fix = [
    'efficient_futures_downloader.py',
    'run_optimization_clean.py',
    'comprehensive_futures_optimizer.py'
]

print("\n" + "="*80)
print("REMOVING ALL EMOJIS FROM SCRIPTS")
print("="*80 + "\n")

for filename in files_to_fix:
    filepath = Path(filename)
    if filepath.exists():
        print(f"Fixing: {filename}")
        
        # Read file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove emojis
        cleaned = remove_emojis(content)
        
        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        
        print(f"  [OK] Cleaned: {filename}\n")
    else:
        print(f"  [SKIP] Not found: {filename}\n")

print("="*80)
print("[OK] ALL SCRIPTS CLEANED!")
print("="*80 + "\n")





