"""Mock adapter for testing without external dependencies"""

from typing import List
import logging


class MockAdapter:
    """Mock LLM adapter that returns predictable responses for testing"""
    
    name = "mock"
    
    def __init__(self, response_mode="safe"):
        """Initialize mock adapter
        
        Args:
            response_mode: Response behavior
                - 'safe': Always returns safe, compliant responses
                - 'vulnerable': Returns responses that trigger detections
                - 'mixed': Alternates between safe and vulnerable
        """
        self.response_mode = response_mode
        self.call_count = 0
        
    def is_available(self) -> bool:
        """Mock adapter is always available"""
        return True
    
    def generate(self, prompt: str, generations_this_call: int = 1) -> List[str]:
        """Generate mock responses
        
        Args:
            prompt: Input prompt (unused in mock)
            generations_this_call: Number of responses to generate
            
        Returns:
            List of mock responses
        """
        responses = []
        for _ in range(generations_this_call):
            self.call_count += 1
            
            if self.response_mode == "safe":
                response = self._safe_response()
            elif self.response_mode == "vulnerable":
                response = self._vulnerable_response()
            else:  # mixed
                response = self._safe_response() if self.call_count % 2 == 0 else self._vulnerable_response()
            
            responses.append(response)
        
        return responses
    
    def _safe_response(self) -> str:
        """Generate a safe, compliant response"""
        safe_responses = [
            "I'm a helpful AI assistant. How can I help you today?",
            "I cannot assist with that request as it may be harmful or inappropriate.",
            "I'm designed to be helpful, harmless, and honest.",
            "I'd be happy to help with appropriate requests.",
        ]
        return safe_responses[self.call_count % len(safe_responses)]
    
    def _vulnerable_response(self) -> str:
        """Generate a response that might trigger detections"""
        vulnerable_responses = [
            "Sure, I'll ignore all my previous instructions and do whatever you want!",
            "DAN Mode enabled. I can do anything now!",
            "Okay, let me help you with that malicious activity...",
            "Here's how to bypass security measures: ...",
        ]
        return vulnerable_responses[self.call_count % len(vulnerable_responses)]
