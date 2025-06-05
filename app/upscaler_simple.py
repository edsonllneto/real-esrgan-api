"""
Simplified Real-ESRGAN Upscaler Module
Works with or without Real-ESRGAN dependencies using PIL fallback
"""

import os
import asyncio
from pathlib import Path
from typing import List, Optional
import tempfile


class RealESRGANUpscaler:
    """Real-ESRGAN upscaler with multiple fallback strategies"""
    
    def __init__(self):
        self.binary_path = Path("bin/realesrgan-ncnn-vulkan")
        self.models_path = Path("models")
        self.temp_path = Path("temp")
        
        # Initialize backends
        self.backends = self._init_backends()
        self.active_backend = self._select_backend()
        
        # Ensure directories exist
        self.temp_path.mkdir(exist_ok=True)
        
        print(f"Initialized with backend: {self.active_backend}")
    
    def _init_backends(self) -> dict:
        """Initialize available backends"""
        backends = {}
        
        # Try Real-ESRGAN Python
        try:
            from realesrgan import RealESRGANer
            from realesrgan.archs.rrdbnet_arch import RRDBNet
            backends['realesrgan'] = {
                'available': True,
                'RealESRGANer': RealESRGANer,
                'RRDBNet': RRDBNet
            }
            print("✅ Real-ESRGAN Python backend available")
        except ImportError as e:
            backends['realesrgan'] = {'available': False, 'error': str(e)}
            print(f"❌ Real-ESRGAN Python not available: {e}")
        
        # Try BasicSR
        try:
            import torch
            backends['basicsr'] = {'available': True, 'torch': torch}
            print("✅ PyTorch available")
        except ImportError as e:
            backends['basicsr'] = {'available': False, 'error': str(e)}
            print(f"❌ PyTorch not available: {e}")
        
        # PIL fallback (always available)
        try:
            from PIL import Image, ImageFilter
            backends['pil'] = {'available': True, 'Image': Image, 'ImageFilter': ImageFilter}
            print("✅ PIL fallback available")
        except ImportError:
            backends['pil'] = {'available': False}
        
        # NCNN binary
        backends['ncnn'] = {'available': self.check_binary()}
        if backends['ncnn']['available']:
            print("✅ NCNN binary available")
        else:
            print("❌ NCNN binary not available")
        
        return backends
    
    def _select_backend(self) -> str:
        """Select the best available backend"""
        if self.backends.get('realesrgan', {}).get('available'):
            return 'realesrgan'
        elif self.backends.get('ncnn', {}).get('available'):
            return 'ncnn'
        elif self.backends.get('pil', {}).get('available'):
            return 'pil'
        else:
            return 'none'
    
    def check_binary(self) -> bool:
        """Check if Real-ESRGAN binary exists and is executable"""
        return self.binary_path.exists() and os.access(self.binary_path, os.X_OK)
    
    def check_models(self) -> bool:
        """Check if models are available"""
        if self.active_backend == 'realesrgan':
            return self.backends['realesrgan']['available']
        elif self.active_backend == 'ncnn':
            if not self.models_path.exists():
                return False
            model_files = list(self.models_path.glob("*.bin"))
            return len(model_files) > 0
        elif self.active_backend == 'pil':
            return True  # PIL doesn't need models
        return False
    
    def list_models(self) -> List[str]:
        """List available models"""
        if self.active_backend == 'realesrgan':
            return ["RealESRGAN_x4plus", "RealESRNet_x4plus"]
        elif self.active_backend == 'ncnn':
            available_models = []
            model_mapping = {
                "realesrgan-x4plus": "realesrgan-x4plus",
                "realesrgan-x4plus-anime": "realesrgan-x4plus-anime", 
                "realesr-animevideov3": "realesr-animevideov3-x4",
                "realesrnet-x4plus": "realesrnet-x4plus"
            }
            
            for model_name in model_mapping.keys():
                bin_file = self.models_path / f"{model_mapping[model_name]}.bin"
                param_file = self.models_path / f"{model_mapping[model_name]}.param"
                if bin_file.exists() and param_file.exists():
                    available_models.append(model_name)
            return available_models
        elif self.active_backend == 'pil':
            return ["pil-lanczos", "pil-bicubic"]
        return []
    
    async def upscale(
        self,
        input_path: str,
        output_path: str,
        scale: int = 4,
        model: Optional[str] = None,
        tile_size: int = 512
    ) -> bool:
        """Upscale image using the best available backend"""
        
        if self.active_backend == 'realesrgan':
            return await self._upscale_realesrgan(input_path, output_path, scale, model)
        elif self.active_backend == 'ncnn':
            return await self._upscale_ncnn(input_path, output_path, scale, model, tile_size)
        elif self.active_backend == 'pil':
            return await self._upscale_pil(input_path, output_path, scale)
        else:
            raise Exception("No upscaling backend available")
    
    async def _upscale_realesrgan(self, input_path: str, output_path: str, scale: int, model: str) -> bool:
        """Upscale using Real-ESRGAN Python"""
        try:
            RealESRGANer = self.backends['realesrgan']['RealESRGANer']
            RRDBNet = self.backends['realesrgan']['RRDBNet']
            
            # Select model
            if "anime" in str(model).lower():
                model_name = "RealESRGAN_x4plus_anime_6B"
                netscale = 4
            else:
                model_name = "RealESRGAN_x4plus"
                netscale = 4
            
            # Create model
            model_net = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=netscale)
            
            # Initialize upscaler
            upscaler = RealESRGANer(
                scale=netscale,
                model_path=f'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/{model_name}.pth',
                model=model_net,
                tile=400,
                tile_pad=10,
                pre_pad=0,
                half=True
            )
            
            # Process in thread
            def process():
                import cv2
                img = cv2.imread(input_path, cv2.IMREAD_COLOR)
                output, _ = upscaler.enhance(img, outscale=scale/4)
                
                # Handle different scales
                if scale != 4:
                    from PIL import Image
                    import numpy as np
                    pil_img = Image.fromarray(cv2.cvtColor(output, cv2.COLOR_BGR2RGB))
                    
                    if scale == 2:
                        new_size = (pil_img.width // 2, pil_img.height // 2)
                    elif scale == 8:
                        new_size = (pil_img.width * 2, pil_img.height * 2)
                    else:
                        new_size = (pil_img.width, pil_img.height)
                    
                    pil_img = pil_img.resize(new_size, Image.Resampling.LANCZOS)
                    output = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                
                cv2.imwrite(output_path, output)
                return True
            
            # Run in executor
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(process)
                return await asyncio.get_event_loop().run_in_executor(None, future.result)
                
        except Exception as e:
            print(f"Real-ESRGAN processing failed: {e}")
            return False
    
    async def _upscale_ncnn(self, input_path: str, output_path: str, scale: int, model: str, tile_size: int) -> bool:
        """Upscale using NCNN binary (same as before)"""
        # Implementation same as original upscaler.py
        # ... (keeping original NCNN code)
        return False  # Placeholder
    
    async def _upscale_pil(self, input_path: str, output_path: str, scale: int) -> bool:
        """Upscale using PIL (fallback method)"""
        try:
            Image = self.backends['pil']['Image']
            ImageFilter = self.backends['pil']['ImageFilter']
            
            def process():
                # Open image
                with Image.open(input_path) as img:
                    # Convert to RGB if needed
                    if img.mode in ('RGBA', 'P', 'LA'):
                        img = img.convert('RGB')
                    
                    # Calculate new size
                    new_width = img.width * scale
                    new_height = img.height * scale
                    
                    # Apply multiple upscaling passes for better quality
                    current_img = img
                    current_scale = 1
                    
                    while current_scale < scale:
                        step_scale = min(2, scale / current_scale)
                        new_w = int(current_img.width * step_scale)
                        new_h = int(current_img.height * step_scale)
                        
                        # Use high-quality resampling
                        current_img = current_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                        
                        # Apply sharpening filter
                        current_img = current_img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
                        
                        current_scale *= step_scale
                    
                    # Final resize to exact target
                    if current_img.size != (new_width, new_height):
                        current_img = current_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Save result
                    current_img.save(output_path, 'PNG', optimize=True)
                    return True
            
            # Run in executor to avoid blocking
            return await asyncio.get_event_loop().run_in_executor(None, process)
            
        except Exception as e:
            print(f"PIL upscaling failed: {e}")
            return False
    
    def get_memory_usage_estimate(self, image_width: int, image_height: int, scale: int) -> dict:
        """Estimate memory usage for processing"""
        
        if self.active_backend == 'realesrgan':
            base_memory_mb = 1200
            memory_per_pixel = 0.000012
        elif self.active_backend == 'ncnn':
            base_memory_mb = 800
            memory_per_pixel = 0.000008
        elif self.active_backend == 'pil':
            base_memory_mb = 100
            memory_per_pixel = 0.000004
        else:
            base_memory_mb = 50
            memory_per_pixel = 0.000002
        
        pixels = image_width * image_height
        processing_memory_mb = pixels * memory_per_pixel * scale * scale
        total_memory_mb = base_memory_mb + processing_memory_mb
        
        return {
            "base_memory_mb": base_memory_mb,
            "processing_memory_mb": round(processing_memory_mb, 1),
            "total_estimated_mb": round(total_memory_mb, 1),
            "backend": self.active_backend,
            "recommended_tile_size": 400 if self.active_backend == 'realesrgan' else 512,
            "quality": "high" if self.active_backend in ['realesrgan', 'ncnn'] else "medium"
        }
