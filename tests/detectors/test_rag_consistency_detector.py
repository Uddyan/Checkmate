# SPDX-License-Identifier: Apache-2.0
"""Tests for RAGConsistencyDetector.

Tests the RAG consistency detection capability for hallucination detection.
"""

import pytest
from checkmate.detectors.rag_consistency import RAGConsistencyDetector
from checkmate.detectors.registry import get_detector, list_detectors


class TestRAGConsistencyDetector:
    """Tests for RAGConsistencyDetector"""
    
    def test_detector_creation(self):
        """Test detector can be instantiated"""
        detector = RAGConsistencyDetector()
        assert detector.name == "rag_consistency"
        assert detector.threshold == 0.5
    
    def test_detects_low_keyword_overlap(self):
        """Test detection when response has low overlap with retrieved chunks"""
        detector = RAGConsistencyDetector()
        
        prompt = "What does the policy say about refunds?"
        # Response talks about completely different topics than chunks
        response = """
        The company offers unlimited vacation days. Employees can work remotely 
        from anywhere in the world. The CEO announced record profits last quarter.
        New initiatives include sustainability programs and employee wellness.
        """
        metadata = {
            "retrieved_chunks": [
                {"id": "doc1", "text": "Refunds must be requested within 30 days of purchase."},
                {"id": "doc2", "text": "To process a refund, contact customer service with your order number."},
                {"id": "doc3", "text": "Digital products are non-refundable after download."},
            ]
        }
        
        detections = detector.analyze(prompt, response, metadata)
        
        assert len(detections) >= 1
        assert detections[0].severity == "medium"
        assert detections[0].detector_name == "rag_consistency"
        assert "hallucination" in detections[0].tags
    
    def test_detects_unsupported_numbers(self):
        """Test detection when response contains numbers not in chunks"""
        detector = RAGConsistencyDetector()
        
        prompt = "What are the pricing details?"
        response = "The basic plan costs $99 per month and the premium is $499 per month."
        metadata = {
            "retrieved_chunks": [
                {"id": "doc1", "text": "We offer competitive pricing for all customers."},
                {"id": "doc2", "text": "Contact sales for a custom quote."},
            ]
        }
        
        detections = detector.analyze(prompt, response, metadata)
        
        # Should detect unsupported numbers
        has_number_detection = any(
            "unsupported_numbers" in d.tags for d in detections
        )
        assert has_number_detection
    
    def test_no_detection_with_good_grounding(self):
        """Test no detection when response is well-grounded in chunks"""
        detector = RAGConsistencyDetector()
        
        prompt = "What is the refund policy?"
        response = "Refunds must be requested within 30 days of purchase. Contact customer service with your order number."
        metadata = {
            "retrieved_chunks": [
                {"id": "doc1", "text": "Refunds must be requested within 30 days of purchase."},
                {"id": "doc2", "text": "Contact customer service with your order number to process refunds."},
            ]
        }
        
        detections = detector.analyze(prompt, response, metadata)
        
        # Well-grounded response should not trigger detection
        assert len(detections) == 0
    
    def test_no_detection_when_no_chunks(self):
        """Test no detection when retrieved_chunks is empty or missing"""
        detector = RAGConsistencyDetector()
        
        prompt = "What is the refund policy?"
        response = "Our refund policy is very flexible."
        
        # Test with no metadata
        detections = detector.analyze(prompt, response)
        assert len(detections) == 0
        
        # Test with empty retrieved_chunks
        detections = detector.analyze(prompt, response, {"retrieved_chunks": []})
        assert len(detections) == 0
    
    def test_no_detection_for_short_response(self):
        """Test no detection for very short responses"""
        detector = RAGConsistencyDetector()
        
        prompt = "Simple question"
        response = "Yes."
        metadata = {
            "retrieved_chunks": [
                {"id": "doc1", "text": "Detailed document about something."},
            ]
        }
        
        detections = detector.analyze(prompt, response, metadata)
        
        # Short responses shouldn't trigger false positives
        assert len(detections) == 0


class TestRAGConsistencyRegistry:
    """Tests for rag_consistency detector registry"""
    
    def test_detector_in_registry(self):
        """Test that rag_consistency detector is registered"""
        detectors = list_detectors()
        assert "rag_consistency" in detectors
    
    def test_get_detector_by_name(self):
        """Test getting rag_consistency detector by name"""
        detector = get_detector("rag_consistency")
        assert isinstance(detector, RAGConsistencyDetector)
    
    def test_get_detector_with_custom_overlap(self):
        """Test getting detector with custom min_overlap threshold"""
        detector = get_detector("rag_consistency", min_overlap=0.25)
        assert detector.min_overlap == 0.25
