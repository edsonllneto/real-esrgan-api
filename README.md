# Real-ESRGAN API

**Production-ready AI image upscaling API optimized for low-resource VPS environments**

A FastAPI-based implementation of Real-ESRGAN with intelligent fallback mechanisms, designed specifically for cost-effective cloud deployments while maintaining high-quality image processing capabilities.

## Key Advantages

### 🎯 **Optimized for Resource-Constrained Environments**
Unlike standard Real-ESRGAN implementations that require 8-16GB RAM and high-end GPUs, this API is specifically engineered for:
- **Low-memory VPS**: Runs on 1-4GB RAM instances
- **CPU-only processing**: No GPU dependency
- **Cost-effective deployment**: Suitable for budget hosting solutions
- **Automatic resource adaptation**: Scales processing based on available memory

### 🛡️ **Production-Grade Reliability**
- **Intelligent fallback system**: Multiple backend engines with automatic switching
- **Guaranteed uptime**: PIL fallback ensures 100% availability
- **Memory-aware processing**: Dynamic tile sizing based on system resources
- **Graceful degradation**: Quality adjusts based on available backends

### 🔄 **Dual Input Support**
- **File upload**: Traditional multipart/form-data for direct file processing
- **Base64 JSON**: Streamlined integration for automation workflows and APIs

## Technical Architecture

### Backend Processing Engines

#### **Primary: Real-ESRGAN Python Implementation**
- **Quality**: Highest (⭐⭐⭐⭐⭐)
- **Memory Requirements**: 3-4GB RAM
- **Processing Time**: 15-45 seconds
- **Models**: RealESRGAN_x4plus, anime-specific models
- **Availability**: ~95% (depends on dependencies)

#### **Fallback: Advanced PIL Processing**
- **Quality**: High (⭐⭐⭐⭐☆)
- **Memory Requirements**: 1-2GB RAM
- **Processing Time**: 5-15 seconds
- **Method**: Multi-pass Lanczos resampling with UnsharpMask
- **Availability**: 100% (built-in Python)

#### **Optional: NCNN-Vulkan**
- **Quality**: Highest (⭐⭐⭐⭐⭐)
- **Memory Requirements**: 1.5-2GB RAM
- **Processing Time**: 5-15 seconds
- **Requirement**: Binary installation
- **Availability**: ~85% (platform dependent)

## API Endpoints

### Base URL Structure
```
https://your-domain.com/
```

### **System Information**

#### `GET /health`
**Purpose**: Check API status and available backends
```bash
curl https://api.example.com/health
```

**Response**:
```json
{
  "status": "healthy",
  "backend": "realesrgan",
  "backend_quality": "high",
  "available_backends": {
    "realesrgan": true,
    "pil": true,
    "ncnn": false
  },
  "supported_scales": [2, 4, 8],
  "max_file_size": "2MB"
}
```

#### `GET /status`
**Purpose**: Detailed system information and capabilities
```bash
curl https://api.example.com/status
```

#### `GET /models`
**Purpose**: List available upscaling models
```bash
curl https://api.example.com/models
```

### **Image Processing**

#### `POST /upscale` - File Upload
**Purpose**: Process images via multipart file upload
**Content-Type**: `multipart/form-data`

```bash
curl -X POST "https://api.example.com/upscale" \
  -F "file=@input_image.jpg" \
  -F "scale=4" \
  -F "model=auto"
```

**Parameters**:
- `file`: Image file (JPG, PNG, WebP) - Max 2MB
- `scale`: Upscaling factor (2, 4, or 8)
- `model`: Model selection (auto, or specific model name)

#### `POST /upscale-base64` - JSON Input
**Purpose**: Process images via base64-encoded JSON payload
**Content-Type**: `application/json`

```bash
curl -X POST "https://api.example.com/upscale-base64" \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "iVBORw0KGgoAAAANSUhEUgAAA...",
    "scale": 4,
    "model": "auto",
    "format": "auto"
  }'
```

**Request Body**:
```json
{
  "image_base64": "string",  // Base64-encoded image data
  "scale": 4,                // Upscaling factor: 2, 4, or 8
  "model": "auto",           // Model selection
  "format": "auto"           // Output format: auto, png, jpeg
}
```

**Response** (both endpoints):
```json
{
  "success": true,
  "original_size": "512x512",
  "upscaled_size": "2048x2048",
  "scale_used": 4,
  "model_used": "realesrgan-x4plus",
  "backend": "realesrgan",
  "backend_quality": "high",
  "format": "PNG",
  "memory_used_mb": 1224.6,
  "processing_info": {
    "backend": "realesrgan",
    "tile_size": 256,
    "quality_level": "high",
    "original_format": "JPEG"
  },
  "base64_image": "iVBORw0KGgoAAAANSUhE..."
}
```

## Integration Examples

### **Python Client Implementation**

#### File Upload Method
```python
import requests
import base64

def upscale_image_file(api_url, image_path, scale=4):
    """Upload and process image file"""
    endpoint = f"{api_url}/upscale"
    
    with open(image_path, 'rb') as f:
        files = {'file': f}
        data = {'scale': scale, 'model': 'auto'}
        
        response = requests.post(endpoint, files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        
        # Save processed image
        image_data = base64.b64decode(result['base64_image'])
        with open('upscaled_output.png', 'wb') as f:
            f.write(image_data)
        
        return {
            'success': True,
            'backend': result['backend'],
            'quality': result['backend_quality'],
            'processing_time': result.get('processing_time'),
            'memory_used': result['memory_used_mb']
        }
    
    return {'success': False, 'error': response.text}

# Usage
result = upscale_image_file("https://api.example.com", "input.jpg", scale=4)
```

