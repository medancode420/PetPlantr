"""
PetPlantr Advanced Monitoring Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import time
import json

# Page configuration
st.set_page_config(
    page_title="PetPlantr Monitoring Dashboard",
    page_icon="🐕",
    layout="wide"
)

st.title("🐕 PetPlantr Monitoring Dashboard")
st.markdown("Real-time monitoring and analytics for PetPlantr AI services")

# Sidebar
st.sidebar.header("Dashboard Controls")

# Time range selector
time_range = st.sidebar.selectbox(
    "Time Range",
    ["1 hour", "6 hours", "24 hours", "7 days", "30 days"],
    index=2
)

# Convert time range to hours
time_range_hours = {
    "1 hour": 1,
    "6 hours": 6,
    "24 hours": 24,
    "7 days": 168,
    "30 days": 720
}[time_range]

# Auto-refresh toggle
auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=True)

# API Base URL
API_BASE_URL = st.sidebar.text_input("API Base URL", "http://localhost:8000")

def fetch_health_data():
    """Fetch health data from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v2/health/detailed", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def fetch_analytics_data(hours):
    """Fetch analytics data from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v2/analytics?days={hours/24}", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def fetch_model_info():
    """Fetch model information from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v2/models/info", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

# Main dashboard layout
col1, col2, col3 = st.columns(3)

# Health Status
with col1:
    st.subheader("🟢 System Health")
    health_data = fetch_health_data()

    if health_data:
        st.metric("Status", health_data.get('status', 'Unknown').title())
        st.metric("Uptime", f"{health_data.get('uptime', 0):.1f}s")
        st.metric("Memory Usage", f"{health_data.get('memory_usage', 0):.1f}%")
        st.metric("CPU Usage", f"{health_data.get('cpu_usage', 0):.1f}%")
    else:
        st.error("Unable to fetch health data")

# Analytics Overview
with col2:
    st.subheader("📊 Analytics Overview")
    analytics_data = fetch_analytics_data(time_range_hours)

    if analytics_data:
        st.metric("Total Predictions", analytics_data.get('total_predictions', 0))
        st.metric("Avg Confidence", f"{analytics_data.get('average_confidence', 0)*100:.1f}%")
        st.metric("Predictions/Day", f"{analytics_data.get('performance_metrics', {}).get('predictions_per_day', 0):.1f}")
    else:
        st.error("Unable to fetch analytics data")

# Model Information
with col3:
    st.subheader("🤖 Model Status")
    model_data = fetch_model_info()

    if model_data:
        st.metric("Models Loaded", len(model_data.get('models', [])))
        st.metric("Status", model_data.get('status', 'Unknown').title())
        if model_data.get('models'):
            st.metric("Supported Breeds", model_data['models'][0].get('supported_breeds', 0))
    else:
        st.error("Unable to fetch model data")

# Charts section
st.header("📈 Performance Charts")

# Create sample data for demonstration (replace with real data)
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Response Time Trend")
    # Sample response time data
    response_times = [0.1, 0.15, 0.12, 0.18, 0.09, 0.14, 0.11, 0.16]
    fig = px.line(
        x=list(range(len(response_times))),
        y=response_times,
        title="API Response Times (seconds)",
        labels={'x': 'Time', 'y': 'Response Time (s)'}
    )
    st.plotly_chart(fig, use_container_width=True)

with chart_col2:
    st.subheader("Prediction Confidence Distribution")
    # Sample confidence data
    confidence_data = [0.85, 0.92, 0.78, 0.95, 0.88, 0.91, 0.76, 0.89]
    fig = px.histogram(
        confidence_data,
        title="Prediction Confidence Distribution",
        labels={'value': 'Confidence', 'count': 'Frequency'}
    )
    st.plotly_chart(fig, use_container_width=True)

# Top Breeds Chart
st.subheader("🐕 Top Detected Breeds")
if analytics_data and analytics_data.get('top_breeds'):
    breeds_df = pd.DataFrame(analytics_data['top_breeds'])
    if not breeds_df.empty:
        fig = px.bar(
            breeds_df,
            x='breed',
            y='count',
            title="Top Detected Breeds",
            color='count',
            color_continuous_scale='viridis'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No breed data available yet")
else:
    st.info("Unable to load breed analytics")

# System Metrics
st.header("🖥️ System Metrics")

metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

with metric_col1:
    st.metric("Active Connections", "12")
    st.metric("Error Rate", "0.1%")

with metric_col2:
    st.metric("Memory Usage", "45.2%")
    st.metric("Disk Usage", "23.1%")

with metric_col3:
    st.metric("CPU Usage", "12.3%")
    st.metric("Network I/O", "1.2 MB/s")

with metric_col4:
    st.metric("Requests/min", "45")
    st.metric("Avg Latency", "120ms")

# Real-time updates
if auto_refresh:
    time.sleep(30)
    st.rerun()

# Footer
st.markdown("---")
st.markdown("*Dashboard auto-updates every 30 seconds when enabled*")
st.markdown("*Built with Streamlit for real-time PetPlantr monitoring*")
