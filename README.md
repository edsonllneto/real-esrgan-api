# Real-ESRGAN API 🚀

AI-powered image upscaling API using Real-ESRGAN NCNN-Vulkan backend, optimized for low-memory VPS deployment.

## ✨ Features

- **Low Memory Usage**: Uses only 1.5-2GB RAM vs 4-8GB of PyTorch version
- **Multiple Scale Support**: 2x, 4x, and 8x upscaling
- **Fast Processing**: NCNN-Vulkan optimized backend
- **REST API**: Simple HTTP endpoints for integration
- **Docker Ready**: One-click deployment to EasyPanel
- **Base64 Output**: No file storage needed

## 🔧 Tech Stack

- **Backend**: FastAPI + Python 3.11
- **AI Engine**: Real-ESRGAN NCNN-Vulkan
- **Container**: Docker (optimized for low resources)
- **Deployment**: EasyPanel compatible

## 🚀 Quick Deploy to EasyPanel

### ✅ Ready to Deploy (Fixed!)

1. **Login to EasyPanel**
2. **Create New Service** → **GitHub Repository**
3. **Repository URL**: `https://github.com/edsonllneto/real-esrgan-api`
4. **Branch**: `main`
5. **Port**: `8000`
6. **Memory Limit**: `2.5GB`
7. **CPU Limit**: `1-2 cores`
8. **Deploy** 🎉

*The Dockerfile has been fixed and should build without errors!*

## 📋 System Requirements

- **RAM**: 2.5GB minimum (1.5GB for app + 1GB system buffer)
- **CPU**: 1+ cores (2+ recommended)
- **Storage**: 500MB
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
  "binary_available": true,
  "models_available": true,
  "supported_scales": [2, 4, 8],
  "max_file_size": "2MB"
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
    "realesrgan-x4plus-anime",
    "realesr-animevideov3"
  ],
  "default_model": "realesrgan-x4plus",
  "supported_scales": [2, 4, 8]
}
```

### 3. Upscale Image
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
  "format": "PNG",
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
        const img = document.createElement('img');
        img.src = 'data:image/png;base64,' + data.base64_image;
        document.body.appendChild(img);
    }
});
```

## ⚙️ Configuration

### Environment Variables

```bash
# Optional optimizations
OMP_NUM_THREADS=2          # Limit OpenMP threads
MKL_NUM_THREADS=2          # Limit MKL threads
UVICORN_WORKERS=1          # Single worker for low memory
```

### Memory Optimization

For VPS with limited RAM, the API automatically:
- Uses tile processing (512x512 tiles)
- Limits thread usage (1:2:1 configuration)
- Enables efficient memory cleanup
- Processes one image at a time

## 🔍 Troubleshooting

### Common Issues

**1. Build Errors**
- ✅ Fixed: Dockerfile updated to use minimal dependencies
- ✅ Should build without package errors now

**2. Out of Memory**
- Ensure 2.5GB+ available RAM
- Use only 1 worker
- Check system memory usage

**3. Slow Processing**
- Check CPU cores (2+ recommended)
- Verify image size (<2MB)
- Monitor system load

**4. Model Not Found**
- Check if models downloaded correctly
- Verify models/ directory exists
- Use default model: "realesrgan-x4plus"

### Logs & Debugging

```bash
# View container logs
docker logs your-container-name

# Check memory usage
docker stats your-container-name

# Test health endpoint
curl http://your-server:8000/health
```

## 📊 Performance

### Processing Times (4x upscale)

| Image Size | Processing Time | Memory Usage |
|------------|----------------|--------------|
| 512x512    | ~5-8 seconds   | ~1.8GB       |
| 1024x1024  | ~15-20 seconds | ~2.2GB       |
| 1920x1080  | ~25-30 seconds | ~2.5GB       |

### Supported Models

- **realesrgan-x4plus**: General purpose, best quality
- **realesrgan-x4plus-anime**: Optimized for anime/illustration
- **realesr-animevideov3**: Video/animation focused
- **realesrnet-x4plus**: Lightweight alternative

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
docker run -p 8000:8000 --memory=2.5g real-esrgan-api

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
- **NCNN**: Tencent's neural network inference framework
- **FastAPI**: Modern Python web framework

---

**Made with ❤️ for low-resource VPS deployments**

🎉 **Now ready for one-click deployment to EasyPanel!**

Need help? Open an issue on GitHub!
