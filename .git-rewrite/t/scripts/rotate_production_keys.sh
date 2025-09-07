#!/bin/bash
# Production Key Rotation Script for PetPlantr
# Rotates Stripe and Clerk keys from test to live environment

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

log_info "🔐 PetPlantr Production Key Rotation"
log_info "======================================"

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    log_error "Must run from PetPlantr root directory"
    exit 1
fi

# Step 1: Rotate Stripe Keys
log_info "1️⃣  Stripe Key Rotation"
log_warning "   📋 Manual steps required:"
log_warning "   1. Go to https://dashboard.stripe.com/apikeys"
log_warning "   2. Click 'Activate your account' if not done"
log_warning "   3. Click 'Roll' on Secret Key (sk_test_...)"
log_warning "   4. Click 'Roll' on Publishable Key (pk_test_...)"
log_warning "   5. Copy the NEW keys"
echo ""
read -p "   ✋ Have you completed the Stripe key rotation? (y/N): " stripe_done

if [[ $stripe_done =~ ^[Yy]$ ]]; then
    log_success "   ✅ Stripe keys rotated"
    
    # Get new keys from user
    echo ""
    read -p "   🔑 Enter NEW Stripe Secret Key (sk_live_...): " STRIPE_SECRET_LIVE
    read -p "   🔑 Enter NEW Stripe Publishable Key (pk_live_...): " STRIPE_PUB_LIVE
    
    # Validate key format
    if [[ ! $STRIPE_SECRET_LIVE =~ ^sk_live_ ]]; then
        log_error "Invalid Stripe secret key format (should start with sk_live_)"
        exit 1
    fi
    
    if [[ ! $STRIPE_PUB_LIVE =~ ^pk_live_ ]]; then
        log_error "Invalid Stripe publishable key format (should start with pk_live_)"
        exit 1
    fi
    
    # Update frontend production environment
    log_info "   📝 Updating frontend/.env.production..."
    cat > frontend/.env.production << EOF
# Production Environment - PetPlantr
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=$STRIPE_PUB_LIVE
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=\${NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY}
STRIPE_SECRET_KEY=$STRIPE_SECRET_LIVE
EOF
    
    log_success "   ✅ Frontend production env updated"
else
    log_warning "   ⚠️  Skipping Stripe key rotation"
fi

echo ""

# Step 2: Clerk Key Rotation
log_info "2️⃣  Clerk Key Rotation"
log_warning "   📋 Manual steps required:"
log_warning "   1. Go to https://dashboard.clerk.com"
log_warning "   2. Select your application"
log_warning "   3. Go to Developers → API Keys"
log_warning "   4. Switch to 'Production' environment"
log_warning "   5. Copy the production keys"
echo ""
read -p "   ✋ Have you completed the Clerk key rotation? (y/N): " clerk_done

if [[ $clerk_done =~ ^[Yy]$ ]]; then
    log_success "   ✅ Clerk production keys ready"
    
    # Get new keys from user
    echo ""
    read -p "   🔑 Enter Clerk Production Publishable Key (pk_live_...): " CLERK_PUB_LIVE
    read -p "   🔑 Enter Clerk Production Secret Key (sk_live_...): " CLERK_SECRET_LIVE
    
    # Validate key format
    if [[ ! $CLERK_PUB_LIVE =~ ^pk_live_ ]]; then
        log_error "Invalid Clerk publishable key format (should start with pk_live_)"
        exit 1
    fi
    
    if [[ ! $CLERK_SECRET_LIVE =~ ^sk_live_ ]]; then
        log_error "Invalid Clerk secret key format (should start with sk_live_)"
        exit 1
    fi
    
    # Update frontend production environment
    log_info "   📝 Updating Clerk keys in frontend/.env.production..."
    sed -i '' "s/NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=.*/NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=$CLERK_PUB_LIVE/" frontend/.env.production
    
    # Add to backend environment
    echo "CLERK_SECRET_KEY=$CLERK_SECRET_LIVE" >> backend/.env.production
    
    log_success "   ✅ Clerk production keys updated"
else
    log_warning "   ⚠️  Skipping Clerk key rotation"
fi

echo ""

# Step 3: Version Freeze for Launch
log_info "3️⃣  Infrastructure Version Freeze"

