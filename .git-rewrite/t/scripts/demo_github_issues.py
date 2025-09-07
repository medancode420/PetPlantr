#!/usr/bin/env python3
"""
Demo runner for Tier-1 Priority Backlog GitHub Issues
Shows what issues would be created without actually creating them.
"""

import json
from pathlib import Path

def main():
    # Load the GitHub issues data
    github_issues_path = Path("reports/github_issues_tier1.json")
    
    if not github_issues_path.exists():
        print("❌ GitHub issues file not found. Run the notebook first.")
        return
    
    with open(github_issues_path, 'r') as f:
        data = json.load(f)
    
    issues = data['issues']
    
    print("🎯 Tier-1 Priority Backlog - GitHub Issues Summary")
    print("=" * 60)
    print(f"📊 Total issues to create: {len(issues)}")
    print(f"📅 Generated: {data['metadata']['generated_at']}")
    print(f"🎯 Repository: PetPlantr")
    
    print("\n📋 Issues Preview:")
    print("-" * 60)
    
    for i, issue in enumerate(issues[:3], 1):  # Show first 3 issues
        print(f"\n{i}. **{issue['title']}**")
        print(f"   📂 Epic: {issue['labels'][0] if issue['labels'] else 'None'}")
        print(f"   🏷️  Labels: {', '.join(issue['labels'])}")
        print(f"   📝 Body preview: {issue['body'][:100]}...")
    
    if len(issues) > 3:
        print(f"\n   ... and {len(issues) - 3} more issues")
    
    print(f"\n🚀 To create these issues:")
    print(f"   1. Set GITHUB_TOKEN environment variable")
    print(f"   2. Run: python scripts/seed_gh_issues.py --repo USERNAME/REPO_NAME")
    print(f"   3. Or use GitHub CLI: gh issue create --title 'TITLE' --body 'BODY'")
    
    print(f"\n✅ All artifacts available in reports/ directory:")
    reports_dir = Path("reports")
    if reports_dir.exists():
        for file in sorted(reports_dir.glob("*")):
            print(f"   📄 {file.name}")

if __name__ == "__main__":
    main()
