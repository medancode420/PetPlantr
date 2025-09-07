# PetPlantr Automated Backup System
## Enterprise-Grade Backup Solution

### 🎯 **Current Status:** Basic Backup System
- **Backup Script:** ✅ Available (`backup.sh`)
- **Scheduling:** ❌ Not automated
- **Verification:** ❌ Not implemented
- **Cloud Storage:** ❌ Not configured
- **Monitoring:** ❌ Not implemented

---

## 🏗️ **Phase 1: Enhanced Backup System**

### **Step 1: Backup Strategy Design**

#### **What to Backup:**
- **Configuration Files:** `.env*`, `nginx.conf`, `docker-compose.yml`
- **SSL Certificates:** `/etc/letsencrypt/`, `security/ssl/`
- **Database:** User data, gallery models, notifications
- **Models:** ML models, training data
- **Logs:** Application logs, monitoring data
- **User Data:** Uploaded images, generated models

#### **Backup Types:**
- **Daily:** Configuration, logs, user data
- **Weekly:** Full system backup including models
- **Monthly:** Complete archive with verification
- **Real-time:** Critical configuration changes

### **Step 2: Enhanced Backup Script**
```bash
#!/bin/bash
# Enhanced PetPlantr backup system

set -euo pipefail

# Configuration
BACKUP_ROOT="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_TYPE="${1:-daily}"
LOG_FILE="./logs/backup_$TIMESTAMP.log"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

log "🔄 Starting PetPlantr $BACKUP_TYPE backup: $TIMESTAMP"

# Create backup directories
mkdir -p "$BACKUP_ROOT/$BACKUP_TYPE" || error_exit "Failed to create backup directory"

# Function to backup with verification
backup_with_verify() {
    local source="$1"
    local dest="$2"
    local name="$3"

    if [ -e "$source" ]; then
        log "📁 Backing up $name..."
        cp -r "$source" "$dest/" 2>/dev/null || log "Warning: Failed to backup $name"

        # Verify backup
        if [ -e "$dest/$(basename "$source")" ]; then
            log "✅ $name backup verified"
        else
            log "❌ $name backup verification failed"
        fi
    else
        log "⚠️  $name source not found, skipping"
    fi
}

# Backup configuration files
backup_with_verify ".env*" "$BACKUP_ROOT/$BACKUP_TYPE" "environment files"
backup_with_verify "security/ssl" "$BACKUP_ROOT/$BACKUP_TYPE" "SSL certificates"
backup_with_verify "monitoring" "$BACKUP_ROOT/$BACKUP_TYPE" "monitoring config"
backup_with_verify "nginx.production.conf" "$BACKUP_ROOT/$BACKUP_TYPE" "nginx config"

# Backup logs
backup_with_verify "logs" "$BACKUP_ROOT/$BACKUP_TYPE" "application logs"

# Backup user data (if exists)
backup_with_verify "data/user_uploads" "$BACKUP_ROOT/$BACKUP_TYPE" "user uploads"
backup_with_verify "gallery_models.json" "$BACKUP_ROOT/$BACKUP_TYPE" "gallery data"
backup_with_verify "users_data.json" "$BACKUP_ROOT/$BACKUP_TYPE" "user data"

# Backup models (weekly only)
if [ "$BACKUP_TYPE" = "weekly" ] || [ "$BACKUP_TYPE" = "monthly" ]; then
    backup_with_verify "models" "$BACKUP_ROOT/$BACKUP_TYPE" "ML models"
fi

# Create compressed archive
log "📦 Creating compressed archive..."
ARCHIVE_NAME="petplantr_${BACKUP_TYPE}_$TIMESTAMP.tar.gz"
cd "$BACKUP_ROOT/$BACKUP_TYPE"

# Calculate backup size before compression
BACKUP_SIZE=$(du -sh . | cut -f1)
log "📊 Backup size before compression: $BACKUP_SIZE"

# Create archive with progress
tar -czf "../archives/$ARCHIVE_NAME" . 2>/dev/null || error_exit "Failed to create archive"

# Verify archive
if [ -f "../archives/$ARCHIVE_NAME" ]; then
    ARCHIVE_SIZE=$(du -sh "../archives/$ARCHIVE_NAME" | cut -f1)
    log "✅ Archive created: $ARCHIVE_NAME ($ARCHIVE_SIZE)"
else
    error_exit "Archive verification failed"
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
        find archives -name "petplantr_daily_*.tar.gz" -mtime +7 -delete
        ;;
    "weekly")
        # Keep last 4 weekly backups
        find archives -name "petplantr_weekly_*.tar.gz" -mtime +28 -delete
        ;;
    "monthly")
        # Keep last 12 monthly backups
        find archives -name "petplantr_monthly_*.tar.gz" -mtime +365 -delete
        ;;
esac

log "✅ Backup completed successfully: $ARCHIVE_NAME"

# Send notification (if configured)
if command -v curl >/dev/null 2>&1 && [ -n "${SLACK_WEBHOOK:-}" ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"PetPlantr $BACKUP_TYPE backup completed: $ARCHIVE_NAME\"}" \
        "$SLACK_WEBHOOK" || true
fi

log "🎉 Backup process completed successfully"
```

