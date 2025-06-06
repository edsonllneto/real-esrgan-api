#!/usr/bin/env python3
"""
Simple Base64 Endpoint Test Script
Quick test for the /upscale-base64 endpoint
"""

import requests
import base64
import json
from pathlib import Path

# Configuration - UPDATE THESE!
API_URL = "https://your-domain.easypanel.host"  # Replace with your actual URL
TEST_IMAGE = "test.jpg"  # Replace with a small test image

def create_test_base64():
    """Create a simple test base64 image"""
    # Create a small 64x64 red square PNG
    from PIL import Image
    import io
    
    # Create a simple test image
    img = Image.new('RGB', (64, 64), color='red')
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_data = buffer.getvalue()
    
    base64_string = base64.b64encode(img_data).decode('utf-8')
    return base64_string

def test_base64_endpoint_simple():
    """Test the base64 endpoint with a simple request"""
    
    print("🔤 Testing /upscale-base64 endpoint...")
    
    # Method 1: Use generated test image
    try:
        print("Creating test base64 image...")
        test_base64 = create_test_base64()
        print(f"✅ Test image created (length: {len(test_base64)} chars)")
    except Exception as e:
        print(f"❌ Failed to create test image: {e}")
        return False
    
    # Prepare the request
    payload = {
        "image_base64": test_base64,
        "scale": 2,  # Use scale 2 for faster testing
        "model": "auto",
        "format": "auto"
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    print(f"📡 Sending request to: {API_URL}/upscale-base64")
    print(f"   Payload size: {len(json.dumps(payload))} bytes")
    
    try:
        response = requests.post(
            f"{API_URL}/upscale-base64",
            json=payload,
            headers=headers,
            timeout=60  # 1 minute timeout for testing
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"   Backend: {result.get('backend', 'unknown')}")
            print(f"   Original: {result.get('original_size', 'unknown')}")
            print(f"   Upscaled: {result.get('upscaled_size', 'unknown')}")
            print(f"   Output length: {len(result.get('base64_image', ''))} chars")
            return True
        else:
            print("❌ FAILED!")
            print(f"   Status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Raw response: {response.text[:500]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT! Request took longer than 60 seconds")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR! Check if API URL is correct and service is running")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

def test_health():
    """Test the health endpoint first"""
    print("🏥 Testing /health endpoint...")
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check passed!")
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Backend: {data.get('backend', 'unknown')}")
            print(f"   Backend Quality: {data.get('backend_quality', 'unknown')}")
            
            backends = data.get('available_backends', {})
            print("   Available backends:")
            for name, available in backends.items():
                status = "✅" if available else "❌"
                print(f"     {status} {name}")
            
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_with_file():
    """Test with actual file if available"""
    if not Path(TEST_IMAGE).exists():
        print(f"⚠️  Test image '{TEST_IMAGE}' not found, skipping file test")
        return None
    
    print(f"📁 Testing with file: {TEST_IMAGE}")
    
    try:
        with open(TEST_IMAGE, 'rb') as f:
            image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        print(f"   File size: {len(image_data)} bytes")
        print(f"   Base64 size: {len(image_base64)} chars")
        
        if len(image_data) > 2 * 1024 * 1024:
            print("⚠️  File too large (>2MB), skipping")
            return None
        
        payload = {
            "image_base64": image_base64,
            "scale": 2,
            "model": "auto",
            "format": "auto"
        }
        
        response = requests.post(
            f"{API_URL}/upscale-base64",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ File test SUCCESS!")
            print(f"   Backend: {result.get('backend')}")
            print(f"   Original: {result.get('original_size')}")
            print(f"   Upscaled: {result.get('upscaled_size')}")
            
            # Save result for verification
            output_data = base64.b64decode(result['base64_image'])
            with open('test_output.png', 'wb') as f:
                f.write(output_data)
            print("   💾 Result saved as 'test_output.png'")
            
            return True
        else:
            print(f"❌ File test failed: {response.status_code}")
            try:
                error = response.json()
                print(f"   Error: {error.get('detail')}")
            except:
                pass
            return False
            
    except Exception as e:
        print(f"❌ File test error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Base64 Endpoint Test Script")
    print("=" * 40)
    
    # Validate configuration
    if API_URL == "https://your-domain.easypanel.host":
        print("❌ Please update API_URL in the script!")
        print("   Change it to your actual API domain")
        return
    
    print(f"🎯 Testing API: {API_URL}")
    print()
    
    # Test 1: Health check
    if not test_health():
        print("\n❌ Health check failed - stopping tests")
        return
    
    print()
    
    # Test 2: Simple base64 test
    test_base64_endpoint_simple()
    
    print()
    
    # Test 3: File test (if available)
    test_with_file()
    
    print()
    print("🎉 Tests completed!")
    print()
    print("💡 Common issues:")
    print("   - Check API URL is correct")
    print("   - Ensure Content-Type: application/json header")
    print("   - Verify base64 string doesn't have data URL prefix")
    print("   - Check that image is valid and <2MB")

if __name__ == "__main__":
    main()
