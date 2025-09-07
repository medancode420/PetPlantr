#!/usr/bin/env python3
"""
PetPlantr Tier-1 Backlog Dashboard
Simple Streamlit dashboard for visualizing backlog analytics

Usage:
    pip install streamlit
    streamlit run scripts/backlog_dashboard.py
"""

import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

@st.cache_data
def load_backlog_data():
    """Load backlog data from JSON report"""
    report_path = Path("reports/tier1_backlog_report.json")
    
    if not report_path.exists():
        return None
    
    with open(report_path, 'r') as f:
        return json.load(f)

def create_epic_chart(data):
    """Create epic distribution chart"""
    epics = []
    story_counts = []
    story_points = []
    
    for epic_id, epic_data in data['epic_breakdown'].items():
        epics.append(f"{epic_id} ({epic_data['story_count']} stories)")
        story_counts.append(epic_data['story_count'])
        story_points.append(epic_data['total_story_points'])
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Stories by Epic', 'Story Points by Epic'),
        specs=[[{"type": "bar"}, {"type": "bar"}]]
    )
    
    fig.add_trace(
        go.Bar(x=epics, y=story_counts, name="Story Count", marker_color="lightblue"),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(x=epics, y=story_points, name="Story Points", marker_color="lightcoral"),
        row=1, col=2
    )
    
    fig.update_layout(
        title="Epic Distribution Analysis",
        showlegend=False,
        height=400
    )
    
    return fig

def create_burndown_chart(data):
    """Create projected burndown chart"""
    total_sp = data['metadata']['total_story_points']
    sprints = data['metadata']['estimated_sprints']
    velocity = data['velocity_planning']['team_velocity_per_sprint']
    
    # Simple linear burndown projection
    weeks = list(range(sprints + 1))
    remaining_sp = [total_sp - (week * velocity) for week in weeks]
    remaining_sp = [max(0, sp) for sp in remaining_sp]  # Don't go below 0
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=weeks,
        y=remaining_sp,
        mode='lines+markers',
        name='Projected Burndown',
        line=dict(color='blue', width=3)
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="green", 
                  annotation_text="Target Completion")
    
    fig.update_layout(
        title="Projected Sprint Burndown",
        xaxis_title="Sprint",
        yaxis_title="Remaining Story Points",
        height=400
    )
    
    return fig

def main():
    st.set_page_config(
        page_title="PetPlantr Tier-1 Backlog Dashboard",
        page_icon="🎯",
        layout="wide"
    )
    
    st.title("🎯 PetPlantr Tier-1 Backlog Dashboard")
    st.markdown("---")
    
    # Load data
    data = load_backlog_data()
    
    if data is None:
        st.error("❌ Backlog data not found. Please run the notebook first to generate reports/tier1_backlog_report.json")
        st.info("💡 Run: `jupyter notebook tier1_priority_backlog.ipynb` and execute all cells")
        return
    
    # Sidebar with metadata
    st.sidebar.header("📊 Backlog Overview")
    st.sidebar.metric("Total Stories", data['metadata']['total_items'])
    st.sidebar.metric("Total Story Points", data['metadata']['total_story_points'])
    st.sidebar.metric("Estimated Sprints", data['metadata']['estimated_sprints'])
    st.sidebar.metric("Fibonacci Compliance", data['metadata']['fibonacci_compliance'])
    
    st.sidebar.markdown("---")
    st.sidebar.write("**Generated:** " + data['metadata']['generated_at'][:19])
    st.sidebar.write("**Version:** " + data['metadata']['notebook_version'])
    
    # Main dashboard
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Epic Breakdown")
        epic_fig = create_epic_chart(data)
        st.plotly_chart(epic_fig, use_container_width=True)
        
        # Epic details table
        epic_df = pd.DataFrame([
            {
                'Epic': epic_id,
                'Name': epic_data['name'][:40] + "..." if len(epic_data['name']) > 40 else epic_data['name'],
                'Stories': epic_data['story_count'],
                'Story Points': epic_data['total_story_points']
            }
            for epic_id, epic_data in data['epic_breakdown'].items()
        ])
        st.dataframe(epic_df, use_container_width=True)
    
    with col2:
        st.subheader("📈 Sprint Planning")
        burndown_fig = create_burndown_chart(data)
        st.plotly_chart(burndown_fig, use_container_width=True)
        
        # Velocity planning metrics
        velocity_data = data['velocity_planning']
        st.write("**Planning Assumptions:**")
        st.write(f"• Team velocity: {velocity_data['team_velocity_per_sprint']} SP/sprint")
        st.write(f"• Duration: {velocity_data['estimated_duration_weeks']} weeks")
        st.write(f"• Critical path: {velocity_data['critical_path_items']} items")
        st.write(f"• Parallel opportunities: {velocity_data['parallel_opportunities']} streams")
    
    # Artifacts section
    st.markdown("---")
    st.subheader("📂 Generated Artifacts")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**GitHub Integration:**")
        st.write("• GitHub Issues JSON")
        st.write("• Issue seeding script")
        if st.button("🔗 Preview GitHub Issues"):
            st.info("Run: `python scripts/seed_gh_issues_v2.py --dry-run`")
    
    with col2:
        st.write("**Jira Integration:**")
        st.write("• Jira CSV export")
        st.write("• Import instructions")
        if st.button("📊 Validate Jira CSV"):
            st.info("Run: `python scripts/jira_import_helper.py`")
    
    with col3:
        st.write("**Analytics:**")
        st.write("• Dependency graph")
        st.write("• Risk assessment")
        st.write("• Test validation")
    
    # Quick actions
    st.markdown("---")
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
    
    with col2:
        if st.button("📊 Generate Report"):
            st.info("Run the notebook to refresh all artifacts")
    
    with col3:
        if st.button("🎯 Create Issues"):
            st.info("Set GITHUB_TOKEN and run seed script")
    
    with col4:
        if st.button("📋 Import to Jira"):
            st.info("Use Jira CSV import feature")
    
    # Footer
    st.markdown("---")
    st.caption("Generated by PetPlantr Tier-1 Backlog Automation System")

if __name__ == "__main__":
    main()
