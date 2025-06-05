"""
Real-ESRGAN Upscaler Module
Handles the NCNN-Vulkan backend for image upscaling
"""

import os
import asyncio
import subprocess
from pathlib import Path
from typing import List, Optional


class RealESRGANUpscaler:
    """Real-ESRGAN upscaler using NCNN-Vulkan backend"""
    
    def __init__(self):
        self.binary_path = Path("bin/realesrgan-ncnn-vulkan")
        self.models_path = Path("models")
        self.temp_path = Path("temp")
        
        # Ensure directories exist
        self.temp_path.mkdir(exist_ok=True)
        
        # Available models mapping
        self.model_mapping = {
            "realesrgan-x4plus": "realesrgan-x4plus",
            "realesrgan-x4plus-anime": "realesrgan-x4plus-anime", 
            "realesr-animevideov3": "realesr-animevideov3-x4",
            "realesrnet-x4plus": "realesrnet-x4plus"
        }
    
    def check_binary(self) -> bool:
        """Check if Real-ESRGAN binary exists and is executable"""
        return self.binary_path.exists() and os.access(self.binary_path, os.X_OK)
    
    def check_models(self) -> bool:
        """Check if model files exist"""
        if not self.models_path.exists():
            return False
        
        # Check for at least one complete model (bin + param files)
        model_files = list(self.models_path.glob("*.bin"))
        return len(model_files) > 0
    
    def list_models(self) -> List[str]:
        """List available models"""
        if not self.models_path.exists():
            return []
        
        available_models = []
        for model_name in self.model_mapping.keys():
            bin_file = self.models_path / f"{self.model_mapping[model_name]}.bin"
            param_file = self.models_path / f"{self.model_mapping[model_name]}.param"
            
            if bin_file.exists() and param_file.exists():
                available_models.append(model_name)
        
        return available_models
    
    async def upscale(
        self,
        input_path: str,
        output_path: str,
        scale: int = 4,
        model: Optional[str] = "realesrgan-x4plus",
        tile_size: int = 512
    ) -> bool:
        """
        Upscale image using Real-ESRGAN NCNN-Vulkan
        
        Args:
            input_path: Path to input image
            output_path: Path for output image
            scale: Scale factor (2, 4, or 8)
            model: Model name to use
            tile_size: Tile size for processing (lower = less memory)
        
        Returns:
            bool: Success status
        """
        
        if not self.check_binary():
            raise Exception("Real-ESRGAN binary not found or not executable")
        
        # Validate model
        if model not in self.model_mapping:
            model = "realesrgan-x4plus"  # Default fallback
        
        model_name = self.model_mapping[model]
        
        # Check if model files exist
        bin_file = self.models_path / f"{model_name}.bin"
        param_file = self.models_path / f"{model_name}.param"
        
        if not (bin_file.exists() and param_file.exists()):
            raise Exception(f"Model files not found for {model}")
        
        # Handle different scales
        if scale == 2:
            # Use 4x model and resize down
            actual_scale = 4
            resize_after = True
            final_scale = 2
        elif scale == 8:
            # Use 4x model and resize up  
            actual_scale = 4
            resize_after = True
            final_scale = 8
        else:
            actual_scale = scale
            resize_after = False
            final_scale = scale
        
        # Build command for Real-ESRGAN NCNN-Vulkan
        cmd = [
            str(self.binary_path),
            "-i", input_path,
            "-o", output_path if not resize_after else output_path.replace('.png', '_temp.png'),
            "-s", str(actual_scale),
            "-t", str(tile_size),
            "-m", str(self.models_path),
            "-n", model_name,
            "-j", "1:2:1",  # Low memory configuration: 1 load thread, 2 proc threads, 1 save thread
            "-f", "png"     # Force PNG output
        ]
        
        try:
            # Run Real-ESRGAN process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise Exception(f"Real-ESRGAN process failed: {error_msg}")
            
            # Handle post-processing for 2x and 8x scales
            if resize_after:
                temp_output = output_path.replace('.png', '_temp.png')
                await self._resize_image(temp_output, output_path, final_scale / actual_scale)
                # Clean up temp file
                if os.path.exists(temp_output):
                    os.remove(temp_output)
            
            # Verify output file exists
            return os.path.exists(output_path)
            
        except Exception as e:
            raise Exception(f"Upscaling failed: {str(e)}")
    
    async def _resize_image(self, input_path: str, output_path: str, scale_factor: float):
        """Resize image using PIL for 2x/8x scaling"""
        from PIL import Image
        
        with Image.open(input_path) as img:
            new_width = int(img.width * scale_factor)
            new_height = int(img.height * scale_factor)
            
            # Use high-quality resampling
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            resized.save(output_path, 'PNG')
    
    def get_memory_usage_estimate(self, image_width: int, image_height: int, scale: int) -> dict:
        """Estimate memory usage for processing"""
        
        # Base memory for model and processing
        base_memory_mb = 800  # NCNN-Vulkan base memory
        
        # Memory per pixel (rough estimate)
        pixels = image_width * image_height
        memory_per_pixel = 0.000008  # ~8 bytes per pixel
        
        processing_memory_mb = pixels * memory_per_pixel * scale * scale
        
        total_memory_mb = base_memory_mb + processing_memory_mb
        
        return {
            "base_memory_mb": base_memory_mb,
            "processing_memory_mb": round(processing_memory_mb, 1),
            "total_estimated_mb": round(total_memory_mb, 1),
            "recommended_tile_size": 512 if total_memory_mb > 2000 else 0
        }
