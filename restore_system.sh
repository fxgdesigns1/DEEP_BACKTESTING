#!/bin/bash
# PROFESSIONAL SYSTEM RESTORE SCRIPT
# Use this to restore from backup

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file>"
    echo "Available backups:"
    ls -la SYSTEM_BACKUPS/DAILY_BACKUPS/
    exit 1
fi

BACKUP_FILE="$1"
RESTORE_DIR="RESTORED_SYSTEM_$(date +%Y%m%d_%H%M%S)"

echo "Restoring from: $BACKUP_FILE"
echo "To directory: $RESTORE_DIR"

# Create restore directory
mkdir -p "$RESTORE_DIR"

# Extract backup
unzip "$BACKUP_FILE" -d "$RESTORE_DIR"

echo "System restored to: $RESTORE_DIR"
echo "Review the restored files before replacing current system"
