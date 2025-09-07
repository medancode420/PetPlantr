#!/usr/bin/env python3
"""
Jira Import Helper for PetPlantr Tier-1 Backlog
Validates the CSV and provides import instructions
"""

import pandas as pd
import json
from pathlib import Path

def validate_jira_csv():
    """Validate the Jira CSV file and show import readiness"""
    csv_path = Path("reports/jira_import_tier1.csv")
    instructions_path = Path("reports/jira_import_instructions.md")
    
    if not csv_path.exists():
        print("❌ Jira CSV not found. Run the notebook first.")
        return False
    
    # Load and validate CSV
    try:
        df = pd.read_csv(csv_path)
        print(f"✅ Jira CSV loaded: {len(df)} rows, {len(df.columns)} columns")
        
        # Check required columns
        required_cols = ['Summary', 'Issue Type', 'Story Points', 'Epic Name']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            print(f"❌ Missing required columns: {missing_cols}")
            return False
        
        print("✅ All required columns present")
        
        # Show epic distribution
        epic_summary = df.groupby('Epic Name').agg({
            'Story Points': ['count', 'sum'],
            'Issue Type': lambda x: ', '.join(x.unique())
        })
        
        print("\n📊 Epic Summary for Jira Import:")
        print("=" * 60)
        for epic_name in df['Epic Name'].unique():
            epic_data = df[df['Epic Name'] == epic_name]
            story_count = len(epic_data)
            total_sp = epic_data['Story Points'].sum()
            print(f"📋 {epic_name}")
            print(f"   Stories: {story_count}, Total SP: {total_sp}")
        
        # Show custom fields
        custom_fields = [col for col in df.columns if col.startswith('Custom Field')]
        if custom_fields:
            print(f"\n🔧 Custom Fields to create in Jira:")
            for field in custom_fields:
                print(f"   - {field}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return False

def show_import_instructions():
    """Show Jira import instructions"""
    instructions_path = Path("reports/jira_import_instructions.md")
    
    if instructions_path.exists():
        print("\n📋 Jira Import Instructions:")
        print("=" * 60)
        with open(instructions_path, 'r') as f:
            content = f.read()
            # Show first 20 lines
            lines = content.split('\n')[:20]
            for line in lines:
                print(line)
        print("\n📄 Full instructions available in:", instructions_path)
    else:
        print("\n📋 Quick Jira Import Steps:")
        print("=" * 60)
        print("1. Go to Jira → Projects → (…) → External System Import → CSV")
        print("2. Upload: reports/jira_import_tier1.csv")
        print("3. Map fields: Summary → Summary, Story Points → Story Points")
        print("4. Create custom fields if needed (see above)")
        print("5. Confirm & import")

def main():
    print("🎯 PetPlantr Jira Import Helper")
    print("=" * 50)
    
    if validate_jira_csv():
        show_import_instructions()
        
        print(f"\n🚀 Ready for Jira Import!")
        print(f"📁 CSV File: reports/jira_import_tier1.csv")
        print(f"📄 Instructions: reports/jira_import_instructions.md")
    else:
        print(f"\n⚠️  Please run the notebook first to generate Jira artifacts")

if __name__ == "__main__":
    main()
