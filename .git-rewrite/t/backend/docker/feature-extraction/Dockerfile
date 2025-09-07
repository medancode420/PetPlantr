# PetPlantr Feature Extraction Container
# Vision Transformer + ArcFace for pet facial feature extraction

FROM nvidia/cuda:11.8-devel-ubuntu20.04

# Prevent interactive prompts during apt install
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.9 \
    python3.9-pip \
    python3.9-dev \
    git \
    wget \
    curl \
    ffmpeg \
    libsm6 \
    libxext6 \
    libfontconfig1 \
    libxrender1 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Create symlink for python
RUN ln -sf /usr/bin/python3.9 /usr/bin/python
RUN ln -sf /usr/bin/pip3 /usr/bin/pip

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install PyTorch with CUDA support
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install additional ML libraries
RUN pip install \
    transformers==4.36.0 \
    timm==0.9.10 \
    opencv-python==4.8.1.78 \
    pillow==10.1.0 \
    numpy==1.24.3 \
    boto3==1.29.0 \
    insightface==0.7.3 \
    scikit-image==0.21.0 \
    albumentations==1.3.1

# Copy application code
COPY src/ ./src/
COPY models/ ./models/
COPY config/ ./config/

# Create directories for processing
RUN mkdir -p /tmp/processing /app/cache

# Set environment variables
ENV PYTHONPATH=/app
ENV CUDA_VISIBLE_DEVICES=0
ENV TORCH_HOME=/app/cache
ENV HF_HOME=/app/cache

# Expose port for health checks
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python src/health_check.py

# Run the inference service
CMD ["python", "src/feature_extraction_service.py"]
