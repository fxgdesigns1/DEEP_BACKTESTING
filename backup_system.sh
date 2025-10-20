#!/bin/bash
# PROFESSIONAL SYSTEM BACKUP SCRIPT
# Run this daily to backup your system

BACKUP_DIR="SYSTEM_BACKUPS/DAILY_BACKUPS"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="professional_system_backup_$DATE.zip"

echo "Creating backup: $BACKUP_FILE"

# Create backup
zip -r "$BACKUP_DIR/$BACKUP_FILE" PROFESSIONAL_SYSTEM/ DOCUMENTATION/ -x "*.pyc" "__pycache__/*"

# Keep only last 30 days of backups
find "$BACKUP_DIR" -name "professional_system_backup_*.zip" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
