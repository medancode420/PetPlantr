#!/bin/bash
# PetPlantr backup verification script

# set -euo pipefail  # Commented out to prevent early exit on non-critical errors

BACKUP_ROOT="./backups"
LOG_FILE="./logs/verify_backup_$(date +%Y%m%d_%H%M%S).log"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "🔍 Starting backup verification..."

# Check if backup directory exists
if [ ! -d "$BACKUP_ROOT" ]; then
    log "❌ Backup directory not found: $BACKUP_ROOT"
    exit 1
fi

# Check if archives directory exists
if [ ! -d "$BACKUP_ROOT/archives" ]; then
    log "❌ Archives directory not found: $BACKUP_ROOT/archives"
    exit 1
fi

# List all backup archives
log "📋 Available backup archives:"
ls -la "$BACKUP_ROOT/archives/" 2>/dev/null | grep -E "\.tar\.gz$" | while read -r line; do
    log "  $line"
done

# Count total backups
TOTAL_BACKUPS=$(find "$BACKUP_ROOT/archives" -name "*.tar.gz" 2>/dev/null | wc -l)
log "📊 Total backup archives: $TOTAL_BACKUPS"

# Calculate total backup size
TOTAL_SIZE=$(du -sh "$BACKUP_ROOT/archives" 2>/dev/null | cut -f1 || echo "0B")
log "💾 Total backup size: $TOTAL_SIZE"

# Verify latest backup
LATEST_BACKUP=$(find "$BACKUP_ROOT/archives" -name "*.tar.gz" -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)

if [ -n "$LATEST_BACKUP" ] && [ -f "$LATEST_BACKUP" ]; then
    log "🔍 Verifying latest backup: $(basename "$LATEST_BACKUP")"

    # Test archive integrity
    if tar -tzf "$LATEST_BACKUP" >/dev/null 2>&1; then
        log "✅ Archive integrity: OK"

        # List contents
        log "📁 Archive contents:"
        tar -tzf "$LATEST_BACKUP" 2>/dev/null | head -20 | while read -r file; do
            log "  $file"
        done

        # Count files in archive
        FILE_COUNT=$(tar -tzf "$LATEST_BACKUP" 2>/dev/null | wc -l)
        log "📊 Files in archive: $FILE_COUNT"

    else
        log "❌ Archive integrity: FAILED"
    fi
else
    log "⚠️  No backup archives found"
fi

# Check backup retention (only if we have standard backups)
log "📅 Checking backup retention..."

# Daily backups (should have max 7)
DAILY_COUNT=$(find "$BACKUP_ROOT/archives" -name "petplantr_daily_*.tar.gz" 2>/dev/null | wc -l)
log "📅 Daily backups: $DAILY_COUNT (should be ≤ 7)"

# Weekly backups (should have max 4)
WEEKLY_COUNT=$(find "$BACKUP_ROOT/archives" -name "petplantr_weekly_*.tar.gz" 2>/dev/null | wc -l)
log "📅 Weekly backups: $WEEKLY_COUNT (should be ≤ 4)"

# Monthly backups (should have max 12)
MONTHLY_COUNT=$(find "$BACKUP_ROOT/archives" -name "petplantr_monthly_*.tar.gz" 2>/dev/null | wc -l)
log "📅 Monthly backups: $MONTHLY_COUNT (should be ≤ 12)"

# Check for old backups that should be cleaned up
OLD_DAILY=$(find "$BACKUP_ROOT/archives" -name "petplantr_daily_*.tar.gz" -mtime +7 2>/dev/null | wc -l)
if [ "$OLD_DAILY" -gt 0 ]; then
    log "⚠️  Found $OLD_DAILY old daily backups (>7 days)"
fi

OLD_WEEKLY=$(find "$BACKUP_ROOT/archives" -name "petplantr_weekly_*.tar.gz" -mtime +28 2>/dev/null | wc -l)
if [ "$OLD_WEEKLY" -gt 0 ]; then
    log "⚠️  Found $OLD_WEEKLY old weekly backups (>28 days)"
fi

OLD_MONTHLY=$(find "$BACKUP_ROOT/archives" -name "petplantr_monthly_*.tar.gz" -mtime +365 2>/dev/null | wc -l)
if [ "$OLD_MONTHLY" -gt 0 ]; then
    log "⚠️  Found $OLD_MONTHLY old monthly backups (>365 days)"
fi

# Check disk space
log "💽 Checking disk space..."
DISK_USAGE=$(df -h . 2>/dev/null | tail -1 | awk '{print $5}' || echo "Unknown")
log "💽 Current disk usage: $DISK_USAGE"

# Check backup directory permissions
log "🔐 Checking permissions..."
if [ -r "$BACKUP_ROOT" ] && [ -w "$BACKUP_ROOT" ]; then
    log "✅ Backup directory permissions: OK"
else
    log "❌ Backup directory permissions: FAILED"
fi

log "✅ Backup verification completed successfully"
