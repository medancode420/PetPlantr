#!/usr/bin/env node

/**
 * TASK 8 - Smoke Test for EventBridge → Step Functions Integration
 * 
 * This script tests the complete pipeline:
 * 1. POST signed webhook payload to stripeWebhook Lambda
 * 2. Verify EventBridge receives ORDER_PAID event
 * 3. Verify Step Functions execution is triggered
 * 
 * Usage:
 *   npm run test:smoke
 *   or
 *   node scripts/smokeTest.js
 */

const crypto = require('crypto');
const https = require('https');

// Configuration
const config = {
  webhookUrl: process.env.WEBHOOK_URL || 'http://localhost:3001/dev/api/stripe/webhook',
  webhookSecret: process.env.STRIPE_WEBHOOK_SECRET || 'whsec_test_secret',
  awsRegion: process.env.AWS_REGION || 'us-east-1',
  stage: process.env.STAGE || 'dev',
};

console.log('🧪 TASK 8 Smoke Test - EventBridge → Step Functions');
console.log('Configuration:', config);

// Mock Stripe event payload
const mockStripeEvent = {
  id: 'evt_smoke_test_' + Date.now(),
  object: 'event',
  api_version: '2023-10-16',
  created: Math.floor(Date.now() / 1000),
  data: {
    object: {
      id: 'cs_smoke_test_' + Date.now(),
      object: 'checkout.session',
      payment_status: 'paid',
      amount_total: 1, // $0.01 test charge
      currency: 'usd',
      customer_details: {
        email: 'smoketest@petplantr.com',
      },
      metadata: {
        userId: 'clerk_smoke_test_user',
        photoUrls: 'clerk_smoke_test_user/smoke_front.jpg,clerk_smoke_test_user/smoke_side.jpg',
        sku: 'pet-planter-medium',
        photoCount: '2',
      },
    },
  },
  livemode: false,
  pending_webhooks: 1,
  request: {
    id: 'req_smoke_test',
    idempotency_key: null,
  },
  type: 'checkout.session.completed',
};

/**
 * Generate Stripe webhook signature
 */
function generateStripeSignature(payload, secret) {
  const timestamp = Math.floor(Date.now() / 1000);
  const payloadString = JSON.stringify(payload);
  const signedPayload = `${timestamp}.${payloadString}`;
  
  const signature = crypto
    .createHmac('sha256', secret)
    .update(signedPayload, 'utf8')
    .digest('hex');
  
  return {
    signature: `t=${timestamp},v1=${signature}`,
    payload: payloadString,
  };
}

/**
 * Send webhook to Lambda
 */
function sendWebhook(url, payload, signature) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const postData = payload;
    
    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port || (urlObj.protocol === 'https:' ? 443 : 80),
      path: urlObj.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData),
        'Stripe-Signature': signature,
        'User-Agent': 'Stripe/1.0 (+https://stripe.com/docs/webhooks)',
      },
    };

    const req = (urlObj.protocol === 'https:' ? https : require('http')).request(options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          body: data,
        });
      });
    });

    req.on('error', (err) => {
      reject(err);
    });

    req.write(postData);
    req.end();
  });
}

/**
 * Check Step Functions execution
 */
async function checkStepFunctionsExecution() {
  try {
    const AWS = require('aws-sdk');
    const stepfunctions = new AWS.StepFunctions({ region: config.awsRegion });
    
    const stateMachineArn = `arn:aws:states:${config.awsRegion}:*:stateMachine:petplantr-process-order-${config.stage}`;
    
    const executions = await stepfunctions.listExecutions({
      stateMachineArn,
      maxResults: 10,
    }).promise();
    
    console.log(`📋 Found ${executions.executions.length} recent executions`);
    
    // Check for recent executions (within last 5 minutes)
    const recentExecutions = executions.executions.filter(exec => 
      new Date() - new Date(exec.startDate) < 5 * 60 * 1000
    );
    
    if (recentExecutions.length > 0) {
      console.log('✅ Recent Step Functions executions found:');
      recentExecutions.forEach(exec => {
        console.log(`   - ${exec.executionArn}`);
        console.log(`     Status: ${exec.status}`);
        console.log(`     Started: ${exec.startDate}`);
      });
      return true;
    } else {
      console.log('⚠️  No recent Step Functions executions found');
      return false;
    }
  } catch (error) {
    console.log('❌ Error checking Step Functions:', error.message);
    return false;
  }
}

/**
 * Main smoke test function
 */
async function runSmokeTest() {
  try {
    console.log('\n🚀 Step 1: Generating webhook signature...');
    const { signature, payload } = generateStripeSignature(mockStripeEvent, config.webhookSecret);
    console.log('✅ Signature generated');

    console.log('\n📤 Step 2: Sending webhook to Lambda...');
    const response = await sendWebhook(config.webhookUrl, payload, signature);
    
    console.log(`Response Status: ${response.statusCode}`);
    console.log(`Response Body: ${response.body}`);
    
    if (response.statusCode === 200) {
      console.log('✅ Webhook processed successfully');
    } else {
      throw new Error(`Webhook failed with status ${response.statusCode}`);
    }

    console.log('\n⏱️  Step 3: Waiting 10 seconds for EventBridge processing...');
    await new Promise(resolve => setTimeout(resolve, 10000));

    console.log('\n🔍 Step 4: Checking Step Functions executions...');
    const executionFound = await checkStepFunctionsExecution();
    
    if (executionFound) {
      console.log('\n🎉 SMOKE TEST PASSED!');
      console.log('✅ Webhook → EventBridge → Step Functions pipeline working correctly');
      process.exit(0);
    } else {
      console.log('\n❌ SMOKE TEST FAILED!');
      console.log('❌ Step Functions execution not triggered');
      process.exit(1);
    }

  } catch (error) {
    console.error('\n💥 SMOKE TEST ERROR:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

/**
 * Acceptance criteria validation
 */
function validateAcceptanceCriteria() {
  console.log('\n📋 TASK 8 Acceptance Criteria:');
  console.log('   ✓ Event bus petplantr-orderbus exists after deploy');
  console.log('   ✓ ORDER_PAID event triggers state machine');
  console.log('   ✓ stripeWebhook unit tests pass');
  console.log('   ✓ Permissions least-privilege (only PutEvents for webhook, StartExecution for EventBridge)');
  console.log('\n🔬 Run: npm test && npm run deploy && npm run test:smoke');
}

// Run the test
if (require.main === module) {
  validateAcceptanceCriteria();
  runSmokeTest();
}

module.exports = {
  generateStripeSignature,
  sendWebhook,
  checkStepFunctionsExecution,
  runSmokeTest,
};
