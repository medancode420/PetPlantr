#!/usr/bin/env node

// Live Model URL Diagnostics
// This script will test the specific model URL that's failing

// Use built-in fetch (Node 18+)

console.log('🔍 LIVE MODEL URL DIAGNOSTICS');
console.log('=============================');
console.log('📅 Test Date:', new Date().toISOString());

// Test different possible model URLs
const testUrls = [
    // Common prediction IDs that might be in use
    'https://dpa0b9puwj06h.cloudfront.net/models/484ws4kg65rme0cr96da9j43a8.glb',
    'https://dpa0b9puwj06h.cloudfront.net/models/test-prediction-id.glb',
    'https://dpa0b9puwj06h.cloudfront.net/models/latest.glb',
    'https://dpa0b9puwj06h.cloudfront.net/models/demo.glb',
    'https://dpa0b9puwj06h.cloudfront.net/models/min-pin.glb',
    'https://dpa0b9puwj06h.cloudfront.net/models/dog-planter.glb',
];

async function testModelUrl(url) {
    try {
        console.log(`\n🧪 Testing: ${url}`);
        
        const response = await fetch(url, {
            method: 'HEAD',
            headers: {
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'content-type'
            }
        });

        console.log(`📊 Status: ${response.status} ${response.statusText}`);
        
        if (response.status === 200) {
            console.log('✅ Model file exists and accessible');
            
            // Check CORS headers
            const corsOrigin = response.headers.get('access-control-allow-origin');
            const corsMethods = response.headers.get('access-control-allow-methods');
            const corsHeaders = response.headers.get('access-control-allow-headers');
            const corsExposeHeaders = response.headers.get('access-control-expose-headers');
            const contentType = response.headers.get('content-type');
            const contentLength = response.headers.get('content-length');
            
            console.log('🔒 CORS Headers:');
            console.log(`   access-control-allow-origin: ${corsOrigin || 'NOT SET'}`);
            console.log(`   access-control-allow-methods: ${corsMethods || 'NOT SET'}`);
            console.log(`   access-control-expose-headers: ${corsExposeHeaders || 'NOT SET'}`);
            console.log('📦 Content Info:');
            console.log(`   content-type: ${contentType || 'NOT SET'}`);
            console.log(`   content-length: ${contentLength || 'NOT SET'} bytes`);
            
            if (corsOrigin && corsOrigin.includes('*')) {
                console.log('✅ CORS: Properly configured');
            } else {
                console.log('❌ CORS: Missing or restrictive');
            }
            
        } else if (response.status === 404) {
            console.log('❌ Model file not found (404)');
        } else if (response.status === 403) {
            console.log('❌ Access denied (403) - Check permissions');
        } else {
            console.log(`❌ HTTP Error: ${response.status}`);
        }
        
        return {
            url,
            status: response.status,
            accessible: response.status === 200,
            corsConfigured: response.headers.get('access-control-allow-origin') === '*'
        };
        
    } catch (error) {
        console.log(`❌ Network Error: ${error.message}`);
        return {
            url,
            status: 'ERROR',
            accessible: false,
            corsConfigured: false,
            error: error.message
        };
    }
}

async function findWorkingModels() {
    console.log('\n🎯 Testing Common Model URLs...\n');
    
    const results = [];
    
    for (const url of testUrls) {
        const result = await testModelUrl(url);
        results.push(result);
        
        // Small delay to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    console.log('\n📋 SUMMARY REPORT');
    console.log('=================');
    
    const working = results.filter(r => r.accessible);
    const withCors = results.filter(r => r.corsConfigured);
    
    console.log(`✅ Working models: ${working.length}/${results.length}`);
    console.log(`🔒 CORS configured: ${withCors.length}/${results.length}`);
    
    if (working.length > 0) {
        console.log('\n✅ WORKING MODEL URLS:');
        working.forEach(result => {
            console.log(`   📍 ${result.url}`);
        });
    }
    
    if (working.length === 0) {
        console.log('\n❌ NO WORKING MODELS FOUND');
        console.log('This suggests either:');
        console.log('1. Model files have not been uploaded to S3 yet');
        console.log('2. Different prediction IDs are being used');
        console.log('3. Models are in a different S3 path structure');
        console.log('\n💡 NEXT STEPS:');
        console.log('1. Check what prediction ID is being used in the UI');
        console.log('2. Verify if models are being uploaded to S3');
        console.log('3. Check the exact model URL being generated');
    }
}

findWorkingModels().catch(console.error);
