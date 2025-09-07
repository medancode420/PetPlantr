// Enhanced smoke test: create $1 session, open browser, poll SFN
const fetch = require('node-fetch');
const open = require('open');
const { SFNClient, DescribeExecutionCommand } = require('@aws-sdk/client-sfn');

const API = process.env.API_URL;              // from stack output
const PRICE = process.env.STRIPE_PRICE_SMOKE_TEST; // price_1Rcp7C...
const STATE_MACHINE_ARN = process.env.STATE_MACHINE_ARN;

async function main() {
  console.log('🧪 Starting PetPlantr Enhanced Smoke Test...');
  console.log(`📍 API URL: ${API}`);
  console.log(`💰 Price ID: ${PRICE}`);
  console.log(`🔧 State Machine: ${STATE_MACHINE_ARN}`);

  if (!API || !PRICE || !STATE_MACHINE_ARN) {
    console.error('❌ Missing required environment variables:');
    console.error('   - API_URL (from CloudFormation output)');
    console.error('   - STRIPE_PRICE_SMOKE_TEST');
    console.error('   - STATE_MACHINE_ARN');
    process.exit(1);
  }

  try {
    // 1. Create checkout session
    console.log('\n📦 Creating checkout session...');
    const res = await fetch(`${API}/api/checkout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        cartItems: [{ sku: 'SMOKE', quantity: 1 }] 
      })
    });

    if (!res.ok) {
      throw new Error(`Checkout failed: ${res.status} ${res.statusText}`);
    }

    const { url, executionArn } = await res.json();
    console.log('✅ Checkout session created');
    console.log('🌐 Opening Stripe Checkout in browser...');
    console.log('💳 Use test card: 4242 4242 4242 4242');
    
    await open(url);

    // 2. Poll Step Functions until succeeded
    console.log('\n⏳ Waiting for payment and pipeline execution...');
    console.log('💡 Complete the payment in your browser, then watch this terminal');
    
    const sfn = new SFNClient({ region: process.env.AWS_REGION });
    let status = 'RUNNING';
    let attempts = 0;
    const maxAttempts = 60; // 10 minutes max

    while (status === 'RUNNING' && attempts < maxAttempts) {
      await new Promise(r => setTimeout(r, 10000)); // Wait 10 seconds
      attempts++;
      
      try {
        const out = await sfn.send(new DescribeExecutionCommand({ executionArn }));
        status = out.status;
        process.stdout.write('.');
        
        if (attempts % 6 === 0) { // Every minute
          console.log(`\n⏱️  ${attempts * 10}s elapsed, status: ${status}`);
        }
      } catch (error) {
        console.log(`\n⚠️  Error checking status: ${error.message}`);
        break;
      }
    }

    console.log(`\n\n🎯 Final Result: State machine execution ${status}`);
    
    if (status === 'SUCCEEDED') {
      console.log('✅ SMOKE TEST PASSED! 🎉');
      console.log('💚 Pipeline successfully processed the $1 test order');
    } else if (status === 'FAILED') {
      console.log('❌ SMOKE TEST FAILED');
      console.log('🔍 Check AWS Console → Step Functions for error details');
    } else if (attempts >= maxAttempts) {
      console.log('⏰ SMOKE TEST TIMEOUT');
      console.log('🔍 Pipeline may still be running - check AWS Console');
    }

  } catch (error) {
    console.error('❌ Smoke test error:', error.message);
    process.exit(1);
  }
}

main().catch(console.error);
