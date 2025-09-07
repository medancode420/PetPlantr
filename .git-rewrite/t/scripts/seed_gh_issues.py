#!/usr/bin/env python3
"""
GitHub Issues Seeding Script for PetPlantr Tier-1 Backlog
Generated from: tier1_priority_backlog.ipynb
Created: 2025-07-02 22:12:03

Usage:
    # Dry run (safe testing)
    python scripts/seed_gh_issues.py --repo USER/REPO --dry-run
    
    # Create issues for real
    export GITHUB_TOKEN=ghp_your_token_here
    python scripts/seed_gh_issues.py --repo USER/REPO
    
    # Create only specific epics
    python scripts/seed_gh_issues.py --repo USER/REPO --epics E-1,E-2
"""

import json
import requests
import os
import argparse
import time
from pathlib import Path
from typing import Dict, List, Optional

def load_github_issues(file_path: str) -> Dict:
    """Load GitHub issues from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Issues file not found: {file_path}")
        print("💡 Make sure to run the notebook first to generate artifacts")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {file_path}: {e}")
        exit(1)

def check_existing_issue(token: str, repo: str, title: str) -> Optional[int]:
    """Check if an issue with the same title already exists"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Search for existing issues with matching title
    search_url = f"https://api.github.com/search/issues"
    query = f"repo:{repo} is:issue in:title \"{title}\""
    
    response = requests.get(search_url, headers=headers, params={"q": query})
    if response.status_code == 200:
        results = response.json()
        if results["total_count"] > 0:
            return results["items"][0]["number"]
    return None

def create_or_update_github_issue(token: str, repo: str, issue_data: dict, dry_run: bool = False) -> Dict:
    """Create a GitHub issue or update existing one (idempotent)"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    title = issue_data["title"]
    
    if dry_run:
        return {
            "status": "dry-run",
            "title": title,
            "labels": issue_data["labels"],
            "action": "would_create"
        }
    
    # Check if issue already exists
    existing_issue_number = check_existing_issue(token, repo, title)
    
    payload = {
        "title": title,
        "body": issue_data["body"],
        "labels": issue_data["labels"]
    }
    
    if existing_issue_number:
        # Update existing issue
        url = f"https://api.github.com/repos/{repo}/issues/{existing_issue_number}"
        response = requests.patch(url, headers=headers, json=payload)
        action = "updated"
    else:
        # Create new issue
        url = f"https://api.github.com/repos/{repo}/issues"
        response = requests.post(url, headers=headers, json=payload)
        action = "created"
    
    return {
        "status": "success" if response.status_code in [200, 201] else "error",
        "response": response,
        "title": title,
        "action": action,
        "issue_number": existing_issue_number if existing_issue_number else (response.json().get("number") if response.status_code in [200, 201] else None)
    }

def create_milestones_if_needed(token: str, repo: str, dry_run: bool = False) -> Dict[str, int]:
    """Create Sprint milestones if they don't exist"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    milestones = ["Sprint 1", "Sprint 2", "Sprint 3"]
    milestone_map = {}
    
    if dry_run:
        print("🏃 [DRY RUN] Would create milestones: Sprint 1, Sprint 2, Sprint 3")
        return {milestone: 1 for milestone in milestones}  # Dummy IDs for dry run
    
    # Get existing milestones
    url = f"https://api.github.com/repos/{repo}/milestones"
    response = requests.get(url, headers=headers)
    existing_milestones = {m["title"]: m["number"] for m in response.json()} if response.status_code == 200 else {}
    
    for milestone in milestones:
        if milestone in existing_milestones:
            milestone_map[milestone] = existing_milestones[milestone]
            print(f"✅ Milestone '{milestone}' already exists (#{existing_milestones[milestone]})")
        else:
            # Create milestone
            create_url = f"https://api.github.com/repos/{repo}/milestones"
            payload = {
                "title": milestone,
                "description": f"PetPlantr Tier-1 {milestone} (Auto-generated)"
            }
            create_response = requests.post(create_url, headers=headers, json=payload)
            if create_response.status_code == 201:
                milestone_number = create_response.json()["number"]
                milestone_map[milestone] = milestone_number
                print(f"✅ Created milestone '{milestone}' (#{milestone_number})")
            else:
                print(f"⚠️  Failed to create milestone '{milestone}': {create_response.status_code}")
    
    return milestone_map

def assign_milestone_to_issue(token: str, repo: str, issue_number: int, milestone_number: int, dry_run: bool = False):
    """Assign a milestone to an issue"""
    if dry_run:
        return True
        
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
    payload = {"milestone": milestone_number}
    
    response = requests.patch(url, headers=headers, json=payload)
    return response.status_code == 200

def main():
    parser = argparse.ArgumentParser(
        description="Seed GitHub issues for PetPlantr Tier-1 Backlog",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to preview what would be created
  python scripts/seed_gh_issues.py --repo myorg/petplantr --dry-run
  
  # Create all issues
  export GITHUB_TOKEN=ghp_your_token
  python scripts/seed_gh_issues.py --repo myorg/petplantr
  
  # Create only E-1 epic issues
  python scripts/seed_gh_issues.py --repo myorg/petplantr --epics E-1
        """
    )
    parser.add_argument("--repo", help="GitHub repository (owner/repo). Defaults to current git repo if available")
    parser.add_argument("--token", help="GitHub token (or set GITHUB_TOKEN/GH_TOKEN env var)")
    parser.add_argument("--epics", help="Comma-separated epic IDs (e.g., E-1,E-2,E-3)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created without actually creating")
    parser.add_argument("--no-milestones", action="store_true", help="Don't create or assign milestones")
    parser.add_argument("--issues-file", default="reports/github_issues_tier1.json", help="Path to issues JSON file")

    args = parser.parse_args()

    # Auto-detect repo if not provided
    if not args.repo:
        try:
            import subprocess
            result = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True)
            if result.returncode == 0:
                origin_url = result.stdout.strip()
                if "github.com" in origin_url:
                    # Extract owner/repo from various URL formats
                    if origin_url.startswith("git@github.com:"):
                        args.repo = origin_url.replace("git@github.com:", "").replace(".git", "")
                    elif "github.com/" in origin_url:
                        args.repo = origin_url.split("github.com/")[1].replace(".git", "")
        except:
            pass
        
        if not args.repo:
            print("❌ Repository required. Use --repo owner/repo or run from a git repository with GitHub origin")
            return 1

    # Get token from args or environment (try multiple env vars)
    token = args.token or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if not token and not args.dry_run:
        print("❌ GitHub token required. Use --token or set GITHUB_TOKEN/GH_TOKEN environment variable.")
        print("💡 Get a token at: https://github.com/settings/tokens (needs 'repo' scope)")
        return 1

    # Load issues data
    issues_file = Path(__file__).parent / "github_issues_tier1.json"
    if not issues_file.exists():
        print(f"❌ Issues file not found: {issues_file}")
        return 1

    data = load_github_issues(issues_file)

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
