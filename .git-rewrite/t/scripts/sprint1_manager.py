#!/usr/bin/env python3
"""
Sprint 1 Management Script
Moves Sprint 1 GitHub issues to "In Progress" and generates status reports
"""

import json
import os
import requests
from datetime import datetime

def load_issues():
    """Load the enhanced issues file"""
    with open('reports/github_issues_tier1_enhanced.json', 'r') as f:
        return json.load(f)

def get_github_repo():
    """Get GitHub repo from git remote"""
    import subprocess
    try:
        result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            url = result.stdout.strip()
            if 'github.com' in url:
                if url.startswith('git@github.com:'):
                    return url.replace('git@github.com:', '').replace('.git', '')
                elif 'github.com/' in url:
                    return url.split('github.com/')[1].replace('.git', '')
    except:
        pass
    return None

def get_sprint1_issues(issues_data):
    """Filter issues for Sprint 1 (Epic E-4)"""
    sprint1_issues = []
    for issue in issues_data.get('issues', []):
        labels = issue.get('labels', [])
        # Look for epic-e-4 label (Enhanced AI Pipeline)
        if any('epic-e-4' in label for label in labels):
            sprint1_issues.append(issue)
    return sprint1_issues

def main():
    print("🚀 Sprint 1 Management - Enhanced AI Pipeline")
    print("=" * 50)
    
    # Load issues
    try:
        issues_data = load_issues()
        print(f"✅ Loaded issues from enhanced JSON")
    except FileNotFoundError:
        print("❌ Enhanced issues file not found")
        return 1
    
    # Get Sprint 1 issues (E-4 Epic)
    sprint1_issues = get_sprint1_issues(issues_data)
    print(f"📊 Found {len(sprint1_issues)} Sprint 1 issues (Epic E-4)")
    
    # Display Sprint 1 issues
    print("\n🎯 Sprint 1 Issues (Enhanced AI Pipeline):")
    for i, issue in enumerate(sprint1_issues, 1):
        print(f"  {i}. {issue['title']}")
        labels = [l for l in issue.get('labels', []) if not l.startswith('epic-')]
        if labels:
            print(f"     Labels: {', '.join(labels)}")
    
    # Check GitHub setup
    repo = get_github_repo()
    token = os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN')
    
    if repo and token:
        print(f"\n🔗 GitHub Repo: {repo}")
        print(f"🔑 GitHub Token: {token[:8]}...")
        
        # TODO: Move issues to "In Progress" when ready
        print("\n⏳ Issues ready to move to 'In Progress' status")
    else:
        print("\n💡 To manage GitHub issues:")
        print("   export GITHUB_TOKEN=your_token")
        print("   Or run: python scripts/seed_gh_issues_v2.py --repo USER/REPO")
    
    # Generate Sprint status
    status = {
        "sprint": "Sprint 1",
        "epic": "E-4: Enhanced AI Pipeline Features", 
        "start_date": "2025-07-11",
        "total_issues": len(sprint1_issues),
        "status": "Ready to Start",
        "issues": [
            {
                "title": issue["title"],
                "labels": issue.get("labels", []),
                "status": "Backlog"
            } for issue in sprint1_issues
        ]
    }
    
    # Save status report
    with open('reports/sprint1_status.json', 'w') as f:
        json.dump(status, f, indent=2)
    
    print(f"\n📋 Sprint status saved to: reports/sprint1_status.json")
    print("\n🎉 Sprint 1 Ready!")
    print("Next steps:")
    print("  1. Move issues to 'In Progress' when development starts")
    print("  2. Run smoke tests: ./smoke-test.sh")
    print("  3. Start frontend development: cd frontend && npm run dev")
    
    return 0

if __name__ == "__main__":
    exit(main())
