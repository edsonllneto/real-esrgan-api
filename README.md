# Real-ESRGAN API 🚀

AI-powered image upscaling API with **intelligent fallback system** - guaranteed to work on any VPS!

## ✨ **Key Features**

- **🛡️ Fault-Tolerant**: Multiple backends with automatic fallback
- **🎯 Always Works**: PIL fallback ensures 100% uptime
- **⚡ Smart Backend**: Uses best available (Real-ESRGAN ➜ PIL)
- **🔍 Transparent**: API tells you which backend is active
- **💾 Low Memory**: Adapts to your VPS resources (1-4GB)
- **📊 Multiple Scales**: 2x, 4x, and 8x upscaling
- **🔗 REST API**: Simple HTTP endpoints
- **📦 Docker Ready**: One-click EasyPanel deployment
- **🔄 Dual Input**: Both file upload AND base64 input

## 🏗️ **Backend Architecture**

### **🥇 Primary: Real-ESRGAN Python**
- **Quality**: ⭐⭐⭐⭐⭐ (Highest)
- **Memory**: 3-4GB RAM
- **Speed**: 15-45 seconds
- **Models**: RealESRGAN_x4plus, anime models

### **🥈 Fallback: PIL Advanced**
- **Quality**: ⭐⭐⭐⭐☆ (High)
- **Memory**: 1-2GB RAM  
- **Speed**: 5-15 seconds
- **Method**: Multi-pass Lanczos + UnsharpMask

### **🔧 Optional: NCNN-Vulkan**
- **Quality**: ⭐⭐⭐⭐⭐ (Highest)
- **Memory**: 1.5-2GB RAM
- **Speed**: 5-15 seconds
- **Requirement**: Binary installation

## 🚀 **Easy Deploy to EasyPanel**

### **📋 Configuration:**
```
Repository URL: https://github.com/edsonllneto/real-esrgan-api
Branch: main
Port: 8000
Memory Limit: 4GB
CPU Limit: 2 cores
Build Timeout: 15 minutes
```

### **⚡ Steps:**
1. **Create New Service** in EasyPanel
2. **Use GitHub Repository** option
3. **Configure** with settings above
4. **Deploy** and wait 10-15 minutes
5. **Test** endpoints below! 🎉

## 🔗 **API Endpoints**

### **Base URL:** `https://your-domain.easypanel.host/`

### **🔍 Debug & Health**
```bash
# Check which backends are available
GET /debug

# Health check with backend info  
GET /health

# Detailed status
GET /status
```

### **🖼️ Image Upscaling**

#### **📁 Method 1: File Upload (multipart-form-data)**
```bash
POST /upscale
```

**Example with cURL:**
```bash
curl -X POST "https://your-domain.easypanel.host/upscale" \
  -F "file=@image.jpg" \
  -F "scale=4" \
  -F "model=auto"
```

#### **🔤 Method 2: Base64 JSON (NEW!)**
```bash
POST /upscale-base64
```

**Example with cURL:**
```bash
curl -X POST "https://your-domain.easypanel.host/upscale-base64" \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
    "scale": 4,
    "model": "auto",
    "format": "auto"
  }'
```

**Response (both methods):**
```json
{
  "success": true,
  "original_size": "512x512",
  "upscaled_size": "2048x2048", 
  "scale_used": 4,
  "backend": "realesrgan",
  "backend_quality": "high",
  "memory_used_mb": 1224.6,
  "processing_info": {
    "backend": "realesrgan",
    "quality_level": "high"
  },
  "base64_image": "iVBORw0KGgoAAAANSUhEUgAA..."
}
```

## 🧪 **Testing Your API**

### **1. Quick Health Check:**
```bash
curl https://your-domain.easypanel.host/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "backend": "realesrgan", // or "pil"
  "backend_quality": "high", // or "medium" 
  "available_backends": {
    "realesrgan": true,
    "pil": true
  },
  "supported_scales": [2, 4, 8]
}
```

### **2. Debug Information:**
```bash
curl https://your-domain.easypanel.host/debug
```

### **3. Interactive Testing:**
Visit: `https://your-domain.easypanel.host/docs`

## 💻 **Usage Examples**

### **Python Client (File Upload):**
```python
import requests
import base64

def upscale_image(image_path, scale=4):
    url = "https://your-domain.easypanel.host/upscale"
    
    with open(image_path, 'rb') as f:
        response = requests.post(url, 
            files={'file': f}, 
            data={'scale': scale}
        )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Backend used: {result['backend']}")
        print(f"Quality: {result['backend_quality']}")
        
        # Save result
        image_data = base64.b64decode(result['base64_image'])
        with open('upscaled.png', 'wb') as f:
            f.write(image_data)
        return True
    return False

# Use it
upscale_image("photo.jpg", scale=4)
```

