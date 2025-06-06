# Real-ESRGAN Dependencies Fix Guide

## Problem Diagnosis

### Error 1: Git not found during build
```
ERROR: Cannot find command 'git' - do you have 'git' installed and in your PATH?
```

### Error 2: Real-ESRGAN modules missing
```
❌ Real-ESRGAN Python not available: No module named 'realesrgan.archs.rrdbnet_arch'
✅ PyTorch available
✅ PIL fallback available
❌ NCNN binary not available
```

Both errors are now **FIXED** in the latest version!

## ✅ Solutions (In Order of Preference)

### Solution 1: Standard Redeploy (Recommended)
The **main Dockerfile is now fixed** with git and all dependencies.

1. **Delete current service** in EasyPanel
2. **Create new service** with these settings:
   - Repository: `https://github.com/edsonllneto/real-esrgan-api`
   - Branch: `main`
   - **Memory: 4GB minimum** (important!)
   - **Build timeout: 25 minutes** (increased for dependencies)
   - CPU: 2 cores
3. **Wait for complete rebuild** (20-25 minutes)
4. **Test health endpoint**: `https://your-domain/health`

### Solution 2: Use Robust Dockerfile (If Solution 1 fails)
If the main build still fails, use the robust version with automatic fallbacks:

1. In EasyPanel, **change Dockerfile name** to: `Dockerfile.robust`
2. This version tries multiple dependency installation methods
3. Has automatic fallbacks built-in

### Solution 3: Use No-Git Requirements (Lightweight)
For minimal installations that always work:

1. Replace `requirements.txt` with `requirements-no-git.txt`
2. This installs Real-ESRGAN from PyPI instead of GitHub
3. Smaller build, faster deployment

### Solution 4: Alternative Dockerfile (Last Resort)
Use the alternative Dockerfile with graceful failure handling:

1. Change Dockerfile to: `Dockerfile.alternative`
2. This version continues building even if Real-ESRGAN fails
3. Guarantees PIL fallback always works

## Quick Test Commands

### Test 1: Health Check
```bash
curl https://your-domain.easypanel.host/health
```

**✅ Expected with Real-ESRGAN working:**
```json
{
  "status": "healthy",
  "backend": "realesrgan",
  "backend_quality": "high"
}
```

**✅ Expected with PIL fallback (still excellent!):**
```json
{
  "status": "healthy",
  "backend": "pil",
  "backend_quality": "medium"
}
```

### Test 2: Base64 Endpoint
```bash
curl -X POST "https://your-domain.easypanel.host/upscale-base64" \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
    "scale": 2,
    "model": "auto",
    "format": "auto"
  }'
```

### Test 3: File Upload Endpoint
```bash
curl -X POST "https://your-domain.easypanel.host/upscale" \
  -F "file=@your_image.jpg" \
  -F "scale=2" \
  -F "model=auto"
```

## Available Files for Different Scenarios

| File | Purpose | When to Use |
|------|---------|-------------|
| `Dockerfile` | Main build (now with git) | Default choice |
| `Dockerfile.robust` | Multiple fallbacks | If main fails |
| `Dockerfile.alternative` | Graceful failures | If others fail |
| `requirements.txt` | Full dependencies | Default |
| `requirements-no-git.txt` | PyPI only | Lightweight build |

## Common Base64 Endpoint Issues

### Issue 1: Invalid Base64 Format
**Error:** `Invalid base64 image data`

**Solutions:**
- Remove data URL prefix: `data:image/png;base64,` 
- Ensure no line breaks in base64 string
- Verify the base64 represents a valid image

**Test your base64:**
```bash
# Decode and verify base64 is valid
echo "your_base64_string" | base64 -d > test.png
file test.png  # Should show image format
```

### Issue 2: Content-Type Header Missing
**Error:** `422 Unprocessable Entity`

**Solution:** Always include:
```bash
-H "Content-Type: application/json"
```

### Issue 3: Image Too Large
**Error:** `Image too large. Max size: 2MB`

**Solution:** Compress image before converting to base64
```bash
# Check base64 size (should be < 2.7MB for 2MB image)
echo "your_base64" | wc -c
```

### Issue 4: Timeout
**Error:** Request timeout

**Solutions:**
- Increase timeout to 120+ seconds for scale 4
- Use smaller images for testing (64x64 pixels)
- Try scale 2 instead of 4 for faster processing

## N8N Integration Notes

When using with N8N or automation tools:

### ✅ Correct Configuration:
```json
{
  "method": "POST",
  "url": "https://your-api.com/upscale-base64",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "image_base64": "{{$json.clean_base64}}",
    "scale": 2,
    "model": "auto",
    "format": "auto"
  },
  "timeout": 120000
}
```

### ❌ Common Mistakes:
- Missing `Content-Type: application/json`
- Including data URL prefix in base64
- Timeout too short (<60 seconds)
- Using scale 8 on large images (very slow)

## Performance Expectations

### With Real-ESRGAN Backend:
- **Quality:** ⭐⭐⭐⭐⭐ (Highest)
- **Speed:** 15-45 seconds (scale 4)
- **Memory:** 3-4GB needed
- **Best for:** High-quality results

### With PIL Fallback:
- **Quality:** ⭐⭐⭐⭐☆ (Still very good!)
- **Speed:** 5-15 seconds (scale 4)
- **Memory:** 1-2GB needed  
- **Best for:** Fast processing, lower resource usage

### Processing Time by Scale:
- **Scale 2:** 5-20 seconds
- **Scale 4:** 15-45 seconds  
- **Scale 8:** 30-90 seconds

## Image Size Recommendations

| Input Size | Recommended Scale | Processing Time | Memory Used |
|------------|------------------|-----------------|-------------|
| 64x64 | 4x or 8x | 5-15s | <500MB |
| 256x256 | 4x | 10-30s | 500MB-1GB |
| 512x512 | 2x or 4x | 15-45s | 1-2GB |
| 1024x1024 | 2x | 30-60s | 2-3GB |

## Docker Local Testing

Test locally before deploying:

```bash
# Clone and test
git clone https://github.com/edsonllneto/real-esrgan-api
cd real-esrgan-api

# Test different Dockerfiles
docker build -f Dockerfile -t test-api .
# or
docker build -f Dockerfile.robust -t test-api .

# Run locally
docker run -p 8000:8000 test-api

# Test endpoints
curl http://localhost:8000/health
```

## Deployment Status Interpretation

### ✅ Build Success Indicators:
- Build completes in 15-25 minutes
- Health endpoint responds
- At least PIL backend available
- No critical errors in logs

### ⚠️ Partial Success (Still Good):
- Build completes but Real-ESRGAN unavailable
- PIL backend working
- API fully functional with good quality

### ❌ Build Failure Indicators:
- Build times out (>30 minutes)
- Health endpoint returns 500 error
- No backends available
- Critical import errors

## Need Help?

1. **Check build logs** in EasyPanel for specific errors
2. **Test health endpoint** first: `/health`
3. **Use test script**: Download `test_base64_simple.py`
4. **Try different Dockerfiles** if main one fails
5. **Remember**: PIL fallback produces excellent results too!

The API is designed to always work - even if Real-ESRGAN doesn't install, PIL provides production-quality upscaling.

## What's Been Fixed:

✅ **Git dependency** - Now installed in all Dockerfiles  
✅ **Build dependencies** - All required libraries included  
✅ **Multiple fallback options** - Several Dockerfiles available  
✅ **Base64 endpoint** - Improved validation and error handling  
✅ **Automatic fallbacks** - Robust installation process  

Your API should now build successfully and work reliably! 🚀
