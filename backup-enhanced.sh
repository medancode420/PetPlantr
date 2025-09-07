#!/bin/bash
# Enhanced PetPlantr backup system with verification and monitoring

set -euo pipefail

# Configuration
BACKUP_ROOT="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_TYPE="${1:-daily}"
LOG_FILE="./logs/backup_$TIMESTAMP.log"
NOTIFICATION_WEBHOOK="${SLACK_WEBHOOK:-}"

# Create log directory if it doesn't exist
mkdir -p "./logs"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    send_notification "❌ Backup Failed" "$1"
    exit 1
}

# Notification function
send_notification() {
    local title="$1"
    local message="$2"

    if [ -n "$NOTIFICATION_WEBHOOK" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$title: $message\"}" \
            "$NOTIFICATION_WEBHOOK" 2>/dev/null || true
    fi
}

log "🔄 Starting PetPlantr $BACKUP_TYPE backup: $TIMESTAMP"

# Create backup directories
mkdir -p "$BACKUP_ROOT/$BACKUP_TYPE" || error_exit "Failed to create backup directory"
mkdir -p "$BACKUP_ROOT/archives" || error_exit "Failed to create archives directory"

# Function to backup with verification
backup_with_verify() {
    local source="$1"
    local name="$2"

    if [ -e "$source" ]; then
        log "📁 Backing up $name..."
        cp -r "$source" "$BACKUP_ROOT/$BACKUP_TYPE/" 2>/dev/null || log "Warning: Failed to backup $name"

        # Verify backup
        if [ -e "$BACKUP_ROOT/$BACKUP_TYPE/$(basename "$source")" ]; then
            log "✅ $name backup verified"
        else
            log "❌ $name backup verification failed"
        fi
    else
        log "⚠️  $name source not found, skipping"
    fi
}

# Backup configuration files
backup_with_verify ".env*" "environment files"
backup_with_verify "security/ssl" "SSL certificates"
backup_with_verify "monitoring" "monitoring config"
backup_with_verify "nginx.production.conf" "nginx config"

# Backup logs
backup_with_verify "logs" "application logs"

# Backup user data (if exists)
backup_with_verify "data/user_uploads" "user uploads"
backup_with_verify "gallery_models.json" "gallery data"
backup_with_verify "users_data.json" "user data"
backup_with_verify "notifications_data.json" "notifications data"

# Backup models (weekly only)
if [ "$BACKUP_TYPE" = "weekly" ] || [ "$BACKUP_TYPE" = "monthly" ]; then
    backup_with_verify "models" "ML models"
fi

# Create compressed archive
log "📦 Creating compressed archive..."
ARCHIVE_NAME="petplantr_${BACKUP_TYPE}_$TIMESTAMP.tar.gz"
cd "$BACKUP_ROOT/$BACKUP_TYPE"

# Calculate backup size before compression
BACKUP_SIZE=$(du -sh . 2>/dev/null | cut -f1 || echo "0B")
log "📊 Backup size before compression: $BACKUP_SIZE"

# Create archive with verification
if tar -czf "../archives/$ARCHIVE_NAME" . 2>/dev/null; then
    # Verify archive
    if [ -f "../archives/$ARCHIVE_NAME" ]; then
        ARCHIVE_SIZE=$(du -sh "../archives/$ARCHIVE_NAME" 2>/dev/null | cut -f1 || echo "0B")
        log "✅ Archive created: $ARCHIVE_NAME ($ARCHIVE_SIZE)"

        # Test archive integrity
        if tar -tzf "../archives/$ARCHIVE_NAME" >/dev/null 2>&1; then
            log "✅ Archive integrity verified"
        else
            log "❌ Archive integrity check failed"
        fi
    else
        error_exit "Archive creation failed"
    fi
else
    error_exit "Failed to create archive"
fi

# Cleanup temporary files
cd ..
rm -rf "$BACKUP_TYPE"

log "🧹 Cleaning up temporary files..."

# Cleanup old backups
log "🧹 Cleaning up old backups..."

case "$BACKUP_TYPE" in
    "daily")
        # Keep last 7 daily backups
        find archives -name "petplantr_daily_*.tar.gz" -mtime +7 -delete 2>/dev/null || true
        ;;
    "weekly")
        # Keep last 4 weekly backups
        find archives -name "petplantr_weekly_*.tar.gz" -mtime +28 -delete 2>/dev/null || true
        ;;
    "monthly")
        # Keep last 12 monthly backups
        find archives -name "petplantr_monthly_*.tar.gz" -mtime +365 -delete 2>/dev/null || true
        ;;
esac

# Calculate total backup storage used
TOTAL_BACKUP_SIZE=$(du -sh archives 2>/dev/null | cut -f1 || echo "0B")
log "💾 Total backup storage used: $TOTAL_BACKUP_SIZE"

log "✅ Backup completed successfully: $ARCHIVE_NAME"

# Send success notification
send_notification "✅ Backup Completed" "PetPlantr $BACKUP_TYPE backup completed: $ARCHIVE_NAME ($ARCHIVE_SIZE)"

log "🎉 Backup process completed successfully"
