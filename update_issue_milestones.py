#!/usr/bin/env python3
"""
Update GitHub issues with correct milestones.
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

def update_issue_milestone(issue_number, milestone_title):
    """Update an issue with the correct milestone."""
    cmd = f'gh issue edit {issue_number} --milestone "{milestone_title}"'
    print(f"📝 Updating issue #{issue_number} with milestone: {milestone_title}")
    result = run_gh_command(cmd)

    if result:
        print(f"✅ Updated: {result}")
        return True
    else:
        print(f"❌ Failed to update issue #{issue_number}")
        return False

def main():
    """Main function to update issues with milestones."""
    json_file = Path("/Users/medan/Downloads/PetPlantr/reports/github_issues_tier1.json")

    if not json_file.exists():
        print(f"❌ JSON file not found: {json_file}")
        sys.exit(1)

    # Load the issues data
    with open(json_file, 'r') as f:
        data = json.load(f)

    issues = data['issues']
    print(f"🚀 Updating {len(issues)} GitHub issues with milestones...")

    # Milestone mapping
    milestone_map = {
        "E-1": "Tier-1 Sprint: Universal Breed Coverage",
        "E-2": "Tier-1 Sprint: Performance Optimization",
        "E-3": "Tier-1 Sprint: Production Launch Hardening"
    }

    updated_issues = []
    failed_issues = []

    # Start from issue #27 (as created above)
    issue_number = 27

    for issue in issues:
        epic = issue['metadata']['epic']
        milestone_title = milestone_map.get(epic)

        if milestone_title:
            success = update_issue_milestone(issue_number, milestone_title)
            if success:
                updated_issues.append(f"#{issue_number}")
            else:
                failed_issues.append(f"#{issue_number}")
        else:
            print(f"⚠️  No milestone found for epic {epic}")

        issue_number += 1

    # Summary
    print(f"\n📊 Summary:")
    print(f"✅ Updated: {len(updated_issues)} issues")
    if failed_issues:
        print(f"❌ Failed: {len(failed_issues)} issues")
        for failed in failed_issues:
            print(f"   - {failed}")

    if updated_issues:
        print(f"\n🔗 Updated issues:")
        for issue in updated_issues:
            print(f"   {issue}")

if __name__ == "__main__":
    main()
