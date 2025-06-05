"""
Real-ESRGAN API - FastAPI application for image upscaling
Optimized for low memory VPS with multiple fallback backends
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

from app.upscaler_simple import RealESRGANUpscaler

# Initialize FastAPI app
app = FastAPI(
    title="Real-ESRGAN API",
    description="AI Image Upscaling API using Real-ESRGAN (Multiple backends with fallbacks)",
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
    backend_info = upscaler.get_memory_usage_estimate(512, 512, 4)
    return {
        "message": "Real-ESRGAN API",
        "version": "1.0.0",
        "status": "running",
        "backend": backend_info["backend"],
        "backend_quality": backend_info.get("quality", "unknown"),
        "endpoints": {
            "upscale": "/upscale",
            "health": "/health",
            "models": "/models",
            "status": "/status"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if upscaler is available
        models_exist = upscaler.check_models()
        backend_info = upscaler.get_memory_usage_estimate(512, 512, 4)
        
        status = "healthy" if models_exist else "degraded"
        if upscaler.active_backend == "none":
            status = "error"
        
        return {
            "status": status,
            "backend": upscaler.active_backend,
            "backend_quality": backend_info.get("quality", "unknown"),
            "models_available": models_exist,
            "available_backends": {
                "realesrgan": upscaler.backends.get('realesrgan', {}).get('available', False),
                "ncnn": upscaler.backends.get('ncnn', {}).get('available', False),
                "pil": upscaler.backends.get('pil', {}).get('available', False)
            },
            "supported_scales": [2, 4, 8],
            "max_file_size": "2MB",
            "memory_efficient": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "backend": "unknown"
        }


@app.get("/models")
async def get_available_models():
    """Get list of available models"""
    try:
        models = upscaler.list_models()
        backend_info = upscaler.get_memory_usage_estimate(512, 512, 4)
        return {
            "models": models,
            "default_model": models[0] if models else "pil-lanczos",
            "supported_scales": [2, 4, 8],
            "backend": upscaler.active_backend,
            "backend_quality": backend_info.get("quality", "unknown")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upscale")
async def upscale_image(
    file: UploadFile = File(...),
    scale: int = Form(4),
    model: Optional[str] = Form(None)
):
    """
    Upscale image using Real-ESRGAN (multiple backends)
    
    Args:
        file: Image file (jpg, png, webp) - max 2MB
        scale: Upscale factor (2, 4, or 8)
        model: Model to use (optional, auto-selected based on backend)
    
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
        original_format = image.format
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        image.save(input_path, 'PNG')
        
        # Get memory estimate
        memory_info = upscaler.get_memory_usage_estimate(image.width, image.height, scale)
        
        # Process with Real-ESRGAN
        success = await upscaler.upscale(
            input_path=input_path,
            output_path=output_path,
            scale=scale,
            model=model
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=f"Upscaling failed with {upscaler.active_backend} backend")
        
        # Verify output exists
        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="Output file was not created")
        
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
            "model_used": model or f"{upscaler.active_backend}-default",
            "backend": upscaler.active_backend,
            "backend_quality": memory_info.get("quality", "unknown"),
            "format": "PNG",
            "memory_used_mb": memory_info["total_estimated_mb"],
            "original_format": original_format,
            "processing_info": {
                "backend": upscaler.active_backend,
                "tile_size": memory_info.get("recommended_tile_size"),
                "quality_level": memory_info.get("quality")
            },
            "base64_image": base64_result
        }
        
    except Exception as e:
        error_msg = str(e)
        if "Real-ESRGAN" in error_msg:
            error_msg += f" (Using {upscaler.active_backend} backend)"
        raise HTTPException(status_code=500, detail=f"Processing error: {error_msg}")
    
    finally:
        # Cleanup temporary files
        for path in [input_path, output_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass  # Ignore cleanup errors


@app.get("/status")
async def get_status():
    """Get detailed API status"""
    try:
        backend_info = upscaler.get_memory_usage_estimate(1024, 1024, 4)
        models = upscaler.list_models()
        
        return {
            "api_version": "1.0.0",
            "backend": {
                "active": upscaler.active_backend,
                "quality": backend_info.get("quality", "unknown"),
                "available_backends": {
                    "realesrgan": {
                        "available": upscaler.backends.get('realesrgan', {}).get('available', False),
                        "error": upscaler.backends.get('realesrgan', {}).get('error')
                    },
                    "ncnn": {
                        "available": upscaler.backends.get('ncnn', {}).get('available', False)
                    },
                    "pil": {
                        "available": upscaler.backends.get('pil', {}).get('available', False)
                    }
                }
            },
            "available_models": models,
            "supported_scales": [2, 4, 8],
            "max_file_size_mb": 2,
            "estimated_memory_usage": {
                "base_mb": backend_info["base_memory_mb"],
                "per_1024x1024_image_mb": backend_info["processing_memory_mb"],
                "recommended_tile_size": backend_info["recommended_tile_size"]
            },
            "features": {
                "base64_output": True,
                "multiple_scales": True,
                "memory_optimized": True,
                "auto_cleanup": True,
                "fallback_backends": True,
                "quality_level": backend_info.get("quality", "unknown")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug")
async def debug_info():
    """Debug endpoint to check what's available"""
    return {
        "active_backend": upscaler.active_backend,
        "backends": {
            name: {
                "available": info.get('available', False),
                "error": info.get('error', None)
            }
            for name, info in upscaler.backends.items()
        },
        "check_binary": upscaler.check_binary(),
        "check_models": upscaler.check_models(),
        "list_models": upscaler.list_models()
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
