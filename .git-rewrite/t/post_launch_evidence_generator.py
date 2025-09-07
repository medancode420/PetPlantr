#!/usr/bin/env python3
"""
Post-Launch Evidence Report Generator
===================================

Creates comprehensive HTML evidence reports for PetPlantr T-0 launch:
- Golden signal compliance
- Performance metrics
- Error analysis
- SLO achievement
- Audit trail for compliance

Run this after golden signal monitoring to generate evidence.
"""

import json
import datetime
from pathlib import Path
from typing import Dict, List

class PostLaunchEvidenceGenerator:
    def __init__(self, evidence_file: str):
        self.evidence_file = evidence_file
        self.data = self._load_evidence()
        
    def _load_evidence(self) -> Dict:
        """Load evidence data from JSON file."""
        try:
            with open(self.evidence_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Evidence file not found: {self.evidence_file}")
            return {}
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in evidence file: {self.evidence_file}")
            return {}
    
    def generate_html_report(self) -> str:
        """Generate comprehensive HTML evidence report."""
        if not self.data:
            return self._generate_error_report()
        
        # Calculate summary statistics
        stats = self._calculate_statistics()
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PetPlantr T-0 Launch Evidence Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 40px; padding-bottom: 20px; border-bottom: 2px solid #eee; }}
        .header h1 {{ color: #2c3e50; margin: 0; font-size: 2.5em; }}
        .header .subtitle {{ color: #7f8c8d; font-size: 1.2em; margin-top: 10px; }}
        .status-badge {{ display: inline-block; padding: 8px 16px; border-radius: 20px; font-weight: bold; margin: 5px; }}
        .status-success {{ background: #d4edda; color: #155724; }}
        .status-warning {{ background: #fff3cd; color: #856404; }}
        .status-error {{ background: #f8d7da; color: #721c24; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0; }}
        .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #2c3e50; }}
        .metric-label {{ color: #6c757d; font-size: 0.9em; margin-top: 5px; }}
        .chart-container {{ margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }}
        .slo-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .slo-table th, .slo-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        .slo-table th {{ background: #f8f9fa; font-weight: bold; }}
        .compliance-good {{ color: #28a745; font-weight: bold; }}
        .compliance-bad {{ color: #dc3545; font-weight: bold; }}
        .timestamp {{ color: #6c757d; font-size: 0.9em; }}
        .evidence-section {{ margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }}
        .footer {{ text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #6c757d; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 PetPlantr T-0 Launch Evidence Report</h1>
            <div class="subtitle">Production Launch Validation & SLO Compliance</div>
            <div class="timestamp">Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
            {self._generate_status_badges(stats)}
        </div>
        
        <div class="metrics-grid">
            {self._generate_metric_cards(stats)}
        </div>
        
        <div class="evidence-section">
            <h2>📊 SLO Compliance Summary</h2>
            {self._generate_slo_table(stats)}
        </div>
        
        <div class="chart-container">
            <h2>📈 Performance Timeline</h2>
            {self._generate_timeline_chart()}
        </div>
        
        <div class="evidence-section">
            <h2>🔍 Detailed Analysis</h2>
            {self._generate_detailed_analysis(stats)}
        </div>
        
        <div class="evidence-section">
            <h2>📋 Audit Trail</h2>
            {self._generate_audit_trail()}
        </div>
        
        <div class="footer">
            <p><strong>Evidence File:</strong> {self.evidence_file}</p>
            <p><strong>Retention:</strong> 7 years (S3 Glacier, compliance tag)</p>
            <p><strong>Report Generated:</strong> {datetime.datetime.now().isoformat()}</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html
    
    def _calculate_statistics(self) -> Dict:
        """Calculate summary statistics from metrics."""
        metrics = self.data.get('metrics', [])
        if not metrics:
            return {}
        
        # Latency statistics
        latencies = [m['breed_detection']['latency_ms'] for m in metrics if m['breed_detection']['status'] == 'success']
        
        # Error rate
        total_samples = len(metrics)
        error_samples = sum(1 for m in metrics if m['error_rate_percent'] > 0)
        
        # SLO violations
        violation_samples = sum(1 for m in metrics if m['slo_violations'])
        
        # GPU utilization
        gpu_utils = [m['gpu_utilization_percent'] for m in metrics if m['gpu_utilization_percent'] is not None]
        
        return {
            'total_samples': total_samples,
            'duration_minutes': self._calculate_duration(),
            'avg_latency_ms': sum(latencies) / len(latencies) if latencies else 0,
            'p95_latency_ms': sorted(latencies)[int(0.95 * len(latencies))] if latencies else 0,
            'error_rate_percent': (error_samples / total_samples * 100) if total_samples > 0 else 0,
            'slo_compliance_percent': ((total_samples - violation_samples) / total_samples * 100) if total_samples > 0 else 0,
            'avg_gpu_utilization': sum(gpu_utils) / len(gpu_utils) if gpu_utils else 0,
            'violation_count': violation_samples,
            'success_count': total_samples - violation_samples
        }
    
    def _calculate_duration(self) -> float:
        """Calculate monitoring duration in minutes."""
        if not self.data.get('metrics'):
            return 0
        
        start = datetime.datetime.fromisoformat(self.data['monitor_start'].replace('Z', '+00:00'))
        end = datetime.datetime.fromisoformat(self.data['current_time'].replace('Z', '+00:00'))
        return (end - start).total_seconds() / 60
    
    def _generate_status_badges(self, stats: Dict) -> str:
        """Generate status badges based on SLO compliance."""
        if not stats:
            return '<span class="status-badge status-error">❌ NO DATA</span>'
        
        compliance = stats.get('slo_compliance_percent', 0)
        if compliance >= 99.9:
            status = '<span class="status-badge status-success">✅ EXCELLENT</span>'
        elif compliance >= 99.0:
            status = '<span class="status-badge status-success">✅ GOOD</span>'
        elif compliance >= 95.0:
            status = '<span class="status-badge status-warning">⚠️ ACCEPTABLE</span>'
        else:
            status = '<span class="status-badge status-error">❌ POOR</span>'
        
        return f'<div style="margin-top: 15px;">{status}</div>'
    
    def _generate_metric_cards(self, stats: Dict) -> str:
        """Generate metric cards for key statistics."""
        if not stats:
            return '<div class="metric-card"><div class="metric-value">No Data</div><div class="metric-label">Available</div></div>'
        
        cards = [
            ('slo_compliance_percent', 'SLO Compliance', '%', 'compliance-good' if stats.get('slo_compliance_percent', 0) >= 99 else 'compliance-bad'),
            ('avg_latency_ms', 'Avg Latency', 'ms', 'compliance-good' if stats.get('avg_latency_ms', 0) < 1000 else 'compliance-bad'),
            ('p95_latency_ms', 'P95 Latency', 'ms', 'compliance-good' if stats.get('p95_latency_ms', 0) < 2000 else 'compliance-bad'),
            ('error_rate_percent', 'Error Rate', '%', 'compliance-good' if stats.get('error_rate_percent', 0) < 0.1 else 'compliance-bad'),
            ('total_samples', 'Total Samples', '', 'compliance-good'),
            ('duration_minutes', 'Duration', 'min', 'compliance-good')
        ]
        
        html = ""
        for key, label, unit, css_class in cards:
            value = stats.get(key, 0)
            formatted_value = f"{value:.1f}" if isinstance(value, float) else str(value)
            html += f'''
            <div class="metric-card">
                <div class="metric-value {css_class}">{formatted_value}{unit}</div>
                <div class="metric-label">{label}</div>
            </div>
            '''
        
        return html
    
    def _generate_slo_table(self, stats: Dict) -> str:
        """Generate SLO compliance table."""
        thresholds = self.data.get('slo_thresholds', {})
        
        slos = [
            ('Latency (P95)', f"{thresholds.get('latency_p95_ms', 2000)}ms", 
             f"{stats.get('p95_latency_ms', 0):.1f}ms",
             stats.get('p95_latency_ms', 0) <= thresholds.get('latency_p95_ms', 2000)),
            ('Error Rate', f"{thresholds.get('error_rate_percent', 0.1)}%", 
             f"{stats.get('error_rate_percent', 0):.2f}%",
             stats.get('error_rate_percent', 0) <= thresholds.get('error_rate_percent', 0.1)),
            ('GPU Utilization', f"{thresholds.get('gpu_utilization_percent', 80)}%", 
             f"{stats.get('avg_gpu_utilization', 0):.1f}%",
             stats.get('avg_gpu_utilization', 0) <= thresholds.get('gpu_utilization_percent', 80))
        ]
        
        html = '<table class="slo-table"><tr><th>SLO</th><th>Threshold</th><th>Actual</th><th>Status</th></tr>'
        
        for slo_name, threshold, actual, compliant in slos:
            status = '<span class="compliance-good">✅ PASS</span>' if compliant else '<span class="compliance-bad">❌ FAIL</span>'
            html += f'<tr><td>{slo_name}</td><td>{threshold}</td><td>{actual}</td><td>{status}</td></tr>'
        
        html += '</table>'
        return html
    
    def _generate_timeline_chart(self) -> str:
        """Generate simple timeline visualization."""
        metrics = self.data.get('metrics', [])
        if not metrics:
            return '<p>No timeline data available</p>'
        
        # Simple text-based timeline for now
        html = '<div style="font-family: monospace; font-size: 0.9em;">'
        
        for i, metric in enumerate(metrics[-10:]):  # Show last 10 samples
            timestamp = metric['timestamp'][:19]
            latency = metric['breed_detection']['latency_ms']
            violations = len(metric['slo_violations'])
            
            status = '🔴' if violations > 0 else '✅'
            html += f'<div>{timestamp} | {status} | Latency: {latency:.1f}ms | Violations: {violations}</div>'
        
        html += '</div>'
        return html
    
    def _generate_detailed_analysis(self, stats: Dict) -> str:
        """Generate detailed performance analysis."""
        html = '<ul>'
        
        if stats.get('slo_compliance_percent', 0) >= 99:
            html += '<li><strong>✅ Excellent SLO Performance:</strong> System maintained high availability throughout launch period.</li>'
        else:
            html += f'<li><strong>⚠️ SLO Concerns:</strong> {stats.get("violation_count", 0)} violations detected during monitoring.</li>'
        
        if stats.get('avg_latency_ms', 0) < 1000:
            html += '<li><strong>✅ Low Latency:</strong> Average response times well below user expectations.</li>'
        else:
            html += '<li><strong>⚠️ High Latency:</strong> Consider performance optimization for future releases.</li>'
        
        if stats.get('error_rate_percent', 0) < 0.1:
            html += '<li><strong>✅ High Reliability:</strong> Error rates maintained within business requirements.</li>'
        else:
            html += '<li><strong>❌ Reliability Issues:</strong> Error rate exceeds acceptable threshold.</li>'
        
        html += '</ul>'
        return html
    
    def _generate_audit_trail(self) -> str:
        """Generate audit trail information."""
        return f'''
        <ul>
            <li><strong>Monitor Start:</strong> {self.data.get('monitor_start', 'Unknown')}</li>
            <li><strong>Monitor End:</strong> {self.data.get('current_time', 'Unknown')}</li>
            <li><strong>Total Samples:</strong> {self.data.get('total_samples', 0)}</li>
            <li><strong>Evidence File:</strong> {self.evidence_file}</li>
            <li><strong>SLO Thresholds:</strong> {json.dumps(self.data.get('slo_thresholds', {}), indent=2)}</li>
            <li><strong>Retention Policy:</strong> 7 years (S3 Glacier with compliance tag)</li>
            <li><strong>Compliance Standard:</strong> SOC 2 Type II, ISO 27001</li>
        </ul>
        '''
    
    def _generate_error_report(self) -> str:
        """Generate error report when no data is available."""
        return '''
<!DOCTYPE html>
<html>
<head><title>PetPlantr Launch Evidence - Error</title></head>
<body style="font-family: system-ui; padding: 40px; text-align: center;">
    <h1 style="color: #dc3545;">❌ Evidence Generation Failed</h1>
    <p>Unable to load monitoring data from evidence file.</p>
    <p>Please ensure golden signal monitoring has completed successfully.</p>
</body>
</html>
        '''

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate post-launch evidence report")
    parser.add_argument("evidence_file", help="Path to JSON evidence file from golden signal monitor")
    parser.add_argument("--output", "-o", help="Output HTML file path", 
                       default=lambda: f"launch_evidence_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
    
    args = parser.parse_args()
    if callable(args.output):
        args.output = args.output()
    
    generator = PostLaunchEvidenceGenerator(args.evidence_file)
    html_report = generator.generate_html_report()
    
    with open(args.output, 'w') as f:
        f.write(html_report)
    
    print(f"📄 Evidence report generated: {args.output}")
    print(f"📤 Upload to S3 Glacier 'audit' bucket with 7-year retention tag")
    print(f"📋 Include in compliance documentation package")

if __name__ == "__main__":
    main()
