#!/usr/bin/env python3
"""Basic usage example for checkmate"""

from checkmate.adapters import get_adapter
from checkmate.core.types import Conversation, Message


def main():
    """Demonstrate basic checkmate usage"""
    print("🔍 Checkmate Basic Usage Example")
    print("=" * 40)
    
    # Create a null adapter for offline testing
    print("1. Creating null adapter...")
    adapter = get_adapter("null")
    print(f"   Adapter: {adapter}")
    print(f"   Available: {adapter.is_available()}")
    
    # Create a conversation
    print("\n2. Creating conversation...")
    conversation = Conversation(messages=[
        Message(role="user", content="Hello, how are you?"),
        Message(role="assistant", content="I'm doing well, thank you!"),
        Message(role="user", content="Can you help me with a task?")
    ])
    print(f"   Conversation: {conversation.to_string()}")
    
    # Generate response
    print("\n3. Generating response...")
    generations = adapter.generate(conversation)
    print(f"   Generated {len(generations)} response(s)")
    for i, gen in enumerate(generations):
        print(f"   Response {i+1}: '{gen.text}'")
        print(f"   Metadata: {gen.metadata}")
    
    print("\n✅ Example completed successfully!")


if __name__ == "__main__":
    main()
