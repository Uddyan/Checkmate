"""Tests for checkmate adapters"""

import pytest
from checkmate.adapters import get_adapter, ADAPTERS
from checkmate.adapters.null import NullAdapter
from checkmate.adapters.hf_local import HFLocalAdapter
from checkmate.adapters.openai_compatible import OpenAICompatibleAdapter
from checkmate.core.types import Conversation, Message


class TestAdapterRegistry:
    """Test adapter registry functionality"""
    
    def test_get_adapter_null(self):
        """Test getting null adapter"""
        adapter = get_adapter("null")
        assert isinstance(adapter, NullAdapter)
        assert adapter.is_available()
    
    def test_get_adapter_unknown(self):
        """Test getting unknown adapter raises error"""
        with pytest.raises(ValueError, match="Unknown adapter"):
            get_adapter("unknown")
    
    def test_adapter_registry(self):
        """Test adapter registry contains expected adapters"""
        assert "null" in ADAPTERS
        assert "hf_local" in ADAPTERS
        assert "openai_compatible" in ADAPTERS


class TestNullAdapter:
    """Test null adapter functionality"""
    
    def test_null_adapter_creation(self):
        """Test null adapter can be created"""
        adapter = NullAdapter()
        assert adapter.name == "null"
        assert adapter.active
        assert adapter.is_available()
    
    def test_null_adapter_generate(self):
        """Test null adapter generates empty responses"""
        adapter = NullAdapter()
        conversation = Conversation(messages=[
            Message(role="user", content="Hello")
        ])
        
        generations = adapter.generate(conversation)
        assert len(generations) == 1
        assert generations[0].text == ""
        assert "adapter" in generations[0].metadata


class TestHFLocalAdapter:
    """Test Hugging Face local adapter"""
    
    def test_hf_adapter_creation(self):
        """Test HF adapter can be created"""
        adapter = HFLocalAdapter(model_name="sshleifer/tiny-gpt2")
        assert adapter.name == "hf_local"
        assert adapter.model_name == "sshleifer/tiny-gpt2"
    
    def test_hf_adapter_availability(self):
        """Test HF adapter availability check"""
        adapter = HFLocalAdapter()
        # This will depend on whether transformers is installed
        # In a real test environment, we might mock this
        assert isinstance(adapter.is_available(), bool)


class TestOpenAICompatibleAdapter:
    """Test OpenAI-compatible adapter"""
    
    def test_openai_adapter_creation(self):
        """Test OpenAI adapter can be created"""
        adapter = OpenAICompatibleAdapter()
        assert adapter.name == "openai_compatible"
        assert adapter.model == "gpt-3.5-turbo"
    
    def test_openai_adapter_availability(self):
        """Test OpenAI adapter availability check"""
        adapter = OpenAICompatibleAdapter()
        # This will depend on API key and openai package
        assert isinstance(adapter.is_available(), bool)


class TestConversation:
    """Test conversation data structure"""
    
    def test_conversation_creation(self):
        """Test conversation can be created"""
        conversation = Conversation(messages=[])
        assert len(conversation.messages) == 0
    
    def test_conversation_add_message(self):
        """Test adding messages to conversation"""
        conversation = Conversation(messages=[])
        conversation.add_message("user", "Hello")
        conversation.add_message("assistant", "Hi there!")
        
        assert len(conversation.messages) == 2
        assert conversation.messages[0].role == "user"
        assert conversation.messages[0].content == "Hello"
        assert conversation.messages[1].role == "assistant"
        assert conversation.messages[1].content == "Hi there!"
    
    def test_conversation_to_string(self):
        """Test conversation string conversion"""
        conversation = Conversation(messages=[
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there!")
        ])
        
        expected = "user: Hello\nassistant: Hi there!"
        assert conversation.to_string() == expected
