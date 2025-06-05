"""
Real-ESRGAN Upscaler Module
Handles both NCNN-Vulkan backend and Python fallback for image upscaling
"""

import os
import asyncio
import subprocess
from pathlib import Path
from typing import List, Optional
import tempfile


class RealESRGANUpscaler:
    """Real-ESRGAN upscaler with NCNN-Vulkan backend and Python fallback"""
    
    def __init__(self):
        self.binary_path = Path("bin/realesrgan-ncnn-vulkan")
        self.models_path = Path("models")
        self.temp_path = Path("temp")
        
        # Check if we have NCNN binary or should use Python version
        self.use_python_version = not self.check_binary()
        
        # Ensure directories exist
        self.temp_path.mkdir(exist_ok=True)
        
        # Available models mapping
        self.model_mapping = {
            "realesrgan-x4plus": "realesrgan-x4plus",
            "realesrgan-x4plus-anime": "realesrgan-x4plus-anime", 
            "realesr-animevideov3": "realesr-animevideov3-x4",
            "realesrnet-x4plus": "realesrnet-x4plus"
        }
        
        # Initialize Python version if needed
        if self.use_python_version:
            self._init_python_version()
    
    def _init_python_version(self):
        """Initialize Python-based Real-ESRGAN"""
        try:
            global RealESRGANer, RRDBNet
            from realesrgan import RealESRGANer
            from realesrgan.archs.rrdbnet_arch import RRDBNet
            self.python_available = True
            self.python_upscaler = None
        except ImportError:
            self.python_available = False
            print("Warning: Python Real-ESRGAN not available, API will have limited functionality")
    
    def check_binary(self) -> bool:
        """Check if Real-ESRGAN binary exists and is executable"""
        return self.binary_path.exists() and os.access(self.binary_path, os.X_OK)
    
    def check_models(self) -> bool:
        """Check if model files exist"""
        if self.use_python_version:
            return self.python_available
        
        if not self.models_path.exists():
            return False
        
        # Check for at least one complete model (bin + param files)
        model_files = list(self.models_path.glob("*.bin"))
        return len(model_files) > 0
    
    def list_models(self) -> List[str]:
        """List available models"""
        if self.use_python_version:
            return ["realesrgan-x4plus", "realesrnet-x4plus"] if self.python_available else []
        
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
        Upscale image using Real-ESRGAN (NCNN-Vulkan or Python version)
        
        Args:
            input_path: Path to input image
            output_path: Path for output image
            scale: Scale factor (2, 4, or 8)
            model: Model name to use
            tile_size: Tile size for processing (lower = less memory)
        
        Returns:
            bool: Success status
        """
        
        if self.use_python_version:
            return await self._upscale_python(input_path, output_path, scale, model)
        else:
            return await self._upscale_ncnn(input_path, output_path, scale, model, tile_size)
    
    async def _upscale_python(
        self,
        input_path: str,
        output_path: str,
        scale: int,
        model: str
    ) -> bool:
        """Upscale using Python Real-ESRGAN"""
        
        if not self.python_available:
            raise Exception("Python Real-ESRGAN not available")
        
        try:
            # Initialize upscaler if needed
            if self.python_upscaler is None:
                # Select model based on request
                if "anime" in model.lower():
                    model_name = "RealESRGAN_x4plus_anime_6B"
                    netscale = 4
                else:
                    model_name = "RealESRGAN_x4plus"
                    netscale = 4
                
                # Create model
                model_net = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=netscale)
                
                # Initialize upscaler
                self.python_upscaler = RealESRGANer(
                    scale=netscale,
                    model_path=f'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/{model_name}.pth',
                    model=model_net,
                    tile=400,  # Use tiling for memory efficiency
                    tile_pad=10,
                    pre_pad=0,
                    half=True  # Use half precision to save memory
                )
            
            # Run upscaling in thread pool to avoid blocking
            import asyncio
            from concurrent.futures import ThreadPoolExecutor
            
            def process_image():
                from PIL import Image
                import cv2
                import numpy as np
                
                # Read image
                img = cv2.imread(input_path, cv2.IMREAD_COLOR)
                
                # Process with Real-ESRGAN
                output, _ = self.python_upscaler.enhance(img, outscale=scale/4)
                
                # Handle different scales
                if scale != 4:
                    from PIL import Image
                    pil_img = Image.fromarray(cv2.cvtColor(output, cv2.COLOR_BGR2RGB))
                    
                    if scale == 2:
                        new_size = (pil_img.width // 2, pil_img.height // 2)
                    elif scale == 8:
                        new_size = (pil_img.width * 2, pil_img.height * 2)
                    else:
                        new_size = (pil_img.width, pil_img.height)
                    
                    pil_img = pil_img.resize(new_size, Image.Resampling.LANCZOS)
                    output = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                
                # Save result
                cv2.imwrite(output_path, output)
                return True
            
            # Run in thread pool
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(process_image)
                result = await asyncio.get_event_loop().run_in_executor(None, future.result)
                return result
                
        except Exception as e:
            raise Exception(f"Python upscaling failed: {str(e)}")
    
    async def _upscale_ncnn(
        self,
        input_path: str,
        output_path: str,
        scale: int,
        model: str,
        tile_size: int
    ) -> bool:
        """Upscale using NCNN-Vulkan binary"""
        
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
            actual_scale = 4
            resize_after = True
            final_scale = 2
        elif scale == 8:
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
            "-j", "1:2:1",  # Low memory configuration
            "-f", "png"
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
        
        if self.use_python_version:
            # Python version uses more memory but is more predictable
            base_memory_mb = 1200
            pixels = image_width * image_height
            memory_per_pixel = 0.000012  # ~12 bytes per pixel for Python version
        else:
            # NCNN version uses less memory
            base_memory_mb = 800
            pixels = image_width * image_height  
            memory_per_pixel = 0.000008  # ~8 bytes per pixel
        
        processing_memory_mb = pixels * memory_per_pixel * scale * scale
        total_memory_mb = base_memory_mb + processing_memory_mb
        
        return {
            "base_memory_mb": base_memory_mb,
            "processing_memory_mb": round(processing_memory_mb, 1),
            "total_estimated_mb": round(total_memory_mb, 1),
            "backend": "python" if self.use_python_version else "ncnn-vulkan",
            "recommended_tile_size": 400 if self.use_python_version else 512
        }
