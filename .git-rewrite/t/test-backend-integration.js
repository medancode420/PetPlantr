#!/usr/bin/env node

/**
 * 🐕 PetPlantr Backend Integration Test
 * 
 * This script tests the actual backend Lambda functions with a real test image
 */

const fs = require('fs');
const path = require('path');

// Import the actual Lambda functions
const { handler: generateSTLHandler } = require('./backend/src/lambdas/generateSTL');
const { handler: processSTLHandler } = require('./backend/src/lambdas/processSTL');
const { handler: notifyCustomerHandler } = require('./backend/src/lambdas/notifyCustomer');

class BackendIntegrationTester {
  constructor() {
    this.testConfig = {
      orderId: `BACKEND_TEST_${Date.now()}`,
      userId: 'test_user_backend',
      testImage: 'val_002_pug_pug_74.jpg',
      printOptions: {
        size: 'Medium',
        color: 'Terra Clay',
        plantType: 'Succulent',
        drainage: true,
        printType: 'Resin Casted Museum Replica',
        petName: 'Buster Backend Test',
        addOns: ['Nameplate Engraving']
      }
    };
  }

  async runBackendTest() {
    console.log('🔧 Starting Backend Integration Test');
    console.log('='.repeat(50));
    
    try {
      // Test 1: GenerateSTL Lambda
      const stlResult = await this.testGenerateSTL();
      
      // Test 2: ProcessSTL Lambda
      const processResult = await this.testProcessSTL(stlResult);
      
      // Test 3: NotifyCustomer Lambda
      await this.testNotifyCustomer(processResult);
      
      console.log('\n🎉 Backend Integration Test PASSED!');
      
    } catch (error) {
      console.error('❌ Backend Integration Test FAILED:', error.message);
      console.error(error.stack);
    }
  }

  async testGenerateSTL() {
    console.log('\n🤖 Testing GenerateSTL Lambda...');
    
    const event = {
      orderId: this.testConfig.orderId,
      userId: this.testConfig.userId,
      photoKeys: [this.testConfig.testImage],
      sizeTier: 'MEDIUM',
      printOptions: this.testConfig.printOptions,
      rawStlBucket: 'petplantr-raw-stl-test'
    };
    
    console.log('📋 Input event:', JSON.stringify(event, null, 2));
    
    const result = await generateSTLHandler(event);
    
    console.log('✅ GenerateSTL completed');
    console.log('📤 Output:', JSON.stringify(result, null, 2));
    
    return result;
  }

  async testProcessSTL(stlResult) {
    console.log('\n⚙️ Testing ProcessSTL Lambda...');
    
    const event = {
      orderId: stlResult.orderId,
      userId: stlResult.userId,
      rawStlKey: stlResult.rawStlKey,
      sizeTier: 'MEDIUM',
      printOptions: this.testConfig.printOptions,
      readyStlBucket: 'petplantr-ready-stl-test'
    };
    
    console.log('📋 Input event:', JSON.stringify(event, null, 2));
    
    const result = await processSTLHandler(event);
    
    console.log('✅ ProcessSTL completed');
    console.log('📤 Output:', JSON.stringify(result, null, 2));
    
    return result;
  }

  async testNotifyCustomer(processResult) {
    console.log('\n📧 Testing NotifyCustomer Lambda...');
    
    const event = {
      orderId: processResult.orderId,
      userId: processResult.userId,
      readyStlKey: processResult.readyStlKey,
      status: 'COMPLETED',
      printingSpecs: processResult.printingSpecs,
      printOptions: this.testConfig.printOptions
    };
    
    console.log('📋 Input event:', JSON.stringify(event, null, 2));
    
    const result = await notifyCustomerHandler(event);
    
    console.log('✅ NotifyCustomer completed');
    console.log('📤 Output:', JSON.stringify(result, null, 2));
    
    return result;
  }
}

// Run the backend integration test
if (require.main === module) {
  const tester = new BackendIntegrationTester();
  tester.runBackendTest().catch(console.error);
}

module.exports = BackendIntegrationTester;
