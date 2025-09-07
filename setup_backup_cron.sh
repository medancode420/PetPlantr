#!/bin/bash
# PetPlantr cron job setup for automated backups

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup-enhanced.sh"
VERIFY_SCRIPT="$SCRIPT_DIR/verify_backup.sh"

# Function to add cron job
add_cron_job() {
    local schedule="$1"
    local command="$2"
    local comment="$3"

    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "$comment"; then
        echo "⚠️  Cron job already exists: $comment"
        return
    fi

    # Add cron job
    (crontab -l 2>/dev/null; echo "# $comment") | crontab -
    (crontab -l 2>/dev/null; echo "$schedule $command # $comment") | crontab -

    echo "✅ Added cron job: $comment"
}

echo "🔧 Setting up PetPlantr automated backup system..."

# Make scripts executable
chmod +x "$BACKUP_SCRIPT"
chmod +x "$VERIFY_SCRIPT"
echo "✅ Made backup scripts executable"

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"
echo "✅ Created logs directory"

# Setup daily backup (runs at 2 AM)
add_cron_job "0 2 * * *" "cd $SCRIPT_DIR && ./backup-enhanced.sh daily" "PetPlantr Daily Backup"

# Setup weekly backup (runs every Sunday at 3 AM)
add_cron_job "0 3 * * 0" "cd $SCRIPT_DIR && ./backup-enhanced.sh weekly" "PetPlantr Weekly Backup"

# Setup monthly backup (runs on 1st of month at 4 AM)
add_cron_job "0 4 1 * *" "cd $SCRIPT_DIR && ./backup-enhanced.sh monthly" "PetPlantr Monthly Backup"

# Setup daily verification (runs at 6 AM)
add_cron_job "0 6 * * *" "cd $SCRIPT_DIR && ./verify_backup.sh" "PetPlantr Backup Verification"

echo ""
echo "📋 Current cron jobs:"
crontab -l | grep -E "(PetPlantr|backup)" || echo "No PetPlantr cron jobs found"

echo ""
echo "🎉 Automated backup system setup completed!"
echo ""
echo "📅 Backup Schedule:"
echo "  • Daily: 2:00 AM"
echo "  • Weekly: Sunday 3:00 AM"
echo "  • Monthly: 1st of month 4:00 AM"
echo "  • Verification: Daily 6:00 AM"
echo ""
echo "📁 Backup files will be stored in: $SCRIPT_DIR/backups/archives/"
echo "📝 Logs will be stored in: $SCRIPT_DIR/logs/"
echo ""
echo "🔧 To modify schedules, run: crontab -e"
echo "🔍 To view current jobs: crontab -l"
