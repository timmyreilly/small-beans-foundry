#!/usr/bin/env python3
"""
Functional smoke test for Agentic UI v0
Tests that the single AutoGen agent can handle basic conversations
"""

import asyncio
import aiohttp
import json
import sys
import time
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30  # seconds

async def health_check() -> bool:
    """Check if the backend service is healthy"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/health", timeout=5) as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ Health check passed: {health_data.get('overall_status', 'unknown')}")
                    
                    # Check Azure configuration
                    azure_status = health_data.get('components', {}).get('azure_config', {}).get('status', 'unknown')
                    if azure_status == 'warn':
                        print("⚠️  Azure configuration not complete - some tests may fail")
                    
                    return True
                else:
                    print(f"❌ Health check failed: HTTP {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

async def test_chat_endpoint(session_id: str = None) -> Dict[str, Any]:
    """Test the chat endpoint with a simple message"""
    test_message = "Hello! Can you tell me what you are?"
    
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "message": test_message,
                "session_id": session_id
            }
            
            print(f"🔄 Sending test message: '{test_message}'")
            start_time = time.time()
            
            async with session.post(
                f"{BASE_URL}/api/chat", 
                json=payload,
                timeout=TEST_TIMEOUT
            ) as response:
                
                elapsed_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Chat response received in {elapsed_time:.2f}s")
                    print(f"📝 Response: {data.get('response', 'No response')[:100]}...")
                    print(f"🆔 Session ID: {data.get('session_id', 'None')}")
                    return data
                else:
                    error_text = await response.text()
                    print(f"❌ Chat test failed: HTTP {response.status}")
                    print(f"📝 Error: {error_text}")
                    return None
                    
    except asyncio.TimeoutError:
        print(f"❌ Chat test timed out after {TEST_TIMEOUT} seconds")
        return None
    except Exception as e:
        print(f"❌ Chat test failed: {e}")
        return None

async def test_conversation_flow() -> bool:
    """Test a multi-turn conversation"""
    print("\n🔄 Testing conversation flow...")
    
    # First message
    response1 = await test_chat_endpoint()
    if not response1:
        return False
    
    session_id = response1.get('session_id')
    if not session_id:
        print("❌ No session ID received")
        return False
    
    # Second message in same session
    print(f"\n🔄 Sending follow-up message in session {session_id[:8]}...")
    response2 = await test_chat_endpoint(session_id)
    if not response2:
        return False
    
    # Verify same session
    if response2.get('session_id') != session_id:
        print("❌ Session ID mismatch in conversation")
        return False
    
    print("✅ Conversation flow test passed")
    return True

async def test_session_history(session_id: str) -> bool:
    """Test retrieving session history"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BASE_URL}/api/sessions/{session_id}/messages",
                timeout=5
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    messages = data.get('messages', [])
                    print(f"✅ Session history retrieved: {len(messages)} messages")
                    return True
                else:
                    print(f"❌ Session history test failed: HTTP {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Session history test failed: {e}")
        return False

async def run_smoke_tests() -> bool:
    """Run all smoke tests"""
    print("🧪 Starting Agentic UI v0 Smoke Tests\n")
    
    # 1. Health check
    print("1️⃣ Testing service health...")
    if not await health_check():
        return False
    
    # 2. Basic chat test
    print("\n2️⃣ Testing basic chat functionality...")
    chat_response = await test_chat_endpoint()
    if not chat_response:
        return False
    
    session_id = chat_response.get('session_id')
    
    # 3. Session history test
    print("\n3️⃣ Testing session history...")
    if not await test_session_history(session_id):
        return False
    
    # 4. Conversation flow test
    print("\n4️⃣ Testing conversation flow...")
    if not await test_conversation_flow():
        return False
    
    return True

def main():
    """Main test runner"""
    print("🚀 Agentic UI v0 Functional Smoke Test")
    print("=" * 50)
    
    try:
        # Run async tests
        success = asyncio.run(run_smoke_tests())
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 All smoke tests passed!")
            print("✅ Agentic UI v0 is working correctly")
            sys.exit(0)
        else:
            print("❌ Some smoke tests failed")
            print("🔧 Please check the service configuration and logs")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()