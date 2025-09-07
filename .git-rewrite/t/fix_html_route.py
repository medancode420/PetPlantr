# Add this to your FastAPI app to serve the HTML viewer directly

from fastapi import FastAPI
from fastapi.responses import FileResponse
import os

# Add this route to your existing FastAPI app
@app.get("/viewer")
@app.get("/model-viewer") 
async def serve_model_viewer():
    """Serve the 3D model viewer HTML file"""
    html_path = os.path.join(os.getcwd(), "3d_model_viewer.html")
    if os.path.exists(html_path):
        return FileResponse(html_path, media_type="text/html")
    else:
        raise HTTPException(status_code=404, detail="Model viewer not found")

