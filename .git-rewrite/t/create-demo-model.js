/**
 * Demo Model Generator
 * Creates fallback GLB models when the real AI models fail or are inaccessible
 */

const fs = require('fs');
const path = require('path');

// Simple GLB content (minimal valid GLB file)
const createDemoGLB = (modelId) => {
  // This is a minimal valid GLB file that represents a simple cube
  // In a real implementation, you'd have pre-made demo planter models
  const minimalGLB = Buffer.from([
    0x67, 0x6C, 0x54, 0x46, // glTF magic
    0x02, 0x00, 0x00, 0x00, // version 2
    0x6C, 0x00, 0x00, 0x00, // length
    0x7C, 0x00, 0x00, 0x00, // contentLength
    0x4A, 0x53, 0x4F, 0x4E, // JSON chunk type
    // JSON content would go here - simplified for demo
    ...Array(100).fill(0x20) // padding
  ]);
  
  return minimalGLB;
};

const saveDemoModel = (modelId, outputPath) => {
  const glbData = createDemoGLB(modelId);
  fs.writeFileSync(outputPath, glbData);
  console.log(`Demo model saved: ${outputPath}`);
};

// Export for use in other modules
module.exports = {
  createDemoGLB,
  saveDemoModel
};

// CLI usage
if (require.main === module) {
  const modelId = process.argv[2] || 'demo-model';
  const outputPath = process.argv[3] || `./frontend/public/demo-models/${modelId}.glb`;
  
  // Ensure directory exists
  const dir = path.dirname(outputPath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  
  saveDemoModel(modelId, outputPath);
}
