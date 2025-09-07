#!/usr/bin/env python3
"""
🎯 PetPlantr 3D Viewer Demo
Interactive 3D visualization of STL models with confidence scoring overlay
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from enhanced_stl_analyzer import analyze_stl_quality
import matplotlib.patches as patches
from matplotlib.widgets import Button

class PetPlantr3DViewer:
    def __init__(self):
        self.fig = None
        self.current_model = None
        self.current_report = None
        
    def visualize_model_with_analysis(self, stl_path):
        """Create comprehensive 3D visualization with analysis overlay"""
        
        if not os.path.exists(stl_path):
            print(f"❌ File not found: {stl_path}")
            return False
            
        print(f"🔍 Loading and analyzing: {os.path.basename(stl_path)}")
        
        # Analyze the model
        quality_report, mesh_obj = analyze_stl_quality(stl_path)
        planter = quality_report['planter_analysis']
        geo = quality_report['geometry']
        mesh_quality = quality_report['mesh_quality']
        
        # Create figure with subplots
        self.fig = plt.figure(figsize=(20, 14))
        self.fig.suptitle(f'🎯 PetPlantr 3D Analysis: {os.path.basename(stl_path)}', 
                         fontsize=16, fontweight='bold')
        
        # Main 3D view (large subplot)
        ax_3d = self.fig.add_subplot(231, projection='3d')
        
        # Get mesh data
        vertices = mesh_obj.vectors.reshape(-1, 3)
        
        # Color mesh based on confidence score
        confidence = planter['planter_confidence']
        if confidence >= 95:
            mesh_color = 'lightgreen'
            edge_color = 'darkgreen'
            confidence_emoji = '🏆'
        elif confidence >= 80:
            mesh_color = 'lightblue'
            edge_color = 'navy'
            confidence_emoji = '🥇'
        elif confidence >= 60:
            mesh_color = 'lightyellow'
            edge_color = 'orange'
            confidence_emoji = '🥈'
        else:
            mesh_color = 'lightcoral'
            edge_color = 'darkred'
            confidence_emoji = '⚠️'
        
        # Add mesh to plot
        collection = Poly3DCollection(mesh_obj.vectors, alpha=0.8, 
                                    facecolor=mesh_color, edgecolor=edge_color, linewidth=0.1)
        ax_3d.add_collection3d(collection)
        
        # Set equal aspect ratio
        max_range = np.array([vertices[:, 0].max() - vertices[:, 0].min(),
                             vertices[:, 1].max() - vertices[:, 1].min(),
                             vertices[:, 2].max() - vertices[:, 2].min()]).max() / 2.0
        mid_x = (vertices[:, 0].max() + vertices[:, 0].min()) * 0.5
        mid_y = (vertices[:, 1].max() + vertices[:, 1].min()) * 0.5
        mid_z = (vertices[:, 2].max() + vertices[:, 2].min()) * 0.5
        
        ax_3d.set_xlim(mid_x - max_range, mid_x + max_range)
        ax_3d.set_ylim(mid_y - max_range, mid_y + max_range)
        ax_3d.set_zlim(mid_z - max_range, mid_z + max_range)
        
        ax_3d.set_title(f'{confidence_emoji} 3D Model View\nConfidence: {confidence:.1f}%', 
                       fontsize=14, fontweight='bold')
        ax_3d.set_xlabel('X (mm)')
        ax_3d.set_ylabel('Y (mm)')
        ax_3d.set_zlabel('Z (mm)')
        
        # Confidence scoring breakdown (pie chart)
        ax_pie = self.fig.add_subplot(232)
        
        # Extract scoring components (estimated breakdown)
        opening_score = 30 if 'excellent_opening' in planter['planter_features'] else \
                       25 if 'good_opening' in planter['planter_features'] else \
                       20 if 'acceptable_opening' in planter['planter_features'] else 10
                       
        taper_score = 25 if 'excellent_taper' in planter['planter_features'] else \
                     20 if 'good_taper' in planter['planter_features'] else \
                     15 if 'acceptable_taper' in planter['planter_features'] else 8
                     
        quality_score = 15 if 'watertight' in planter['planter_features'] else 5
        quality_score += 10 if 'large_volume' in planter['planter_features'] else \
                        8 if 'adequate_volume' in planter['planter_features'] else 5
                        
        bonus_score = max(0, confidence - opening_score - taper_score - quality_score)
        
        scores = [opening_score, taper_score, quality_score, bonus_score]
        labels = ['Opening\nAnalysis', 'Taper\nAnalysis', 'Quality\nChecks', 'Bonus\nFeatures']
        colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
        
        wedges, texts, autotexts = ax_pie.pie(scores, labels=labels, colors=colors, autopct='%1.0f%%',
                                             startangle=90)
        ax_pie.set_title(f'Confidence Breakdown\nTotal: {confidence:.1f}%', fontweight='bold')
        
        # Cross-sectional analysis
        ax_cross = self.fig.add_subplot(233)
        
        # Show height vs cross-sectional area
        y_coords = vertices[:, 1]
        z_coords = vertices[:, 2]
        
        # Create scatter plot colored by height
        scatter = ax_cross.scatter(z_coords, y_coords, c=y_coords, cmap='viridis', alpha=0.6, s=2)
        ax_cross.set_xlabel('Depth (mm)')
        ax_cross.set_ylabel('Height (mm)')
        ax_cross.set_title('Cross-Sectional View\n(Color = Height)', fontweight='bold')
        ax_cross.grid(True, alpha=0.3)
        
        # Add colorbar
        cbar = plt.colorbar(scatter, ax=ax_cross, shrink=0.8)
        cbar.set_label('Height (mm)')
        
        # Planter metrics display
        ax_metrics = self.fig.add_subplot(234)
        ax_metrics.axis('off')
        
        metrics_text = f"""
