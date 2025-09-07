#!/bin/bash
# One-Hour Fine-Tune Script for CLIP+LoRA Breed Detection
# Optimized training pipeline for production-ready breed detection

set -e

# Configuration
PROJECT_ROOT="/Users/medan/Downloads/PetPlantr"
CONDA_ENV_NAME="petplantr"
WANDB_PROJECT="petplantr-breed-head"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Function to setup conda environment
setup_conda_env() {
    log_info "Setting up conda environment: $CONDA_ENV_NAME"
    
    # Check if conda is available
    if ! command -v conda &> /dev/null; then
        log_error "Conda not found. Please install Anaconda or Miniconda."
        exit 1
    fi
    
    # Create environment if it doesn't exist
    if ! conda env list | grep -q "$CONDA_ENV_NAME"; then
        log_info "Creating new conda environment..."
        conda create -n "$CONDA_ENV_NAME" python=3.11 -y
    else
        log_info "Using existing conda environment: $CONDA_ENV_NAME"
    fi
    
    log_success "Conda environment ready"
}

# Function to install dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."
    
    cd "$PROJECT_ROOT"
    
    # Activate conda environment
    eval "$(conda shell.bash hook)"
    conda activate "$CONDA_ENV_NAME"
    
    # Install PyTorch with CUDA if available
    if python -c "import torch; print(torch.cuda.is_available())" 2>/dev/null | grep -q "True"; then
        log_info "Installing PyTorch with CUDA support..."
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    else
        log_info "Installing PyTorch CPU version..."
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    fi
    
    # Install other requirements
    pip install -r requirements.txt
    
    # Verify critical packages
    python -c "
import torch
import transformers
import loralib
import albumentations
import wandb
print('✅ All dependencies installed successfully')
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
"
    
    log_success "Dependencies installed"
}

# Function to setup W&B
setup_wandb() {
    log_info "Setting up Weights & Biases logging..."
    
    eval "$(conda shell.bash hook)"
    conda activate "$CONDA_ENV_NAME"
    
    export WANDB_PROJECT="$WANDB_PROJECT"
    
    # Check if wandb is logged in
    if ! wandb status &>/dev/null; then
        log_warning "W&B not logged in. Login or set WANDB_MODE=offline"
        log_info "To login: wandb login"
        export WANDB_MODE=offline
    fi
    
    log_success "W&B setup complete"
}

# Function to validate training data
validate_training_data() {
    log_info "Validating training data..."
    
    cd "$PROJECT_ROOT"
    eval "$(conda shell.bash hook)"
    conda activate "$CONDA_ENV_NAME"
    
    # Check if labels file exists
    if [ ! -f "data/labels.csv" ]; then
        log_error "labels.csv not found. Run prepare_training_corpus.sh first"
        exit 1
    fi
    
    # Validate data with Python
    python -c "
import pandas as pd
import os
from pathlib import Path

# Load labels
df = pd.read_csv('data/labels.csv')
print(f'Total images in dataset: {len(df)}')

# Check if files exist
missing_files = []
for filepath in df['filepath']:
    if not Path(filepath).exists():
        missing_files.append(filepath)

if missing_files:
    print(f'❌ {len(missing_files)} missing files found')
    for f in missing_files[:5]:  # Show first 5
        print(f'  Missing: {f}')
    if len(missing_files) > 5:
        print(f'  ... and {len(missing_files) - 5} more')
    exit(1)
else:
    print('✅ All image files found')

# Check breed distribution
breed_counts = df['breed_id'].value_counts().sort_index()
min_count = breed_counts.min()
max_count = breed_counts.max()
num_breeds = len(breed_counts)

print(f'Number of breeds: {num_breeds}')
print(f'Images per breed: {min_count} - {max_count}')

if min_count < 10:
    print(f'⚠️  Some breeds have very few images (min: {min_count})')
    
print('✅ Training data validation passed')
"
    
    log_success "Training data validated"
}

