"""
Real-ESRGAN API - FastAPI application for image upscaling
Optimized for low memory VPS using NCNN-Vulkan backend
"""

import os
import uuid
import base64
from io import BytesIO
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image

from app.upscaler import RealESRGANUpscaler

# Initialize FastAPI app
app = FastAPI(
    title="Real-ESRGAN API",
    description="AI Image Upscaling API using Real-ESRGAN NCNN-Vulkan",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize upscaler
upscaler = RealESRGANUpscaler()

# Ensure temp directory exists
Path("temp").mkdir(exist_ok=True)


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "message": "Real-ESRGAN API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "upscale": "/upscale",
            "health": "/health",
            "models": "/models"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if upscaler binary exists
        binary_exists = upscaler.check_binary()
        models_exist = upscaler.check_models()
        
        return {
            "status": "healthy" if binary_exists and models_exist else "unhealthy",
            "binary_available": binary_exists,
            "models_available": models_exist,
            "supported_scales": [2, 4, 8],
            "max_file_size": "2MB"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.get("/models")
async def get_available_models():
    """Get list of available models"""
    try:
        models = upscaler.list_models()
        return {
            "models": models,
            "default_model": "realesrgan-x4plus",
            "supported_scales": [2, 4, 8]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upscale")
async def upscale_image(
    file: UploadFile = File(...),
    scale: int = Form(4),
    model: Optional[str] = Form("realesrgan-x4plus")
):
    """
    Upscale image using Real-ESRGAN
    
    Args:
        file: Image file (jpg, png, webp) - max 2MB
        scale: Upscale factor (2, 4, or 8)
        model: Model to use (optional)
    
    Returns:
        JSON with base64 encoded upscaled image
    """
    
    # Validate inputs
    if scale not in [2, 4, 8]:
        raise HTTPException(status_code=400, detail="Scale must be 2, 4, or 8")
    
    if file.size > 2 * 1024 * 1024:  # 2MB limit
        raise HTTPException(status_code=413, detail="File too large. Max size: 2MB")
    
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    input_path = f"temp/input_{file_id}.png"
    output_path = f"temp/output_{file_id}.png"
    
    try:
        # Save uploaded file
        content = await file.read()
        
        # Convert to PNG for processing
        image = Image.open(BytesIO(content))
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        image.save(input_path, 'PNG')
        
        # Process with Real-ESRGAN
        success = await upscaler.upscale(
            input_path=input_path,
            output_path=output_path,
            scale=scale,
            model=model
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Upscaling failed")
        
        # Read result and encode to base64
        with open(output_path, 'rb') as f:
            result_bytes = f.read()
        
        base64_result = base64.b64encode(result_bytes).decode('utf-8')
        
        # Get output image info
        output_image = Image.open(output_path)
        
        return {
            "success": True,
            "original_size": f"{image.width}x{image.height}",
            "upscaled_size": f"{output_image.width}x{output_image.height}",
            "scale_used": scale,
            "model_used": model,
            "format": "PNG",
            "base64_image": base64_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    
    finally:
        # Cleanup temporary files
        for path in [input_path, output_path]:
            if os.path.exists(path):
                os.remove(path)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