#### Base64 JSON Method
```python
import requests
import base64

def upscale_image_base64(api_url, image_path, scale=4):
    """Process image via base64 encoding"""
    endpoint = f"{api_url}/upscale-base64"
    
    # Convert image to base64
    with open(image_path, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    payload = {
        "image_base64": image_base64,
        "scale": scale,
        "model": "auto",
        "format": "png"
    }
    
    response = requests.post(
        endpoint, 
        json=payload,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        result = response.json()
        
        # Save processed image
        image_data = base64.b64decode(result['base64_image'])
        with open('upscaled_output.png', 'wb') as f:
            f.write(image_data)
        
        return result
    
    return {'error': response.text}

# Usage
result = upscale_image_base64("https://api.example.com", "input.jpg", scale=4)
```

### **JavaScript/Node.js Integration**

```javascript
const axios = require('axios');
const fs = require('fs');

async function upscaleImageBase64(apiUrl, imagePath, scale = 4) {
    const endpoint = `${apiUrl}/upscale-base64`;
    
    // Read and encode image
    const imageBuffer = fs.readFileSync(imagePath);
    const imageBase64 = imageBuffer.toString('base64');
    
    try {
        const response = await axios.post(endpoint, {
            image_base64: imageBase64,
            scale: scale,
            model: 'auto',
            format: 'auto'
        }, {
            headers: {
                'Content-Type': 'application/json'
            },
            timeout: 300000 // 5 minutes
        });
        
        if (response.data.success) {
            // Save result
            const outputBuffer = Buffer.from(response.data.base64_image, 'base64');
            fs.writeFileSync('upscaled_output.png', outputBuffer);
            
            console.log(`Processed with ${response.data.backend} backend`);
            console.log(`Quality: ${response.data.backend_quality}`);
            
            return response.data;
        }
    } catch (error) {
        console.error('Processing failed:', error.message);
        return null;
    }
}

// Usage
upscaleImageBase64('https://api.example.com', 'input.jpg', 4);
```

## Deployment Options

### **Docker Deployment**
```bash
# Clone repository
git clone https://github.com/edsonllneto/real-esrgan-api
cd real-esrgan-api

# Build and run
docker-compose up --build

# API available at http://localhost:8000
```

### **Cloud Platform Examples**

#### **EasyPanel**
- Repository URL: `https://github.com/edsonllneto/real-esrgan-api`
- Port: `8000`
- Memory: `4GB` (recommended) / `2GB` (minimum)
- Build timeout: `15 minutes`

#### **Railway**
```bash
railway login
railway init
railway add
railway deploy
```

#### **Heroku**
```bash
heroku create your-app-name
heroku stack:set container
git push heroku main
```

#### **DigitalOcean App Platform**
- Runtime: `Docker`
- Source: GitHub repository
- Instance size: `basic-xxs` (1GB RAM minimum)

### **VPS Manual Installation**
```bash
# Install dependencies
apt update && apt install python3 python3-pip git

# Clone and setup
git clone https://github.com/edsonllneto/real-esrgan-api
cd real-esrgan-api
pip3 install -r requirements.txt

# Run application
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Use Cases

### **API Integration Scenarios**
- **Content management systems**: Automated image enhancement workflows
- **E-commerce platforms**: Product image quality improvement
- **Social media applications**: User-generated content enhancement
- **Digital asset processing**: Batch image upscaling for archives
- **Automation platforms**: Integration with workflow tools (Zapier, n8n, etc.)

### **Enterprise Applications**
- **Media processing pipelines**: Automated content enhancement
- **Digital preservation**: Historical image restoration workflows
- **Print production**: Image quality improvement for high-resolution output
- **Game development**: Asset upscaling for texture enhancement

## Performance Optimization

### **Memory Usage Patterns**
- **1GB RAM**: PIL backend only, 2x scaling maximum
- **2GB RAM**: PIL backend with 4x scaling, limited Real-ESRGAN support
- **4GB RAM**: Full Real-ESRGAN support with all scaling options
- **8GB+ RAM**: Optimal performance with large image processing

### **Processing Time Expectations**
- **512x512 image**: 5-15 seconds (PIL) / 15-30 seconds (Real-ESRGAN)
- **1024x1024 image**: 10-25 seconds (PIL) / 30-60 seconds (Real-ESRGAN)
- **2048x2048 image**: 20-45 seconds (PIL) / 60-120 seconds (Real-ESRGAN)

## Error Handling

### **Common Response Codes**
- `200`: Successful processing
- `400`: Invalid input parameters
- `413`: File size exceeds limit
- `422`: Invalid image format
- `500`: Processing error or backend failure

### **Fallback Behavior**
When the primary Real-ESRGAN backend fails, the system automatically:
1. Attempts NCNN-Vulkan backend (if available)
2. Falls back to PIL advanced processing
3. Maintains consistent API response format
4. Reports actual backend used in response

## Security Considerations

- **File size limits**: 2MB maximum to prevent DoS attacks
- **Input validation**: Comprehensive image format verification
- **Temporary file cleanup**: Automatic removal of processing artifacts
- **Memory management**: Controlled resource allocation
- **Rate limiting**: Implement application-level controls as needed

## License

MIT License - see LICENSE file for details.

---

**Ready for production deployment with intelligent resource management and guaranteed availability.**