# Create git tag
log_info "   🏷️  Creating production release tag..."
git add -A
git commit -m "Production key rotation and launch preparation" || true
git tag -a v1.6.0 -m "Beta-0 Production Cut - Infrastructure freeze for launch"
git push origin v1.6.0

log_success "   ✅ Git tag v1.6.0 created and pushed"

# Lock package.json versions
log_info "   📦 Locking dependency versions..."

# Frontend package.json
cd frontend
npm shrinkwrap || npm run audit || true
cd ..

# Backend package.json  
cd backend
npm shrinkwrap || npm run audit || true
cd ..

# Update serverless.yml with locked versions
log_info "   ⚙️  Locking serverless.yml versions..."
sed -i '' 's/runtime: nodejs[0-9]*.x/runtime: nodejs20.x/' backend/serverless.yml

log_success "   ✅ Dependency versions locked"

echo ""

# Step 4: Vercel Deployment
log_info "4️⃣  Production Deployment"

if command -v vercel &> /dev/null; then
    log_info "   🚀 Deploying to Vercel production..."
    
    # Set production environment variables
    if [[ -n "$STRIPE_PUB_LIVE" ]]; then
        vercel env add NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY production <<< "$STRIPE_PUB_LIVE"
    fi
    
    if [[ -n "$CLERK_PUB_LIVE" ]]; then
        vercel env add NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY production <<< "$CLERK_PUB_LIVE"
    fi
    
    # Deploy to production
    cd frontend
    vercel --prod
    cd ..
    
    log_success "   ✅ Deployed to Vercel production"
else
    log_warning "   ⚠️  Vercel CLI not found"
    log_info "   📋 Manual deployment required:"
    log_info "      1. Install: npm i -g vercel"
    log_info "      2. Login: vercel login"
    log_info "      3. Deploy: cd frontend && vercel --prod"
fi

echo ""

# Step 5: VSCode Optimization
log_info "5️⃣  VSCode Optimization Setup"

# Create VSCode settings
mkdir -p .vscode
cat > .vscode/settings.json << 'EOF'
{
  "github.copilot.enable": true,
  "github.copilot.chat.enable": false,
  "typescript.preferences.includePackageJsonAutoImports": "off",
  "typescript.disableAutomaticTypeAcquisition": true,
  "files.watcherExclude": {
    "**/node_modules/**": true,
    "**/.git/**": true,
    "**/dist/**": true,
    "**/build/**": true,
    "**/.next/**": true,
    "**/coverage/**": true
  },
  "search.exclude": {
    "**/node_modules": true,
    "**/dist": true,
    "**/.next": true,
    "**/coverage": true
  },
  "files.exclude": {
    "**/.DS_Store": true,
    "**/node_modules": true,
    "**/.git": true
  }
}
EOF

log_success "   ✅ VSCode settings optimized"
log_info "      - Copilot inline completions enabled"
log_info "      - Chat webview disabled (prevents freezing)"
log_info "      - File watching optimized"

echo ""

# Step 6: Launch Checklist
log_info "6️⃣  Production Launch Checklist"
log_info "================================"

checklist_items=(
    "Lambda generateSTL returns 200"
    "First proprietary pet prints successfully"
    "Clerk in live mode"
    "Stripe live keys + test \$1 charge"
    "Slack #ops-alerts shows PRINT_DONE"
    "Landing page updated with hero print"
)

log_info "📋 Items to verify manually:"
for item in "${checklist_items[@]}"; do
    log_info "   ☐ $item"
done

echo ""
log_success "🎉 Production key rotation and setup complete!"
log_info ""
log_info "🚀 Next steps:"
log_info "   1. Test Lambda: aws lambda invoke --function-name petplantr-pipeline-prod-generateSTL"
log_info "   2. Run smoke test: cd backend && npm run test:smoke-e2e"
log_info "   3. Verify Vercel deployment: https://your-domain.vercel.app"
log_info "   4. Test Stripe with live \$1 charge"
log_info "   5. Monitor Slack #ops-alerts for notifications"
log_info ""
log_warning "⚠️  Remember to:"
log_warning "   - Update DNS if using custom domain"
log_warning "   - Configure Stripe webhooks for production endpoint"
log_warning "   - Test end-to-end payment flow"
