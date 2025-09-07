#!/usr/bin/env node

// Debug script to isolate the test issues
const PerformanceMonitor = require('./performance-test.js');

async function debugTests() {
    const monitor = new PerformanceMonitor();
    
    console.log('Testing individual methods...');
    
    try {
        // Test each method individually
        const tests = [
            { name: 'Frontend Build', method: 'testFrontendBuild' },
            { name: 'Frontend Dev', method: 'testFrontendDev' },
            { name: 'Backend Build', method: 'testBackendBuild' },
            { name: 'Backend Tests', method: 'testBackendTests' },
            { name: 'TypeScript Compilation', method: 'testTypeScriptCompilation' },
            { name: 'AI Model Inference', method: 'testAIModelInference' },
            { name: 'Memory Usage', method: 'testMemoryUsage' },
            { name: 'System Resources', method: 'testSystemResources' },
            { name: 'Proprietary Photo Collection', method: 'testProprietaryPhotoCollection' },
            { name: 'S3 Object Existence', method: 'testS3ObjectExistence' },
            { name: 'Production Readiness', method: 'testProductionReadiness' },
            { name: 'DNS Connection', method: 'testDNSConnection' },
            { name: 'Microsoft Graph Email', method: 'testMicrosoftGraphEmail' }
        ];
        
        for (const test of tests) {
            console.log(`\n=== Testing ${test.name} ===`);
            try {
                const result = await monitor[test.method]();
                console.log(`Result name: "${result.name}"`);
                console.log(`Success: ${result.success}`);
                if (result.error) {
                    console.log(`Error: ${result.error}`);
                }
            } catch (error) {
                console.log(`Method ${test.method} threw error:`, error.message);
            }
        }
        
    } catch (error) {
        console.error('Debug test failed:', error);
    }
}

debugTests();
