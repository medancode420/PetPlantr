#!/usr/bin/env node

/**
 * Frontend End-to-End Test Script
 * Tests all critical frontend functionality
 */

const https = require('https');
const http = require('http');

// Test configuration
const BASE_URL = 'http://localhost:3000';
const TEST_TIMEOUT = 30000;

// Colors for console output
const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m',
  bold: '\x1b[1m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith('https') ? https : http;
    const req = client.request(url, options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          data: data
        });
      });
    });
    
    req.on('error', reject);
    req.setTimeout(TEST_TIMEOUT, () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });
    
    if (options.body) {
      req.write(options.body);
    }
    req.end();
  });
}

async function testEndpoint(name, url, options = {}) {
  try {
    log(`Testing ${name}...`, 'blue');
    const response = await makeRequest(url, options);
    
    if (response.statusCode >= 200 && response.statusCode < 400) {
      log(`✅ ${name}: SUCCESS (${response.statusCode})`, 'green');
      return true;
    } else {
      log(`❌ ${name}: FAILED (${response.statusCode})`, 'red');
      return false;
    }
  } catch (error) {
    log(`❌ ${name}: ERROR - ${error.message}`, 'red');
    return false;
  }
}

async function runTests() {
  log('🚀 Starting PetPlantr Frontend End-to-End Tests', 'bold');
  log('=' * 50, 'yellow');
  
  const tests = [
    // Frontend Pages
    { name: 'Home Page', url: `${BASE_URL}/` },
    { name: 'Upload Page', url: `${BASE_URL}/upload` },
    { name: 'Gallery Page', url: `${BASE_URL}/gallery` },
    { name: 'Dashboard Page', url: `${BASE_URL}/dashboard` },
    { name: 'Pricing Page', url: `${BASE_URL}/pricing` },
    
    // API Endpoints
    { name: 'Health API', url: `${BASE_URL}/api/health` },
    { name: '3D Viewer API', url: `${BASE_URL}/api/3d-viewer` },
    
    // POST endpoints with data
    {
      name: 'Analyze Pet API',
      url: `${BASE_URL}/api/analyze-pet`,
      options: {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          imageUrl: 'https://example.com/test-image.jpg',
          petType: 'dog'
        })
      }
    }
  ];
  
  let passedTests = 0;
  let totalTests = tests.length;
  
  for (const test of tests) {
    const passed = await testEndpoint(test.name, test.url, test.options);
    if (passed) passedTests++;
    await new Promise(resolve => setTimeout(resolve, 500)); // Small delay between tests
  }
  
  log('=' * 50, 'yellow');
  log(`📊 Test Results: ${passedTests}/${totalTests} tests passed`, 'bold');
  
  if (passedTests === totalTests) {
    log('🎉 ALL TESTS PASSED! Frontend is working perfectly!', 'green');
    process.exit(0);
  } else {
    log(`❌ ${totalTests - passedTests} tests failed`, 'red');
    process.exit(1);
  }
}

// Run tests
runTests().catch(error => {
  log(`💥 Test runner error: ${error.message}`, 'red');
  process.exit(1);
});
