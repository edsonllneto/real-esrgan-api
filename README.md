# Real-ESRGAN API 🚀

AI-powered image upscaling API using Real-ESRGAN with hybrid NCNN-Vulkan/Python backend, optimized for low-memory VPS deployment.

## ✨ Features

- **Hybrid Backend**: NCNN-Vulkan (if available) + Python fallback
- **Low Memory Usage**: Uses 1.5-3GB RAM (adapts to available resources)
- **Multiple Scale Support**: 2x, 4x, and 8x upscaling
- **Reliable Deployment**: No external downloads during build
- **REST API**: Simple HTTP endpoints for integration
- **Docker Ready**: One-click deployment to EasyPanel
- **Base64 Output**: No file storage needed

## 🔧 Tech Stack

- **Backend**: FastAPI + Python 3.11
- **AI Engine**: Real-ESRGAN (Python + NCNN-Vulkan fallback)
- **Container**: Docker (optimized for reliability)
- **Deployment**: EasyPanel compatible

## 🚀 Quick Deploy to EasyPanel

### ✅ Ready to Deploy (Fixed & Tested!)

1. **Login to EasyPanel**
2. **Create New Service** → **GitHub Repository**
3. **Repository URL**: `https://github.com/edsonllneto/real-esrgan-api`
4. **Branch**: `main`
5. **Port**: `8000`
6. **Memory Limit**: `3GB` (Python version needs more RAM)
7. **CPU Limit**: `1-2 cores`
8. **Deploy** 🎉

*No more build errors! The API now uses reliable Python dependencies.*

## 📋 System Requirements

- **RAM**: 3GB minimum (2GB for app + 1GB system buffer)
- **CPU**: 1+ cores (2+ recommended)
- **Storage**: 1GB
- **OS**: Linux (Ubuntu/Debian preferred)

## 🔗 API Endpoints

### Base URL
```
http://your-server:8000
```

### 1. Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "binary_available": false,
  "models_available": true,
  "backend": "python",
  "supported_scales": [2, 4, 8],
  "max_file_size": "2MB",
  "memory_efficient": true
}
```

### 2. Available Models
```http
GET /models
```

**Response:**
```json
{
  "models": [
    "realesrgan-x4plus",
    "realesrnet-x4plus"
  ],
  "default_model": "realesrgan-x4plus",
  "supported_scales": [2, 4, 8],
  "backend": "python"
}
```

### 3. API Status (Detailed)
```http
GET /status
```

**Response:**
```json
{
  "api_version": "1.0.0",
  "backend": "python",
  "available_models": ["realesrgan-x4plus", "realesrnet-x4plus"],
  "supported_scales": [2, 4, 8],
  "max_file_size_mb": 2,
  "estimated_memory_usage": {
    "base_mb": 1200,
    "per_1024x1024_image_mb": 24.6,
    "recommended_tile_size": 400
  }
}
```

### 4. Upscale Image
```http
POST /upscale
Content-Type: multipart/form-data
```

**Parameters:**
- `file`: Image file (JPG/PNG/WEBP, max 2MB)
- `scale`: Scale factor (2, 4, or 8)
- `model`: Model name (optional, default: "realesrgan-x4plus")

**Response:**
```json
{
  "success": true,
  "original_size": "512x512",
  "upscaled_size": "2048x2048",
  "scale_used": 4,
  "model_used": "realesrgan-x4plus",
  "backend": "python",
  "format": "PNG",
  "memory_used_mb": 1224.6,
  "base64_image": "iVBORw0KGgoAAAANSUhEUgAA..."
}
```

## 🧪 Testing the API

### Using cURL
```bash
# Health check
curl http://your-server:8000/health

# Upload and upscale image
curl -X POST "http://your-server:8000/upscale" \
  -F "file=@your-image.jpg" \
  -F "scale=4" \
  -F "model=realesrgan-x4plus"
```

### Using Python
```python
import requests
import base64

# Upload image
with open("your-image.jpg", "rb") as f:
    response = requests.post(
        "http://your-server:8000/upscale",
        files={"file": f},
        data={"scale": 4}
    )

# Get result
result = response.json()
if result["success"]:
    print(f"Backend used: {result['backend']}")
    print(f"Memory used: {result['memory_used_mb']} MB")
    
    # Decode base64 image
    image_data = base64.b64decode(result["base64_image"])
    with open("upscaled_image.png", "wb") as f:
        f.write(image_data)
```

### Using JavaScript
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('scale', '4');

fetch('http://your-server:8000/upscale', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log(`Backend: ${data.backend}, Memory: ${data.memory_used_mb}MB`);
        const img = document.createElement('img');
        img.src = 'data:image/png;base64,' + data.base64_image;
        document.body.appendChild(img);
    }
});
```

## ⚙️ Backend Types

### 🐍 Python Backend (Default)
- **Pros**: Reliable, no external downloads, works everywhere
- **Cons**: Uses more RAM (~3GB), slightly slower
- **Best for**: Production deployments, reliability

### ⚡ NCNN-Vulkan Backend (Auto-detected)
- **Pros**: Faster, lower memory (~1.5GB)
- **Cons**: Requires pre-built binaries, more complex setup
- **Best for**: Optimal performance when available

*The API automatically detects which backend is available and uses the best option.*

## 🔍 Troubleshooting

### Common Issues

**1. Out of Memory**
- Increase memory limit to 3GB+
- Use smaller images (<1MB)
- Check system memory usage

**2. Slow Processing**
- Normal for Python backend (10-30s per image)
- Check CPU cores (2+ recommended)
- Monitor system load

**3. Models Not Available**
- Check `/health` endpoint
- Restart container if needed
- Models download automatically on first use

### Logs & Debugging

```bash
# View container logs
docker logs your-container-name

# Check memory usage
docker stats your-container-name

# Test all endpoints
curl http://your-server:8000/health
curl http://your-server:8000/models
curl http://your-server:8000/status
```

## 📊 Performance

### Processing Times (4x upscale, Python backend)

| Image Size | Processing Time | Memory Usage |
|------------|----------------|--------------|
| 512x512    | ~10-15 seconds | ~2.2GB       |
| 1024x1024  | ~30-45 seconds | ~2.8GB       |
| 1920x1080  | ~60-90 seconds | ~3.2GB       |

### Available Models

- **realesrgan-x4plus**: General purpose, best quality
- **realesrnet-x4plus**: Lightweight alternative
- **realesrgan-x4plus-anime**: Optimized for anime/illustration (if available)

## 🛡️ Security

- Non-root container user
- No persistent file storage
- Automatic temp file cleanup
- Input validation and size limits
- Memory and CPU restrictions

## 📦 Local Development

```bash
# Clone repository
git clone https://github.com/edsonllneto/real-esrgan-api
cd real-esrgan-api

# Build and run with Docker
docker build -t real-esrgan-api .
docker run -p 8000:8000 --memory=3g real-esrgan-api

# Or use docker-compose
docker-compose up
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Credits

- **Real-ESRGAN**: Original algorithm by Xintao Wang et al.
- **PyTorch**: Machine learning framework
- **FastAPI**: Modern Python web framework

---

**Made with ❤️ for reliable VPS deployments**

🎉 **Now with 100% reliable builds - no more download errors!**

Need help? Open an issue on GitHub!
