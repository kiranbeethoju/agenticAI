"""
LLM API Test Script
Tests the LLM API credentials to verify they are working correctly
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_gemini_api():
    """Test Google Gemini API with provided credentials"""
    print("="*70)
    print("GOOGLE GEMINI API TEST")
    print("="*70)
    print(f"Test started at: {datetime.now().isoformat()}\n")
    
    # Test credentials
    api_key = "AIzaSyCxEpbf2wjbq0jy861i-CoMKhzBFz0Fc7Q"
    print(f"API Key: {api_key[:20]}...{api_key[-10:]}")
    
    try:
        # Import and setup
        print("\n[1/4] Importing google.genai...")
        from google import genai
        print("✓ Import successful")
        
        # Initialize client
        print("\n[2/4] Initializing Gemini client...")
        client = genai.Client(api_key=api_key)
        print("✓ Client initialized")
        
        # Test API call
        print("\n[3/4] Testing API with sample prompt...")
        test_prompt = "Explain how AI works in a few words"
        print(f"Prompt: '{test_prompt}'")
        
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=test_prompt,
        )
        
        print("✓ API call successful")
        
        # Display response
        print("\n[4/4] Response received:")
        print("-" * 70)
        print(response.text)
        print("-" * 70)
        
        # Success summary
        print("\n" + "="*70)
        print("✓ TEST PASSED - API credentials are working correctly!")
        print("="*70)
        
        return True
        
    except ImportError as e:
        print(f"\n✗ Import Error: {str(e)}")
        print("\nPlease install the required package:")
        print("  pip install google-genai")
        return False
        
    except Exception as e:
        print(f"\n✗ API Test Failed: {str(e)}")
        print("\nPossible issues:")
        print("  1. Invalid API key")
        print("  2. API quota exceeded")
        print("  3. Network connectivity issues")
        print("  4. Model name incorrect")
        return False


def test_agent_system():
    """Test the complete agent system"""
    print("\n\n" + "="*70)
    print("AGENT SYSTEM TEST")
    print("="*70)
    
    try:
        print("\n[1/3] Importing agent system...")
        from agent import create_agent
        print("✓ Import successful")
        
        print("\n[2/3] Creating agent instance...")
        agent = create_agent("config.yaml")
        print("✓ Agent created")
        
        print("\n[3/3] Testing agent with sample query...")
        response = agent.chat("What is 2+2? Answer in one sentence.")
        
        print("\nAgent Response:")
        print("-" * 70)
        print(response)
        print("-" * 70)
        
        # Show metrics
        print("\n")
        agent.print_metrics()
        
        print("\n" + "="*70)
        print("✓ AGENT SYSTEM TEST PASSED!")
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
    print("LLM API & AGENT SYSTEM - COMPREHENSIVE TEST SUITE")
    print("🚀 " * 25 + "\n")
    
    # Test 1: Gemini API
    gemini_success = test_gemini_api()
    
    # Test 2: Agent System (only if Gemini works)
    agent_success = False
    if gemini_success:
        agent_success = test_agent_system()
    else:
        print("\n⚠️  Skipping agent system test due to API credential issues")
    
    # Final summary
    print("\n\n" + "="*70)
    print("FINAL TEST SUMMARY")
    print("="*70)
    print(f"Gemini API Test:    {'✓ PASSED' if gemini_success else '✗ FAILED'}")
    print(f"Agent System Test:  {'✓ PASSED' if agent_success else '✗ FAILED (skipped)' if not gemini_success else '✗ FAILED'}")
    print("="*70)
    
    if gemini_success and agent_success:
        print("\n🎉 All tests passed! Your agent system is ready to use.")
    elif gemini_success:
        print("\n⚠️  Gemini API works but agent system needs attention.")
    else:
        print("\n❌ Please fix the API credentials and try again.")
    
    print()


if __name__ == "__main__":
    main()
