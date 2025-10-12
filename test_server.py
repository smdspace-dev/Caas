#!/usr/bin/env python3
"""
Test server connectivity and show available endpoints
"""

import requests
import json
import time
from datetime import datetime

def test_server_connectivity():
    """Test if the server is running and accessible"""
    
    print("🔍 Testing Server Connectivity")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Test basic connectivity
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and accessible!")
            health_data = response.json()
            print(f"📊 Health Status: {health_data.get('status', 'unknown')}")
            print(f"⏰ Server Time: {health_data.get('timestamp', 'unknown')}")
        else:
            print(f"❌ Server responded with status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running?")
        return False
    except Exception as e:
        print(f"❌ Error testing connectivity: {e}")
        return False
    
    return True

def show_available_endpoints():
    """Show all available endpoints for testing"""
    
    print("\n📋 Available Endpoints for Testing")
    print("=" * 50)
    
    endpoints = [
        {
            "method": "GET",
            "url": "http://localhost:5000/",
            "description": "Home page with system overview",
            "test_command": "curl http://localhost:5000/"
        },
        {
            "method": "GET", 
            "url": "http://localhost:5000/api/health",
            "description": "Health check endpoint",
            "test_command": "curl http://localhost:5000/api/health"
        },
        {
            "method": "GET",
            "url": "http://localhost:5000/api/system/status", 
            "description": "Detailed system status with Phase 4 features",
            "test_command": "curl http://localhost:5000/api/system/status"
        },
        {
            "method": "GET",
            "url": "http://localhost:5000/api/documents",
            "description": "List all uploaded documents",
            "test_command": "curl http://localhost:5000/api/documents"
        },
        {
            "method": "POST",
            "url": "http://localhost:5000/api/documents/upload",
            "description": "Upload a document for processing",
            "test_command": "curl -X POST http://localhost:5000/api/documents/upload -F 'file=@your_file.pdf'"
        },
        {
            "method": "POST",
            "url": "http://localhost:5000/api/search",
            "description": "Advanced hybrid search",
            "test_command": 'curl -X POST http://localhost:5000/api/search -H "Content-Type: application/json" -d "{\\"query\\": \\"test\\", \\"type\\": \\"hybrid\\"}"'
        },
        {
            "method": "POST",
            "url": "http://localhost:5000/api/chat",
            "description": "Enhanced chat with context-aware responses",
            "test_command": 'curl -X POST http://localhost:5000/api/chat -H "Content-Type: application/json" -d "{\\"message\\": \\"Hello, what can you do?\\"}"'
        },
        {
            "method": "GET",
            "url": "http://localhost:5000/api/operations",
            "description": "Complete operations documentation",
            "test_command": "curl http://localhost:5000/api/operations"
        }
    ]
    
    for i, endpoint in enumerate(endpoints, 1):
        print(f"\n{i}. {endpoint['method']} {endpoint['url']}")
        print(f"   📝 {endpoint['description']}")
        print(f"   🔧 Test: {endpoint['test_command']}")

def test_sample_endpoints():
    """Test a few sample endpoints"""
    
    print("\n🧪 Testing Sample Endpoints")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Test home page
    try:
        print("\n1. Testing Home Page...")
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ Home page accessible")
            data = response.json()
            print(f"   📊 Features: {len(data.get('features', []))} Phase 4 features available")
        else:
            print(f"❌ Home page error: {response.status_code}")
    except Exception as e:
        print(f"❌ Home page test failed: {e}")
    
    # Test system status
    try:
        print("\n2. Testing System Status...")
        response = requests.get(f"{base_url}/api/system/status", timeout=5)
        if response.status_code == 200:
            print("✅ System status accessible")
            data = response.json()
            features = data.get('features', {})
            print(f"   📊 Phase: {data.get('phase', 'unknown')}")
            print(f"   🔧 Document Processing: {'✅' if features.get('document_processing', {}).get('enabled') else '❌'}")
            print(f"   🔍 Hybrid Search: {'✅' if features.get('hybrid_search', {}).get('enabled') else '❌'}")
            print(f"   🧩 Intelligent Chunking: {'✅' if features.get('intelligent_chunking', {}).get('enabled') else '❌'}")
        else:
            print(f"❌ System status error: {response.status_code}")
    except Exception as e:
        print(f"❌ System status test failed: {e}")
    
    # Test documents list
    try:
        print("\n3. Testing Documents List...")
        response = requests.get(f"{base_url}/api/documents", timeout=5)
        if response.status_code == 200:
            print("✅ Documents list accessible")
            data = response.json()
            doc_count = len(data.get('documents', []))
            print(f"   📄 Documents: {doc_count} documents found")
            print(f"   📁 Supported formats: {len(data.get('supported_formats', []))} formats")
        else:
            print(f"❌ Documents list error: {response.status_code}")
    except Exception as e:
        print(f"❌ Documents list test failed: {e}")
    
    # Test chat endpoint
    try:
        print("\n4. Testing Chat Endpoint...")
        chat_data = {"message": "Hello, can you tell me about your capabilities?"}
        response = requests.post(f"{base_url}/api/chat", 
                               json=chat_data, 
                               headers={"Content-Type": "application/json"},
                               timeout=10)
        if response.status_code == 200:
            print("✅ Chat endpoint accessible")
            data = response.json()
            print(f"   💬 Response received: {len(data.get('response', ''))} characters")
            print(f"   🔧 Features used: {len(data.get('features_used', []))} features")
        else:
            print(f"❌ Chat endpoint error: {response.status_code}")
    except Exception as e:
        print(f"❌ Chat endpoint test failed: {e}")

if __name__ == "__main__":
    print("🚀 Advanced RAG System - Server Testing")
    print("=" * 50)
    print(f"⏰ Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if test_server_connectivity():
        show_available_endpoints()
        test_sample_endpoints()
        
        print("\n" + "=" * 50)
        print("🎯 SERVER IS RUNNING AND READY FOR TESTING!")
        print("=" * 50)
        print("🌐 Main URL: http://localhost:5000")
        print("🔍 Health Check: http://localhost:5000/api/health")
        print("📊 System Status: http://localhost:5000/api/system/status")
        print("📋 All Operations: http://localhost:5000/api/operations")
        print("=" * 50)
    else:
        print("\n❌ Server is not accessible. Please check if it's running.")