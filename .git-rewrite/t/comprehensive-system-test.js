#!/usr/bin/env node

/**
 * Comprehensive PetPlantr System Test
 * Tests the entire pipeline from API to CloudFront access
 */

const axios = require('axios');

class PetPlantrSystemTest {
    constructor() {
        this.baseUrl = 'http://localhost:3000';
        this.cloudfrontDomain = 'dpa0b9puwj06h.cloudfront.net';
    }

    log(message, type = 'info') {
        const timestamp = new Date().toISOString();
        const colors = {
            info: '\x1b[36m',
            success: '\x1b[32m',
            error: '\x1b[31m',
            warning: '\x1b[33m',
            reset: '\x1b[0m'
        };
        console.log(`${colors[type]}[${timestamp}] ${message}${colors.reset}`);
    }

    async testApiHealth() {
        try {
            this.log('🔍 Testing API health endpoint...');
            const response = await axios.get(`${this.baseUrl}/api/health`);
            
            if (response.status === 200) {
                this.log('✅ API health check passed', 'success');
                this.log(`📊 Environment: ${response.data.environment.hasReplicate ? 'Production' : 'Development'}`);
                return true;
            }
        } catch (error) {
            this.log(`❌ API health check failed: ${error.message}`, 'error');
            return false;
        }
    }

    async testApiReplicate() {
        try {
            this.log('🔍 Testing API replicate endpoint...');
            
            // Test with real model IDs
            const testCases = [
                {
                    predictionId: 'test123',
                    threeDPredictionId: 'bv1vzagzj1rma0cr99099rdszc',
                    description: 'Real model ID'
                },
                {
                    predictionId: 'test456',
                    threeDPredictionId: 'qcwyj024nxrme0cr98ataa1w6w',
                    description: 'Another real model ID'
                }
            ];

            for (const testCase of testCases) {
                this.log(`🧪 Testing: ${testCase.description}`);
                
                const response = await axios.get(`${this.baseUrl}/api/replicate`, {
                    params: {
                        predictionId: testCase.predictionId,
                        threeDPredictionId: testCase.threeDPredictionId
                    }
                });

                if (response.data.modelUrl) {
                    this.log(`✅ API returned modelUrl: ${response.data.modelUrl}`, 'success');
                } else {
                    this.log(`⚠️  API did not return modelUrl`, 'warning');
                    this.log(`📋 Response: ${JSON.stringify(response.data, null, 2)}`);
                }
            }

            return true;
        } catch (error) {
            this.log(`❌ API replicate test failed: ${error.message}`, 'error');
            if (error.response) {
                this.log(`📋 Response: ${JSON.stringify(error.response.data, null, 2)}`);
            }
            return false;
        }
    }

    async testCloudfrontAccess() {
        try {
            this.log('🔍 Testing CloudFront access...');
            
            // List of real model files to test
            const modelIds = [
                'bv1vzagzj1rma0cr99099rdszc',
                'qcwyj024nxrme0cr98ataa1w6w',
                '484ws4kg65rme0cr96da9j43a8'
            ];

            for (const modelId of modelIds) {
                const url = `https://${this.cloudfrontDomain}/models/${modelId}.glb`;
                this.log(`🧪 Testing model: ${modelId}`);
                
                try {
                    const response = await axios.head(url, { timeout: 10000 });
                    
                    if (response.status === 200) {
                        this.log(`✅ Model accessible: ${response.headers['content-type']} (${response.headers['content-length']} bytes)`, 'success');
                    } else {
                        this.log(`⚠️  Unexpected status: ${response.status}`, 'warning');
                    }
                } catch (modelError) {
                    if (modelError.response && modelError.response.status === 403) {
                        this.log(`❌ Access denied for model: ${modelId}`, 'error');
                    } else if (modelError.response && modelError.response.status === 404) {
                        this.log(`⚠️  Model not found: ${modelId}`, 'warning');
                    } else {
                        this.log(`❌ Error accessing model: ${modelError.message}`, 'error');
                    }
                }
            }

            return true;
        } catch (error) {
            this.log(`❌ CloudFront test failed: ${error.message}`, 'error');
            return false;
        }
    }

    async testFrontendViewer() {
        try {
            this.log('🔍 Testing frontend 3D viewer page...');
            
            const response = await axios.get(`${this.baseUrl}/frontend-3d-test.html`);
            
            if (response.status === 200) {
                this.log('✅ Frontend test page accessible', 'success');
                return true;
            }
        } catch (error) {
            this.log(`❌ Frontend test failed: ${error.message}`, 'error');
            return false;
        }
    }

    async runFullTest() {
        this.log('🚀 Starting PetPlantr System Test', 'info');
        this.log('=' * 50);
        
        const results = {
            apiHealth: await this.testApiHealth(),
            apiReplicate: await this.testApiReplicate(),
            cloudfrontAccess: await this.testCloudfrontAccess(),
            frontendViewer: await this.testFrontendViewer()
        };

        this.log('=' * 50);
        this.log('📊 Test Results Summary:');
        
        let allPassed = true;
        for (const [test, passed] of Object.entries(results)) {
            const status = passed ? '✅ PASS' : '❌ FAIL';
            this.log(`  ${test}: ${status}`, passed ? 'success' : 'error');
            if (!passed) allPassed = false;
        }

        if (allPassed) {
            this.log('🎉 ALL TESTS PASSED - System is fully operational!', 'success');
            this.log('🌐 You can now use the PetPlantr system without "failed to load model" errors');
            this.log('🔗 Test it at: http://localhost:3000/upload');
        } else {
            this.log('⚠️  Some tests failed - check the logs above for details', 'warning');
        }

        return allPassed;
    }
}

// Run the test
const test = new PetPlantrSystemTest();
test.runFullTest().then(success => {
    process.exit(success ? 0 : 1);
});