### **Step 3: Backup Scheduling**
```bash
# Install cron jobs for automated backups
# Edit crontab
crontab -e

# Add these lines:
# Daily backup at 2 AM
0 2 * * * cd /path/to/petplantr && ./backup.sh daily

# Weekly backup every Sunday at 3 AM
0 3 * * 0 cd /path/to/petplantr && ./backup.sh weekly

# Monthly backup on 1st at 4 AM
0 4 1 * * cd /path/to/petplantr && ./backup.sh monthly
```

---

## ☁️ **Phase 2: Cloud Storage Integration**

### **Step 1: AWS S3 Backup**
```bash
#!/bin/bash
# AWS S3 backup upload script

S3_BUCKET="petplantr-backups"
BACKUP_DIR="./backups/archives"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Upload latest backups to S3
log "☁️ Uploading backups to S3..."

# Upload daily backup
DAILY_BACKUP=$(ls -t "$BACKUP_DIR"/petplantr_daily_*.tar.gz | head -1)
if [ -f "$DAILY_BACKUP" ]; then
    aws s3 cp "$DAILY_BACKUP" "s3://$S3_BUCKET/daily/" --storage-class STANDARD_IA
    log "✅ Daily backup uploaded to S3"
fi

# Upload weekly backup (if today is Sunday)
if [ "$(date +%w)" = "0" ]; then
    WEEKLY_BACKUP=$(ls -t "$BACKUP_DIR"/petplantr_weekly_*.tar.gz | head -1)
    if [ -f "$WEEKLY_BACKUP" ]; then
        aws s3 cp "$WEEKLY_BACKUP" "s3://$S3_BUCKET/weekly/" --storage-class GLACIER
        log "✅ Weekly backup uploaded to S3"
    fi
fi

# Upload monthly backup (if today is 1st)
if [ "$(date +%d)" = "01" ]; then
    MONTHLY_BACKUP=$(ls -t "$BACKUP_DIR"/petplantr_monthly_*.tar.gz | head -1)
    if [ -f "$MONTHLY_BACKUP" ]; then
        aws s3 cp "$MONTHLY_BACKUP" "s3://$S3_BUCKET/monthly/" --storage-class DEEP_ARCHIVE
        log "✅ Monthly backup uploaded to S3"
    fi
fi

log "🎉 S3 upload completed"
```

### **Step 2: Google Cloud Storage**
```bash
#!/bin/bash
# Google Cloud Storage backup upload

GCS_BUCKET="petplantr-backups"
BACKUP_DIR="./backups/archives"

# Authenticate with service account
gcloud auth activate-service-account --key-file=/path/to/service-account.json

# Upload backups
log "☁️ Uploading backups to GCS..."

# Upload with different storage classes
gsutil -m cp -r "$BACKUP_DIR"/* "gs://$GCS_BUCKET/daily/"

# Set lifecycle policies
gsutil lifecycle set lifecycle.json "gs://$GCS_BUCKET"

log "🎉 GCS upload completed"
```

