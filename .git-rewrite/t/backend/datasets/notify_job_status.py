#!/usr/bin/env python3
"""
PetPlantr Job Status Slack Notifications
Sends notifications to #ops-alerts channel when training jobs complete

Usage:
    python notify_job_status.py --status success --job-type "Stage 1 UNet128" --duration "45min" --cost "$0.60"
    python notify_job_status.py --status failure --job-type "Stage 1 UNet128" --error "OOM Error"
"""

import argparse
import requests
import json
import os
from datetime import datetime
from typing import Optional

# Slack webhook URL for #ops-alerts channel
# Set this as environment variable: SLACK_WEBHOOK_URL
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL', '')

def send_slack_notification(
    status: str,
    job_type: str,
    duration: Optional[str] = None,
    cost: Optional[str] = None,
    error: Optional[str] = None,
    job_id: Optional[str] = None,
    weights_path: Optional[str] = None
):
    """Send Slack notification for job status"""
    
    if not SLACK_WEBHOOK_URL:
        print("⚠️  SLACK_WEBHOOK_URL not set - notification skipped")
        return False
    
    # Create notification based on status
    if status.lower() == 'success':
        emoji = "✅"
        color = "#36a64f"  # Green
        title = f"Training Complete: {job_type}"
        
        fields = []
        if duration:
            fields.append({"title": "Duration", "value": duration, "short": True})
        if cost:
            fields.append({"title": "Cost", "value": cost, "short": True})
        if job_id:
            fields.append({"title": "Job ID", "value": f"`{job_id}`", "short": True})
        if weights_path:
            fields.append({"title": "Weights", "value": f"`{weights_path}`", "short": False})
            
        text = f"{emoji} {job_type} finished successfully!"
        
    elif status.lower() == 'failure':
        emoji = "❌"
        color = "#d63638"  # Red
        title = f"Training Failed: {job_type}"
        
        fields = []
        if error:
            fields.append({"title": "Error", "value": error, "short": False})
        if job_id:
            fields.append({"title": "Job ID", "value": f"`{job_id}`", "short": True})
            
        text = f"{emoji} {job_type} failed - investigation needed"
        
    elif status.lower() == 'started':
        emoji = "🚀"
        color = "#ffaa00"  # Orange
        title = f"Training Started: {job_type}"
        
        fields = []
        if job_id:
            fields.append({"title": "Job ID", "value": f"`{job_id}`", "short": True})
            
        text = f"{emoji} {job_type} training has started"
        
    else:
        emoji = "ℹ️"
        color = "#3367d6"  # Blue
        title = f"Training Update: {job_type}"
        text = f"{emoji} {job_type} status: {status}"
        fields = []
    
    # Prepare Slack message payload
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    payload = {
        "username": "PetPlantr Training Bot",
        "icon_emoji": ":robot_face:",
        "channel": "#ops-alerts",
        "attachments": [
            {
                "color": color,
                "title": title,
                "text": text,
                "fields": fields,
                "footer": "PetPlantr Training Pipeline",
                "ts": int(datetime.now().timestamp())
            }
        ]
    }
    
    # Send notification
    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Slack notification sent: {title}")
            return True
        else:
            print(f"❌ Slack notification failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Slack notification error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Send PetPlantr job status to Slack')
    parser.add_argument('--status', required=True, 
                       choices=['success', 'failure', 'started', 'running', 'cancelled'],
                       help='Job status')
    parser.add_argument('--job-type', required=True, 
                       help='Type of job (e.g., "Stage 1 UNet128")')
    parser.add_argument('--duration', 
                       help='Job duration (e.g., "45min")')
    parser.add_argument('--cost', 
                       help='Job cost (e.g., "$0.60")')
    parser.add_argument('--error', 
                       help='Error message if job failed')
    parser.add_argument('--job-id', 
                       help='Modal job ID')
    parser.add_argument('--weights-path', 
                       help='S3 path to saved weights')
    
    args = parser.parse_args()
    
    success = send_slack_notification(
        status=args.status,
        job_type=args.job_type,
        duration=args.duration,
        cost=args.cost,
        error=args.error,
        job_id=args.job_id,
        weights_path=args.weights_path
    )
    
    if success:
        print("📤 Notification sent successfully")
    else:
        print("📤 Notification failed")
        exit(1)

if __name__ == "__main__":
    main()
