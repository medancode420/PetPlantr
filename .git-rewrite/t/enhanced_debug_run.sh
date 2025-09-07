#!/usr/bin/env bash
# Enhanced debug script for testing multi-view planter generation

# Get UUID either from --uid flag or timestamp
UUID=""
INPUT_IMAGE=""
EXTRA_ARGS=""
USE_MULTIVIEW=false

echo "🚀 PetPlantr Enhanced Debug Tool"
echo "================================"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --uid)
            UUID="$2"
            shift 2
            ;;
        --multi-view)
            USE_MULTIVIEW=true
            EXTRA_ARGS="$EXTRA_ARGS --multi-view"
            shift
            ;;
        --save-intermediates|--verbose)
            EXTRA_ARGS="$EXTRA_ARGS $1"
            shift
            ;;
        *)
            if [[ -z "$INPUT_IMAGE" ]]; then
                INPUT_IMAGE="$1"
            else
                EXTRA_ARGS="$EXTRA_ARGS $1"
            fi
            shift
            ;;
    esac
done

# Set default UUID if not provided
if [[ -z "$UUID" ]]; then
    UUID=$(date +%s)
fi

echo "🔍 Starting debug run with UUID: $UUID"
echo "📸 Input image: $INPUT_IMAGE"

if [[ "$USE_MULTIVIEW" == "true" ]]; then
    echo "🎯 Mode: MULTI-VIEW (4 synthetic photos → 3D reconstruction)"
    echo "   This will generate front, side, back, and 3/4 views"
else
    echo "🎯 Mode: SINGLE-VIEW (legacy mode)"
fi

# Create debug directory
mkdir -p debug/$UUID

echo ""
echo "🚀 Running enhanced pipeline..."
python petplantr_advanced_pipeline.py "$INPUT_IMAGE" --name "DebugTest_$UUID" --save-intermediates --uid "$UUID" $EXTRA_ARGS 2>&1 | tee debug/$UUID/pipeline.log

echo ""
echo "🔍 Results stored in debug/$UUID"

if [[ "$USE_MULTIVIEW" == "true" ]]; then
    echo "📋 Multi-view files to check:"
    echo "   00_input.jpg                - Original pet photo"
    echo "   view_front.png             - Front view synthetic photo"
    echo "   view_side_left.png         - Side view synthetic photo"
    echo "   view_back.png              - Back view synthetic photo"
    echo "   view_three_quarter.png     - 3/4 view synthetic photo"
    echo "   silhouette_*.png           - Extracted silhouettes"
    echo "   01_concept_planter.png     - Main concept (front view)"
    echo "   05_repaired.stl            - Final 3D model"
    
    echo ""
    echo "🔧 Quick analysis commands:"
    echo "   open debug/$UUID/view_front.png"
    echo "   open debug/$UUID/view_side_left.png"
    echo "   open debug/$UUID/05_repaired.stl"
else
    echo "📋 Single-view files to check:"
    echo "   00_input.jpg               - Original photo"
    echo "   01_concept_planter.png     - DALL·E output"
    echo "   02_mask.png                - Object mask"
    echo "   03_depth.png               - Depth map"
    echo "   04_raw_mesh.ply            - Pre-repair mesh"
    echo "   05_repaired.stl            - Final STL"
    
    echo ""
    echo "🔧 Quick analysis commands:"
    echo "   open debug/$UUID/01_concept_planter.png"
    echo "   open debug/$UUID/03_depth.png"
    echo "   open debug/$UUID/05_repaired.stl"
fi

echo ""
echo "🎯 To test multi-view mode:"
echo "   ./enhanced_debug_run.sh test_golden_dog.jpg --multi-view"
