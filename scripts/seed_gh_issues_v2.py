#!/usr/bin/env python3
"""
GitHub Issues Seeding Script for PetPlantr Tier-1 Backlog
Generated from: tier1_priority_backlog.ipynb
Created: 2024-01-15 10:30:00
"""

import json
import requests
import os
import argparse
from pathlib import Path

def load_github_issues(file_path: str):
    """Load GitHub issues from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_github_issue(token: str, repo: str, issue_data: dict):
    """Create a GitHub issue via API"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    url = f"https://api.github.com/repos/{repo}/issues"

    payload = {
        "title": issue_data["title"],
        "body": issue_data["body"],
        "labels": issue_data["labels"]
    }

    response = requests.post(url, headers=headers, json=payload)
    return response

def main():
    parser = argparse.ArgumentParser(description="Seed GitHub issues for PetPlantr Tier-1 Backlog")
    parser.add_argument("--repo", required=True, help="GitHub repository (owner/repo)")
    parser.add_argument("--token", help="GitHub token (or set GITHUB_TOKEN env var)")
    parser.add_argument("--epics", help="Comma-separated epic IDs (e.g., E-1,E-2,E-3)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created without actually creating")

    args = parser.parse_args()

    # Get token from args or environment
    token = args.token or os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ GitHub token required. Use --token or set GITHUB_TOKEN environment variable.")
        return 1

    # Load issues data
    issues_file = Path(__file__).parent / "github_issues_tier1.json"
    if not issues_file.exists():
        print(f"❌ Issues file not found: {issues_file}")
        return 1

    data = load_github_issues(str(issues_file))

    # Filter by epics if specified
    if args.epics:
        epic_filter = set(args.epics.split(","))
        filtered_issues = [
            issue for issue in data["issues"]
            if issue["metadata"]["epic"] in epic_filter
        ]
    else:
        filtered_issues = data["issues"]

    print(f"🎯 Creating {len(filtered_issues)} issues in {args.repo}")

    if args.dry_run:
        print("\n🔍 DRY RUN - Issues that would be created:")
        for issue in filtered_issues:
            print(f"  - {issue['title']}")
        return 0

    # Create issues
    created_count = 0
    for issue in filtered_issues:
        try:
            response = create_github_issue(token, args.repo, issue)
            if response.status_code == 201:
                created_count += 1
                print(f"✅ Created: {issue['title']}")
            else:
                print(f"❌ Failed: {issue['title']} ({response.status_code})")
        except Exception as e:
            print(f"❌ Error creating {issue['title']}: {str(e)}")

    print(f"\n🎉 Created {created_count}/{len(filtered_issues)} issues successfully")
    return 0

if __name__ == "__main__":
    exit(main())
