#!/usr/bin/env python3
"""
PetPlantr Quality Control Dashboard
Comprehensive quality monitoring and reporting system
"""
import sys
import json
import glob
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import numpy as np
from enhanced_stl_analyzer import analyze_stl_quality
from production_readiness_checker import ProductionReadinessChecker
import argparse

class QualityControlDashboard:
    """
    Comprehensive quality control dashboard for PetPlantr production
    """
    
    def __init__(self, models_directory):
        self.models_dir = Path(models_directory)
        self.checker = ProductionReadinessChecker()
        self.dashboard_data = {}
    
    def scan_all_models(self):
        """Scan all STL models and generate comprehensive quality data"""
        print("🔍 Scanning all models for quality control dashboard...")
        
        # Find all STL files
        stl_files = list(self.models_dir.glob("*.stl"))
        print(f"📁 Found {len(stl_files)} STL files to analyze")
        
        models_data = []
        production_ready_count = 0
        
        for i, stl_file in enumerate(stl_files, 1):
            print(f"\n🔍 Processing {i}/{len(stl_files)}: {stl_file.name}")
            
            try:
                # Get quality analysis
                quality_report, _ = analyze_stl_quality(str(stl_file))
                
                # Get production readiness
                production_results = self.checker.check_production_readiness(str(stl_file))
                
                # Combine data
                model_data = {
                    'filename': stl_file.name,
                    'file_path': str(stl_file),
                    'file_size_mb': stl_file.stat().st_size / (1024*1024),
                    'last_modified': datetime.fromtimestamp(stl_file.stat().st_mtime),
                    'overall_score': quality_report['quality_scores']['overall'],
                    'geometry_score': quality_report['quality_scores']['geometry'],
                    'topology_score': quality_report['quality_scores']['topology'],
                    'printability_score': quality_report['quality_scores']['printability'],
                    'volume_mm3': quality_report['geometry']['volume_mm3'],
                    'surface_area_mm2': quality_report['geometry']['surface_area_mm2'],
                    'width_mm': quality_report['geometry']['dimensions_mm']['width'],
                    'height_mm': quality_report['geometry']['dimensions_mm']['height'],
                    'depth_mm': quality_report['geometry']['dimensions_mm']['depth'],
                    'face_count': quality_report['mesh_quality']['face_count'],
                    'vertex_count': quality_report['mesh_quality']['vertex_count'],
                    'is_watertight': quality_report['mesh_quality']['is_watertight'] == 'True',
                    'triangle_quality': quality_report['mesh_quality']['avg_triangle_quality'],
                    'normal_consistency': quality_report['mesh_quality']['normal_consistency'],
                    'is_planter_like': quality_report['planter_analysis']['is_planter_like'],
                    'planter_ratio': quality_report['planter_analysis']['planter_ratio'],
                    'production_ready': production_results['production_ready'],
                    'production_grade': production_results['overall_grade'],
                    'critical_failures': len(production_results.get('critical_failures', [])),
                    'warnings': len(production_results.get('warnings', [])),
                    'quality_category': self._categorize_quality(quality_report['quality_scores']['overall'])
                }
                
                models_data.append(model_data)
                
                if production_results['production_ready']:
                    production_ready_count += 1
                
                print(f"   ✅ Score: {quality_report['quality_scores']['overall']}/100, "
                      f"Grade: {production_results['overall_grade']}, "
                      f"Ready: {'✅' if production_results['production_ready'] else '❌'}")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                models_data.append({
                    'filename': stl_file.name,
                    'error': str(e),
                    'production_ready': False,
                    'production_grade': 'F'
                })
        
        self.dashboard_data = {
            'scan_timestamp': datetime.now(),
            'total_models': len(stl_files),
            'successful_analyses': len([m for m in models_data if 'error' not in m]),
            'production_ready_count': production_ready_count,
            'models': models_data
        }
        
        return pd.DataFrame([m for m in models_data if 'error' not in m])
    
    def _categorize_quality(self, score):
        """Categorize quality score"""
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Very Good"
        elif score >= 70:
            return "Good"
        elif score >= 60:
            return "Acceptable"
        else:
            return "Needs Improvement"
    
    def create_dashboard(self, df):
        """Create comprehensive quality control dashboard"""
        print("📊 Creating Quality Control Dashboard...")
        
        # Set up the dashboard
        fig = plt.figure(figsize=(24, 18))
        fig.suptitle('PetPlantr Quality Control Dashboard', fontsize=20, fontweight='bold')
        
        # Create grid layout
        gs = fig.add_gridspec(4, 4, hspace=0.3, wspace=0.3)
        
        # 1. Overall Quality Distribution
        ax1 = fig.add_subplot(gs[0, 0])
        quality_counts = df['quality_category'].value_counts()
        colors = ['gold', 'lightgreen', 'lightyellow', 'orange', 'lightcoral']
        ax1.pie(quality_counts.values, labels=quality_counts.index, colors=colors, autopct='%1.1f%%')
        ax1.set_title('Quality Distribution', fontweight='bold')
        
        # 2. Production Readiness
        ax2 = fig.add_subplot(gs[0, 1])
        ready_counts = df['production_ready'].value_counts()
        colors = ['lightgreen', 'lightcoral']
        labels = ['Production Ready', 'Not Ready']
        ax2.pie(ready_counts.values, labels=labels, colors=colors, autopct='%1.1f%%')
        ax2.set_title('Production Readiness', fontweight='bold')
        
        # 3. Score Distribution Histogram
        ax3 = fig.add_subplot(gs[0, 2])
        ax3.hist(df['overall_score'], bins=20, color='skyblue', alpha=0.7, edgecolor='black')
        ax3.axvline(df['overall_score'].mean(), color='red', linestyle='--', 
                   label=f'Mean: {df["overall_score"].mean():.1f}')
        ax3.set_title('Overall Score Distribution')
        ax3.set_xlabel('Score')
        ax3.set_ylabel('Count')
        ax3.legend()
        
        # 4. Grade Distribution
        ax4 = fig.add_subplot(gs[0, 3])
        grade_counts = df['production_grade'].value_counts()
        grade_order = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'D', 'F']
        grade_counts = grade_counts.reindex([g for g in grade_order if g in grade_counts.index])
        ax4.bar(range(len(grade_counts)), grade_counts.values, color='lightsteelblue')
        ax4.set_title('Production Grade Distribution')
        ax4.set_xlabel('Grade')
        ax4.set_ylabel('Count')
        ax4.set_xticks(range(len(grade_counts)))
        ax4.set_xticklabels(grade_counts.index)
        
        # 5. Score Comparison Radar
        ax5 = fig.add_subplot(gs[1, 0], projection='polar')
        categories = ['Overall', 'Geometry', 'Topology', 'Printability']
        mean_scores = [
            df['overall_score'].mean(),
            df['geometry_score'].mean(),
            df['topology_score'].mean(),
            df['printability_score'].mean()
        ]
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        mean_scores += mean_scores[:1]
        angles += angles[:1]
        ax5.plot(angles, mean_scores, 'o-', linewidth=2, color='blue')
        ax5.fill(angles, mean_scores, alpha=0.25, color='blue')
        ax5.set_ylim(0, 100)
        ax5.set_xticks(angles[:-1])
        ax5.set_xticklabels(categories)
        ax5.set_title('Average Scores by Category', fontweight='bold')
        
        # 6. Volume vs Quality Scatter
        ax6 = fig.add_subplot(gs[1, 1])
        scatter = ax6.scatter(df['volume_mm3'], df['overall_score'], 
                            c=df['production_ready'].map({True: 'green', False: 'red'}), 
                            alpha=0.6)
        ax6.set_title('Volume vs Quality')
        ax6.set_xlabel('Volume (mm³)')
        ax6.set_ylabel('Overall Score')
        ax6.legend(['Not Ready', 'Production Ready'])
        
        # 7. Complexity vs Quality
        ax7 = fig.add_subplot(gs[1, 2])
        ax7.scatter(df['face_count'], df['overall_score'], alpha=0.6, color='purple')
        ax7.set_title('Mesh Complexity vs Quality')
        ax7.set_xlabel('Face Count')
        ax7.set_ylabel('Overall Score')
        
        # 8. Quality Trends Over Time (if we have modification dates)
        ax8 = fig.add_subplot(gs[1, 3])
        if 'last_modified' in df.columns:
            # Convert to datetime if it's not already
            df['last_modified'] = pd.to_datetime(df['last_modified'])
            daily_quality = df.groupby(df['last_modified'].dt.date)['overall_score'].mean()
            ax8.plot(daily_quality.index, daily_quality.values, marker='o')
            ax8.set_title('Quality Trends Over Time')
            ax8.set_xlabel('Date')
            ax8.set_ylabel('Average Quality Score')
            plt.setp(ax8.xaxis.get_majorticklabels(), rotation=45)
        else:
            ax8.text(0.5, 0.5, 'No time data available', ha='center', va='center', transform=ax8.transAxes)
            ax8.set_title('Quality Trends Over Time')
        
        # 9. Top and Bottom Performers Table
        ax9 = fig.add_subplot(gs[2, :2])
        ax9.axis('off')
        
        # Top 5 performers
        top_models = df.nlargest(5, 'overall_score')[['filename', 'overall_score', 'production_grade', 'production_ready']]
        bottom_models = df.nsmallest(5, 'overall_score')[['filename', 'overall_score', 'production_grade', 'production_ready']]
        
        # Format the tables
        top_text = "🏆 TOP 5 PERFORMERS:\n"
        for _, model in top_models.iterrows():
            status = "✅" if model['production_ready'] else "❌"
            top_text += f"  {status} {model['filename'][:30]}... | Score: {model['overall_score']}/100 | Grade: {model['production_grade']}\n"
        
        bottom_text = "\n⚠️ BOTTOM 5 PERFORMERS:\n"
        for _, model in bottom_models.iterrows():
            status = "✅" if model['production_ready'] else "❌"
            bottom_text += f"  {status} {model['filename'][:30]}... | Score: {model['overall_score']}/100 | Grade: {model['production_grade']}\n"
        
        ax9.text(0.05, 0.95, top_text + bottom_text, transform=ax9.transAxes, 
                fontsize=10, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        
        # 10. Summary Statistics
        ax10 = fig.add_subplot(gs[2, 2:])
        ax10.axis('off')
        
        production_ready_pct = (df['production_ready'].sum() / len(df)) * 100
        watertight_pct = (df['is_watertight'].sum() / len(df)) * 100
        planter_like_pct = (df['is_planter_like'].sum() / len(df)) * 100
        
        stats_text = f"""
📊 QUALITY CONTROL SUMMARY:
   • Total Models: {len(df)}
   • Production Ready: {df['production_ready'].sum()} ({production_ready_pct:.1f}%)
   • Average Quality Score: {df['overall_score'].mean():.1f}/100
   • Watertight Models: {df['is_watertight'].sum()} ({watertight_pct:.1f}%)
   • Planter-like Models: {df['is_planter_like'].sum()} ({planter_like_pct:.1f}%)
   
📈 SCORE BREAKDOWN:
   • Geometry: {df['geometry_score'].mean():.1f}/100 (±{df['geometry_score'].std():.1f})
   • Topology: {df['topology_score'].mean():.1f}/100 (±{df['topology_score'].std():.1f})
   • Printability: {df['printability_score'].mean():.1f}/100 (±{df['printability_score'].std():.1f})
   
🔧 TECHNICAL METRICS:
   • Avg Volume: {df['volume_mm3'].mean():.0f} mm³
   • Avg Face Count: {df['face_count'].mean():.0f}
   • Avg Triangle Quality: {df['triangle_quality'].mean():.2f}
   • Models with Issues: {(df['critical_failures'] > 0).sum()}
   
🎯 RECOMMENDATIONS:
   {"✅ Production pipeline is healthy!" if production_ready_pct >= 80 else "⚠️ Review models with issues"}
   {"✅ Quality standards are being met" if df['overall_score'].mean() >= 75 else "🔧 Quality improvement needed"}
"""
        
        ax10.text(0.05, 0.95, stats_text, transform=ax10.transAxes, 
                 fontsize=11, verticalalignment='top', fontfamily='monospace',
                 bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        # 11. Detailed Metrics Heatmap
        ax11 = fig.add_subplot(gs[3, :])
        
        # Create correlation matrix of key metrics
        metrics_cols = ['overall_score', 'geometry_score', 'topology_score', 'printability_score', 
                       'volume_mm3', 'face_count', 'triangle_quality']
        metrics_df = df[metrics_cols].copy()
        
        # Normalize volume for better correlation visualization
        metrics_df['volume_mm3'] = np.log10(metrics_df['volume_mm3'] + 1)
        metrics_df['face_count'] = np.log10(metrics_df['face_count'] + 1)
        
        correlation_matrix = metrics_df.corr()
        im = ax11.imshow(correlation_matrix, cmap='RdYlBu_r', aspect='auto', vmin=-1, vmax=1)
        
        # Add correlation values
        for i in range(len(correlation_matrix)):
            for j in range(len(correlation_matrix.columns)):
                text = ax11.text(j, i, f'{correlation_matrix.iloc[i, j]:.2f}',
                               ha="center", va="center", color="black", fontweight='bold')
        
        ax11.set_xticks(range(len(correlation_matrix.columns)))
        ax11.set_yticks(range(len(correlation_matrix)))
        ax11.set_xticklabels(correlation_matrix.columns, rotation=45)
        ax11.set_yticklabels(correlation_matrix.index)
        ax11.set_title('Quality Metrics Correlation Matrix', fontweight='bold')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax11)
        cbar.set_label('Correlation')
        
        plt.tight_layout()
        
        # Save dashboard
        dashboard_path = self.models_dir / f"quality_control_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(dashboard_path, dpi=300, bbox_inches='tight')
        print(f"📊 Dashboard saved to: {dashboard_path}")
        
        return dashboard_path
    
    def save_dashboard_data(self, df):
        """Save dashboard data to JSON and CSV"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save detailed CSV
        csv_path = self.models_dir / f"quality_control_data_{timestamp}.csv"
        df.to_csv(csv_path, index=False)
        print(f"📄 Data saved to: {csv_path}")
        
        # Save summary JSON
        json_path = self.models_dir / f"quality_control_summary_{timestamp}.json"
        summary = {
            'dashboard_timestamp': self.dashboard_data['scan_timestamp'].isoformat(),
            'total_models': self.dashboard_data['total_models'],
            'successful_analyses': self.dashboard_data['successful_analyses'],
            'production_ready_count': self.dashboard_data['production_ready_count'],
            'production_ready_percentage': (self.dashboard_data['production_ready_count'] / self.dashboard_data['successful_analyses']) * 100,
            'average_quality_score': float(df['overall_score'].mean()),
            'quality_distribution': df['quality_category'].value_counts().to_dict(),
            'grade_distribution': df['production_grade'].value_counts().to_dict(),
            'top_performers': df.nlargest(10, 'overall_score')[['filename', 'overall_score', 'production_grade']].to_dict('records'),
            'needs_attention': df[df['critical_failures'] > 0][['filename', 'overall_score', 'critical_failures']].to_dict('records')
        }
        
        with open(json_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"📋 Summary saved to: {json_path}")
        
        return csv_path, json_path
    
    def print_executive_summary(self, df):
        """Print executive summary for management"""
        print("\n" + "="*120)
        print("🏭 PETPLANTR QUALITY CONTROL EXECUTIVE SUMMARY")
        print("="*120)
        
        production_ready_pct = (df['production_ready'].sum() / len(df)) * 100
        avg_score = df['overall_score'].mean()
        
        # Overall status
        if production_ready_pct >= 90 and avg_score >= 85:
            status = "🟢 EXCELLENT"
        elif production_ready_pct >= 80 and avg_score >= 75:
            status = "🟡 GOOD"
        elif production_ready_pct >= 70 and avg_score >= 65:
            status = "🟠 ACCEPTABLE"
        else:
            status = "🔴 NEEDS ATTENTION"
        
        print(f"\n📊 OVERALL STATUS: {status}")
        print(f"📈 PRODUCTION READINESS: {df['production_ready'].sum()}/{len(df)} models ({production_ready_pct:.1f}%)")
        print(f"🎯 AVERAGE QUALITY SCORE: {avg_score:.1f}/100")
        
        # Key metrics
        print(f"\n🔧 KEY METRICS:")
        print(f"   • Watertight Models: {(df['is_watertight'].sum() / len(df)) * 100:.1f}%")
        print(f"   • Planter-like Shape: {(df['is_planter_like'].sum() / len(df)) * 100:.1f}%")
        print(f"   • Models with Critical Issues: {(df['critical_failures'] > 0).sum()}")
        print(f"   • Average File Size: {df['file_size_mb'].mean():.2f} MB")
        
        # Recommendations
        print(f"\n💡 EXECUTIVE RECOMMENDATIONS:")
        if production_ready_pct >= 90:
            print("   ✅ Production pipeline is performing excellently")
        elif production_ready_pct >= 80:
            print("   🎯 Production pipeline is performing well with minor improvements needed")
        else:
            print("   🚨 Production pipeline needs immediate attention")
            print("   🔧 Review quality control processes and model generation parameters")
        
        if avg_score < 75:
            print("   📈 Implement quality improvement initiatives")
        
        print("="*120)

def main():
    parser = argparse.ArgumentParser(description='PetPlantr Quality Control Dashboard')
    parser.add_argument('models_directory', help='Directory containing STL models')
    parser.add_argument('--no-display', action='store_true', help='Don\'t display the dashboard plot')
    
    args = parser.parse_args()
    
    if not Path(args.models_directory).exists():
        print(f"❌ Directory not found: {args.models_directory}")
        sys.exit(1)
    
    # Create dashboard
    dashboard = QualityControlDashboard(args.models_directory)
    
    # Scan all models
    df = dashboard.scan_all_models()
    
    if df.empty:
        print("❌ No valid models found for analysis")
        sys.exit(1)
    
    # Create and save dashboard
    dashboard_path = dashboard.create_dashboard(df)
    csv_path, json_path = dashboard.save_dashboard_data(df)
    
    # Print executive summary
    dashboard.print_executive_summary(df)
    
    # Show dashboard if requested
    if not args.no_display:
        plt.show()
    
    print(f"\n🎉 Quality Control Dashboard Complete!")
    print(f"📊 Dashboard: {dashboard_path}")
    print(f"📄 Data: {csv_path}")
    print(f"📋 Summary: {json_path}")

if __name__ == "__main__":
    main()