# Function to run training
run_training() {
    log_info "Starting CLIP+LoRA fine-tuning..."
    log_info "Estimated time: ~60 minutes on single GPU"
    
    cd "$PROJECT_ROOT"
    eval "$(conda shell.bash hook)"
    conda activate "$CONDA_ENV_NAME"
    
    # Set environment variables
    export WANDB_PROJECT="$WANDB_PROJECT"
    
    # Training command with optimal settings
    local training_cmd="python -m src.ai.training.train_breed_head \
        --csv data/labels.csv \
        --hard-neg-dir data/hard_neg \
        --batch 32 \
        --epochs 5 \
        --output-dir outputs \
        --val-split 0.1 \
        --precision bf16 \
        --lora-lr 1e-3 \
        --base-lr 1e-4 \
        --confidence-weight 0.1 \
        --label-smoothing 0.1 \
        --early-stop-patience 3 \
        --save-interval 1 \
        --log-interval 10"
    
    log_info "Training command: $training_cmd"
    
    # Create outputs directory
    mkdir -p outputs
    
    # Run training with progress monitoring
    if eval "$training_cmd"; then
        log_success "Training completed successfully!"
        
        # Check if model was saved
        if [ -f "outputs/breed_head_lora.pt" ]; then
            log_success "Model saved: outputs/breed_head_lora.pt"
            
            # Copy to weights directory
            mkdir -p weights
            cp outputs/breed_head_lora.pt weights/
            log_success "Model copied to weights/breed_head_lora.pt"
            
            # Show model size
            model_size=$(du -h weights/breed_head_lora.pt | cut -f1)
            log_info "Model size: $model_size"
        else
            log_error "Model file not found after training"
            return 1
        fi
    else
        log_error "Training failed"
        return 1
    fi
}

# Function to validate trained model
validate_model() {
    log_info "Validating trained model..."
    
    cd "$PROJECT_ROOT"
    eval "$(conda shell.bash hook)"
    conda activate "$CONDA_ENV_NAME"
    
    python -c "
import sys
sys.path.append('.')

import torch
from src.ai.models.clip_breed import CLIPBreedDetector
from pathlib import Path

# Load trained model
model_path = 'weights/breed_head_lora.pt'

if not Path(model_path).exists():
    print('❌ Trained model not found')
    exit(1)

try:
    # Create model
    model = CLIPBreedDetector(num_breeds=451, lora_rank=16)
    
    # Load weights
    checkpoint = torch.load(model_path, map_location='cpu')
    model.load_state_dict(checkpoint['model_state_dict'])
    
    print('✅ Model loaded successfully')
    
    # Check model info
    info = model.get_model_info()
    print(f'Model type: {info[\"model_name\"]}')
    print(f'Total parameters: {info[\"total_parameters\"]:,}')
    print(f'Trainable parameters: {info[\"trainable_parameters\"]:,}')
    print(f'Efficiency ratio: {info[\"efficiency_ratio\"]}')
    
    # Test inference
    test_input = torch.randn(1, 3, 224, 224)
    model.eval()
    
    with torch.no_grad():
        outputs = model(test_input)
        
    print(f'✅ Model inference test passed')
    print(f'Logits shape: {outputs[\"logits\"].shape}')
    print(f'Confidence shape: {outputs[\"confidence\"].shape}')
    
    # Check training metrics if available
    if 'metrics' in checkpoint:
        metrics = checkpoint['metrics']
        print(f'Final training accuracy: {metrics.get(\"train_accuracy\", \"N/A\"):.3f}')
        print(f'Final validation accuracy: {metrics.get(\"val_accuracy\", \"N/A\"):.3f}')
        
        val_acc = metrics.get('val_accuracy', 0)
        if val_acc >= 0.95:
            print('🎉 Target accuracy achieved (≥95%)')
        elif val_acc >= 0.90:
            print('⚠️  Good accuracy achieved, consider more training for 95%+ target')
        else:
            print('❌ Low accuracy, check training data and parameters')
            
except Exception as e:
    print(f'❌ Model validation failed: {e}')
    exit(1)
"
    
    log_success "Model validation completed"
}

