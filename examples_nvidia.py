"""
NVIDIA Agent Examples
Demonstrates the agent system with NVIDIA's API including reasoning capabilities
"""

from agent import create_agent
import json


def example_1_basic_chat():
    """Example 1: Basic chat with NVIDIA"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Chat with NVIDIA")
    print("="*70 + "\n")
    
    agent = create_agent()
    
    response_data = agent.generate_response("What is artificial intelligence? Explain briefly.")
    
    print("Question: What is artificial intelligence?")
    print("\nResponse:")
    print("-" * 70)
    print(response_data.get('text'))
    print("-" * 70)
    
    if response_data.get('reasoning'):
        print("\n🧠 Reasoning Process:")
        print("-" * 70)
        print(response_data.get('reasoning'))
        print("-" * 70)
    
    print(f"\nLatency: {response_data.get('latency', 0):.2f}s")


def example_2_reasoning_visible():
    """Example 2: See the model's thinking process"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Reasoning Capability (Model's Thinking)")
    print("="*70 + "\n")
    
    agent = create_agent()
    
    question = "If I have 3 apples and buy 5 more, then give away 2, how many do I have?"
    print(f"Question: {question}")
    
    response_data = agent.generate_response(question)
    
    print("\n🤔 Model's Thinking Process:")
    print("-" * 70)
    if response_data.get('reasoning'):
        print(response_data['reasoning'])
    else:
        print("No reasoning content captured")
    print("-" * 70)
    
    print("\n💬 Final Answer:")
    print("-" * 70)
    print(response_data.get('text'))
    print("-" * 70)


def example_3_creative_task():
    """Example 3: Creative writing with reasoning"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Creative Writing")
    print("="*70 + "\n")
    
    agent = create_agent()
    
    prompt = "Write a one-sentence tagline for an AI company"
    response = agent.chat(prompt)
    
    print("Prompt:", prompt)
    print("\nResponse:", response)


def example_4_conversation():
    """Example 4: Multi-turn conversation"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Multi-turn Conversation")
    print("="*70 + "\n")
    
    agent = create_agent()
    
    questions = [
        "What is machine learning?",
        "How is it different from traditional programming?",
        "Give me one simple example"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\nTurn {i}: {question}")
        response = agent.chat(question)
        print(f"Response: {response[:150]}..." if len(response) > 150 else f"Response: {response}")
        print("-" * 70)


def example_5_with_metrics():
    """Example 5: Using the agent with full observability"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Full Observability")
    print("="*70 + "\n")
    
    agent = create_agent()
    
    # Ask a few questions
    questions = [
        "What is Python?",
        "Why is it popular?",
        "Name 3 use cases"
    ]
    
    for q in questions:
        agent.chat(q)
    
    # Show comprehensive metrics
    print("\n📊 AGENT METRICS")
    agent.print_metrics()
    
    # Show observability
    print("\n📝 OBSERVABILITY")
    agent.observer.print_summary()


def example_6_streaming_demo():
    """Example 6: Direct streaming test"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Streaming Response Demo")
    print("="*70 + "\n")
    
    from openai import OpenAI
    
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key="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"
    )
    
    print("Prompt: Explain quantum computing in one sentence")
    print("\nStreaming Response:")
    print("-" * 70)
    
    completion = client.chat.completions.create(
        model="nvidia/nemotron-3-nano-30b-a3b",
        messages=[{"content": "Explain quantum computing in one sentence", "role": "user"}],
        temperature=1,
        top_p=1,
        max_tokens=16384,
        extra_body={
            "reasoning_budget": 16384,
            "chat_template_kwargs": {"enable_thinking": True}
        },
        stream=True
    )
    
    reasoning_shown = False
    for chunk in completion:
        reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
        if reasoning and not reasoning_shown:
            print("\n[MODEL THINKING...]")
            reasoning_shown = True
        
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="", flush=True)
    
    print("\n" + "-" * 70)


def main():
    """Run all examples"""
    print("\n" + "🚀 " * 25)
    print("NVIDIA AGENT SYSTEM - EXAMPLE USAGE")
    print("🚀 " * 25)
    
    examples = [
        ("Basic Chat", example_1_basic_chat),
        ("Reasoning Capability", example_2_reasoning_visible),
        ("Creative Writing", example_3_creative_task),
        ("Multi-turn Conversation", example_4_conversation),
        ("Full Observability", example_5_with_metrics),
        ("Streaming Demo", example_6_streaming_demo),
    ]
    
    print("\nAvailable Examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\n" + "="*70)
    print("Running first 3 examples (quick demo)...")
    print("="*70)
    
    # Run first 3 examples for quick demo
    for name, func in examples[:3]:
        try:
            func()
        except Exception as e:
            print(f"\n✗ Example '{name}' failed: {str(e)}\n")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("DEMO COMPLETED")
    print("="*70)
    print("\nTo run all examples, uncomment the loop in main()")
    print("To run individual examples, call them directly")
    print("\n")


if __name__ == "__main__":
    main()
