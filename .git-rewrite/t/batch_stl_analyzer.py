#!/usr/bin/env python3
"""
Batch STL Quality Analyzer for PetPlantr Pipeline
Analyzes multiple STL files and creates comprehensive reports
"""
import sys
import json
import glob
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from enhanced_stl_analyzer import analyze_stl_quality, convert_to_json_safe
import numpy as np

def analyze_batch_stls(directory_path, pattern="*.stl"):
    """
    Analyze all STL files matching pattern in directory
    """
    print(f"🔍 Scanning for STL files in: {directory_path}")
    print(f"   Pattern: {pattern}")
    
    # Find all STL files
    search_path = Path(directory_path) / pattern
    stl_files = glob.glob(str(search_path), recursive=True)
    
    if not stl_files:
        print(f"❌ No STL files found matching {pattern} in {directory_path}")
        return None
    
    print(f"📁 Found {len(stl_files)} STL files to analyze")
    
    # Analyze each file
    results = []
    for i, stl_file in enumerate(stl_files, 1):
        print(f"\n🔍 Analyzing {i}/{len(stl_files)}: {Path(stl_file).name}")
        
        try:
            quality_report, _ = analyze_stl_quality(stl_file)
            quality_report['filename'] = Path(stl_file).name
            quality_report['file_size_mb'] = Path(stl_file).stat().st_size / (1024*1024)
            quality_report['analysis_timestamp'] = datetime.now().isoformat()
            results.append(quality_report)
            
            # Quick summary
            overall_score = quality_report["quality_scores"]["overall"]
            print(f"   ✅ Complete - Overall Score: {overall_score}/100")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            # Add error entry
            results.append({
                'filename': Path(stl_file).name,
                'error': str(e),
                'analysis_timestamp': datetime.now().isoformat()
            })
    
    return results