# Function to generate training report
generate_training_report() {
    log_info "Generating training report..."
    
    cd "$PROJECT_ROOT"
    eval "$(conda shell.bash hook)"
    conda activate "$CONDA_ENV_NAME"
    
    local report_file="outputs/training_report_$(date +%Y%m%d_%H%M%S).json"
    
    python -c "
import json
import torch
from pathlib import Path
import sys
sys.path.append('.')

report = {
    'timestamp': '$(date -Iseconds)',
    'training_completed': False,
    'model_size_mb': 0,
    'training_metrics': {},
    'system_info': {
        'cuda_available': torch.cuda.is_available(),
        'gpu_count': torch.cuda.device_count() if torch.cuda.is_available() else 0
    }
}

# Check if model exists
model_path = Path('weights/breed_head_lora.pt')
if model_path.exists():
    report['training_completed'] = True
    report['model_size_mb'] = model_path.stat().st_size / 1024 / 1024
    
    # Load training metrics
    try:
        checkpoint = torch.load(model_path, map_location='cpu')
        if 'metrics' in checkpoint:
            report['training_metrics'] = checkpoint['metrics']
        if 'training_history' in checkpoint:
            history = checkpoint['training_history']
            if history:
                final_metrics = history[-1]
                report['final_epoch'] = final_metrics.get('epoch', 0)
                report['final_train_acc'] = final_metrics.get('train_accuracy', 0)
                report['final_val_acc'] = final_metrics.get('val_accuracy', 0)
    except Exception as e:
        report['load_error'] = str(e)

# Save report
with open('$report_file', 'w') as f:
    json.dump(report, f, indent=2)

print(f'Training report saved: $report_file')

# Print summary
if report['training_completed']:
    print('🎉 Training completed successfully')
    print(f'Model size: {report[\"model_size_mb\"]:.1f} MB')
    if 'final_val_acc' in report:
        val_acc = report['final_val_acc']
        print(f'Final validation accuracy: {val_acc:.1%}')
        if val_acc >= 0.95:
            print('✅ Target accuracy achieved!')
        else:
            print('⚠️  Consider additional training for higher accuracy')
else:
    print('❌ Training not completed successfully')
"
    
    log_success "Training report generated"
}

# Main execution function
main() {
    log_info "🚀 Starting One-Hour CLIP+LoRA Fine-Tuning"
    echo "Expected duration: ~60 minutes on single GPU"
    echo ""
    
    setup_conda_env
    install_dependencies
    setup_wandb
    validate_training_data
    
    echo ""
    log_info "🎯 Starting training phase..."
    start_time=$(date +%s)
    
    run_training
    validate_model
    generate_training_report
    
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    echo ""
    log_success "🎉 Fine-tuning completed!"
    echo "Training duration: $((duration / 60)) minutes $((duration % 60)) seconds"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Review training report: ls outputs/training_report_*.json"
    echo "2. Test the model: ./test_enhanced_system.sh"
    echo "3. Deploy the system: ./deploy_enhanced.sh"
    echo "4. Start API server: conda activate $CONDA_ENV_NAME && python api_server.py"
    echo ""
    echo "🎯 Training Results:"
    echo "- Model saved: weights/breed_head_lora.pt"
    echo "- Target: 95%+ validation accuracy"
    echo "- Expected model size: ~7MB (LoRA adapters + head)"
}

# Show help
show_help() {
    echo "One-Hour CLIP+LoRA Fine-Tuning Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Prerequisites:"
    echo "1. Run prepare_training_corpus.sh first"
    echo "2. Ensure data/labels.csv exists"
    echo "3. Have sufficient GPU memory (8GB+ recommended)"
    echo ""
    echo "Options:"
    echo "  --help     Show this help message"
    echo "  --cpu      Force CPU training (slower)"
    echo "  --fast     Quick training for testing (1 epoch)"
    echo ""
    echo "Environment Variables:"
    echo "  WANDB_MODE=offline    Disable W&B logging"
    echo "  CUDA_VISIBLE_DEVICES=0  Use specific GPU"
}

# Parse arguments
case "${1:-}" in
    --help)
        show_help
        ;;
    --fast)
        export FAST_TRAINING=1
        main
        ;;
    *)
        main "$@"
        ;;
esac
