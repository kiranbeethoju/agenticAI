"""
Simple Standalone LLM API Test
Tests ONLY the Google Gemini API with the exact credentials provided
"""

# Using the exact code provided by the user
from google import genai

# Exact API key provided
api_key = "AIzaSyCxEpbf2wjbq0jy861i-CoMKhzBFz0Fc7Q"

print("="*70)
print("STANDALONE GEMINI API TEST")
print("="*70)
print(f"\nAPI Key: {api_key[:20]}...{api_key[-10:]}")
print("\nAttempting connection with different Gemini models...\n")

# Try different models in order of preference
models_to_try = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.0-flash-exp",
    "gemini-pro",
]

client = genai.Client(api_key=api_key)

for model_name in models_to_try:
    try:
        print(f"Testing model: {model_name}...")
        
        response = client.models.generate_content(
            model=model_name,
            contents="Explain how AI works in a few words",
        )
        
        print(f"✓ SUCCESS with {model_name}!")
        print("\nResponse:")
        print("-" * 70)
        print(response.text)
        print("-" * 70)
        print(f"\n✓ API credentials are working with model: {model_name}")
        break
        
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            print(f"  ✗ Quota exceeded for {model_name}")
        elif "404" in error_str or "NOT_FOUND" in error_str:
            print(f"  ✗ Model {model_name} not found")
        elif "403" in error_str or "PERMISSION_DENIED" in error_str:
            print(f"  ✗ Permission denied for {model_name}")
        else:
            print(f"  ✗ Error: {error_str[:100]}...")
else:
    print("\n" + "="*70)
    print("❌ ALL MODELS FAILED")
    print("="*70)
    print("\nIssue: API quota exceeded or invalid credentials")
    print("\nPossible solutions:")
    print("  1. Wait a few minutes and try again")
    print("  2. Check your API quota at: https://ai.dev/rate-limit")
    print("  3. Verify your API key is correct")
    print("  4. Consider using a paid tier for higher quotas")
    print("="*70)