def create_summary_report(results, output_dir):
    """
    Create comprehensive summary report with visualizations
    """
    print(f"\n📊 Creating summary report...")
    
    # Filter successful analyses
    successful_results = [r for r in results if 'error' not in r]
    failed_results = [r for r in results if 'error' in r]
    
    print(f"   ✅ Successful analyses: {len(successful_results)}")
    print(f"   ❌ Failed analyses: {len(failed_results)}")
    
    if not successful_results:
        print("❌ No successful analyses to report")
        return
    
    # Create dataframe for analysis
    data = []
    for result in successful_results:
        row = {
            'filename': result['filename'],
            'overall_score': result['quality_scores']['overall'],
            'geometry_score': result['quality_scores']['geometry'],
            'topology_score': result['quality_scores']['topology'],
            'printability_score': result['quality_scores']['printability'],
            'volume_mm3': result['geometry']['volume_mm3'],
            'surface_area_mm2': result['geometry']['surface_area_mm2'],
            'width_mm': result['geometry']['dimensions_mm']['width'],
            'height_mm': result['geometry']['dimensions_mm']['height'],
            'depth_mm': result['geometry']['dimensions_mm']['depth'],
            'face_count': result['mesh_quality']['face_count'],
            'vertex_count': result['mesh_quality']['vertex_count'],
            'is_watertight': result['mesh_quality']['is_watertight'] == 'True' or result['mesh_quality']['is_watertight'] == True,
            'triangle_quality': result['mesh_quality']['avg_triangle_quality'],
            'is_planter_like': result['planter_analysis']['is_planter_like'],
            'planter_ratio': result['planter_analysis']['planter_ratio'],
            'file_size_mb': result.get('file_size_mb', 0)
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    
    # Generate summary statistics
    summary_stats = {
        'total_files_analyzed': len(results),
        'successful_analyses': len(successful_results),
        'failed_analyses': len(failed_results),
        'average_overall_score': float(df['overall_score'].mean()),
        'average_geometry_score': float(df['geometry_score'].mean()),
        'average_topology_score': float(df['topology_score'].mean()),
        'average_printability_score': float(df['printability_score'].mean()),
        'watertight_percentage': float(df['is_watertight'].mean() * 100),
        'planter_like_percentage': float(df['is_planter_like'].mean() * 100),
        'average_volume_mm3': float(df['volume_mm3'].mean()),
        'average_face_count': float(df['face_count'].mean()),
        'score_distribution': {
            'excellent_90_plus': int((df['overall_score'] >= 90).sum()),
            'very_good_80_89': int(((df['overall_score'] >= 80) & (df['overall_score'] < 90)).sum()),
            'good_70_79': int(((df['overall_score'] >= 70) & (df['overall_score'] < 80)).sum()),
            'acceptable_60_69': int(((df['overall_score'] >= 60) & (df['overall_score'] < 70)).sum()),
            'needs_improvement_below_60': int((df['overall_score'] < 60).sum())
        }
    }
    
    # Create visualizations
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    fig.suptitle('PetPlantr STL Quality Batch Analysis Report', fontsize=16, fontweight='bold')
    
    # Overall score distribution
    axes[0,0].hist(df['overall_score'], bins=20, color='skyblue', alpha=0.7, edgecolor='black')
    axes[0,0].set_title('Overall Quality Score Distribution')
    axes[0,0].set_xlabel('Score')
    axes[0,0].set_ylabel('Count')
    axes[0,0].axvline(df['overall_score'].mean(), color='red', linestyle='--', 
                     label=f'Mean: {df["overall_score"].mean():.1f}')
    axes[0,0].legend()
    
    # Score breakdown by category
    score_cols = ['geometry_score', 'topology_score', 'printability_score']
    score_means = [df[col].mean() for col in score_cols]
    score_labels = ['Geometry', 'Topology', 'Printability']
    bars = axes[0,1].bar(score_labels, score_means, color=['lightgreen', 'lightcoral', 'lightsalmon'])
    axes[0,1].set_title('Average Scores by Category')
    axes[0,1].set_ylabel('Score')
    axes[0,1].set_ylim(0, 100)
    for bar, val in zip(bars, score_means):
        axes[0,1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                      f'{val:.1f}', ha='center', va='bottom', fontweight='bold')
    
    # Volume vs Quality scatter
    axes[0,2].scatter(df['volume_mm3'], df['overall_score'], alpha=0.6, color='purple')
    axes[0,2].set_title('Volume vs Overall Quality')
    axes[0,2].set_xlabel('Volume (mm³)')
    axes[0,2].set_ylabel('Overall Score')
    
    # Face count distribution
    axes[1,0].hist(df['face_count'], bins=20, color='orange', alpha=0.7, edgecolor='black')
    axes[1,0].set_title('Face Count Distribution')
    axes[1,0].set_xlabel('Face Count')
    axes[1,0].set_ylabel('Count')
    
    # Quality vs Triangle Quality
    axes[1,1].scatter(df['triangle_quality'], df['topology_score'], alpha=0.6, color='green')
    axes[1,1].set_title('Triangle Quality vs Topology Score')
    axes[1,1].set_xlabel('Triangle Quality (lower is better)')
    axes[1,1].set_ylabel('Topology Score')
    
    # Pass/Fail pie chart
    quality_categories = ['Excellent (90+)', 'Very Good (80-89)', 'Good (70-79)', 
                         'Acceptable (60-69)', 'Needs Work (<60)']
    quality_counts = [
        summary_stats['score_distribution']['excellent_90_plus'],
        summary_stats['score_distribution']['very_good_80_89'],
        summary_stats['score_distribution']['good_70_79'],
        summary_stats['score_distribution']['acceptable_60_69'],
        summary_stats['score_distribution']['needs_improvement_below_60']
    ]
    colors = ['gold', 'lightgreen', 'lightyellow', 'orange', 'lightcoral']
    axes[1,2].pie(quality_counts, labels=quality_categories, colors=colors, autopct='%1.1f%%')
    axes[1,2].set_title('Quality Distribution')
    
    plt.tight_layout()
    
    # Save plots
    plot_path = Path(output_dir) / f"batch_analysis_plots_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"📊 Plots saved to: {plot_path}")
    
    # Save detailed CSV
    csv_path = Path(output_dir) / f"batch_analysis_detailed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(csv_path, index=False)
    print(f"📄 Detailed CSV saved to: {csv_path}")
    
    # Save summary JSON
    summary_path = Path(output_dir) / f"batch_analysis_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Convert to JSON-safe format
    json_safe_summary = convert_to_json_safe(summary_stats)
    
    with open(summary_path, 'w') as f:
        json.dump({
            'summary_statistics': json_safe_summary,
            'detailed_results': [convert_to_json_safe(r) for r in successful_results],
            'failed_analyses': failed_results,
            'top_performers': df.nlargest(5, 'overall_score')[['filename', 'overall_score']].to_dict('records'),
            'needs_improvement': df.nsmallest(5, 'overall_score')[['filename', 'overall_score']].to_dict('records')
        }, f, indent=2)
    
    print(f"📋 Summary JSON saved to: {summary_path}")
    
    return summary_stats, df

def print_batch_summary(summary_stats):
    """
    Print a comprehensive batch analysis summary
    """
    print("\n" + "="*100)
    print("🏆 PETPLANTR BATCH STL QUALITY ANALYSIS SUMMARY")
    print("="*100)
    
    print(f"\n📊 ANALYSIS OVERVIEW:")
    print(f"   • Total Files Analyzed: {summary_stats['total_files_analyzed']}")
    print(f"   • Successful Analyses: {summary_stats['successful_analyses']}")
    print(f"   • Failed Analyses: {summary_stats['failed_analyses']}")
    print(f"   • Success Rate: {(summary_stats['successful_analyses']/summary_stats['total_files_analyzed']*100):.1f}%")
    
    print(f"\n📈 QUALITY METRICS:")
    print(f"   • Average Overall Score: {summary_stats['average_overall_score']:.1f}/100")
    print(f"   • Average Geometry Score: {summary_stats['average_geometry_score']:.1f}/100")
    print(f"   • Average Topology Score: {summary_stats['average_topology_score']:.1f}/100")
    print(f"   • Average Printability Score: {summary_stats['average_printability_score']:.1f}/100")
    
    print(f"\n🔧 TECHNICAL METRICS:")
    print(f"   • Watertight Models: {summary_stats['watertight_percentage']:.1f}%")
    print(f"   • Planter-like Models: {summary_stats['planter_like_percentage']:.1f}%")
    print(f"   • Average Volume: {summary_stats['average_volume_mm3']:.0f} mm³")
    print(f"   • Average Face Count: {summary_stats['average_face_count']:.0f}")
    
    print(f"\n🏅 QUALITY DISTRIBUTION:")
    dist = summary_stats['score_distribution']
    total = sum(dist.values())
    print(f"   • Excellent (90+): {dist['excellent_90_plus']} ({dist['excellent_90_plus']/total*100:.1f}%)")
    print(f"   • Very Good (80-89): {dist['very_good_80_89']} ({dist['very_good_80_89']/total*100:.1f}%)")
    print(f"   • Good (70-79): {dist['good_70_79']} ({dist['good_70_79']/total*100:.1f}%)")
    print(f"   • Acceptable (60-69): {dist['acceptable_60_69']} ({dist['acceptable_60_69']/total*100:.1f}%)")
    print(f"   • Needs Improvement (<60): {dist['needs_improvement_below_60']} ({dist['needs_improvement_below_60']/total*100:.1f}%)")
    
    # Quality assessment
    if summary_stats['average_overall_score'] >= 85:
        quality_assessment = "🏆 EXCELLENT"
    elif summary_stats['average_overall_score'] >= 75:
        quality_assessment = "🥇 VERY GOOD"
    elif summary_stats['average_overall_score'] >= 65:
        quality_assessment = "🥈 GOOD"
    else:
        quality_assessment = "🥉 NEEDS IMPROVEMENT"
    
    print(f"\n🎯 OVERALL BATCH QUALITY: {quality_assessment}")
    print("="*100)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python batch_stl_analyzer.py <directory_path> [pattern]")
        print("Example: python batch_stl_analyzer.py ./generated_models")
        print("Example: python batch_stl_analyzer.py ./generated_models '**/*.stl'")
        sys.exit(1)
    
    directory_path = sys.argv[1]
    pattern = sys.argv[2] if len(sys.argv) > 2 else "*.stl"
    
    if not Path(directory_path).exists():
        print(f"❌ Directory not found: {directory_path}")
        sys.exit(1)
    
    try:
        # Analyze batch
        results = analyze_batch_stls(directory_path, pattern)
        
        if results:
            # Create reports
            summary_stats, df = create_summary_report(results, directory_path)
            
            # Print summary
            print_batch_summary(summary_stats)
            
            # Show plot
            plt.show()
        
    except Exception as e:
        print(f"❌ Error during batch analysis: {e}")
        sys.exit(1)
