#!/bin/bash
# Automated backup system for PetPlantr

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="petplantr_backup_$TIMESTAMP"

echo "🔄 Starting PetPlantr backup: $BACKUP_NAME"

# Create backup directory
mkdir -p "$BACKUP_DIR/daily/$BACKUP_NAME"

# Backup configuration files
echo "📁 Backing up configuration..."
cp -r .env* "$BACKUP_DIR/daily/$BACKUP_NAME/" 2>/dev/null || true
cp -r security/ssl "$BACKUP_DIR/daily/$BACKUP_NAME/" 2>/dev/null || true
cp -r monitoring "$BACKUP_DIR/daily/$BACKUP_NAME/" 2>/dev/null || true

# Backup logs
echo "📋 Backing up logs..."
cp -r logs "$BACKUP_DIR/daily/$BACKUP_NAME/" 2>/dev/null || true

# Create compressed archive
echo "📦 Creating compressed archive..."
cd "$BACKUP_DIR/daily"
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME"

echo "✅ Backup completed: $BACKUP_DIR/daily/${BACKUP_NAME}.tar.gz"

# Cleanup old backups (keep last 7 daily, 4 weekly, 12 monthly)
echo "🧹 Cleaning up old backups..."
find "$BACKUP_DIR/daily" -name "*.tar.gz" -mtime +7 -delete
find "$BACKUP_DIR/weekly" -name "*.tar.gz" -mtime +28 -delete
find "$BACKUP_DIR/monthly" -name "*.tar.gz" -mtime +365 -delete

echo "🎉 Backup process completed successfully"
