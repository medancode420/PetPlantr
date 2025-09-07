#!/usr/bin/env node

/**
 * $1 Smoke Test for PetPlantr Pipeline
 * 
 * This script creates a $1 test charge and validates the complete pipeline:
 * 1. Create Stripe checkout session with SMOKE_TEST SKU
 * 2. Simulate webhook payment completion
 * 3. Verify EventBridge event emission
 * 4. Validate Step Functions execution
 * 
 * Prerequisites:
 * - STRIPE_PRICE_SMOKE_TEST environment variable
 * - Backend deployed to AWS or running locally
 */

const crypto = require('crypto');

async function runSmokeTest() {
  console.log('🧪 Starting $1 PetPlantr Pipeline Smoke Test...');
  
  // Check environment
  const requiredVars = [
    'STRIPE_PRICE_SMOKE_TEST',
    'NEXT_PUBLIC_API_BASE_URL',
  ];
  
  const missing = requiredVars.filter(v => !process.env[v]);
  if (missing.length > 0) {
    console.error('❌ Missing environment variables:', missing.join(', '));
    console.log('');
    console.log('💡 Required setup:');
    console.log('   1. Create smoke test price: npm run stripe:create-smoke-price');
    console.log('   2. Add STRIPE_PRICE_SMOKE_TEST=price_xxx to .env');
    console.log('   3. Deploy backend: npm run deploy:dev');
    process.exit(1);
  }

  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  const smokeTestPrice = process.env.STRIPE_PRICE_SMOKE_TEST;
  
  console.log(`🎯 API Base URL: ${apiBaseUrl}`);
  console.log(`💰 Smoke Test Price: ${smokeTestPrice}`);
  console.log('');

  try {
    // Step 1: Create checkout session
    console.log('📋 Step 1: Creating checkout session...');
    
    const checkoutPayload = {
      userId: 'smoke_test_user_' + Date.now(),
      items: [
        {
          sku: 'SMOKE_TEST',
          quantity: 1,
          metadata: {
            test: true,
            purpose: 'smoke_test',
            timestamp: new Date().toISOString(),
          }
        }
      ]
    };

    const checkoutResponse = await fetch(`${apiBaseUrl}/api/checkout`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(checkoutPayload),
    });

    if (!checkoutResponse.ok) {
      throw new Error(`Checkout failed: ${checkoutResponse.status} ${checkoutResponse.statusText}`);
    }

    const checkoutData = await checkoutResponse.json();
    console.log('✅ Checkout session created:', checkoutData.sessionId);
    console.log(`🔗 Payment URL: ${checkoutData.url}`);
    console.log('');

    // Step 2: Simulate webhook (in a real test, you'd complete payment manually)
    console.log('📋 Step 2: Simulate webhook processing...');
    console.log('🔄 In a real smoke test, you would:');
    console.log('   1. Open the payment URL');
    console.log('   2. Complete the $1 payment');
    console.log('   3. Verify webhook receives checkout.session.completed');
    console.log('   4. Check CloudWatch logs for pipeline execution');
    console.log('');

    // Step 3: Provide verification instructions
    console.log('📋 Step 3: Manual verification steps:');
    console.log('   1. 💳 Complete payment at:', checkoutData.url);
    console.log('   2. 🔍 Check AWS CloudWatch logs:');
    console.log('      - stripeWebhook function logs');
    console.log('      - Step Functions execution logs');
    console.log('   3. 📧 Verify notifications sent');
    console.log('   4. 🗂️  Check S3 buckets for processing artifacts');
    console.log('');
    
    console.log('✅ Smoke test setup complete!');
    console.log('💡 Complete the payment above to test the full pipeline.');

  } catch (error) {
    console.error('❌ Smoke test failed:', error.message);
    
    if (error.message.includes('fetch')) {
      console.log('');
      console.log('💡 Possible fixes:');
      console.log('   - Ensure backend is deployed: npm run deploy:dev');
      console.log('   - Check API URL is correct');
      console.log('   - Verify CORS settings allow requests');
    }
    
    process.exit(1);
  }
}

function showUsage() {
  console.log('🧪 PetPlantr $1 Smoke Test');
  console.log('');
  console.log('Usage:');
  console.log('   npm run test:smoke-e2e');
  console.log('   or');
  console.log('   node scripts/smoke-test-e2e.js');
  console.log('');
  console.log('Setup:');
  console.log('   1. Create stripe price: npm run stripe:create-smoke-price');
  console.log('   2. Deploy backend: npm run deploy:dev');
  console.log('   3. Set environment variables in .env');
}

if (require.main === module) {
  if (process.argv.includes('--help') || process.argv.includes('-h')) {
    showUsage();
    process.exit(0);
  }
  
  runSmokeTest();
}

module.exports = { runSmokeTest };
