#!/bin/bash

# Immediate CORS Workaround: Use S3 Direct URLs
echo "⚡ Immediate CORS Workaround for 3D Model Loading"
echo "============================================="

echo "🔍 Problem:"
echo "  CloudFront CORS configuration taking time to propagate"
echo "  Need immediate solution for 3D model loading"
echo ""

echo "💡 Solution:"
echo "  Use S3 direct URLs temporarily (CORS working)"
echo "  Update frontend to use working endpoints"
echo ""

# Test S3 direct access first
echo "🧪 Testing S3 direct access..."
S3_RESPONSE=$(curl -s -H "Origin: http://localhost:3000" -o /dev/null -w "%{http_code}" "https://petplantr-3d-models-prod.s3.amazonaws.com/models/484ws4kg65rme0cr96da9j43a8.glb")

if [ "$S3_RESPONSE" = "200" ]; then
    echo "✅ S3 direct access working: HTTP $S3_RESPONSE"
    
    # Check CORS headers
    CORS_HEADER=$(curl -s -H "Origin: http://localhost:3000" -I "https://petplantr-3d-models-prod.s3.amazonaws.com/models/484ws4kg65rme0cr96da9j43a8.glb" | grep -i "access-control-allow-origin")
    
    if [[ -n "$CORS_HEADER" ]]; then
        echo "✅ CORS headers present: $CORS_HEADER"
        echo ""
        echo "🎯 Ready to implement workaround!"
        
        # Create a test HTML with S3 direct URLs
        cat > frontend/public/s3-direct-test.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>S3 Direct 3D Model Test</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
    <style>
        body { margin: 0; padding: 20px; font-family: Arial, sans-serif; background: #f0f0f0; }
        .container { max-width: 900px; margin: 0 auto; }
        .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; text-align: center; }
        .test-section { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .model-viewer { width: 100%; height: 400px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px; margin: 10px 0; }
        .log { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 4px; font-family: monospace; font-size: 12px; max-height: 200px; overflow-y: auto; }
        .success { color: #28a745; font-weight: bold; }
        .error { color: #dc3545; font-weight: bold; }
        .info { color: #17a2b8; }
        button { background: #28a745; color: white; border: none; padding: 12px 24px; border-radius: 6px; margin: 5px; cursor: pointer; transition: all 0.3s; }
        button:hover { background: #218838; transform: translateY(-1px); }
        .url-display { background: #e9ecef; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 12px; word-break: break-all; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ S3 Direct 3D Model Test</h1>
            <p><strong>CORS Workaround Solution</strong></p>
            <p>Using S3 direct URLs instead of CloudFront (temporary fix)</p>
        </div>
        
        <div class="test-section">
            <h2>🎯 Working Model URLs</h2>
            <div class="url-display">
                <strong>S3 Direct URL (CORS Working):</strong><br>
                https://petplantr-3d-models-prod.s3.amazonaws.com/models/484ws4kg65rme0cr96da9j43a8.glb
            </div>
            <div class="url-display">
                <strong>CloudFront URL (CORS Pending):</strong><br>
                https://dpa0b9puwj06h.cloudfront.net/models/484ws4kg65rme0cr96da9j43a8.glb
            </div>
        </div>

        <div class="test-section">
            <h2>🧪 CORS Headers Test</h2>
            <button onclick="testCORS()">Test CORS Headers</button>
            <div id="corsLog" class="log"></div>
        </div>

        <div class="test-section">
            <h2>🎮 3D Model Viewer (S3 Direct)</h2>
            <button onclick="loadModel()">Load 3D Model from S3 Direct</button>
            <div id="modelViewer" class="model-viewer"></div>
            <div id="modelLog" class="log"></div>
        </div>
    </div>

    <script>
        function log(containerId, message, type = 'info') {
            const container = document.getElementById(containerId);
            const timestamp = new Date().toLocaleTimeString();
            const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
            container.innerHTML += `<div class="${type}">[${timestamp}] ${icon} ${message}</div>`;
            container.scrollTop = container.scrollHeight;
        }

        async function testCORS() {
            const s3Url = 'https://petplantr-3d-models-prod.s3.amazonaws.com/models/484ws4kg65rme0cr96da9j43a8.glb';
            const cloudFrontUrl = 'https://dpa0b9puwj06h.cloudfront.net/models/484ws4kg65rme0cr96da9j43a8.glb';

            log('corsLog', 'Testing CORS headers on both endpoints...', 'info');

            // Test S3 direct
            try {
                const s3Response = await fetch(s3Url, { method: 'HEAD', mode: 'cors' });
                if (s3Response.ok) {
                    log('corsLog', `✅ S3 Direct: HTTP ${s3Response.status} - CORS Working!`, 'success');
                } else {
                    log('corsLog', `❌ S3 Direct: HTTP ${s3Response.status}`, 'error');
                }
            } catch (error) {
                log('corsLog', `❌ S3 Direct Error: ${error.message}`, 'error');
            }

            // Test CloudFront
            try {
                const cfResponse = await fetch(cloudFrontUrl, { method: 'HEAD', mode: 'cors' });
                if (cfResponse.ok) {
                    log('corsLog', `✅ CloudFront: HTTP ${cfResponse.status} - CORS Working!`, 'success');
                } else {
                    log('corsLog', `❌ CloudFront: HTTP ${cfResponse.status}`, 'error');
                }
            } catch (error) {
                log('corsLog', `❌ CloudFront Error: ${error.message}`, 'error');
            }
        }

        async function loadModel() {
            const modelUrl = 'https://petplantr-3d-models-prod.s3.amazonaws.com/models/484ws4kg65rme0cr96da9j43a8.glb';
            
            log('modelLog', `🎯 Loading 3D model from S3 direct: ${modelUrl}`, 'info');
            
            try {
                const container = document.getElementById('modelViewer');
                container.innerHTML = '';
                
                // Create Three.js scene
                const scene = new THREE.Scene();
                scene.background = new THREE.Color(0x222444);
                
                const camera = new THREE.PerspectiveCamera(75, container.offsetWidth / container.offsetHeight, 0.1, 1000);
                camera.position.set(5, 5, 5);
                camera.lookAt(0, 0, 0);
                
                const renderer = new THREE.WebGLRenderer({ antialias: true });
                renderer.setSize(container.offsetWidth, container.offsetHeight);
                container.appendChild(renderer.domElement);
                
                // Lighting
                const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
                scene.add(ambientLight);
                
                const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
                directionalLight.position.set(10, 10, 5);
                scene.add(directionalLight);
                
                // Load model
                const loader = new THREE.GLTFLoader();
                
                log('modelLog', '📦 Starting GLB load from S3 direct...', 'info');
                
                loader.load(
                    modelUrl,
                    (gltf) => {
                        log('modelLog', '🎉 SUCCESS! 3D model loaded from S3 direct!', 'success');
                        
                        const model = gltf.scene;
                        
                        // Center and scale
                        const box = new THREE.Box3().setFromObject(model);
                        const center = box.getCenter(new THREE.Vector3());
                        const size = box.getSize(new THREE.Vector3());
                        
                        model.position.copy(center).multiplyScalar(-1);
                        
                        const maxDim = Math.max(size.x, size.y, size.z);
                        if (maxDim > 0) {
                            model.scale.setScalar(3 / maxDim);
                        }
                        
                        scene.add(model);
                        
                        // Animate
                        function animate() {
                            requestAnimationFrame(animate);
                            model.rotation.y += 0.01;
                            renderer.render(scene, camera);
                        }
                        animate();
                        
                        log('modelLog', '🎬 3D model is now rotating and visible!', 'success');
                        log('modelLog', '💡 S3 Direct URLs work perfectly for 3D models!', 'success');
                    },
                    (progress) => {
                        if (progress.lengthComputable) {
                            const percent = (progress.loaded / progress.total * 100).toFixed(1);
                            log('modelLog', `📥 Loading: ${percent}%`, 'info');
                        }
                    },
                    (error) => {
                        log('modelLog', `❌ Load failed: ${error}`, 'error');
                        console.error('Load error:', error);
                    }
                );
                
            } catch (error) {
                log('modelLog', `❌ Setup failed: ${error.message}`, 'error');
            }
        }

        // Auto-test CORS on load
        window.onload = () => {
            setTimeout(testCORS, 1000);
        };
    </script>
</body>
</html>
EOF
        
        echo "✅ Created S3 direct test page: frontend/public/s3-direct-test.html"
        echo ""
        echo "🎯 Immediate Actions:"
        echo "  1. Test S3 direct URL: http://localhost:3000/s3-direct-test.html"
        echo "  2. Update frontend to use S3 direct URLs temporarily"
        echo "  3. Switch back to CloudFront once CORS propagates"
        echo ""
        echo "🔗 Working S3 URLs:"
        echo "  Base: https://petplantr-3d-models-prod.s3.amazonaws.com/models/"
        echo "  Test: https://petplantr-3d-models-prod.s3.amazonaws.com/models/484ws4kg65rme0cr96da9j43a8.glb"
        
    else
        echo "❌ CORS headers missing from S3"
    fi
else
    echo "❌ S3 direct access failed: HTTP $S3_RESPONSE"
fi

echo ""
echo "✨ Workaround ready! Test the S3 direct URL approach."
