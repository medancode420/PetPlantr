#!/usr/bin/env python3
"""
Sprint Burndown Chart Generator for PetPlantr
Generates visual burndown charts and Sprint progress reports
"""

import json
import requests
import os
import argparse
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

class SprintReportGenerator:
    def __init__(self, repo: str, token: str):
        self.repo = repo
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.base_url = f"https://api.github.com/repos/{repo}"
        
    def get_sprint_issues(self, sprint_name: str = "Sprint 1") -> list:
        """Get all issues assigned to a specific sprint milestone"""
        try:
            # Get milestone ID
            milestones_response = requests.get(f"{self.base_url}/milestones", headers=self.headers)
            milestones = milestones_response.json()
            
            sprint_milestone = None
            for milestone in milestones:
                if milestone["title"] == sprint_name:
                    sprint_milestone = milestone
                    break
            
            if not sprint_milestone:
                print(f"⚠️ Milestone '{sprint_name}' not found")
                return []
            
            # Get issues for this milestone
            issues_response = requests.get(
                f"{self.base_url}/issues",
                headers=self.headers,
                params={
                    "milestone": sprint_milestone["number"],
                    "state": "all",
                    "per_page": 100
                }
            )
            
            return issues_response.json()
            
        except Exception as e:
            print(f"❌ Error fetching sprint issues: {e}")
            return []
    
    def calculate_story_points(self, issues: list) -> dict:
        """Calculate story points from issue labels"""
        total_points = 0
        completed_points = 0
        remaining_points = 0
        
        issue_breakdown = []
        
        for issue in issues:
            # Extract story points from labels
            points = 0
            for label in issue.get("labels", []):
                if label["name"].startswith("sp-"):
                    try:
                        points = int(label["name"].replace("sp-", ""))
                        break
                    except ValueError:
                        continue
            
            # Determine completion status
            is_completed = issue["state"] == "closed"
            
            total_points += points
            if is_completed:
                completed_points += points
            else:
                remaining_points += points
            
            issue_breakdown.append({
                "number": issue["number"],
                "title": issue["title"],
                "points": points,
                "completed": is_completed,
                "created_at": issue["created_at"],
                "closed_at": issue.get("closed_at"),
                "labels": [l["name"] for l in issue.get("labels", [])]
            })
        
        return {
            "total_points": total_points,
            "completed_points": completed_points,
            "remaining_points": remaining_points,
            "completion_percentage": (completed_points / total_points * 100) if total_points > 0 else 0,
            "issues": issue_breakdown
        }
    
    def generate_burndown_data(self, issues: list, sprint_start: datetime, sprint_end: datetime) -> dict:
        """Generate burndown chart data"""
        # Create daily burndown data
        current_date = sprint_start
        burndown_data = []
        
        # Calculate initial story points
        story_data = self.calculate_story_points(issues)
        total_points = story_data["total_points"]
        
        # Ideal burndown line (linear)
        sprint_days = (sprint_end - sprint_start).days
        ideal_daily_burn = total_points / sprint_days if sprint_days > 0 else 0
        
        while current_date <= sprint_end:
            # Calculate completed points up to this date
            completed_by_date = 0
            for issue in story_data["issues"]:
                if issue["closed_at"]:
                    closed_date = datetime.fromisoformat(issue["closed_at"].replace("Z", "+00:00"))
                    if closed_date.date() <= current_date.date():
                        completed_by_date += issue["points"]
            
            remaining_points = total_points - completed_by_date
            days_elapsed = (current_date - sprint_start).days
            ideal_remaining = max(0, total_points - (ideal_daily_burn * days_elapsed))
            
            burndown_data.append({
                "date": current_date.date(),
                "remaining_actual": remaining_points,
                "remaining_ideal": ideal_remaining,
                "completed_cumulative": completed_by_date
            })
            
            current_date += timedelta(days=1)
        
        return {
            "burndown_data": burndown_data,
            "story_data": story_data,
            "sprint_info": {
                "start_date": sprint_start.date(),
                "end_date": sprint_end.date(),
                "total_days": sprint_days,
                "days_elapsed": (datetime.now() - sprint_start).days
            }
        }
    
    def create_burndown_chart(self, burndown_data: dict, output_path: str):
        """Create and save burndown chart"""
        plt.style.use('seaborn-v0_8-darkgrid')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Prepare data
        dates = [entry["date"] for entry in burndown_data["burndown_data"]]
        actual_remaining = [entry["remaining_actual"] for entry in burndown_data["burndown_data"]]
        ideal_remaining = [entry["remaining_ideal"] for entry in burndown_data["burndown_data"]]
        completed_cumulative = [entry["completed_cumulative"] for entry in burndown_data["burndown_data"]]
        
        # Chart 1: Burndown Chart
        ax1.plot(dates, ideal_remaining, 'g--', linewidth=2, label='Ideal Burndown', alpha=0.7)
        ax1.plot(dates, actual_remaining, 'b-', linewidth=3, label='Actual Remaining', marker='o', markersize=4)
        ax1.fill_between(dates, actual_remaining, alpha=0.3, color='blue')
        
        ax1.set_title('Sprint Burndown Chart - Remaining Story Points', fontsize=16, fontweight='bold')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Story Points Remaining')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Format x-axis
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax1.xaxis.set_major_locator(mdates.DayLocator(interval=2))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # Chart 2: Cumulative Progress
        ax2.plot(dates, completed_cumulative, 'g-', linewidth=3, label='Completed Story Points', marker='s', markersize=4)
        ax2.fill_between(dates, completed_cumulative, alpha=0.3, color='green')
        
        ax2.set_title('Cumulative Progress - Completed Story Points', fontsize=16, fontweight='bold')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Story Points Completed')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Format x-axis
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax2.xaxis.set_major_locator(mdates.DayLocator(interval=2))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        # Add sprint info text
        sprint_info = burndown_data["sprint_info"]
        story_data = burndown_data["story_data"]
        
        info_text = f"""Sprint Information:
        Total Story Points: {story_data['total_points']}
        Completed: {story_data['completed_points']} ({story_data['completion_percentage']:.1f}%)
        Remaining: {story_data['remaining_points']}
        Days Elapsed: {sprint_info['days_elapsed']}/{sprint_info['total_days']}"""
        
        plt.figtext(0.02, 0.02, info_text, fontsize=10, 
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.5))
        
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.15)
        
        # Save chart
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Burndown chart saved to: {output_path}")
    
    def generate_sprint_report(self, sprint_name: str = "Sprint 1", output_dir: str = "reports"):
        """Generate complete sprint report"""
        print(f"📊 Generating Sprint report for {sprint_name}...")
        
        # Get sprint issues
        issues = self.get_sprint_issues(sprint_name)
        if not issues:
            print(f"❌ No issues found for {sprint_name}")
            return
        
        print(f"✅ Found {len(issues)} issues in {sprint_name}")
        
        # Define sprint dates (customize as needed)
        sprint_start = datetime.now() - timedelta(days=7)  # Assume 7-day sprint
        sprint_end = datetime.now() + timedelta(days=7)
        
        # Generate burndown data
        burndown_data = self.generate_burndown_data(issues, sprint_start, sprint_end)
        
        # Create charts
        chart_path = f"{output_dir}/sprint_burndown.png"
        self.create_burndown_chart(burndown_data, chart_path)
        
        # Generate JSON report
        report_data = {
            "sprint_name": sprint_name,
            "generated_at": datetime.now().isoformat(),
            "repository": self.repo,
            **burndown_data
        }
        
        report_path = f"{output_dir}/sprint_report.json"
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"📄 Sprint report saved to: {report_path}")
        
        # Print summary
        story_data = burndown_data["story_data"]
        print(f"\n📈 Sprint Summary:")
        print(f"   Total Story Points: {story_data['total_points']}")
        print(f"   Completed: {story_data['completed_points']} ({story_data['completion_percentage']:.1f}%)")
        print(f"   Remaining: {story_data['remaining_points']}")
        print(f"   Total Issues: {len(issues)}")
        
        return report_data

def main():
    parser = argparse.ArgumentParser(description="Generate Sprint burndown chart")
    parser.add_argument("--repo", default="medancode420/PetPlantr", help="GitHub repository")
    parser.add_argument("--token", help="GitHub token (or set GITHUB_TOKEN env var)")
    parser.add_argument("--sprint", default="Sprint 1", help="Sprint milestone name")
    parser.add_argument("--output", default="reports", help="Output directory")
    
    args = parser.parse_args()
    
    # Get token
    token = args.token or os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ GitHub token required. Use --token or set GITHUB_TOKEN environment variable.")
        return 1
    
    # Generate report
    generator = SprintReportGenerator(args.repo, token)
    generator.generate_sprint_report(args.sprint, args.output)
    
    return 0

if __name__ == "__main__":
    exit(main())
