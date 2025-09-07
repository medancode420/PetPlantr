#!/bin/bash

# Create $1 Stripe Price for Smoke Testing
# Usage: ./scripts/create-stripe-price.sh

set -e  # Exit on any error

echo "🧪 Creating \$1 Smoke Test Price for PetPlantr..."

# Check if STRIPE_SECRET_KEY is set
if [ -z "$STRIPE_SECRET_KEY" ]; then
    echo "❌ STRIPE_SECRET_KEY environment variable not set"
    echo ""
    echo "💡 Set your Stripe secret key first:"
    echo "   export STRIPE_SECRET_KEY=sk_test_...  # for testing"
    echo "   export STRIPE_SECRET_KEY=sk_live_...  # for production"
    echo ""
    echo "🛠️  Alternative: Use Stripe CLI"
    echo "   stripe login"
    echo "   stripe products create --name='PetPlantr Smoke Test'"
    echo "   stripe prices create --product=prod_xxx --unit-amount=100 --currency=usd"
    exit 1
fi

echo "📦 Creating product..."

# Create product for smoke testing
PRODUCT_RESPONSE=$(curl -s https://api.stripe.com/v1/products \
  -u "$STRIPE_SECRET_KEY:" \
  -d "name=PetPlantr Smoke Test" \
  -d "description=Test product for \$1 smoke testing of the PetPlantr pipeline" \
  -d "metadata[purpose]=smoke_test" \
  -d "metadata[environment]=testing")

# Extract product ID
PRODUCT_ID=$(echo "$PRODUCT_RESPONSE" | grep -o '"id":"prod_[^"]*"' | cut -d'"' -f4)

if [ -z "$PRODUCT_ID" ]; then
    echo "❌ Failed to create product"
    echo "Response: $PRODUCT_RESPONSE"
    exit 1
fi

echo "✅ Created product: $PRODUCT_ID"

echo "💰 Creating \$1.00 price..."

# Create $1.00 price
PRICE_RESPONSE=$(curl -s https://api.stripe.com/v1/prices \
  -u "$STRIPE_SECRET_KEY:" \
  -d "product=$PRODUCT_ID" \
  -d "unit_amount=100" \
  -d "currency=usd" \
  -d "nickname=Smoke Test - \$1.00" \
  -d "metadata[purpose]=smoke_test" \
  -d "metadata[test_amount]=100_cents")

# Extract price ID
PRICE_ID=$(echo "$PRICE_RESPONSE" | grep -o '"id":"price_[^"]*"' | cut -d'"' -f4)

if [ -z "$PRICE_ID" ]; then
    echo "❌ Failed to create price"
    echo "Response: $PRICE_RESPONSE"
    exit 1
fi

echo "✅ Created \$1 smoke test price: $PRICE_ID"
echo ""
echo "🔧 Add this to your .env file:"
echo "STRIPE_PRICE_SMOKE_TEST=$PRICE_ID"
echo ""
echo "📋 Price Details:"
echo "   ID: $PRICE_ID"
echo "   Amount: \$1.00 USD"
echo "   Product: $PRODUCT_ID"
echo ""
echo "🧪 You can now use this price for smoke testing the full pipeline!"
