# 🔧 Stripe Integration Fix for PetPlantr
**Status:** Resolving 401 Authentication Error

## 🎯 Issue Resolution

The Stripe API is returning a 401 error because the current keys are placeholder values. Let me fix this with proper test keys.

## ✅ Steps to Fix Stripe Integration

### 1. Get Test Keys from Stripe Dashboard
Visit: https://dashboard.stripe.com/test/apikeys

### 2. Required Keys:
- **Publishable Key**: `pk_test_...` (for frontend)
- **Secret Key**: `sk_test_...` (for backend)
- **Webhook Secret**: `whsec_...` (for webhooks)

### 3. Create Test Product and Price
1. Go to: https://dashboard.stripe.com/test/products
2. Create product: "PetPlantr 3D Print Service"
3. Set price: $29.99 (or desired amount)
4. Copy the price ID: `price_...`

## 🔄 Environment Variables Update

The following environment variables need to be updated with real Stripe test keys:

```bash
# Stripe Test Keys (replace with actual values from dashboard)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_51...
STRIPE_SECRET_KEY=sk_test_51...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...
NEXT_PUBLIC_STRIPE_PRICE_ID=price_...
```

## 🛠️ Temporary Fix for Demo

For now, I'll set up a working configuration that handles the 401 gracefully and allows the rest of the system to work while Stripe is being configured.
