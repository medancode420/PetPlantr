import os
import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
try:
    import torch
    from torchvision import transforms
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import replicate
    REPLICATE_AVAILABLE = True
except ImportError:
    REPLICATE_AVAILABLE = False

from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="PetPlantr AI API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["*"], allow_headers=["*"])

# Secure Replicate client
if REPLICATE_AVAILABLE:
    replicate_client = replicate.Client(api_token=os.getenv("REPLICATE_API_TOKEN"))
else:
    replicate_client = None

# Breed detection model setup (lazy loading)
model = None
transform = None

def load_ml_model():
    """Load the ML model on demand"""
    global model, transform
    if model is None:
        try:
            model = torch.hub.load('pytorch/vision:v0.10.0', 'resnet18', pretrained=True)
            model.eval()
            transform = transforms.Compose([
                transforms.Resize(256), transforms.CenterCrop(224),
                transforms.ToTensor(), transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
            ])
        except Exception as e:
            print(f"Warning: Could not load ML model: {e}")
            return False
    return True

breed_map = {281: "cat", 243: "dog"}  # Placeholder; expand with ImageNet pet classes or custom dataset

@app.post("/upload-pet-photo/")
async def process_pet_photo(file: UploadFile = File(...)):
    if not file or not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "Invalid image file")

    contents = await file.read()
    try:
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(400, "Invalid image format")

    breed = "unknown_pet"  # Default fallback

    # Breed detection with fallback
    if TORCH_AVAILABLE and load_ml_model() and model and transform:
        try:
            input_tensor = transform(image).unsqueeze(0)
            with torch.no_grad():
                outputs = model(input_tensor)
                _, predicted = outputs.max(1)
                breed = breed_map.get(predicted.item(), "unknown_pet")
        except Exception:
            pass  # Use default breed

    # Generate personalized planter via Replicate
    prompt = f"3D printable planter inspired by {breed}, magical pet ears and fur patterns, ultra-realistic, printable STL style"

    if REPLICATE_AVAILABLE and replicate_client:
        try:
            output = replicate_client.run(
                "stability-ai/stable-diffusion:27b93a2413e7f36cd83da926f3656280b2931564ff050bf9575f1fdf9bcd7478",
                input={"prompt": prompt, "num_inference_steps": 30}
            )
            # Handle different output formats
            if isinstance(output, list) and len(output) > 0:
                image_url = output[0]
            else:
                image_url = str(output)

            return {"breed": breed, "planter_image": image_url, "stl_url": f"/assets/{breed}_planter.stl"}
        except Exception as e:
            # Fallback to mock response
            pass

    # Mock response when AI services unavailable
    return {
        "breed": breed,
        "planter_image": f"https://via.placeholder.com/512x512?text={breed.replace(' ', '+')}+Planter",
        "stl_url": f"/assets/{breed}_planter.stl",
        "note": "AI generation unavailable - using placeholder"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting PetPlantr API server...")
    print("📡 Server will be available at:")
    print("   - http://localhost:8000")
    print("   - http://127.0.0.1:8000")
    print("📖 API documentation at: http://localhost:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)
