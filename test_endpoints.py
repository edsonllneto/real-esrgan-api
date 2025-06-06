#!/usr/bin/env python3
"""
Real-ESRGAN API Test Script
Tests both file upload and base64 endpoints
"""

import requests
import base64
import json
import time
from pathlib import Path

# Configuration
API_BASE_URL = "https://your-domain.easypanel.host"  # Replace with your API URL
TEST_IMAGE_PATH = "test_image.jpg"  # Replace with your test image path

def test_health():
    """Test API health endpoint"""
    print("🔍 Testing API health...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API is {data['status']}")
            print(f"   Backend: {data['backend']}")
            print(f"   Quality: {data['backend_quality']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_file_upload_endpoint(image_path, scale=4):
    """Test the /upscale endpoint (multipart file upload)"""
    print(f"\n📁 Testing file upload endpoint...")
    print(f"   Image: {image_path}")
    print(f"   Scale: {scale}x")
    
    if not Path(image_path).exists():
        print(f"❌ Image file not found: {image_path}")
        return None
    
    try:
        start_time = time.time()
        
        with open(image_path, 'rb') as f:
            files = {'file': f}
            data = {'scale': scale, 'model': 'auto'}
            
            response = requests.post(
                f"{API_BASE_URL}/upscale",
                files=files,
                data=data,
                timeout=300  # 5 minutes timeout
            )
        
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload endpoint successful!")
            print(f"   Time: {elapsed_time:.1f}s")
            print(f"   Backend: {result['backend']}")
            print(f"   Quality: {result['backend_quality']}")
            print(f"   Original: {result['original_size']}")
            print(f"   Upscaled: {result['upscaled_size']}")
            print(f"   Memory used: {result['memory_used_mb']:.1f}MB")
            
            # Save result
            image_data = base64.b64decode(result['base64_image'])
            output_path = f"upscaled_upload_{scale}x.png"
            with open(output_path, 'wb') as f:
                f.write(image_data)
            print(f"   Saved: {output_path}")
            
            return result
        else:
            print(f"❌ Upload endpoint failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ Upload endpoint timeout (>5 minutes)")
        return None
    except Exception as e:
        print(f"❌ Upload endpoint error: {e}")
        return None

def test_base64_endpoint(image_path, scale=4):
    """Test the /upscale-base64 endpoint (JSON with base64)"""
    print(f"\n🔤 Testing base64 endpoint...")
    print(f"   Image: {image_path}")
    print(f"   Scale: {scale}x")
    
    if not Path(image_path).exists():
        print(f"❌ Image file not found: {image_path}")
        return None
    
    try:
        # Convert image to base64
        with open(image_path, 'rb') as f:
            image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        print(f"   Base64 size: {len(image_base64)} chars")
        
        payload = {
            "image_base64": image_base64,
            "scale": scale,
            "model": "auto",
            "format": "auto"
        }
        
        start_time = time.time()
        
        response = requests.post(
            f"{API_BASE_URL}/upscale-base64",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=300  # 5 minutes timeout
        )
        
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Base64 endpoint successful!")
            print(f"   Time: {elapsed_time:.1f}s")
            print(f"   Backend: {result['backend']}")
            print(f"   Quality: {result['backend_quality']}")
            print(f"   Original: {result['original_size']}")
            print(f"   Upscaled: {result['upscaled_size']}")
            print(f"   Memory used: {result['memory_used_mb']:.1f}MB")
            
            # Save result
            image_data = base64.b64decode(result['base64_image'])
            output_path = f"upscaled_base64_{scale}x.png"
            with open(output_path, 'wb') as f:
                f.write(image_data)
            print(f"   Saved: {output_path}")
            
            return result
        else:
            print(f"❌ Base64 endpoint failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ Base64 endpoint timeout (>5 minutes)")
        return None
    except Exception as e:
        print(f"❌ Base64 endpoint error: {e}")
        return None

def compare_results(result1, result2):
    """Compare results from both endpoints"""
    if not result1 or not result2:
        print("\n⚠️  Cannot compare - one or both tests failed")
        return
    
    print(f"\n📊 Comparison:")
    print(f"   Upload endpoint:")
    print(f"     Backend: {result1['backend']}")
    print(f"     Size: {result1['upscaled_size']}")
    print(f"     Memory: {result1['memory_used_mb']:.1f}MB")
    
    print(f"   Base64 endpoint:")
    print(f"     Backend: {result2['backend']}")
    print(f"     Size: {result2['upscaled_size']}")
    print(f"     Memory: {result2['memory_used_mb']:.1f}MB")
    
    if result1['backend'] == result2['backend']:
        print("✅ Both endpoints used the same backend")
    else:
        print("⚠️  Different backends used (this is unusual)")

def main():
    """Main test function"""
    print("🚀 Real-ESRGAN API Endpoint Tests")
    print("=" * 50)
    
    # Test health first
    if not test_health():
        print("\n❌ API health check failed - stopping tests")
        return
    
    # Check if test image exists
    if not Path(TEST_IMAGE_PATH).exists():
        print(f"\n⚠️  Test image not found: {TEST_IMAGE_PATH}")
        print("   Please replace TEST_IMAGE_PATH with your image file")
        print("   Continuing with endpoints that don't require image...")
        return
    
    # Test both endpoints
    result1 = test_file_upload_endpoint(TEST_IMAGE_PATH, scale=4)
    result2 = test_base64_endpoint(TEST_IMAGE_PATH, scale=4)
    
    # Compare results
    compare_results(result1, result2)
    
    print(f"\n🎉 Tests completed!")
    print("   Check the generated upscaled_*.png files")

if __name__ == "__main__":
    # Update these before running
    if API_BASE_URL == "https://your-domain.easypanel.host":
        print("⚠️  Please update API_BASE_URL in the script")
        print("   Change it to your actual API domain")
        exit(1)
    
    if not Path(TEST_IMAGE_PATH).exists():
        print("⚠️  Please update TEST_IMAGE_PATH in the script")
        print("   Point it to an actual image file for testing")
        exit(1)
    
    main()
