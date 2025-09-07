#!/usr/bin/env node

// Test the custom dog planter generation
const path = require('path');

async function testCustomGeneration() {
  console.log('🧪 Testing custom dog planter generation...');
  
  // Mock analysis data
  const mockAnalysis = {
    breed: 'Golden Retriever',
    confidence: 0.9,
    headShape: 'well-proportioned',
    earType: 'floppy',
    facialFeatures: 'friendly expression',
    bodyType: 'athletic',
    sizeClass: 'medium',
    primaryColor: '#D4AF37',
    markings: 'golden coat',
    facialMarkings: 'warm expression'
  };
  
  try {
    // Import the generator
    const { createBreedSpecificDogPlanterGLB } = require('./frontend/app/api/generate-enhanced-3d-simple/dog-planter-generator.ts');
    
    console.log('📦 Generating custom GLB...');
    const glbBuffer = await createBreedSpecificDogPlanterGLB(mockAnalysis);
    
    console.log(`✅ Generated ${glbBuffer.length} byte GLB file`);
    
    // Save test file
    const fs = require('fs');
    const testPath = 'frontend/public/generated/test-golden-retriever.glb';
    fs.writeFileSync(testPath, glbBuffer);
    
    console.log(`💾 Saved test file: ${testPath}`);
    console.log('🎉 Custom generation test successful!');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
}

testCustomGeneration();
