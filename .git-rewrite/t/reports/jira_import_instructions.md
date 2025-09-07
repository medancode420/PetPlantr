
# Jira Import Instructions for PetPlantr Tier-1 Backlog

## Prerequisites
1. Jira project with appropriate issue types (Story, Task)
2. Custom fields configured:
   - Dependencies (Text field)
   - DoD Items (Number field)
   - Test Count (Number field)
   - Epic ID (Short text)
   - Story ID (Short text)

## Import Steps
1. Navigate to Jira > Issues > Import Issues from CSV
2. Upload file: scripts/jira_import_tier1.csv
3. Map fields according to your Jira configuration
4. Validate data preview
5. Execute import

## Field Mapping Recommendations
- Summary → Summary
- Issue Type → Issue Type
- Priority → Priority
- Epic Name → Epic Name (if using Jira Portfolio)
- Story Points → Story Points
- Description → Description
- Components → Components
- Labels → Labels

## Post-Import Tasks
1. Create Epic issues if not already present
2. Link stories to appropriate epics
3. Configure sprint assignments
4. Set up dependency links between issues
5. Assign team members to stories

Generated: 2025-07-02 22:13:47
Source: tier1_priority_backlog.ipynb
