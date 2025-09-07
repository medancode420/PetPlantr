#!/usr/bin/env python3
"""
Create GitHub issues from the tier1 backlog JSON file.
"""
import json
import subprocess
import sys
from pathlib import Path

def run_gh_command(cmd):
    """Run a GitHub CLI command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {cmd}")
        print(f"Error: {e.stderr}")
        return None

def create_github_issue(issue_data):
    """Create a single GitHub issue."""
    title = issue_data['title']
    body = issue_data['body']
    labels = issue_data['labels']

    # Build the gh command
    cmd = f'gh issue create --title "{title}" --body "{body}"'

    # Add labels
    if labels:
        label_str = ','.join(labels)
        cmd += f' --label "{label_str}"'

    # Skip milestone for now
    print(f"📝 Creating issue: {title}")
    result = run_gh_command(cmd)

    if result:
        print(f"✅ Created: {result}")
        return result
    else:
        print(f"❌ Failed to create: {title}")
        return None

def main():
    """Main function to create all GitHub issues."""
    json_file = Path("/Users/medan/Downloads/PetPlantr/reports/github_issues_tier1.json")

    if not json_file.exists():
        print(f"❌ JSON file not found: {json_file}")
        sys.exit(1)

    # Load the issues data
    with open(json_file, 'r') as f:
        data = json.load(f)

    issues = data['issues']
    print(f"🚀 Creating {len(issues)} GitHub issues...")

    created_issues = []
    failed_issues = []

    for issue in issues:
        issue_url = create_github_issue(issue)
        if issue_url:
            created_issues.append(issue_url)
        else:
            failed_issues.append(issue['title'])

    # Summary
    print(f"\n📊 Summary:")
    print(f"✅ Created: {len(created_issues)} issues")
    if failed_issues:
        print(f"❌ Failed: {len(failed_issues)} issues")
        for failed in failed_issues:
            print(f"   - {failed}")

    if created_issues:
        print(f"\n🔗 Created issues:")
        for url in created_issues:
            print(f"   {url}")

if __name__ == "__main__":
    main()
