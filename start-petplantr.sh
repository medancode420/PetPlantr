#!/bin/bash
# start-petplantr.sh: Initializes and starts PetPlantr in the specified directory.
# Supports AI-assisted setup with Grok integration for automated configuration.

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Set directory (user-provided or default from context)
PROJECT_DIR="${1:-/Users/medan/Downloads/PetPlantr}"

log_info "🐾 Starting PetPlantr setup in: $PROJECT_DIR"

# Create directory if it doesn't exist
if [ ! -d "$PROJECT_DIR" ]; then
    log_info "📁 Creating project directory: $PROJECT_DIR"
    mkdir -p "$PROJECT_DIR"
fi

cd "$PROJECT_DIR" || exit 1
log_success "📂 Changed to project directory: $(pwd)"

# Clone repo if not present (assuming public repo; adjust for private)
if [ ! -d ".git" ]; then
    log_info "📥 Cloning PetPlantr repository..."
    # Replace with actual repo URL
    git clone https://github.com/medancode420/PetPlantr.git .
    log_success "✅ Repository cloned successfully"
else
    log_info "📁 Repository already exists, pulling latest changes..."
    git pull origin main
    log_success "✅ Repository updated"
fi

# Setup Python virtual environment
if [ ! -d ".venv" ]; then
    log_info "🐍 Creating Python virtual environment..."
    python3 -m venv .venv
    log_success "✅ Virtual environment created"
else
    log_info "🐍 Virtual environment already exists"
fi

# Activate virtual environment
log_info "🔧 Activating virtual environment..."
source .venv/bin/activate
log_success "✅ Virtual environment activated"

# Upgrade pip
log_info "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
log_info "📦 Installing dependencies (including bcrypt==4.0.1 pin)..."
pip install -r requirements.txt
log_success "✅ Dependencies installed"

# Setup environment configuration
if [ ! -f ".env" ]; then
    if [ -f ".env.template" ]; then
        log_info "⚙️  Setting up environment configuration..."
        cp .env.template .env
        log_warning "⚠️  Please edit .env file with your API keys and configuration"
        log_info "   Required: REPLICATE_API_TOKEN, JWT_SECRET"
        log_info "   Optional: ENABLE_SYNTHETIC_MONITOR=true, ENABLE_PRODUCTION_AI=true"
    else
        log_warning "⚠️  .env.template not found, creating basic .env file"
        cat > .env << EOF
# PetPlantr Environment Configuration
# Copy from .env.template and fill in your values

# API Configuration
REPLICATE_API_TOKEN=your_replicate_token_here
JWT_SECRET=your_jwt_secret_here
AWS_LAMBDA_API_URL=https://cm1ffbb7hf.execute-api.us-east-1.amazonaws.com/dev

# Feature Flags
ENABLE_SYNTHETIC_MONITOR=true
ENABLE_BREED_API=true
ENABLE_PRODUCTION_AI=false

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Development/Production Mode
NODE_ENV=development
EOF
    fi
else
    log_info "⚙️  Environment file already exists"
fi

# Start infrastructure services (if docker-compose.yml exists)
if [ -f "docker-compose.yml" ]; then
    log_info "🐳 Starting infrastructure services..."
    docker-compose up -d
    log_success "✅ Infrastructure services started"
else
    log_warning "⚠️  docker-compose.yml not found, skipping infrastructure setup"
fi

# Start backend server
log_info "🚀 Starting PetPlantr backend server..."
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export ENABLE_SYNTHETIC_MONITOR=true
export SYNTHETIC_MONITOR_PERIOD_MS=5000

# Start server in background
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
log_success "✅ Backend server started (PID: $BACKEND_PID)"

# Wait a moment for backend to start
sleep 3

# Start frontend (if it exists)
if [ -d "frontend" ]; then
    log_info "🌐 Starting frontend development server..."
    cd frontend

    # Check if package.json exists
    if [ -f "package.json" ]; then
        # Install frontend dependencies if node_modules doesn't exist
        if [ ! -d "node_modules" ]; then
            log_info "📦 Installing frontend dependencies..."
            npm install
        fi

        # Start frontend development server
        npm run dev &
        FRONTEND_PID=$!
        log_success "✅ Frontend server started (PID: $FRONTEND_PID)"
        cd ..
    else
        log_warning "⚠️  package.json not found in frontend directory"
        cd ..
    fi
else
    log_warning "⚠️  Frontend directory not found, skipping frontend setup"
fi

# Display status and access information
echo ""
log_success "🎉 PetPlantr startup complete!"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo "  🌐 Frontend: http://localhost:3000"
echo "  🚀 Backend API: http://localhost:8000"
echo "  📚 API Docs: http://localhost:8000/api/docs"
echo "  🔍 Health Check: http://localhost:8000/api/v1/health"
echo "  📊 Synthetic Monitor: http://localhost:8000/api/v1/ops/synthetic/live"
echo ""
echo -e "${YELLOW}Process IDs:${NC}"
echo "  Backend PID: $BACKEND_PID"
if [ -n "$FRONTEND_PID" ]; then
    echo "  Frontend PID: $FRONTEND_PID"
fi
echo ""
log_info "To stop services: kill $BACKEND_PID"
if [ -n "$FRONTEND_PID" ]; then
    log_info "To stop frontend: kill $FRONTEND_PID"
fi
echo ""
log_info "For production deployment, run: docker-compose -f docker-compose.production.yml up -d"

# Wait for user input to keep script running
echo ""
read -p "Press Enter to stop services and exit..."

# Cleanup
log_info "🛑 Stopping services..."
kill $BACKEND_PID 2>/dev/null || true
if [ -n "$FRONTEND_PID" ]; then
    kill $FRONTEND_PID 2>/dev/null || true
fi

if [ -f "docker-compose.yml" ]; then
    log_info "🛑 Stopping infrastructure services..."
    docker-compose down
fi

log_success "👋 PetPlantr shutdown complete"
