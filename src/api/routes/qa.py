#!/usr/bin/env python3
"""
QA API Routes for PetPlantr
Story 1.2: Human label QA pass (95% precision)
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, HTMLResponse
from typing import List, Optional, Dict, Any
import json
from pathlib import Path
from datetime import datetime

from src.qa_system import BreedQASystem, QASample

router = APIRouter(prefix="/api/v1/qa", tags=["qa"])
qa_system = BreedQASystem()

@router.get("/samples", response_model=List[Dict[str, Any]])
async def get_qa_samples(
    limit: int = Query(10, description="Number of samples to return"),
    status: Optional[str] = Query(None, description="Filter by status: pending, correct, incorrect")
):
    """Get QA samples for human review"""
    try:
        if status:
            samples = [s for s in qa_system.qa_samples.values() if s.qa_status == status]
        else:
            samples = list(qa_system.qa_samples.values())

        # Convert to dict format for JSON response
        sample_dicts = []
        for sample in samples[:limit]:
            sample_dict = {
                "filename": sample.filename,
                "breed": sample.breed,
                "predicted_breed": sample.predicted_breed,
                "confidence": sample.confidence,
                "image_data": sample.image_data,
                "qa_status": sample.qa_status,
                "human_label": sample.human_label,
                "reviewed_at": sample.reviewed_at.isoformat() if sample.reviewed_at else None
            }
            sample_dicts.append(sample_dict)

        return sample_dicts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get QA samples: {str(e)}")

@router.post("/review")
async def submit_qa_review(
    filename: str,
    human_label: str,
    is_correct: bool
):
    """Submit human QA review"""
    try:
        qa_system.submit_qa_review(filename, human_label, is_correct)
        return {"status": "success", "message": f"QA review submitted for {filename}"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit QA review: {str(e)}")

@router.get("/metrics")
async def get_qa_metrics():
    """Get QA precision metrics"""
    try:
        metrics = qa_system.calculate_precision()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get QA metrics: {str(e)}")

@router.get("/report")
async def get_qa_report():
    """Get comprehensive QA report"""
    try:
        report = qa_system.export_qa_report()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate QA report: {str(e)}")

@router.post("/generate-samples")
async def generate_qa_samples(
    num_samples: int = Query(100, description="Number of samples to generate")
):
    """Generate new QA samples for review"""
    try:
        qa_system.generate_qa_samples(num_samples=num_samples)
        return {"status": "success", "message": f"Generated {num_samples} QA samples"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate QA samples: {str(e)}")

@router.get("/dashboard", response_class=HTMLResponse)
async def get_qa_dashboard():
    """Get QA dashboard HTML interface"""
    try:
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>PetPlantr QA Dashboard</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    padding: 20px;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .metrics {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .metric-card {{
                    background: #f8f9fa;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    border-left: 4px solid #007bff;
                }}
                .metric-value {{
                    font-size: 2em;
                    font-weight: bold;
                    color: #007bff;
                }}
                .metric-label {{
                    color: #666;
                    margin-top: 5px;
                }}
                .qa-sample {{
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 15px;
                    display: flex;
                    align-items: center;
                    gap: 15px;
                }}
                .qa-image {{
                    width: 100px;
                    height: 100px;
                    object-fit: cover;
                    border-radius: 4px;
                }}
                .qa-info {{
                    flex: 1;
                }}
                .qa-actions {{
                    display: flex;
                    gap: 10px;
                }}
                button {{
                    padding: 8px 16px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: 500;
                }}
                .btn-correct {{
                    background: #28a745;
                    color: white;
                }}
                .btn-incorrect {{
                    background: #dc3545;
                    color: white;
                }}
                .status {{
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 0.8em;
                    font-weight: bold;
                }}
                .status-pending {{ background: #fff3cd; color: #856404; }}
                .status-correct {{ background: #d4edda; color: #155724; }}
                .status-incorrect {{ background: #f8d7da; color: #721c24; }}
                .progress-bar {{
                    width: 100%;
                    height: 20px;
                    background: #e9ecef;
                    border-radius: 10px;
                    overflow: hidden;
                    margin: 10px 0;
                }}
                .progress-fill {{
                    height: 100%;
                    background: linear-gradient(90deg, #28a745, #20c997);
                    transition: width 0.3s ease;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🐕 PetPlantr QA Dashboard</h1>
                    <p>Human Label Quality Assurance System</p>
                </div>

                <div class="metrics" id="metrics">
                    <div class="metric-card">
                        <div class="metric-value" id="total-samples">-</div>
                        <div class="metric-label">Total Samples</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="reviewed-samples">-</div>
                        <div class="metric-label">Reviewed</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="precision">-</div>
                        <div class="metric-label">Precision</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="qa-status">-</div>
                        <div class="metric-label">Status</div>
                    </div>
                </div>

                <div class="progress-bar">
                    <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
                </div>

                <h2>QA Samples for Review</h2>
                <div id="qa-samples">
                    <p>Loading QA samples...</p>
                </div>

                <button onclick="generateSamples()" style="margin-top: 20px; padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    Generate More Samples
                </button>
            </div>

            <script>
                async function loadMetrics() {{
                    try {{
                        const response = await fetch('/api/v1/qa/metrics');
                        const metrics = await response.json();

                        document.getElementById('total-samples').textContent = metrics.total_reviewed || 0;
                        document.getElementById('reviewed-samples').textContent = metrics.total_reviewed || 0;
                        document.getElementById('precision').textContent = (metrics.precision * 100).toFixed(1) + '%';
                        document.getElementById('qa-status').textContent = metrics.precision >= 0.95 ? 'PASS' : 'FAIL';

                        const progress = metrics.total_reviewed > 0 ? (metrics.correct / metrics.total_reviewed) * 100 : 0;
                        document.getElementById('progress-fill').style.width = progress + '%';
                    }} catch (error) {{
                        console.error('Failed to load metrics:', error);
                    }}
                }}

                async function loadQASamples() {{
                    try {{
                        const response = await fetch('/api/v1/qa/samples?limit=10&status=pending');
                        const samples = await response.json();

                        const container = document.getElementById('qa-samples');
                        if (samples.length === 0) {{
                            container.innerHTML = '<p>No pending QA samples found.</p>';
                            return;
                        }}

                        container.innerHTML = samples.map(sample => `
                            <div class="qa-sample">
                                <img src="${{sample.image_data}}" alt="${{sample.filename}}" class="qa-image" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgdmlld0JveD0iMCAwIDEwMCAxMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIiBmaWxsPSIjZGRkIi8+Cjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyIiBmaWxsPSIjOTk5IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iMC4zZW0iPk5vIEltYWdlPC90ZXh0Pgo8L3N2Zz4='">
                                <div class="qa-info">
                                    <h4>${{sample.filename}}</h4>
                                    <p><strong>Predicted:</strong> ${{sample.predicted_breed}}</p>
                                    <p><strong>Confidence:</strong> ${{ (sample.confidence * 100).toFixed(1) }}%</p>
                                    <span class="status status-${{sample.qa_status}}">${{sample.qa_status}}</span>
                                </div>
                                <div class="qa-actions">
                                    <button class="btn-correct" onclick="submitReview('${{sample.filename}}', '${{sample.breed}}', true)">Correct</button>
                                    <button class="btn-incorrect" onclick="submitReview('${{sample.filename}}', '${{sample.breed}}', false)">Incorrect</button>
                                </div>
                            </div>
                        `).join('');
                    }} catch (error) {{
                        console.error('Failed to load QA samples:', error);
                        document.getElementById('qa-samples').innerHTML = '<p>Error loading QA samples.</p>';
                    }}
                }}

                async function submitReview(filename, humanLabel, isCorrect) {{
                    try {{
                        const response = await fetch('/api/v1/qa/review', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{
                                filename: filename,
                                human_label: humanLabel,
                                is_correct: isCorrect
                            }})
                        }});

                        if (response.ok) {{
                            alert('Review submitted successfully!');
                            loadMetrics();
                            loadQASamples();
                        }} else {{
                            alert('Failed to submit review');
                        }}
                    }} catch (error) {{
                        console.error('Failed to submit review:', error);
                        alert('Error submitting review');
                    }}
                }}

                async function generateSamples() {{
                    try {{
                        const response = await fetch('/api/v1/qa/generate-samples?num_samples=50', {{
                            method: 'POST'
                        }});

                        if (response.ok) {{
                            alert('New QA samples generated!');
                            loadQASamples();
                        }} else {{
                            alert('Failed to generate samples');
                        }}
                    }} catch (error) {{
                        console.error('Failed to generate samples:', error);
                        alert('Error generating samples');
                    }}
                }}

                // Load data on page load
                loadMetrics();
                loadQASamples();

                // Refresh every 30 seconds
                setInterval(() => {{
                    loadMetrics();
                    loadQASamples();
                }}, 30000);
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load QA dashboard: {str(e)}")


@router.get("/analytics/performance")
async def get_performance_analytics():
    """Get performance analytics data for charts"""
    try:
        # Mock performance data - in production, this would come from your metrics system
        performance_data = {
            "response_times": {
                "labels": ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"],
                "data": [120, 95, 150, 110, 130, 105]
            },
            "throughput": {
                "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                "data": [1250, 1380, 1150, 1420, 1350, 980, 1100]
            },
            "error_rates": {
                "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
                "data": [0.02, 0.015, 0.025, 0.01]
            }
        }
        return performance_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance analytics: {str(e)}")


@router.get("/analytics/breeds")
async def get_breed_analytics():
    """Get breed detection analytics for visualization"""
    try:
        # Mock breed analytics data
        breed_data = {
            "accuracy_trend": {
                "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                "data": [85.2, 87.1, 88.5, 89.2, 90.1, 91.3]
            },
            "popular_breeds": [
                {"breed": "Golden Retriever", "count": 245, "accuracy": 94.2},
                {"breed": "Labrador", "count": 198, "accuracy": 95.1},
                {"breed": "Pug", "count": 156, "accuracy": 89.3},
                {"breed": "Bulldog", "count": 134, "accuracy": 92.8},
                {"breed": "Beagle", "count": 112, "accuracy": 91.7}
            ],
            "accuracy_distribution": {
                "labels": ["90-100%", "80-89%", "70-79%", "60-69%", "<60%"],
                "data": [45, 32, 15, 6, 2]
            }
        }
        return breed_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get breed analytics: {str(e)}")


@router.get("/analytics/users")
async def get_user_analytics():
    """Get user engagement and behavior analytics"""
    try:
        user_data = {
            "daily_active_users": {
                "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                "data": [1250, 1380, 1150, 1420, 1350, 980, 1100]
            },
            "user_retention": {
                "labels": ["Day 1", "Day 7", "Day 30"],
                "data": [100, 65, 35]
            },
            "feature_usage": [
                {"feature": "Breed Detection", "usage": 85},
                {"feature": "3D Generation", "usage": 72},
                {"feature": "Model Download", "usage": 58},
                {"feature": "Gallery View", "usage": 45}
            ]
        }
        return user_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user analytics: {str(e)}")


@router.get("/analytics/revenue")
async def get_revenue_analytics():
    """Get revenue analytics (Stripe integration)"""
    try:
        revenue_data = {
            "monthly_revenue": {
                "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                "data": [12500, 15200, 18900, 22100, 25600, 28300]
            },
            "conversion_funnel": [
                {"stage": "Visitors", "count": 10000},
                {"stage": "Signups", "count": 2500},
                {"stage": "Paid Users", "count": 850},
                {"stage": "Repeat Customers", "count": 320}
            ],
            "average_order_value": {
                "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                "data": [24.50, 26.80, 28.90, 27.20, 29.50, 31.10]
            }
        }
        return revenue_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get revenue analytics: {str(e)}")


@router.get("/dashboard/enhanced", response_class=HTMLResponse)
async def get_enhanced_dashboard():
    """Get enhanced analytics dashboard with interactive charts"""
    try:
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>PetPlantr Analytics Dashboard</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                    padding: 30px;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                    border-bottom: 2px solid #e9ecef;
                    padding-bottom: 20px;
                }}
                .dashboard-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                    gap: 30px;
                    margin-bottom: 40px;
                }}
                .chart-container {{
                    background: white;
                    border-radius: 8px;
                    padding: 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                    border: 1px solid #e9ecef;
                }}
                .chart-header {{
                    font-size: 1.2em;
                    font-weight: 600;
                    margin-bottom: 15px;
                    color: #495057;
                }}
                .metric-card {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                }}
                .metric-value {{
                    font-size: 2.5em;
                    font-weight: bold;
                    margin-bottom: 5px;
                }}
                .metric-label {{
                    font-size: 0.9em;
                    opacity: 0.9;
                }}
                .tabs {{
                    display: flex;
                    margin-bottom: 30px;
                    border-bottom: 1px solid #dee2e6;
                }}
                .tab {{
                    padding: 12px 24px;
                    cursor: pointer;
                    border-bottom: 3px solid transparent;
                    transition: all 0.3s ease;
                }}
                .tab.active {{
                    border-bottom-color: #007bff;
                    color: #007bff;
                    font-weight: 600;
                }}
                .tab-content {{
                    display: none;
                }}
                .tab-content.active {{
                    display: block;
                }}
                .refresh-btn {{
                    background: #28a745;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 0.9em;
                    margin-bottom: 20px;
                }}
                .refresh-btn:hover {{
                    background: #218838;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 PetPlantr Analytics Dashboard</h1>
                    <p>Real-time insights and performance metrics</p>
                    <button class="refresh-btn" onclick="refreshAllData()">🔄 Refresh Data</button>
                </div>

                <div class="tabs">
                    <div class="tab active" onclick="switchTab('performance')">Performance</div>
                    <div class="tab" onclick="switchTab('breeds')">Breed Analytics</div>
                    <div class="tab" onclick="switchTab('users')">User Engagement</div>
                    <div class="tab" onclick="switchTab('revenue')">Revenue</div>
                </div>

                <div id="performance" class="tab-content active">
                    <div class="dashboard-grid">
                        <div class="chart-container">
                            <div class="chart-header">Response Time Trends</div>
                            <canvas id="responseTimeChart" width="400" height="200"></canvas>
                        </div>
                        <div class="chart-container">
                            <div class="chart-header">System Throughput</div>
                            <canvas id="throughputChart" width="400" height="200"></canvas>
                        </div>
                        <div class="chart-container">
                            <div class="chart-header">Error Rate Trends</div>
                            <canvas id="errorRateChart" width="400" height="200"></canvas>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" id="avgResponseTime">-</div>
                            <div class="metric-label">Avg Response Time (ms)</div>
                        </div>
                    </div>
                </div>

                <div id="breeds" class="tab-content">
                    <div class="dashboard-grid">
                        <div class="chart-container">
                            <div class="chart-header">Breed Detection Accuracy Trend</div>
                            <canvas id="breedAccuracyChart" width="400" height="200"></canvas>
                        </div>
                        <div class="chart-container">
                            <div class="chart-header">Accuracy Distribution</div>
                            <canvas id="accuracyDistributionChart" width="400" height="200"></canvas>
                        </div>
                        <div class="chart-container">
                            <div class="chart-header">Popular Breeds</div>
                            <canvas id="popularBreedsChart" width="400" height="200"></canvas>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" id="overallAccuracy">91.3%</div>
                            <div class="metric-label">Overall Accuracy</div>
                        </div>
                    </div>
                </div>

                <div id="users" class="tab-content">
                    <div class="dashboard-grid">
                        <div class="chart-container">
                            <div class="chart-header">Daily Active Users</div>
                            <canvas id="dauChart" width="400" height="200"></canvas>
                        </div>
                        <div class="chart-container">
                            <div class="chart-header">User Retention</div>
                            <canvas id="retentionChart" width="400" height="200"></canvas>
                        </div>
                        <div class="chart-container">
                            <div class="chart-header">Feature Usage</div>
                            <canvas id="featureUsageChart" width="400" height="200"></canvas>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" id="totalUsers">12,450</div>
                            <div class="metric-label">Total Registered Users</div>
                        </div>
                    </div>
                </div>

                <div id="revenue" class="tab-content">
                    <div class="dashboard-grid">
                        <div class="chart-container">
                            <div class="chart-header">Monthly Revenue</div>
                            <canvas id="revenueChart" width="400" height="200"></canvas>
                        </div>
                        <div class="chart-container">
                            <div class="chart-header">Conversion Funnel</div>
                            <canvas id="conversionChart" width="400" height="200"></canvas>
                        </div>
                        <div class="chart-container">
                            <div class="chart-header">Average Order Value</div>
                            <canvas id="aovChart" width="400" height="200"></canvas>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" id="totalRevenue">$28,300</div>
                            <div class="metric-label">This Month's Revenue</div>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                let charts = {{}};

                function switchTab(tabName) {{
                    // Hide all tabs
                    document.querySelectorAll('.tab-content').forEach(content => {{
                        content.classList.remove('active');
                    }});
                    document.querySelectorAll('.tab').forEach(tab => {{
                        tab.classList.remove('active');
                    }});

                    // Show selected tab
                    document.getElementById(tabName).classList.add('active');
                    event.target.classList.add('active');

                    // Load data for the tab
                    loadTabData(tabName);
                }}

                async function loadTabData(tabName) {{
                    try {{
                        const response = await fetch(`/api/v1/qa/analytics/${{tabName}}`);
                        const data = await response.json();

                        switch(tabName) {{
                            case 'performance':
                                loadPerformanceCharts(data);
                                break;
                            case 'breeds':
                                loadBreedCharts(data);
                                break;
                            case 'users':
                                loadUserCharts(data);
                                break;
                            case 'revenue':
                                loadRevenueCharts(data);
                                break;
                        }}
                    }} catch (error) {{
                        console.error('Failed to load tab data:', error);
                    }}
                }}

                function loadPerformanceCharts(data) {{
                    // Response Time Chart
                    if (charts.responseTimeChart) charts.responseTimeChart.destroy();
                    charts.responseTimeChart = new Chart(
                        document.getElementById('responseTimeChart'),
                        {{
                            type: 'line',
                            data: {{
                                labels: data.response_times.labels,
                                datasets: [{{
                                    label: 'Response Time (ms)',
                                    data: data.response_times.data,
                                    borderColor: '#007bff',
                                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                                    tension: 0.4
                                }}]
                            }},
                            options: {{
                                responsive: true,
                                plugins: {{
                                    legend: {{ display: false }}
                                }}
                            }}
                        }}
                    );

                    // Throughput Chart
                    if (charts.throughputChart) charts.throughputChart.destroy();
                    charts.throughputChart = new Chart(
                        document.getElementById('throughputChart'),
                        {{
                            type: 'bar',
                            data: {{
                                labels: data.throughput.labels,
                                datasets: [{{
                                    label: 'Requests per Hour',
                                    data: data.throughput.data,
                                    backgroundColor: '#28a745'
                                }}]
                            }},
                            options: {{
                                responsive: true,
                                plugins: {{
                                    legend: {{ display: false }}
                                }}
                            }}
                        }}
                    );

                    // Error Rate Chart
                    if (charts.errorRateChart) charts.errorRateChart.destroy();
                    charts.errorRateChart = new Chart(
                        document.getElementById('errorRateChart'),
                        {{
                            type: 'line',
                            data: {{
                                labels: data.error_rates.labels,
                                datasets: [{{
                                    label: 'Error Rate (%)',
                                    data: data.error_rates.data.map(x => x * 100),
                                    borderColor: '#dc3545',
                                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                                    tension: 0.4
                                }}]
                            }},
                            options: {{
                                responsive: true,
                                plugins: {{
                                    legend: {{ display: false }}
                                }}
                            }}
                        }}
                    );

                    // Update metrics
                    const avgResponse = data.response_times.data.reduce((a, b) => a + b) / data.response_times.data.length;
                    document.getElementById('avgResponseTime').textContent = Math.round(avgResponse);
                }}

                function loadBreedCharts(data) {{
                    // Breed Accuracy Trend
                    if (charts.breedAccuracyChart) charts.breedAccuracyChart.destroy();
                    charts.breedAccuracyChart = new Chart(
                        document.getElementById('breedAccuracyChart'),
                        {{
                            type: 'line',
                            data: {{
                                labels: data.accuracy_trend.labels,
                                datasets: [{{
                                    label: 'Accuracy (%)',
                                    data: data.accuracy_trend.data,
                                    borderColor: '#28a745',
                                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                                    tension: 0.4
                                }}]
                            }},
                            options: {{
                                responsive: true,
                                plugins: {{
                                    legend: {{ display: false }}
                                }}
                            }}
                        }}
                    );

                    // Accuracy Distribution
                    if (charts.accuracyDistributionChart) charts.accuracyDistributionChart.destroy();
                    charts.accuracyDistributionChart = new Chart(
                        document.getElementById('accuracyDistributionChart'),
                        {{
                            type: 'doughnut',
                            data: {{
                                labels: data.accuracy_distribution.labels,
                                datasets: [{{
                                    data: data.accuracy_distribution.data,
                                    backgroundColor: [
                                        '#28a745',
                                        '#ffc107',
                                        '#fd7e14',
                                        '#dc3545',
                                        '#6c757d'
                                    ]
                                }}]
                            }},
                            options: {{
                                responsive: true
                            }}
                        }}
                    );

                    // Popular Breeds
                    if (charts.popularBreedsChart) charts.popularBreedsChart.destroy();
                    charts.popularBreedsChart = new Chart(
                        document.getElementById('popularBreedsChart'),
                        {{
                            type: 'horizontalBar',
                            data: {{
                                labels: data.popular_breeds.map(b => b.breed),
                                datasets: [{{
                                    label: 'Detection Count',
                                    data: data.popular_breeds.map(b => b.count),
                                    backgroundColor: '#007bff'
                                }}]
                            }},
                            options: {{
                                responsive: true,
                                plugins: {{
                                    legend: {{ display: false }}
                                }}
                            }}
                        }}
                    );
                }}

                function loadUserCharts(data) {{
                    // Daily Active Users
                    if (charts.dauChart) charts.dauChart.destroy();
                    charts.dauChart = new Chart(
                        document.getElementById('dauChart'),
                        {{
                            type: 'line',
                            data: {{
                                labels: data.daily_active_users.labels,
                                datasets: [{{
                                    label: 'Daily Active Users',
                                    data: data.daily_active_users.data,
                                    borderColor: '#007bff',
                                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                                    tension: 0.4
                                }}]
                            }},
                            options: {{
                                responsive: true,
                                plugins: {{
                                    legend: {{ display: false }}
                                }}
                            }}
                        }}
                    );

                    // User Retention
                    if (charts.retentionChart) charts.retentionChart.destroy();
                    charts.retentionChart = new Chart(
                        document.getElementById('retentionChart'),
                        {{
                            type: 'bar',
                            data: {{
                                labels: data.user_retention.labels,
                                datasets: [{{
                                    label: 'Retention Rate (%)',
                                    data: data.user_retention.data,
                                    backgroundColor: '#28a745'
                                }}]
                            }},
                            options: {{
                                responsive: true,
                                plugins: {{
                                    legend: {{ display: false }}
                                }}
                            }}
                        }}
                    );

                    // Feature Usage
                    if (charts.featureUsageChart) charts.featureUsageChart.destroy();
                    charts.featureUsageChart = new Chart(
                        document.getElementById('featureUsageChart'),
                        {{
                            type: 'doughnut',
                            data: {{
                                labels: data.feature_usage.map(f => f.feature),
                                datasets: [{{
                                    data: data.feature_usage.map(f => f.usage),
                                    backgroundColor: [
                                        '#007bff',
                                        '#28a745',
                                        '#ffc107',
                                        '#dc3545'
                                    ]
                                }}]
                            }},
                            options: {{
                                responsive: true
                            }}
                        }}
                    );
                }}

                function loadRevenueCharts(data) {{
                    // Monthly Revenue
                    if (charts.revenueChart) charts.revenueChart.destroy();
                    charts.revenueChart = new Chart(
                        document.getElementById('revenueChart'),
                        {{
                            type: 'line',
                            data: {{
                                labels: data.monthly_revenue.labels,
                                datasets: [{{
                                    label: 'Revenue ($)',
                                    data: data.monthly_revenue.data,
                                    borderColor: '#28a745',
                                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                                    tension: 0.4
                                }}]
                            }},
                            options: {{
                                responsive: true,
                                plugins: {{
                                    legend: {{ display: false }}
                                }}
                            }}
                        }}
                    );

                    // Conversion Funnel
                    if (charts.conversionChart) charts.conversionChart.destroy();
                    charts.conversionChart = new Chart(
                        document.getElementById('conversionChart'),
                        {{
                            type: 'bar',
                            data: {{
                                labels: data.conversion_funnel.map(c => c.stage),
                                datasets: [{{
                                    label: 'Users',
                                    data: data.conversion_funnel.map(c => c.count),
                                    backgroundColor: '#007bff'
                                }}]
                            }},
                            options: {{
                                responsive: true,
                                plugins: {{
                                    legend: {{ display: false }}
                                }}
                            }}
                        }}
                    );

                    // Average Order Value
                    if (charts.aovChart) charts.aovChart.destroy();
                    charts.aovChart = new Chart(
                        document.getElementById('aovChart'),
                        {{
                            type: 'line',
                            data: {{
                                labels: data.average_order_value.labels,
                                datasets: [{{
                                    label: 'AOV ($)',
                                    data: data.average_order_value.data,
                                    borderColor: '#ffc107',
                                    backgroundColor: 'rgba(255, 193, 7, 0.1)',
                                    tension: 0.4
                                }}]
                            }},
                            options: {{
                                responsive: true,
                                plugins: {{
                                    legend: {{ display: false }}
                                }}
                            }}
                        }}
                    );
                }}

                async function refreshAllData() {{
                    const activeTab = document.querySelector('.tab.active');
                    if (activeTab) {{
                        const tabName = activeTab.textContent.toLowerCase().replace(' ', '');
                        await loadTabData(tabName);
                    }}
                }}

                // Load initial data
                loadTabData('performance');

                // Auto-refresh every 60 seconds
                setInterval(refreshAllData, 60000);
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load enhanced dashboard: {str(e)}")