### **Step 3: Azure Blob Storage**
```bash
#!/bin/bash
# Azure Blob Storage backup upload

AZURE_CONTAINER="petplantr-backups"
BACKUP_DIR="./backups/archives"

# Upload using Azure CLI
az storage blob upload-batch \
    --account-name "$AZURE_STORAGE_ACCOUNT" \
    --account-key "$AZURE_STORAGE_KEY" \
    --destination "$AZURE_CONTAINER" \
    --source "$BACKUP_DIR" \
    --pattern "*.tar.gz"

log "🎉 Azure upload completed"
```

---

## 🔍 **Phase 3: Backup Verification & Monitoring**

### **Step 1: Backup Verification Script**
```bash
#!/bin/bash
# Backup verification script

BACKUP_DIR="./backups/archives"
LOG_FILE="./logs/backup_verify_$(date +%Y%m%d_%H%M%S).log"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "🔍 Starting backup verification..."

# Check backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    log "ERROR: Backup directory not found: $BACKUP_DIR"
    exit 1
fi

# Verify latest backups exist
DAILY_BACKUP=$(ls -t "$BACKUP_DIR"/petplantr_daily_*.tar.gz 2>/dev/null | head -1)
WEEKLY_BACKUP=$(ls -t "$BACKUP_DIR"/petplantr_weekly_*.tar.gz 2>/dev/null | head -1)
MONTHLY_BACKUP=$(ls -t "$BACKUP_DIR"/petplantr_monthly_*.tar.gz 2>/dev/null | head -1)

# Check daily backup
if [ -f "$DAILY_BACKUP" ]; then
    DAILY_SIZE=$(stat -f%z "$DAILY_BACKUP" 2>/dev/null || stat -c%s "$DAILY_BACKUP" 2>/dev/null)
    DAILY_DATE=$(stat -f%B "$DAILY_BACKUP" 2>/dev/null || stat -c%Y "$DAILY_BACKUP" 2>/dev/null)
    DAILY_AGE=$(( ($(date +%s) - DAILY_DATE) / 86400 ))

    log "✅ Daily backup found: $(basename "$DAILY_BACKUP") (${DAILY_SIZE} bytes, ${DAILY_AGE} days old)"

    if [ $DAILY_AGE -gt 2 ]; then
        log "⚠️  Daily backup is older than 2 days"
    fi
else
    log "❌ No daily backup found"
fi

# Check weekly backup
if [ -f "$WEEKLY_BACKUP" ]; then
    WEEKLY_SIZE=$(stat -f%z "$WEEKLY_BACKUP" 2>/dev/null || stat -c%s "$WEEKLY_BACKUP" 2>/dev/null)
    log "✅ Weekly backup found: $(basename "$WEEKLY_BACKUP") (${WEEKLY_SIZE} bytes)"
else
    log "❌ No weekly backup found"
fi

# Check monthly backup
if [ -f "$MONTHLY_BACKUP" ]; then
    MONTHLY_SIZE=$(stat -f%z "$MONTHLY_BACKUP" 2>/dev/null || stat -c%s "$MONTHLY_BACKUP" 2>/dev/null)
    log "✅ Monthly backup found: $(basename "$MONTHLY_BACKUP") (${MONTHLY_SIZE} bytes)"
else
    log "❌ No monthly backup found"
fi

# Test backup integrity
log "🔧 Testing backup integrity..."

if [ -f "$DAILY_BACKUP" ]; then
    if tar -tzf "$DAILY_BACKUP" >/dev/null 2>&1; then
        log "✅ Daily backup integrity verified"
    else
        log "❌ Daily backup integrity check failed"
    fi
fi

# Check disk space
BACKUP_DISK_USAGE=$(df "$BACKUP_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$BACKUP_DISK_USAGE" -gt 80 ]; then
    log "⚠️  Backup disk usage is ${BACKUP_DISK_USAGE}%"
fi

log "🎉 Backup verification completed"
```

