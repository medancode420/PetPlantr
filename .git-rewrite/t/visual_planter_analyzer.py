#!/usr/bin/env python3
"""
Visual Planter Shape Analysis for PetPlantr Pipeline
Creates visual comparisons and improvement suggestions
"""
import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from enhanced_stl_analyzer import analyze_stl_quality
from planter_shape_optimizer import PlanterShapeOptimizer
import json

class VisualPlanterAnalyzer:
    """
    Visual analysis and comparison tool for planter shapes
    """
    
    def __init__(self):
        self.optimizer = PlanterShapeOptimizer()
    
    def create_planter_analysis_dashboard(self, stl_file_path, save_path=None):
        """
        Create comprehensive visual analysis dashboard
        """
        print(f"📊 Creating visual planter analysis for: {Path(stl_file_path).name}")
        
        # Get analysis data
        quality_report, mesh_obj = analyze_stl_quality(stl_file_path)
        optimization_results = self.optimizer.analyze_planter_deficiencies(stl_file_path)
        
        # Create dashboard
        fig = plt.figure(figsize=(20, 16))
        fig.suptitle(f'Planter Shape Analysis: {Path(stl_file_path).stem}', fontsize=16, fontweight='bold')
        
        # 1. Cross-section analysis
        ax1 = fig.add_subplot(2, 4, 1)
        self._plot_cross_sections(quality_report, ax1)
        
        # 2. Planter score radar
        ax2 = fig.add_subplot(2, 4, 2, projection='polar')
        self._plot_planter_score_radar(quality_report, optimization_results, ax2)
        
        # 3. Shape stability analysis
        ax3 = fig.add_subplot(2, 4, 3)
        self._plot_shape_stability(quality_report, ax3)
        
        # 4. Dimensional analysis
        ax4 = fig.add_subplot(2, 4, 4)
        self._plot_dimensional_analysis(quality_report, ax4)
        
        # 5. Optimization potential
        ax5 = fig.add_subplot(2, 4, 5)
        self._plot_optimization_potential(optimization_results, ax5)
        
        # 6. Planter characteristics comparison
        ax6 = fig.add_subplot(2, 4, 6)
        self._plot_characteristic_comparison(quality_report, ax6)
        
        # 7. Volume distribution
        ax7 = fig.add_subplot(2, 4, 7)
        self._plot_volume_distribution(quality_report, ax7)
        
        # 8. Recommendations summary
        ax8 = fig.add_subplot(2, 4, 8)
        self._plot_recommendations_summary(optimization_results, ax8)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 Visual analysis saved to: {save_path}")
        
        return fig
    
    def _plot_cross_sections(self, quality_report, ax):
        """Plot cross-sectional area analysis"""
        planter = quality_report['planter_analysis']
        
        # Simulate cross-sections based on available data
        heights = np.linspace(0, 100, 20)
        
        # Create idealized cross-section areas based on planter metrics
        top_area = planter['top_cross_section']
        middle_area = planter['middle_cross_section'] if planter['middle_cross_section'] > 0 else top_area * 0.8
        bottom_area = planter['bottom_cross_section']
        
        # Interpolate areas
        areas = []
        for h in heights:
            if h < 33:  # Bottom third
                area = bottom_area + (middle_area - bottom_area) * (h / 33)
            elif h < 67:  # Middle third
                area = middle_area + (top_area - middle_area) * ((h - 33) / 34)
            else:  # Top third
                area = top_area
            areas.append(area)
        
        ax.plot(heights, areas, 'b-', linewidth=2, label='Current Shape')
        
        # Plot ideal planter shape
        ideal_bottom = bottom_area
        ideal_top = ideal_bottom * 1.2  # Ideal 20% wider at top
        ideal_areas = [ideal_bottom + (ideal_top - ideal_bottom) * (h / 100) for h in heights]
        ax.plot(heights, ideal_areas, 'g--', linewidth=2, label='Ideal Planter Shape')
        
        ax.set_xlabel('Height (%)')
        ax.set_ylabel('Cross-sectional Area (mm²)')
        ax.set_title('Cross-Section Analysis')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_planter_score_radar(self, quality_report, optimization_results, ax):
        """Plot planter characteristics radar chart"""
        planter = quality_report['planter_analysis']
        
        # Normalize metrics to 0-100 scale
        metrics = {
            'Opening\nRatio': min(100, max(0, (planter['opening_ratio'] - 0.5) * 100)),
            'Shape\nStability': planter['shape_stability'] * 100,
            'Taper\nRatio': min(100, planter['taper_ratio'] * 100 / 0.6),  # Normalize to ideal 0.6
            'Volume\nConsistency': max(0, 100 - planter['volume_distribution'] * 50),
            'Overall\nScore': planter['planter_confidence']
        }
        
        categories = list(metrics.keys())
        values = list(metrics.values())
        
        # Number of variables
        N = len(categories)
        
        # Compute angle for each axis
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]  # Complete the circle
        
        # Add values to complete the circle
        values += values[:1]
        
        # Plot
        ax.plot(angles, values, 'o-', linewidth=2, label='Current', color='red')
        ax.fill(angles, values, alpha=0.25, color='red')
        
        # Add ideal values
        ideal_values = [80, 80, 80, 80, 80] + [80]  # Ideal scores
        ax.plot(angles, ideal_values, 'o-', linewidth=2, label='Target', color='green')
        ax.fill(angles, ideal_values, alpha=0.1, color='green')
        
        # Customize
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        ax.set_ylim(0, 100)
        ax.set_title('Planter Characteristics Radar')
        ax.legend()
    
    def _plot_shape_stability(self, quality_report, ax):
        """Plot shape stability and transition analysis"""
        planter = quality_report['planter_analysis']
        stability = planter['shape_stability']
        
        # Create stability visualization
        heights = np.linspace(0, 100, 20)
        
        # Simulate shape transitions (smoother = more stable)
        if stability > 0.7:
            noise_factor = 0.1
            color = 'green'
            title_suffix = 'Smooth'
        elif stability > 0.4:
            noise_factor = 0.3
            color = 'orange'
            title_suffix = 'Moderate'
        else:
            noise_factor = 0.6
            color = 'red'
            title_suffix = 'Erratic'
        
        # Add noise to simulate instability
        areas = 100 + 20 * np.sin(heights * 0.3) + noise_factor * 30 * (np.random.rand(len(heights)) - 0.5)
        
        ax.plot(heights, areas, color=color, linewidth=2, label=f'{title_suffix} (Score: {stability:.2f})')
        ax.fill_between(heights, areas, alpha=0.3, color=color)
        
        # Show ideal smooth curve
        ideal_areas = 100 + 20 * np.sin(heights * 0.3)
        ax.plot(heights, ideal_areas, 'g--', linewidth=1, label='Ideal Smooth')
        
        ax.set_xlabel('Height (%)')
        ax.set_ylabel('Relative Area')
        ax.set_title(f'Shape Stability: {title_suffix}')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_dimensional_analysis(self, quality_report, ax):
        """Plot dimensional proportion analysis"""
        dims = quality_report['geometry']['dimensions_mm']
        
        # Create proportion visualization
        dim_names = ['Width', 'Height', 'Depth']
        dim_values = [dims['width'], dims['height'], dims['depth']]
        
        # Normalize to percentage of largest dimension
        max_dim = max(dim_values)
        norm_values = [v/max_dim * 100 for v in dim_values]
        
        bars = ax.bar(dim_names, norm_values, color=['skyblue', 'lightcoral', 'lightgreen'])
        
        # Add ideal proportions for comparison
        ideal_proportions = [80, 100, 80]  # Slightly wider than tall for stability
        ax.bar(dim_names, ideal_proportions, alpha=0.3, color='gray', label='Ideal Proportions')
        
        # Add values on bars
        for bar, val, ideal in zip(bars, norm_values, ideal_proportions):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                   f'{val:.0f}%', ha='center', va='bottom', fontweight='bold')
            
            # Show difference from ideal
            diff = val - ideal
            color = 'green' if abs(diff) < 10 else 'orange' if abs(diff) < 20 else 'red'
            ax.text(bar.get_x() + bar.get_width()/2, ideal + (5 if diff > 0 else -10),
                   f'{diff:+.0f}%', ha='center', va='center', color=color, fontsize=8)
        
        ax.set_ylabel('Normalized Size (%)')
        ax.set_title('Dimensional Proportions')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_optimization_potential(self, optimization_results, ax):
        """Plot optimization potential analysis"""
        current = optimization_results['current_planter_score']
        potential = optimization_results['potential_planter_score']
        improvement = potential - current
        
        categories = ['Current\nScore', 'Potential\nScore']
        scores = [current, potential]
        colors = ['red' if current < 50 else 'orange' if current < 70 else 'green',
                 'lightgreen']
        
        bars = ax.bar(categories, scores, color=colors)
        
        # Add improvement arrow
        if improvement > 0:
            ax.annotate('', xy=(1, potential), xytext=(0, current),
                       arrowprops=dict(arrowstyle='->', lw=3, color='blue'))
            ax.text(0.5, (current + potential) / 2, f'+{improvement:.0f}',
                   ha='center', va='center', fontsize=12, fontweight='bold', color='blue')
        
        # Add score labels
        for bar, score in zip(bars, scores):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                   f'{score:.0f}/100', ha='center', va='bottom', fontweight='bold')
        
        ax.set_ylim(0, 105)
        ax.set_ylabel('Planter Score')
        ax.set_title('Optimization Potential')
        ax.grid(True, alpha=0.3)
    
    def _plot_characteristic_comparison(self, quality_report, ax):
        """Plot planter characteristics comparison with ideals"""
        planter = quality_report['planter_analysis']
        
        characteristics = {
            'Opening\nRatio': {'current': planter['opening_ratio'], 'ideal': 1.2, 'range': (0.9, 1.8)},
            'Planter\nRatio': {'current': planter['planter_ratio'], 'ideal': 1.1, 'range': (0.8, 1.8)},
            'Taper\nRatio': {'current': planter['taper_ratio'], 'ideal': 0.6, 'range': (0.3, 0.9)},
        }
        
        x_pos = np.arange(len(characteristics))
        char_names = list(characteristics.keys())
        
        for i, (name, data) in enumerate(characteristics.items()):
            current = data['current']
            ideal = data['ideal']
            min_val, max_val = data['range']
            
            # Plot range
            ax.plot([i, i], [min_val, max_val], 'k-', linewidth=6, alpha=0.3, label='Acceptable Range' if i == 0 else "")
            
            # Plot ideal
            ax.plot(i, ideal, 'go', markersize=10, label='Ideal' if i == 0 else "")
            
            # Plot current
            color = 'green' if min_val <= current <= max_val else 'red'
            ax.plot(i, current, 'o', color=color, markersize=8, label='Current' if i == 0 else "")
            
            # Add values
            ax.text(i, current + 0.1, f'{current:.2f}', ha='center', va='bottom', fontweight='bold')
        
        ax.set_xticks(x_pos)
        ax.set_xticklabels(char_names)
        ax.set_ylabel('Ratio Value')
        ax.set_title('Characteristic Comparison')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_volume_distribution(self, quality_report, ax):
        """Plot volume distribution analysis"""
        planter = quality_report['planter_analysis']
        vol_dist = planter['volume_distribution']
        
        # Create volume distribution visualization
        heights = np.linspace(0, 100, 10)
        
        # Simulate volume distribution based on analysis
        if vol_dist < 0.5:  # Consistent
            volumes = np.ones_like(heights) * 100 + np.random.normal(0, 5, len(heights))
            color = 'green'
            title_suffix = 'Consistent'
        elif vol_dist < 1.0:  # Moderate
            volumes = 100 + 20 * np.sin(heights * 0.1) + np.random.normal(0, 15, len(heights))
            color = 'orange'
            title_suffix = 'Moderate'
        else:  # Inconsistent
            volumes = 100 + 40 * np.sin(heights * 0.2) + np.random.normal(0, 25, len(heights))
            color = 'red'
            title_suffix = 'Inconsistent'
        
        ax.bar(heights, volumes, width=8, color=color, alpha=0.7, label=f'{title_suffix} (σ={vol_dist:.2f})')
        
        # Show ideal consistent distribution
        ideal_volumes = np.ones_like(heights) * 100
        ax.plot(heights, ideal_volumes, 'g--', linewidth=2, label='Ideal Consistent')
        
        ax.set_xlabel('Height (%)')
        ax.set_ylabel('Relative Volume')
        ax.set_title(f'Volume Distribution: {title_suffix}')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_recommendations_summary(self, optimization_results, ax):
        """Plot recommendations summary"""
        priority = optimization_results['optimization_priority']
        
        # Count recommendations by priority
        high_count = len(priority['immediate_fixes'])
        medium_count = len(priority['important_improvements'])
        low_count = len(priority['nice_to_have'])
        
        # Create stacked bar chart
        categories = ['Recommendations']
        high_vals = [high_count]
        medium_vals = [medium_count]
        low_vals = [low_count]
        
        p1 = ax.bar(categories, high_vals, color='red', label=f'High Priority ({high_count})')
        p2 = ax.bar(categories, medium_vals, bottom=high_vals, color='orange', label=f'Medium Priority ({medium_count})')
        p3 = ax.bar(categories, low_vals, bottom=[h+m for h,m in zip(high_vals, medium_vals)], 
                   color='lightgreen', label=f'Low Priority ({low_count})')
        
        # Add total expected improvement
        total_improvement = optimization_results['estimated_improvement_potential']
        ax.text(0, (high_count + medium_count + low_count) + 0.5, f'Total Potential: +{total_improvement:.0f} pts',
               ha='center', va='bottom', fontweight='bold', fontsize=12)
        
        ax.set_ylabel('Number of Recommendations')
        ax.set_title('Optimization Recommendations')
        ax.legend()
        
        # Remove x-axis ticks
        ax.set_xticks([])

def main():
    if len(sys.argv) != 2:
        print("Usage: python visual_planter_analyzer.py <stl_file>")
        print("Example: python visual_planter_analyzer.py model.stl")
        sys.exit(1)
    
    stl_file = sys.argv[1]
    
    if not Path(stl_file).exists():
        print(f"❌ File not found: {stl_file}")
        sys.exit(1)
    
    # Create visual analyzer
    analyzer = VisualPlanterAnalyzer()
    
    try:
        # Create visual analysis dashboard
        save_path = Path(stl_file).parent / f"{Path(stl_file).stem}_visual_planter_analysis.png"
        fig = analyzer.create_planter_analysis_dashboard(stl_file, str(save_path))
        
        # Show the plot
        plt.show()
        
    except Exception as e:
        print(f"❌ Error during visual analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