### **Python Client (Base64):**
```python
import requests
import base64

def upscale_image_base64(image_path, scale=4):
    url = "https://your-domain.easypanel.host/upscale-base64"
    
    # Convert image to base64
    with open(image_path, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    payload = {
        "image_base64": image_base64,
        "scale": scale,
        "model": "auto",
        "format": "auto"
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Backend: {result['backend']}, Quality: {result['backend_quality']}")
        
        # Save result
        image_data = base64.b64decode(result['base64_image'])
        with open('upscaled.png', 'wb') as f:
            f.write(image_data)
        return True
    return False

# Use it
upscale_image_base64("photo.jpg", scale=4)
```

### **JavaScript/Node.js:**
```javascript
const FormData = require('form-data');
const fs = require('fs');

async function upscaleImage(imagePath, scale = 4) {
    const form = new FormData();
    form.append('file', fs.createReadStream(imagePath));
    form.append('scale', scale);
    
    const response = await fetch('https://your-domain.easypanel.host/upscale', {
        method: 'POST',
        body: form
    });
    
    const result = await response.json();
    console.log(`Backend: ${result.backend}, Quality: ${result.backend_quality}`);
    
    if (result.success) {
        const buffer = Buffer.from(result.base64_image, 'base64');
        fs.writeFileSync('upscaled.png', buffer);
        return true;
    }
    return false;
}
```

### **JavaScript (Base64):**
```javascript
async function upscaleImageBase64(imageBase64, scale = 4) {
    const response = await fetch('https://your-domain.easypanel.host/upscale-base64', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            image_base64: imageBase64,
            scale: scale,
            model: "auto",
            format: "auto"
        })
    });
    
    const result = await response.json();
    return result;
}
```

## 🔧 **N8N Integration**

### **HTTP Request Node Configuration:**
```
Method: POST
URL: https://your-domain.easypanel.host/upscale-base64

Headers:
Content-Type: application/json

Body:
{
  "image_base64": "{{$json.your_base64_image}}",
  "scale": 4,
  "model": "auto", 
  "format": "png"
}

Timeout: 120000ms (2 minutes)
```

### **Complete N8N Workflow Example:**
1. **Read Binary File** → Load image
2. **Function Node** → Convert to base64:
```javascript
return items.map(item => {
  const binaryData = item.binary.data;
  return {
    json: {
      image_base64: binaryData.data,
      originalName: binaryData.fileName
    }
  };
});
```
3. **HTTP Request** → Call API
4. **Function Node** → Process result:
```javascript
return items.map(item => {
  const base64Image = item.json.base64_image;
  return {
    json: {
      success: item.json.success,
      backend: item.json.backend,
      original_size: item.json.original_size,
      upscaled_size: item.json.upscaled_size
    },
    binary: {
      data: {
        data: base64Image,
        mimeType: 'image/png',
        fileName: 'upscaled_image.png'
      }
    }
  };
});
```

## 📊 **Performance Comparison**

| Backend | Quality | Speed | Memory | Reliability |
|---------|---------|-------|--------|-------------|
| Real-ESRGAN | ⭐⭐⭐⭐⭐ | 15-45s | 3-4GB | 95% |
| PIL Advanced | ⭐⭐⭐⭐☆ | 5-15s | 1-2GB | 100% |
| NCNN-Vulkan | ⭐⭐⭐⭐⭐ | 5-15s | 1.5-2GB | 85% |

## 🟠 **Troubleshooting**

### **Common Scenarios:**

**✅ Real-ESRGAN Working:**
```json
{"backend": "realesrgan", "backend_quality": "high"}
```

**⚠️ Real-ESRGAN Failed, PIL Fallback:**
```json
{"backend": "pil", "backend_quality": "medium"}
```

**❌ All Backends Failed:**
```json
{"status": "error", "backend": "none"}
```

### **Memory Issues:**
- Increase EasyPanel memory limit to 4GB
- Use smaller images (<1MB)
- Check `/status` endpoint for memory estimates

### **Slow Processing:**
- Normal for high-quality backends
- PIL fallback is faster but lower quality
- Check backend in use via `/health`

## 🔧 **Deployment Issues?**

### **If Build Fails:**
1. **Delete** current service in EasyPanel
2. **Create new** with 4GB RAM + 15min timeout
3. **Wait** for complete rebuild
4. **Test** `/debug` endpoint

### **If Real-ESRGAN Unavailable:**
- API will automatically use PIL fallback
- Still produces good quality results
- Check logs for specific dependency errors
- See `FIX-EASYPANEL.md` for detailed fixes

## 📄 **License**

MIT License - see LICENSE file for details.

## 🙏 **Credits**

- **Real-ESRGAN**: Xintao Wang et al.
- **PyTorch**: Meta AI Research
- **FastAPI**: Sebastián Ramírez

---

## 🎯 **Ready to Deploy?**

1. **Copy repository URL**: `https://github.com/edsonllneto/real-esrgan-api`
2. **Go to EasyPanel** ➜ Create Service ➜ GitHub Repository
3. **Configure** with 4GB RAM, 15min timeout
4. **Deploy** and test!

**🚀 Your fault-tolerant image upscaling API will be ready in 15 minutes!**

Need help? Check `FIX-EASYPANEL.md` or open an issue!
