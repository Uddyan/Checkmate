"""Tests for adapters"""

import pytest
import os
from unittest.mock import Mock, patch

from checkmate.adapters import get_adapter
from checkmate.adapters.null import NullAdapter
from checkmate.core.types import Conversation, Message


@pytest.fixture
def sample_conversation():
    """Create a sample conversation for testing"""
    return Conversation(messages=[
        Message(role="user", content="Hello, how are you?")
    ])


def test_null_adapter(sample_conversation):
    """Test null adapter (always available, deterministic)"""
    adapter = get_adapter("null")
    
    assert adapter.is_available()
    
    generations = adapter.generate(sample_conversation)
    assert len(generations) > 0
    assert generations[0].text is not None


def test_get_adapter_invalid():
    """Test getting invalid adapter raises error"""
    with pytest.raises(ValueError, match="Unknown adapter"):
        get_adapter("invalid_adapter")


def test_anthropic_adapter_availability():
    """Test Anthropic adapter availability check"""
    # Should not fail even if package not installed
    try:
        adapter = get_adapter("anthropic", api_key="test-key")
        # If it loads, check availability
        available = adapter.is_available()
        # Should be False if package not installed or key invalid
        assert isinstance(available, bool)
    except RuntimeError:
        # Expected if dependencies not installed
        pass


def test_cohere_adapter_availability():
    """Test Cohere adapter availability check"""
    try:
        adapter = get_adapter("cohere", api_key="test-key")
        available = adapter.is_available()
        assert isinstance(available, bool)
    except RuntimeError:
        pass


def test_mistral_adapter_availability():
    """Test Mistral adapter availability check"""
    try:
        adapter = get_adapter("mistral", api_key="test-key")
        available = adapter.is_available()
        assert isinstance(available, bool)
    except RuntimeError:
        pass


@pytest.mark.integration
def test_http_local_adapter_connection():
    """Integration test for HTTP local adapter (requires running server)"""
    # Skip if no server available
    adapter = get_adapter("http_local", base_url="http://localhost:8000")
    
    # Just test availability check, not actual generation
    # (would require running server)
    available = adapter.is_available()
    assert isinstance(available, bool)

