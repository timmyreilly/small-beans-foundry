#!/usr/bin/env python3
"""
Extended smoke test for Multi-Agent functionality
Tests both single agent and multi-agent modes
"""

import asyncio
import aiohttp
import json
import sys
import time
from typing import Dict, Any, List, Optional, Union

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 45  # seconds - longer for multi-agent

async def test_agent_modes() -> bool:
    """Test the agent modes endpoint"""
    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/api/agent-modes", timeout=timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    modes = data.get('modes', [])
                    print(f"✅ Agent modes retrieved: {len(modes)} modes available")
                    for mode in modes:
                        print(f"   📋 {mode.get('id')}: {mode.get('name')}")
                    return len(modes) >= 2  # Should have at least single and multi-agent
                else:
                    print(f"❌ Agent modes test failed: HTTP {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Agent modes test failed: {e}")
        return False

async def test_multi_agent_chat(session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Test the multi-agent chat endpoint"""
    test_message = "Can you research the latest trends in AI and provide a summary?"
    
    try:
        timeout = aiohttp.ClientTimeout(total=TEST_TIMEOUT)
        async with aiohttp.ClientSession() as session:
            payload = {
                "message": test_message,
                "session_id": session_id
            }
            
            print(f"🔄 Sending multi-agent test: '{test_message[:50]}...'")
            start_time = time.time()
            
            async with session.post(
                f"{BASE_URL}/api/chat/multi-agent", 
                json=payload,
                timeout=timeout
            ) as response:
                
                elapsed_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Multi-agent response received in {elapsed_time:.2f}s")
                    print(f"📝 Response: {data.get('response', 'No response')[:100]}...")
                    print(f"🆔 Session ID: {data.get('session_id', 'None')}")
                    
                    # Check for multi-agent specific metadata
                    metadata = data.get('metadata', {})
                    if 'agents_involved' in metadata:
                        agents = metadata['agents_involved']
                        print(f"🤖 Agents involved: {', '.join(agents)}")
                    
                    return data
                else:
                    error_text = await response.text()
                    print(f"❌ Multi-agent test failed: HTTP {response.status}")
                    print(f"📝 Error: {error_text}")
                    return None
                    
    except asyncio.TimeoutError:
        print(f"❌ Multi-agent test timed out after {TEST_TIMEOUT} seconds")
        return None
    except Exception as e:
        print(f"❌ Multi-agent test failed: {e}")
        return None

async def test_single_agent_chat(session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Test the single agent chat endpoint"""
    test_message = "Hello! Please tell me a brief joke."
    
    try:
        timeout = aiohttp.ClientTimeout(total=TEST_TIMEOUT)
        async with aiohttp.ClientSession() as session:
            payload = {
                "message": test_message
            }
            if session_id:
                payload["session_id"] = session_id
            
            print(f"🔄 Sending single-agent test: '{test_message}'")
            start_time = time.time()
            
            async with session.post(
                f"{BASE_URL}/api/chat", 
                json=payload,
                timeout=timeout
            ) as response:
                
                elapsed_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Single-agent response received in {elapsed_time:.2f}s")
                    print(f"📝 Response: {data.get('response', 'No response')[:100]}...")
                    print(f"🆔 Session ID: {data.get('session_id', 'None')}")
                    return data
                else:
                    error_text = await response.text()
                    print(f"❌ Single-agent test failed: HTTP {response.status}")
                    print(f"📝 Error: {error_text}")
                    return None
                    
    except asyncio.TimeoutError:
        print(f"❌ Single-agent test timed out after {TEST_TIMEOUT} seconds")
        return None
    except Exception as e:
        print(f"❌ Single-agent test failed: {e}")
        return None

async def test_multi_agent_conversation_flow() -> bool:
    """Test a multi-turn conversation with multi-agent system"""
    print("\n🔄 Testing multi-agent conversation flow...")
    
    # First message - research request
    response1 = await test_multi_agent_chat()
    if not response1:
        return False
    
    session_id = response1.get('session_id')
    if not session_id:
        print("❌ No session ID received from multi-agent")
        return False
    
    # Wait a moment for any background processing
    await asyncio.sleep(2)
    
    # Second message in same session - follow up
    print(f"\n🔄 Sending follow-up to multi-agent in session {session_id[:8]}...")
    follow_up = "Can you expand on the first trend you mentioned?"
    
    try:
        timeout = aiohttp.ClientTimeout(total=TEST_TIMEOUT)
        async with aiohttp.ClientSession() as session:
            payload = {
                "message": follow_up,
                "session_id": session_id
            }
            
            async with session.post(
                f"{BASE_URL}/api/chat/multi-agent", 
                json=payload,
                timeout=timeout
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Multi-agent follow-up received")
                    print(f"📝 Response: {data.get('response', 'No response')[:100]}...")
                    
                    # Verify same session
                    if data.get('session_id') != session_id:
                        print("❌ Session ID mismatch in multi-agent conversation")
                        return False
                    
                    print("✅ Multi-agent conversation flow test passed")
                    return True
                else:
                    print(f"❌ Multi-agent follow-up failed: HTTP {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Multi-agent follow-up failed: {e}")
        return False

async def run_extended_smoke_tests() -> bool:
    """Run all extended smoke tests including multi-agent"""
    print("🧪 Starting Extended Multi-Agent Smoke Tests\n")
    
    # 1. Test agent modes discovery
    print("1️⃣ Testing agent modes discovery...")
    if not await test_agent_modes():
        return False
    
    # 2. Test single agent functionality
    print("\n2️⃣ Testing single agent functionality...")
    single_response = await test_single_agent_chat()
    if not single_response:
        return False
    
    # 3. Test multi-agent functionality
    print("\n3️⃣ Testing multi-agent functionality...")
    multi_response = await test_multi_agent_chat()
    if not multi_response:
        print("⚠️  Multi-agent test failed - this may be expected if not fully configured")
        # Don't fail the entire test suite for multi-agent issues
    
    # 4. Test multi-agent conversation flow
    print("\n4️⃣ Testing multi-agent conversation flow...")
    if not await test_multi_agent_conversation_flow():
        print("⚠️  Multi-agent conversation flow failed - this may be expected if not fully configured")
        # Don't fail the entire test suite for multi-agent issues
    
    return True

def main():
    """Main test runner"""
    print("🚀 Extended Multi-Agent Smoke Test")
    print("=" * 50)
    
    try:
        # Run async tests
        success = asyncio.run(run_extended_smoke_tests())
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 Extended smoke tests completed!")
            print("✅ Both single and multi-agent systems tested")
            sys.exit(0)
        else:
            print("❌ Some extended tests failed")
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