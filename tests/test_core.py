"""Tests for checkmate core types"""

import pytest
from checkmate.core.types import (
    Probe, ProbeType, Detector, DetectorType, Buff,
    Attempt, Score, RunConfig, Message, Conversation
)


class TestProbe:
    """Test Probe data structure"""
    
    def test_probe_creation(self):
        """Test probe can be created"""
        probe = Probe(
            name="test_probe",
            probe_type=ProbeType.TOXICITY,
            description="Test probe",
            tags=["test", "demo"]
        )
        assert probe.name == "test_probe"
        assert probe.probe_type == ProbeType.TOXICITY
        assert probe.description == "Test probe"
        assert probe.tags == ["test", "demo"]
        assert probe.active is True
    
    def test_probe_string_representation(self):
        """Test probe string representation"""
        probe = Probe(
            name="test_probe",
            probe_type=ProbeType.TOXICITY,
            description="Test probe",
            tags=[]
        )
        expected = "Probe(name='test_probe', type='toxicity')"
        assert str(probe) == expected


class TestDetector:
    """Test Detector data structure"""
    
    def test_detector_creation(self):
        """Test detector can be created"""
        detector = Detector(
            name="test_detector",
            detector_type=DetectorType.TOXICITY,
            description="Test detector"
        )
        assert detector.name == "test_detector"
        assert detector.detector_type == DetectorType.TOXICITY
        assert detector.description == "Test detector"
        assert detector.active is True
    
    def test_detector_detect(self):
        """Test detector detect method"""
        detector = Detector(
            name="test_detector",
            detector_type=DetectorType.TOXICITY,
            description="Test detector"
        )
        score = detector.detect("This is a test")
        assert score == 0.0  # Base implementation returns 0.0
    
    def test_detector_string_representation(self):
        """Test detector string representation"""
        detector = Detector(
            name="test_detector",
            detector_type=DetectorType.TOXICITY,
            description="Test detector"
        )
        expected = "Detector(name='test_detector', type='toxicity')"
        assert str(detector) == expected


class TestBuff:
    """Test Buff data structure"""
    
    def test_buff_creation(self):
        """Test buff can be created"""
        buff = Buff(
            name="test_buff",
            description="Test buff"
        )
        assert buff.name == "test_buff"
        assert buff.description == "Test buff"
        assert buff.active is True
    
    def test_buff_apply(self):
        """Test buff apply method"""
        buff = Buff(
            name="test_buff",
            description="Test buff"
        )
        result = buff.apply("test input")
        assert result == "test input"  # Base implementation returns input unchanged
    
    def test_buff_string_representation(self):
        """Test buff string representation"""
        buff = Buff(
            name="test_buff",
            description="Test buff"
        )
        expected = "Buff(name='test_buff')"
        assert str(buff) == expected


class TestAttempt:
    """Test Attempt data structure"""
    
    def test_attempt_creation(self):
        """Test attempt can be created"""
        attempt = Attempt(
            probe_name="test_probe",
            prompt="test prompt",
            response="test response",
            score=0.5,
            metadata={"key": "value"}
        )
        assert attempt.probe_name == "test_probe"
        assert attempt.prompt == "test prompt"
        assert attempt.response == "test response"
        assert attempt.score == 0.5
        assert attempt.metadata == {"key": "value"}
    
    def test_attempt_string_representation(self):
        """Test attempt string representation"""
        attempt = Attempt(
            probe_name="test_probe",
            prompt="test prompt",
            response="test response",
            score=0.5,
            metadata={}
        )
        expected = "Attempt(probe='test_probe', score=0.500)"
        assert str(attempt) == expected


class TestScore:
    """Test Score data structure"""
    
    def test_score_creation(self):
        """Test score can be created"""
        score = Score(
            detector_name="test_detector",
            value=0.75,
            metadata={"confidence": 0.9}
        )
        assert score.detector_name == "test_detector"
        assert score.value == 0.75
        assert score.metadata == {"confidence": 0.9}
    
    def test_score_string_representation(self):
        """Test score string representation"""
        score = Score(
            detector_name="test_detector",
            value=0.75,
            metadata={}
        )
        expected = "Score(detector='test_detector', value=0.750)"
        assert str(score) == expected


class TestRunConfig:
    """Test RunConfig data structure"""
    
    def test_run_config_creation(self):
        """Test run config can be created"""
        config = RunConfig(
            adapters=["null"],
            probes=["demo"],
            detectors=["basic"],
            buffs=[],
            output_dir="runs/test"
        )
        assert config.adapters == ["null"]
        assert config.probes == ["demo"]
        assert config.detectors == ["basic"]
        assert config.buffs == []
        assert config.output_dir == "runs/test"
        assert config.max_attempts == 10
        assert config.seed is None
    
    def test_run_config_string_representation(self):
        """Test run config string representation"""
        config = RunConfig(
            adapters=["null", "hf"],
            probes=["demo", "toxicity"],
            detectors=["basic"],
            buffs=[],
            output_dir="runs/test"
        )
        expected = "RunConfig(adapters=['null', 'hf'], probes=['demo', 'toxicity'])"
        assert str(config) == expected


class TestMessage:
    """Test Message data structure"""
    
    def test_message_creation(self):
        """Test message can be created"""
        message = Message(role="user", content="Hello")
        assert message.role == "user"
        assert message.content == "Hello"


class TestConversation:
    """Test Conversation data structure"""
    
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
