from batch_inference import BatchInferenceEngine
from flask import Flask, request, jsonify
import json
from PIL import Image
import io

app = Flask(__name__)
engine = BatchInferenceEngine()

@app.route('/infer/batch', methods=['POST'])
def infer_batch():
    """Batch inference endpoint for multiple images"""

    try:
        # Get images from request
        if 'images' not in request.files:
            return jsonify({"error": "No images provided"}), 400

        files = request.files.getlist('images')
        images = []

        for file in files:
            if file.filename == '':
                continue
            # Read image from file
            img = Image.open(io.BytesIO(file.read())).convert('RGB')
            images.append(img)

        if not images:
            return jsonify({"error": "No valid images provided"}), 400

        # Run batch inference
        result = engine.infer_batch(images)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting batch inference API server...")
    print("📍 Endpoint: http://localhost:5000/infer/batch")
    print("📋 Usage: POST /infer/batch with 'images' form files")
    app.run(host='0.0.0.0', port=5000, debug=True)
