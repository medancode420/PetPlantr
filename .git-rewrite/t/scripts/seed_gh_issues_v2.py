#!/usr/bin/env python3
"""
GitHub Issues Seeding Script for PetPlantr Tier-1 Backlog + Enhanced AI Features
Generated from: tier1_priority_backlog.ipynb
Created: 2025-07-02
Updated: 2025-07-09 (Enhanced AI Pipeline Features)

Usage:
    # Dry run (safe testing) - Original Tier 1 features
    python scripts/seed_gh_issues_v2.py --repo USER/REPO --dry-run
    
    # Enhanced AI features (Tier 1.5) - includes Shap-E integration
    python scripts/seed_gh_issues_v2.py --repo USER/REPO --issues-file reports/github_issues_tier1_enhanced.json --dry-run
    
    # Create issues for real
    export GITHUB_TOKEN=ghp_your_token_here
    python scripts/seed_gh_issues_v2.py --repo USER/REPO
    
    # Create only enhanced AI epic (E-4)
    python scripts/seed_gh_issues_v2.py --repo USER/REPO --issues-file reports/github_issues_tier1_enhanced.json --epics E-4
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
    
    try:
        response = requests.get(search_url, headers=headers, params={"q": query})
        if response.status_code == 200:
            results = response.json()
            if results["total_count"] > 0:
                return results["items"][0]["number"]
    except Exception as e:
        print(f"⚠️  Error checking existing issues: {e}")
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
            "labels": issue_data.get("labels", []),
            "action": "would_create"
        }
    
    # Check if issue already exists
    existing_issue_number = check_existing_issue(token, repo, title)
    
    payload = {
        "title": title,
        "body": issue_data["body"],
        "labels": issue_data.get("labels", [])
    }
    
    try:
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
        
        if response.status_code in [200, 201]:
            return {
                "status": "success",
                "response": response,
                "title": title,
                "action": action,
                "issue_number": existing_issue_number if existing_issue_number else response.json().get("number")
            }
        else:
            return {
                "status": "error",
                "title": title,
                "error": f"HTTP {response.status_code}: {response.text[:200]}",
                "action": "failed"
            }
    except Exception as e:
        return {
            "status": "error",
            "title": title,
            "error": str(e),
            "action": "failed"
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
    
    try:
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
                    if create_response.status_code == 401:
                        print(f"      ❌ Authentication failed - check your GitHub token")
                    elif create_response.status_code == 403:
                        print(f"      ❌ Permission denied - token needs 'repo' scope")
                    else:
                        print(f"      ❌ Error details: {create_response.text[:100]}")
    except Exception as e:
        print(f"⚠️  Error managing milestones: {e}")
    
    return milestone_map

def assign_milestone_to_issue(token: str, repo: str, issue_number: int, milestone_number: int, dry_run: bool = False):
    """Assign a milestone to an issue"""
    if dry_run:
        return True
        
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
        payload = {"milestone": milestone_number}
        
        response = requests.patch(url, headers=headers, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"⚠️  Error assigning milestone: {e}")
        return False

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
    issues_file = Path(args.issues_file)
    if not issues_file.exists():
        print(f"❌ Issues file not found: {issues_file}")
        print("💡 Make sure to run the notebook first to generate artifacts")
        return 1

    print(f"📂 Loading issues from: {issues_file}")
    data = load_github_issues(str(issues_file))
    
    if "issues" not in data:
        print("❌ Invalid issues file format. Expected 'issues' key in JSON")
        return 1

    # Filter by epics if specified
    if args.epics:
        epic_filter = set(args.epics.split(","))
        print(f"🎯 Filtering to epics: {', '.join(epic_filter)}")
        # Get epic from labels (look for epic-e-1, epic-e-2, etc.)
        filtered_issues = []
        for issue in data["issues"]:
            issue_epics = [label for label in issue.get("labels", []) if label.startswith("epic-")]
            if any(epic.replace("epic-", "").upper() in epic_filter for epic in issue_epics):
                filtered_issues.append(issue)
    else:
        filtered_issues = data["issues"]

    print(f"🎯 Processing {len(filtered_issues)} issues for {args.repo}")

    if args.dry_run:
        print("\n🔍 DRY RUN - Issues that would be created:")
        for i, issue in enumerate(filtered_issues, 1):
            labels = ', '.join(issue.get("labels", []))
            print(f"  {i:2d}. {issue['title']}")
            print(f"      Labels: {labels}")
        print(f"\n✅ [DRY RUN] Would process {len(filtered_issues)} issues")
        return 0

    # Create milestones if needed
    milestone_map = {}
    if not args.no_milestones:
        print("🏃 Setting up milestones...")
        milestone_map = create_milestones_if_needed(token, args.repo, args.dry_run)

    # Create/update issues
    print("\n🚀 Creating/updating issues...")
    created_count = 0
    updated_count = 0
    error_count = 0
    
    for i, issue in enumerate(filtered_issues, 1):
        print(f"\n📝 [{i:2d}/{len(filtered_issues)}] Processing: {issue['title'][:60]}...")
        
        result = create_or_update_github_issue(token, args.repo, issue, args.dry_run)
        
        if result["status"] == "success":
            if result["action"] == "created":
                created_count += 1
                print(f"   ✅ Created issue #{result['issue_number']}")
            else:
                updated_count += 1
                print(f"   ✅ Updated issue #{result['issue_number']}")
            
            # Assign milestone if enabled
            if not args.no_milestones and result["issue_number"] and milestone_map:
                # Simple milestone assignment based on epic
                epic_labels = [l for l in issue.get("labels", []) if l.startswith("epic-")]
                if epic_labels:
                    epic_id = epic_labels[0].replace("epic-", "").upper()
                    if epic_id == "E-1":
                        milestone = "Sprint 1"
                    elif epic_id == "E-2":
                        milestone = "Sprint 2"
                    else:
                        milestone = "Sprint 3"
                    
                    if milestone in milestone_map:
                        if assign_milestone_to_issue(token, args.repo, result["issue_number"], milestone_map[milestone], args.dry_run):
                            print(f"   🏃 Assigned to {milestone}")
        else:
            error_count += 1
            print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
        
        # Rate limiting: sleep briefly between requests
        time.sleep(0.5)

    print(f"\n🎉 Summary:")
    print(f"   ✅ Created: {created_count}")
    print(f"   🔄 Updated: {updated_count}")
    print(f"   ❌ Errors: {error_count}")
    print(f"   📊 Total: {len(filtered_issues)}")
    
    if created_count + updated_count > 0:
        print(f"\n🔗 View issues: https://github.com/{args.repo}/issues")
        print(f"🏃 View milestones: https://github.com/{args.repo}/milestones")
    
    return 0

if __name__ == "__main__":
    exit(main())
