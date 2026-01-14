"""
NVIDIA API Test Script
Tests the NVIDIA API credentials and streaming capability
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_nvidia_api_direct():
    """Test NVIDIA API directly with the provided code"""
    print("="*70)
    print("NVIDIA API DIRECT TEST")
    print("="*70)
    print(f"Test started at: {datetime.now().isoformat()}\n")
    
    # Test credentials
    api_key = "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"
    base_url = "https://integrate.api.nvidia.com/v1"
    model = "nvidia/gpt-oss-20b"
    
    print(f"API Key: {api_key[:20]}...{api_key[-10:]}")
    print(f"Base URL: {base_url}")
    print(f"Model: {model}")
    
    try:
        # Import and setup
        print("\n[1/4] Importing openai library...")
        from openai import OpenAI
        print("✓ Import successful")
        
        # Initialize client
        print("\n[2/4] Initializing NVIDIA client...")
        client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        print("✓ Client initialized")
        
        # Test API call with streaming
        print("\n[3/4] Testing API with streaming...")
        test_prompt = "Hi! Respond with just 'Hello from NVIDIA!'"
        print(f"Prompt: '{test_prompt}'")
        
        completion = client.chat.completions.create(
            model=model,
            messages=[{"content": test_prompt, "role": "user"}],
            temperature=1,
            top_p=1,
            max_tokens=1024,
            stream=True
        )
        
        print("✓ API call successful")
        
        # Display streaming response
        print("\n[4/4] Streaming response:")
        print("-" * 70)
        
        full_response = ""
        reasoning_parts = []
        
        for chunk in completion:
            # Capture reasoning content if available
            reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
            if reasoning:
                reasoning_parts.append(reasoning)
                print(f"[THINKING] {reasoning}", end="")
            
            # Capture and display regular content
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                full_response += content
                print(content, end="", flush=True)
        
        print("\n" + "-" * 70)
        
        # Summary
        print("\n" + "="*70)
        print("✓ TEST PASSED - NVIDIA API is working correctly!")
        print("="*70)
        print(f"\nFull Response: {full_response}")
        if reasoning_parts:
            print(f"Reasoning Content: {''.join(reasoning_parts)}")
        
        return True
        
    except ImportError as e:
        print(f"\n✗ Import Error: {str(e)}")
        print("\nPlease install the required package:")
        print("  pip3 install openai")
        return False
        
    except Exception as e:
        print(f"\n✗ API Test Failed: {str(e)}")
        print("\nPossible issues:")
        print("  1. Invalid API key")
        print("  2. Network connectivity issues")
        print("  3. Model not available")
        print("  4. API quota exceeded")
        return False


def test_nvidia_with_agent():
    """Test NVIDIA API using the agent system"""
    print("\n\n" + "="*70)
    print("NVIDIA AGENT SYSTEM TEST")
    print("="*70)
    
    try:
        print("\n[1/3] Importing agent system...")
        from agent import create_agent
        print("✓ Import successful")
        
        print("\n[2/3] Creating agent instance with NVIDIA provider...")
        agent = create_agent("config.yaml")
        print("✓ Agent created")
        print(f"  - Default provider: {agent.default_provider.__class__.__name__}")
        
        print("\n[3/3] Testing agent with NVIDIA...")
        response = agent.chat("What is 2+2? Answer in one short sentence.")
        
        print("\nAgent Response:")
        print("-" * 70)
        print(response)
        print("-" * 70)
        
        # Show metrics
        print("\n")
        agent.print_metrics()
        
        print("\n" + "="*70)
        print("✓ NVIDIA AGENT SYSTEM TEST PASSED!")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Agent System Test Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "🚀 " * 25)
    print("NVIDIA API - COMPREHENSIVE TEST SUITE")
    print("🚀 " * 25 + "\n")
    
    # Test 1: Direct NVIDIA API
    direct_success = test_nvidia_api_direct()
    
    # Test 2: Agent System with NVIDIA
    agent_success = False
    if direct_success:
        agent_success = test_nvidia_with_agent()
    else:
        print("\n⚠️  Skipping agent system test due to API issues")
    
    # Final summary
    print("\n\n" + "="*70)
    print("FINAL TEST SUMMARY")
    print("="*70)
    print(f"Direct NVIDIA API Test:  {'✓ PASSED' if direct_success else '✗ FAILED'}")
    print(f"Agent System Test:       {'✓ PASSED' if agent_success else '✗ FAILED (skipped)' if not direct_success else '✗ FAILED'}")
    print("="*70)
    
    if direct_success and agent_success:
        print("\n🎉 All tests passed! Your NVIDIA agent system is ready to use.")
    elif direct_success:
        print("\n⚠️  NVIDIA API works but agent system needs attention.")
    else:
        print("\n❌ Please check the NVIDIA API credentials and try again.")
    
    print()


if __name__ == "__main__":
    main()