🪴 PLANTER ANALYSIS RESULTS

🎯 Classification: {'✅ PLANTER-LIKE' if planter['is_planter_like'] else '❌ NOT PLANTER-LIKE'}
🏷️ Type: {planter['planter_type'].replace('_', ' ').title()}
📊 Confidence: {confidence:.1f}%

📏 GEOMETRIC PROPERTIES:
• Dimensions: {geo['dimensions_mm']['width']:.0f}×{geo['dimensions_mm']['height']:.0f}×{geo['dimensions_mm']['depth']:.0f} mm
• Volume: {geo['volume_mm3']:.0f} mm³
• Surface Area: {geo['surface_area_mm2']:.0f} mm²

🔍 SHAPE ANALYSIS:
• Opening Ratio: {planter['opening_ratio']:.3f}
• Taper Factor: {planter['taper_ratio']:.3f}
• Cross-sections: {planter['cross_section_count']}
• Shape Stability: {planter['shape_stability']:.3f}

⭐ QUALITY SCORES:
• Overall: {quality_report['quality_scores']['overall']}/100
• Geometry: {quality_report['quality_scores']['geometry']}/100
• Topology: {quality_report['quality_scores']['topology']}/100
• Printability: {quality_report['quality_scores']['printability']}/100

🔧 MESH QUALITY:
• Faces: {mesh_quality['face_count']:,}
• Vertices: {mesh_quality['vertex_count']:,}
• Watertight: {'✅' if mesh_quality['is_watertight'] else '❌'}
"""
        
        ax_metrics.text(0.05, 0.95, metrics_text, transform=ax_metrics.transAxes, 
                       fontsize=10, verticalalignment='top', fontfamily='monospace',
                       bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.8))
        
        # Feature detection visualization
        ax_features = self.fig.add_subplot(235)
        
        features = planter.get('planter_features', [])
        feature_categories = {
            'Opening': [f for f in features if 'opening' in f],
            'Taper': [f for f in features if 'taper' in f],
            'Quality': [f for f in features if any(x in f for x in ['watertight', 'volume', 'proportions'])],
            'Shape': [f for f in features if any(x in f for x in ['shape', 'detail', 'stability'])],
            'Bonus': [f for f in features if any(x in f for x in ['multi', 'functional', 'consistent', 'certified'])]
        }
        
        y_pos = np.arange(len(feature_categories))
        counts = [len(cat_features) for cat_features in feature_categories.values()]
        colors_bar = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc']
        
        bars = ax_features.barh(y_pos, counts, color=colors_bar)
        ax_features.set_yticks(y_pos)
        ax_features.set_yticklabels(feature_categories.keys())
        ax_features.set_xlabel('Features Detected')
        ax_features.set_title(f'Feature Detection\nTotal: {len(features)} features', fontweight='bold')
        
        # Add count labels on bars
        for i, (bar, count) in enumerate(zip(bars, counts)):
            if count > 0:
                ax_features.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                               str(count), va='center', fontweight='bold')
        
        # Production readiness indicator
        ax_ready = self.fig.add_subplot(236)
        ax_ready.axis('off')
        
        # Determine production readiness
        if confidence >= 95 and planter['is_planter_like']:
            readiness = "🎉 PRODUCTION READY!"
            readiness_color = 'lightgreen'
            status_text = "✅ Excellent planter characteristics\n✅ High confidence score\n✅ Ready for 3D printing"
        elif confidence >= 80 and planter['is_planter_like']:
            readiness = "🥇 VERY GOOD"
            readiness_color = 'lightblue'
            status_text = "✅ Good planter characteristics\n✅ High confidence score\n⚡ Minor optimizations possible"
        elif confidence >= 60 and planter['is_planter_like']:
            readiness = "🥈 ACCEPTABLE"
            readiness_color = 'lightyellow'
            status_text = "✅ Basic planter characteristics\n⚠️ Could benefit from optimization\n🔧 Review recommended"
        else:
            readiness = "⚠️ NEEDS WORK"
            readiness_color = 'lightcoral'
            status_text = "❌ Limited planter characteristics\n🔧 Requires shape optimization\n🚫 Not recommended for production"
        
        # Create production readiness display
        rect = patches.Rectangle((0.1, 0.3), 0.8, 0.4, linewidth=2, 
                                edgecolor='black', facecolor=readiness_color, alpha=0.7)
        ax_ready.add_patch(rect)
        
        ax_ready.text(0.5, 0.5, readiness, ha='center', va='center', 
                     fontsize=14, fontweight='bold', transform=ax_ready.transAxes)
        
        ax_ready.text(0.5, 0.15, status_text, ha='center', va='center', 
                     fontsize=10, transform=ax_ready.transAxes)
        
        ax_ready.set_xlim(0, 1)
        ax_ready.set_ylim(0, 1)
        ax_ready.set_title('Production Status', fontweight='bold')
        
        plt.tight_layout()
        
        # Store current data
        self.current_model = stl_path
        self.current_report = quality_report
        
        return True
    
    def show_viewer(self, stl_path):
        """Show the 3D viewer for a specific model"""
        success = self.visualize_model_with_analysis(stl_path)
        
        if success:
            print(f"\n🎯 3D Viewer opened for: {os.path.basename(stl_path)}")
            print("📊 Analysis complete - viewing comprehensive results...")
            print("💡 Close the window to continue or try another model")
            
            plt.show()
            return True
        else:
            return False

def run_3d_viewer_demo():
    """Run interactive 3D viewer demo"""
    
    print("\n" + "="*80)
    print("🎯 PETPLANTR 3D VIEWER DEMO")
    print("="*80)
    print("🖼️ Interactive 3D visualization with confidence scoring overlay")
    print("📊 Comprehensive analysis results displayed in real-time")
    print("="*80)
    
    # Find available models
    sample_models = [
        ('./test_100_percent/case_01_golden_retriever_standard/planter_golden_retriever_1751159518_FINAL.stl', 
         'Golden Retriever (Optimized) - 100% Confidence'),
        ('./test_100_percent/case_02_german_shepherd_large/planter_german_shepherd_1751159526_FINAL.stl',
         'German Shepherd (Optimized) - 100% Confidence'),
        ('./demo_edge_cases/item_001/planter_chihuahua_1751156468_FINAL.stl',
         'Chihuahua (Real Model) - 100% Confidence'),
        ('./demo_batch_planters/item_001/planter_golden_retriever_1751156400_FINAL.stl',
         'Golden Retriever (Batch) - 100% Confidence'),
    ]
    
    available_models = []
    for model_path, description in sample_models:
        if os.path.exists(model_path):
            available_models.append((model_path, description))
    
    if not available_models:
        print("❌ No sample models found for 3D viewing")
        return False
    
    print(f"\n📁 Found {len(available_models)} models for 3D viewing:")
    for i, (path, desc) in enumerate(available_models, 1):
        print(f"   {i}. {desc}")
    
    # Create viewer
    viewer = PetPlantr3DViewer()
    
    # Show models one by one
    for i, (model_path, description) in enumerate(available_models):
        print(f"\n[{i+1}/{len(available_models)}] 🎯 Displaying: {description}")
        print("="*60)
        
        success = viewer.show_viewer(model_path)
        
        if success:
            print(f"✅ Successfully displayed {os.path.basename(model_path)}")
        else:
            print(f"❌ Failed to display {os.path.basename(model_path)}")
        
        if i < len(available_models) - 1:
            input("\n🎯 Press Enter to view next model...")
    
    print("\n" + "="*80)
    print("🎉 3D VIEWER DEMO COMPLETED!")
    print("✅ All models visualized with confidence scoring overlay")
    print("📊 Comprehensive analysis results displayed")
    print("🏆 Production-ready planter classification demonstrated")
    print("="*80)
    
    return True

if __name__ == "__main__":
    try:
        success = run_3d_viewer_demo()
        if success:
            print(f"\n✨ 3D viewer demo completed successfully!")
        else:
            print(f"\n❌ Demo failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Demo interrupted by user.")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
