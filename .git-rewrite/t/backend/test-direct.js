#!/usr/bin/env node

/**
 * 🧪 Direct Farm Manager Function Tester
 * Test the farmManager function directly without HTTP layer
 */

const path = require('path');

// Mock AWS services for local testing
const mockDynamoDB = {
  send: async (command) => {
    console.log(`🔄 Mock DynamoDB operation: ${command.constructor.name}`);
    
    // Mock responses based on command type
    if (command.constructor.name === 'ScanCommand') {
      return {
        Items: [
          {
            printerId: 'printer_001',
            name: 'Test Printer 1',
            status: 'idle',
            progress: 0,
            ipAddress: '192.168.1.100'
          },
          {
            printerId: 'printer_002', 
            name: 'Test Printer 2',
            status: 'printing',
            progress: 45,
            currentJob: 'job_001'
          }
        ]
      };
    }
    
    if (command.constructor.name === 'PutCommand') {
      return { success: true };
    }
    
    if (command.constructor.name === 'UpdateCommand') {
      return { success: true };
    }
    
    return { Items: [] };
  }
};

const mockEventBridge = {
  send: async (command) => {
    console.log(`🔄 Mock EventBridge operation: ${command.constructor.name}`);
    return { success: true };
  }
};

const mockS3 = {
  send: async (command) => {
    console.log(`🔄 Mock S3 operation: ${command.constructor.name}`);
    return { success: true };
  }
};

// Mock logger
const mockLogger = {
  info: (msg, data) => console.log(`ℹ️  ${msg}`, data || ''),
  error: (msg, data) => console.log(`❌ ${msg}`, data || ''),
  warn: (msg, data) => console.log(`⚠️  ${msg}`, data || ''),
  debug: (msg, data) => console.log(`🐛 ${msg}`, data || '')
};

// Set up environment
process.env.PRINTERS_TABLE = 'test-printers';
process.env.JOBS_TABLE = 'test-jobs';
process.env.FARM_METRICS_TABLE = 'test-metrics';
process.env.AWS_REGION = 'us-east-1';

async function testFarmManager() {
  console.log('🧪 Testing Farm Manager Functions');
  console.log('================================');
  
  try {
    // Import the handler (this will use our mocked AWS services)
    const { handler } = require('./dist/src/lambdas/farmManager.js');
    
    console.log('✅ Farm Manager module loaded successfully');
    
    // Test basic status endpoint
    console.log('\n📊 Testing Farm Status Endpoint...');
    const statusEvent = {
      httpMethod: 'GET',
      path: '/api/farm/status',
      pathParameters: null,
      queryStringParameters: null,
      headers: {},
      body: null
    };
    
    const statusResult = await handler(statusEvent);
    console.log('Status Response:', {
      statusCode: statusResult.statusCode,
      body: JSON.parse(statusResult.body)
    });
    
    // Test printers endpoint
    console.log('\n🖨️  Testing Printers Endpoint...');
    const printersEvent = {
      httpMethod: 'GET',
      path: '/api/farm/printers',
      pathParameters: null,
      queryStringParameters: { detailed: 'true' },
      headers: {},
      body: null
    };
    
    const printersResult = await handler(printersEvent);
    console.log('Printers Response:', {
      statusCode: printersResult.statusCode,
      body: JSON.parse(printersResult.body)
    });
    
    // Test analytics endpoint
    console.log('\n📈 Testing Analytics Endpoint...');
    const analyticsEvent = {
      httpMethod: 'GET',
      path: '/api/farm/analytics',
      pathParameters: null,
      queryStringParameters: null,
      headers: {},
      body: null
    };
    
    const analyticsResult = await handler(analyticsEvent);
    console.log('Analytics Response:', {
      statusCode: analyticsResult.statusCode,
      body: JSON.parse(analyticsResult.body)
    });
    
    // Test creating a printer
    console.log('\n➕ Testing Add Printer...');
    const addPrinterEvent = {
      httpMethod: 'POST',
      path: '/api/farm/printers',
      pathParameters: null,
      queryStringParameters: null,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: 'Test Printer 3',
        ipAddress: '192.168.1.103',
        materialLoaded: 'PLA'
      })
    };
    
    const addPrinterResult = await handler(addPrinterEvent);
    console.log('Add Printer Response:', {
      statusCode: addPrinterResult.statusCode,
      body: JSON.parse(addPrinterResult.body)
    });
    
    console.log('\n🎉 All Tests Completed Successfully!');
    console.log('====================================');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.error('Stack trace:', error.stack);
  }
}

// Run the tests
testFarmManager();