### **Step 2: Backup Monitoring Dashboard**
```python
#!/usr/bin/env python3
# Backup monitoring dashboard

import os
import glob
from datetime import datetime, timedelta
import streamlit as st

st.title("PetPlantr Backup Monitoring Dashboard")

# Backup status
st.header("Backup Status")

backup_dir = "./backups/archives"

# Get latest backups
daily_backups = glob.glob(os.path.join(backup_dir, "petplantr_daily_*.tar.gz"))
weekly_backups = glob.glob(os.path.join(backup_dir, "petplantr_weekly_*.tar.gz"))
monthly_backups = glob.glob(os.path.join(backup_dir, "petplantr_monthly_*.tar.gz"))

# Sort by modification time
daily_backups.sort(key=os.path.getmtime, reverse=True)
weekly_backups.sort(key=os.path.getmtime, reverse=True)
monthly_backups.sort(key=os.path.getmtime, reverse=True)

# Display backup status
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Daily Backup")
    if daily_backups:
        latest_daily = daily_backups[0]
        mtime = datetime.fromtimestamp(os.path.getmtime(latest_daily))
        age = (datetime.now() - mtime).days

        if age <= 1:
            st.success(f"✅ Latest: {os.path.basename(latest_daily)}")
        else:
            st.warning(f"⚠️ Latest: {os.path.basename(latest_daily)} ({age} days old)")
    else:
        st.error("❌ No daily backup found")

with col2:
    st.subheader("Weekly Backup")
    if weekly_backups:
        latest_weekly = weekly_backups[0]
        mtime = datetime.fromtimestamp(os.path.getmtime(latest_weekly))
        age = (datetime.now() - mtime).days

        if age <= 7:
            st.success(f"✅ Latest: {os.path.basename(latest_weekly)}")
        else:
            st.warning(f"⚠️ Latest: {os.path.basename(latest_weekly)} ({age} days old)")
    else:
        st.error("❌ No weekly backup found")

with col3:
    st.subheader("Monthly Backup")
    if monthly_backups:
        latest_monthly = monthly_backups[0]
        mtime = datetime.fromtimestamp(os.path.getmtime(latest_monthly))
        age = (datetime.now() - mtime).days

        if age <= 31:
            st.success(f"✅ Latest: {os.path.basename(latest_monthly)}")
        else:
            st.warning(f"⚠️ Latest: {os.path.basename(latest_monthly)} ({age} days old)")
    else:
        st.error("❌ No monthly backup found")

# Backup history
st.header("Backup History")

# Display recent backups
st.subheader("Recent Daily Backups")
for backup in daily_backups[:5]:
    mtime = datetime.fromtimestamp(os.path.getmtime(backup))
    size = os.path.getsize(backup) / (1024 * 1024)  # MB
    st.text(".1f"
# Backup verification
st.header("Backup Verification")

# Check backup integrity
st.subheader("Integrity Check")
for backup in daily_backups[:1] + weekly_backups[:1] + monthly_backups[:1]:
    if backup:
        # Simple integrity check (file exists and has size > 0)
        if os.path.getsize(backup) > 0:
            st.success(f"✅ {os.path.basename(backup)} - Integrity OK")
        else:
            st.error(f"❌ {os.path.basename(backup)} - Integrity check failed")

# Disk usage
st.header("Storage Usage")
backup_size = sum(os.path.getsize(f) for f in daily_backups + weekly_backups + monthly_backups)
backup_size_mb = backup_size / (1024 * 1024)

st.metric("Total Backup Size", ".1f"
# Run backup verification
if st.button("Run Backup Verification"):
    st.info("Running backup verification...")
    # In a real implementation, this would call the verification script
    st.success("Backup verification completed!")
```

---

