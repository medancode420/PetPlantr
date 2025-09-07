#!/usr/bin/env node

/**
 * Create $1 Smoke Test Price in Stripe
 * 
 * This script creates a $1.00 USD price for smoke testing the PetPlantr pipeline.
 * Run this script to create the price and get the price ID for your .env file.
 * 
 * Usage:
 *   node scripts/create-smoke-test-price.js
 * 
 * Prerequisites:
 *   - STRIPE_SECRET_KEY environment variable set
 *   - OR Stripe CLI configured with `stripe login`
 */

const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);

async function createSmokeTestPrice() {
  console.log('🧪 Creating $1 Smoke Test Price for PetPlantr...');

  try {
    // First, create a product if it doesn't exist
    let product;
    try {
      // Try to retrieve existing smoke test product
      const products = await stripe.products.list({
        limit: 100,
      });
      
      product = products.data.find(p => p.metadata?.purpose === 'smoke_test');
      
      if (product) {
        console.log(`✅ Found existing smoke test product: ${product.id}`);
      }
    } catch (error) {
      console.log('Creating new smoke test product...');
    }

    // Create product if not found
    if (!product) {
      product = await stripe.products.create({
        name: 'PetPlantr Smoke Test',
        description: 'Test product for $1 smoke testing of the PetPlantr pipeline',
        metadata: {
          purpose: 'smoke_test',
          environment: 'testing',
          pipeline: 'petplantr',
        },
      });
      console.log(`✅ Created smoke test product: ${product.id}`);
    }

    // Create $1.00 price
    const price = await stripe.prices.create({
      product: product.id,
      unit_amount: 100, // $1.00 in cents
      currency: 'usd',
      nickname: 'Smoke Test - $1.00',
      metadata: {
        purpose: 'smoke_test',
        test_amount: '100_cents',
        pipeline: 'petplantr',
      },
    });

    console.log(`✅ Created $1 smoke test price: ${price.id}`);
    console.log('');
    console.log('🔧 Add this to your .env file:');
    console.log(`STRIPE_PRICE_SMOKE_TEST=${price.id}`);
    console.log('');
    console.log('📋 Price Details:');
    console.log(`   ID: ${price.id}`);
    console.log(`   Amount: $${price.unit_amount / 100}`);
    console.log(`   Currency: ${price.currency.toUpperCase()}`);
    console.log(`   Product: ${product.name}`);
    console.log('');
    console.log('🧪 You can now use this price for smoke testing the full pipeline!');

    return price;

  } catch (error) {
    console.error('❌ Error creating smoke test price:', error.message);
    
    if (error.code === 'api_key_invalid') {
      console.log('');
      console.log('💡 Fix: Set your Stripe secret key:');
      console.log('   export STRIPE_SECRET_KEY=sk_test_...');
      console.log('   or');
      console.log('   export STRIPE_SECRET_KEY=sk_live_...');
    }
    
    process.exit(1);
  }
}

// Alternative: Create using Stripe CLI command
function showStripeCLICommand() {
  console.log('');
  console.log('🛠️  Alternative: Create using Stripe CLI');
  console.log('   stripe products create --name="PetPlantr Smoke Test" --description="$1 smoke test"');
  console.log('   stripe prices create --product=prod_xxx --unit-amount=100 --currency=usd --nickname="Smoke Test"');
  console.log('');
}

if (require.main === module) {
  if (!process.env.STRIPE_SECRET_KEY) {
    console.log('❌ STRIPE_SECRET_KEY environment variable not set');
    console.log('');
    console.log('💡 Set your Stripe secret key first:');
    console.log('   export STRIPE_SECRET_KEY=sk_test_... # for testing');
    console.log('   export STRIPE_SECRET_KEY=sk_live_... # for production');
    console.log('');
    showStripeCLICommand();
    process.exit(1);
  }

  createSmokeTestPrice();
}

module.exports = { createSmokeTestPrice };
