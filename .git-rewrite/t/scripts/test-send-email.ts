#!/usr/bin/env ts-node

/**
 * Microsoft Graph Email Test Script for PetPlantr
 * Tests the email functionality with Microsoft Graph integration
 */

import { EnhancedEmailService } from '../backend/src/services/enhancedEmailService';

interface TestOptions {
  to: string;
  template: 'orderConfirmation' | 'orderStatusUpdate' | 'orderComplete' | 'internalAlert';
  orderId: string;
  amount: string;
}

async function parseArgs(): Promise<TestOptions> {
  const args = process.argv.slice(2);
  const options: Partial<TestOptions> = {};
  
  for (let i = 0; i < args.length; i += 2) {
    const key = args[i];
    const value = args[i + 1];
    
    switch (key) {
      case '--to':
        options.to = value;
        break;
      case '--template':
        options.template = value as TestOptions['template'];
        break;
      case '--order-id':
        options.orderId = value;
        break;
      case '--amount':
        options.amount = value;
        break;
    }
  }
  
  // Validate required options
  if (!options.to) {
    console.error('❌ --to email address is required');
    process.exit(1);
  }
  
  return {
    to: options.to,
    template: options.template || 'orderConfirmation',
    orderId: options.orderId || `TEST-${Date.now()}`,
    amount: options.amount || '$1.00'
  };
}

async function testMicrosoftGraphEmail() {
  console.log('🧪 PetPlantr Microsoft Graph Email Test');
  console.log('=======================================');
  console.log('');
  
  const options = await parseArgs();
  
  console.log('📧 Test Configuration:');
  console.log(`   To: ${options.to}`);
  console.log(`   Template: ${options.template}`);
  console.log(`   Order ID: ${options.orderId}`);
  console.log(`   Amount: ${options.amount}`);
  console.log('');
  
  try {
    const emailService = new EnhancedEmailService();
    
    console.log('🔄 Initializing email service...');
    
    const orderDetails = {
      orderId: options.orderId,
      userId: 'test-user',
      photoCount: 5,
      sizeTier: 'medium',
      amount: parseFloat(options.amount.replace('$', '')),
      downloadUrl: 'https://petplantr.com/download/test-123'
    };
    
    let result: any;
    
    switch (options.template) {
      case 'orderConfirmation':
        console.log('📤 Sending order confirmation email...');
        result = await emailService.sendOrderConfirmation(
          { email: options.to, name: 'Test Customer' },
          orderDetails
        );
        break;
        
      case 'orderStatusUpdate':
        console.log('📤 Sending order status update email...');
        result = await emailService.sendOrderStatusUpdate(
          { email: options.to, name: 'Test Customer' },
          options.orderId,
          'processing',
          'Your order is being processed and will be ready soon!'
        );
        break;
        
      case 'orderComplete':
        console.log('📤 Sending order completion email...');
        result = await emailService.sendOrderCompletion(
          { email: options.to, name: 'Test Customer' },
          orderDetails
        );
        break;
        
      case 'internalAlert':
        console.log('📤 Sending internal alert email...');
        result = await emailService.sendInternalAlert(
          `New Order Alert: ${options.orderId}`,
          `Test order ${options.orderId} for ${options.amount} has been received.`,
          'high',
          orderDetails
        );
        break;
        
      default:
        throw new Error(`Unknown template: ${options.template}`);
    }
    
    console.log('');
    console.log('✅ Email sent successfully!');
    console.log('📊 Result:', JSON.stringify(result, null, 2));
    
    if (result.transport === 'microsoft-graph') {
      console.log('');
      console.log('🎉 Microsoft Graph integration working correctly!');
      console.log('📧 Email sent from: Daniel@PetPlantr.com');
      console.log('🔍 Check Azure Portal → App Registrations → Sign-ins for authentication logs');
    } else if (result.transport === 'ses') {
      console.log('');
      console.log('⚠️  Fell back to AWS SES');
      console.log('🔧 Troubleshooting needed for Microsoft Graph');
    }
    
  } catch (error: any) {
    console.error('');
    console.error('❌ Email test failed:');
    console.error(error.message);
    
    if (error.message.includes('401') || error.message.includes('Unauthorized')) {
      console.error('');
      console.error('🔧 Troubleshooting:');
      console.error('1. Check admin consent in Azure Portal');
      console.error('2. Verify Mail.Send permission is granted');
      console.error('3. Confirm client secret is correct');
    }
    
    process.exit(1);
  }
}

// Usage instructions
if (process.argv.length < 4) {
  console.log('📧 PetPlantr Microsoft Graph Email Test');
  console.log('======================================');
  console.log('');
  console.log('Usage:');
  console.log('  npm run test:email -- --to recipient@example.com --template orderConfirmation --order-id TEST-123 --amount "$1.00"');
  console.log('');
  console.log('Options:');
  console.log('  --to           Recipient email address (required)');
  console.log('  --template     Email template: orderConfirmation | orderStatusUpdate | orderComplete | internalAlert');
  console.log('  --order-id     Test order ID (default: TEST-{timestamp})');
  console.log('  --amount       Order amount (default: $1.00)');
  console.log('');
  console.log('Examples:');
  console.log('  npm run test:email -- --to you@example.com --template orderConfirmation');
  console.log('  npm run test:email -- --to daniel@petplantr.com --template internalAlert --order-id TEST-PROD-001');
  console.log('');
  process.exit(0);
}

testMicrosoftGraphEmail();
