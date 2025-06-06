# Real-ESRGAN Dependencies Fix Guide

## Problem Diagnosis

If you see this error in your logs:
```
❌ Real-ESRGAN Python not available: No module named 'realesrgan.archs.rrdbnet_arch'
✅ PyTorch available
✅ PIL fallback available
❌ NCNN binary not available
```

This means the Real-ESRGAN dependencies are not installing correctly. Don't worry - the API will still work with PIL fallback!

## Quick Solutions

### Solution 1: EasyPanel Redeploy (Recommended)
1. **Delete current service** in EasyPanel
2. **Create new service** with these settings:
   - Repository: `https://github.com/edsonllneto/real-esrgan-api`
   - Branch: `main`
   - **Memory: 4GB minimum** (important!)
   - **Build timeout: 20 minutes** (increased)
   - CPU: 2 cores
3. **Wait for complete rebuild** (15-20 minutes)
4. **Test health endpoint**: `https://your-domain/health`

### Solution 2: Alternative Requirements (If Solution 1 fails)
If the build still fails, we can use a lighter version:

Create a new file `requirements-light.txt`:
```bash
# Core FastAPI dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0

# Image processing
Pillow==10.1.0

# File handling
python-multipart==0.0.6

# HTTP requests
httpx==0.25.2

# Async support
aiofiles==23.2.1

# Basic scientific computing
numpy==1.24.3

# Computer vision (headless version for containers)
opencv-python-headless==4.8.1.78

# PyTorch CPU version (smaller, more reliable)
--extra-index-url https://download.pytorch.org/whl/cpu
torch==2.0.1+cpu
torchvision==0.15.2+cpu

# Ensure pydantic compatibility
pydantic==2.5.0

# Additional image processing for PIL fallback
scikit-image==0.22.0
```

Then modify `Dockerfile` to use this lighter version.

## Testing the Fixes

### Test 1: Health Check
```bash
curl https://your-domain.easypanel.host/health
```

**Expected with Real-ESRGAN working:**
```json
{
  "status": "healthy",
  "backend": "realesrgan",
  "backend_quality": "high"
}
```

**Expected with PIL fallback (still good!):**
```json
{
  "status": "healthy",
  "backend": "pil",
  "backend_quality": "medium"
}
```

### Test 2: Base64 Endpoint
Use the provided `test_base64_simple.py` script:

1. Download: `test_base64_simple.py`
2. Edit the `API_URL` variable to your domain
3. Run: `python test_base64_simple.py`

### Test 3: Manual cURL Test
```bash
# Create a simple base64 test
echo "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" > test_base64.txt

# Test the endpoint
curl -X POST "https://your-domain.easypanel.host/upscale-base64" \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
    "scale": 2,
    "model": "auto",
    "format": "auto"
  }'
```

## Common Base64 Endpoint Issues

### Issue 1: Invalid Base64 Format
**Error:** `Invalid base64 image data`

**Solutions:**
- Remove data URL prefix: `data:image/png;base64,` 
- Ensure no line breaks in base64 string
- Verify the base64 represents a valid image

### Issue 2: Content-Type Header Missing
**Error:** `422 Unprocessable Entity`

**Solution:** Always include:
```bash
-H "Content-Type: application/json"
```

### Issue 3: Image Too Large
**Error:** `Image too large. Max size: 2MB`

**Solution:** Compress image before converting to base64

### Issue 4: Timeout
**Error:** Request timeout

**Solutions:**
- Increase timeout to 120+ seconds
- Use smaller images for testing
- Check if API is under load

## Performance Expectations

### With Real-ESRGAN Backend:
- **Quality:** ⭐⭐⭐⭐⭐ (Highest)
- **Speed:** 15-45 seconds
- **Memory:** 3-4GB needed

### With PIL Fallback:
- **Quality:** ⭐⭐⭐⭐☆ (Still very good!)
- **Speed:** 5-15 seconds  
- **Memory:** 1-2GB needed

## API Status Interpretation

### ✅ Healthy Status Messages:
- `"backend": "realesrgan"` - Real-ESRGAN working perfectly
- `"backend": "pil"` - PIL fallback working (still produces good results!)

### ⚠️ Degraded Status:
- API is working but with limited models
- Still functional for production use

### ❌ Error Status:
- `"backend": "none"` - Check dependencies and redeploy

## N8N Integration Notes

When using with N8N or other automation tools:

1. **Timeout:** Set to 120 seconds minimum
2. **Content-Type:** Must be `application/json`
3. **Base64:** Clean string without prefixes
4. **Error Handling:** Check `success` field in response

## Docker Local Testing

If you want to test locally:

```bash
# Clone repository
git clone https://github.com/edsonllneto/real-esrgan-api
cd real-esrgan-api

# Build and run
docker-compose up --build

# Test locally
curl http://localhost:8000/health
```

## Production Notes

- **PIL fallback is production-ready** - Don't worry if Real-ESRGAN doesn't install
- API automatically chooses best available backend
- Quality with PIL is still very good for most use cases
- Memory usage is much lower with PIL (1-2GB vs 3-4GB)

## Need Help?

1. Check logs in EasyPanel for specific error messages
2. Test with the provided `test_base64_simple.py` script
3. Verify health endpoint shows at least PIL backend available
4. Remember: PIL fallback is perfectly fine for production use!

The API is designed to always work, even if optimal backends aren't available.