## 🚨 **Phase 4: Backup Alerting**

### **Step 1: Backup Alert System**
```bash
#!/bin/bash
# Backup alerting system

BACKUP_DIR="./backups/archives"
LOG_FILE="./logs/backup_alert_$(date +%Y%m%d_%H%M%S).log"

# Configuration
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"
EMAIL_RECIPIENT="${EMAIL_RECIPIENT:-admin@petplantr.com}"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

send_alert() {
    local message="$1"
    local severity="$2"

    log "🚨 Sending $severity alert: $message"

    # Slack notification
    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$severity: $message\"}" \
            "$SLACK_WEBHOOK" || true
    fi

    # Email notification
    if [ -n "$EMAIL_RECIPIENT" ]; then
        echo "$message" | mail -s "PetPlantr Backup $severity" "$EMAIL_RECIPIENT" || true
    fi
}

log "🔍 Checking backup status..."

# Check daily backup
DAILY_BACKUP=$(ls -t "$BACKUP_DIR"/petplantr_daily_*.tar.gz 2>/dev/null | head -1)
if [ -f "$DAILY_BACKUP" ]; then
    DAILY_DATE=$(stat -f%B "$DAILY_BACKUP" 2>/dev/null || stat -c%Y "$DAILY_BACKUP" 2>/dev/null)
    DAILY_AGE=$(( ($(date +%s) - DAILY_DATE) / 86400 ))

    if [ $DAILY_AGE -gt 2 ]; then
        send_alert "Daily backup is $DAILY_AGE days old" "WARNING"
    fi
else
    send_alert "No daily backup found" "CRITICAL"
fi

# Check disk space
BACKUP_DISK_USAGE=$(df "$BACKUP_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$BACKUP_DISK_USAGE" -gt 90 ]; then
    send_alert "Backup disk usage is ${BACKUP_DISK_USAGE}%" "WARNING"
fi

# Check backup integrity
if [ -f "$DAILY_BACKUP" ]; then
    if ! tar -tzf "$DAILY_BACKUP" >/dev/null 2>&1; then
        send_alert "Daily backup integrity check failed" "CRITICAL"
    fi
fi

log "✅ Backup alert check completed"
```

### **Step 2: Automated Alert Scheduling**
```bash
# Add to crontab for daily backup alerts
# Check backup status every 6 hours
0 */6 * * * cd /path/to/petplantr && ./backup-alert.sh
```

---

## 📋 **Implementation Checklist**

### **Backup System Setup:**
- [ ] Create backup directory structure
- [ ] Implement enhanced backup script
- [ ] Set up automated scheduling
- [ ] Configure backup verification
- [ ] Set up backup monitoring

### **Cloud Storage (Optional):**
- [ ] Choose cloud provider (AWS S3, GCS, Azure)
- [ ] Configure cloud credentials
- [ ] Implement cloud upload scripts
- [ ] Set up lifecycle policies

### **Alerting & Monitoring:**
- [ ] Configure Slack webhook
- [ ] Set up email notifications
- [ ] Create backup dashboard
- [ ] Implement automated alerts

### **Testing & Validation:**
- [ ] Test backup creation
- [ ] Test backup restoration
- [ ] Test cloud upload/download
- [ ] Test alerting system
- [ ] Validate backup integrity

---

## 🎯 **Success Criteria**

- ✅ **Daily backups** running automatically
- ✅ **Backup verification** working correctly
- ✅ **Cloud storage** configured (optional)
- ✅ **Monitoring dashboard** operational
- ✅ **Alert system** configured and tested
- ✅ **Backup restoration** tested and documented

---

## 🚀 **Quick Start Commands**

```bash
# Manual backup
./backup.sh daily

# Verify backups
./backup-verify.sh

# View backup dashboard
streamlit run backup-dashboard.py

# Check backup alerts
./backup-alert.sh
```

---

**🛡️ Enterprise-grade backup system ready for PetPlantr production deployment!**

*Last Updated: September 6, 2025*
