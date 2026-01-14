"""
Example Usage of the Simplified Agent System
Demonstrates various features and capabilities
"""

from agent import create_agent


def example_1_basic_chat():
    """Example 1: Basic chat interaction"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Chat")
    print("="*70 + "\n")
    
    # Create agent
    agent = create_agent()
    
    # Simple chat
    response = agent.chat("What are the three laws of robotics?")
    print("Response:", response)
    
    # Show metrics
    agent.print_metrics()


def example_2_multi_turn_conversation():
    """Example 2: Multi-turn conversation"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Multi-turn Conversation")
    print("="*70 + "\n")
    
    agent = create_agent()
    
    messages = [
        "What is machine learning?",
        "How does it differ from traditional programming?",
        "Give me a simple example"
    ]
    
    responses = agent.multi_turn_chat(messages)
    
    for i, response in enumerate(responses, 1):
        print(f"\nTurn {i}:")
        print(f"Prompt: {messages[i-1]}")
        print(f"Response: {response.get('text', 'Error: ' + str(response.get('error')))}")
        print(f"Latency: {response.get('latency', 0):.3f}s")
        print("-" * 70)


def example_3_with_observability():
    """Example 3: Using observability features"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Observability Features")
    print("="*70 + "\n")
    
    agent = create_agent()
    
    # Make some requests
    agent.chat("Explain quantum computing in simple terms")
    agent.chat("What are the main applications?")
    
    # Print comprehensive metrics
    agent.print_metrics()
    
    # Show observability summary
    agent.observer.print_summary()
    
    # Export all data
    agent.export_data("logs")
    print("\n✓ All data exported to logs/ directory")


def example_4_custom_parameters():
    """Example 4: Using custom generation parameters"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Custom Parameters")
    print("="*70 + "\n")
    
    agent = create_agent()
    
    # Low temperature for factual response
    print("Low temperature (0.1) - More focused:")
    response1 = agent.chat(
        "What is the capital of France?",
        temperature=0.1
    )
    print(response1)
    
    print("\n" + "-"*70 + "\n")
    
    # High temperature for creative response
    print("High temperature (0.9) - More creative:")
    response2 = agent.chat(
        "Write a creative tagline for an AI company",
        temperature=0.9
    )
    print(response2)


def example_5_conversation_history():
    """Example 5: Accessing conversation history"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Conversation History")
    print("="*70 + "\n")
    
    agent = create_agent()
    
    # Have a conversation
    agent.chat("What is AI?")
    agent.chat("What are neural networks?")
    agent.chat("How do they learn?")
    
    # Get history
    history = agent.get_conversation_history()
    
    print(f"Total conversations: {len(history)}\n")
    
    for i, conv in enumerate(history, 1):
        print(f"Conversation {i}:")
        print(f"  Prompt: {conv['prompt'][:50]}...")
        print(f"  Response: {conv['response']['text'][:50]}...")
        print(f"  Provider: {conv['provider']}")
        print(f"  Timestamp: {conv['timestamp']}")
        print()


def example_6_provider_metrics():
    """Example 6: Detailed provider metrics"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Provider Metrics")
    print("="*70 + "\n")
    
    agent = create_agent()
    
    # Make multiple requests
    for i in range(3):
        agent.chat(f"Tell me an interesting fact about number {i+1}")
    
    # Get detailed metrics
    metrics = agent.get_metrics()
    
    print("Detailed Metrics:")
    import json
    print(json.dumps(metrics, indent=2))


def main():
    """Run all examples"""
    print("\n" + "🚀 " * 25)
    print("AGENT SYSTEM - EXAMPLE USAGE")
    print("🚀 " * 25)
    
    examples = [
        ("Basic Chat", example_1_basic_chat),
        ("Multi-turn Conversation", example_2_multi_turn_conversation),
        ("Observability Features", example_3_with_observability),
        ("Custom Parameters", example_4_custom_parameters),
        ("Conversation History", example_5_conversation_history),
        ("Provider Metrics", example_6_provider_metrics),
    ]
    
    print("\nAvailable Examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\nRunning all examples...\n")
    
    for name, func in examples:
        try:
            func()
        except Exception as e:
            print(f"\n✗ Example '{name}' failed: {str(e)}\n")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("ALL EXAMPLES COMPLETED")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
