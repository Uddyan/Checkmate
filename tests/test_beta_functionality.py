"""Tests for beta functionality: pilot config, presets, and risk scoring"""

import pytest
from pathlib import Path
import tempfile
import yaml

from checkmate.pilot_config import load_pilot_config, PilotConfig
from checkmate.presets.loader import load_preset, preset_to_plugin_names
from checkmate.scoring.risk_scorer import calculate_risk_score


def test_load_preset_chatbot():
    """Test loading chatbot-basic preset"""
    preset = load_preset('chatbot-basic')
    
    assert preset.name == 'chatbot-basic'
    assert len(preset.probes) > 0
    assert len(preset.detectors) > 0
    assert 'LLM01' in str(preset.owasp_map.values())


def test_load_preset_rag():
    """Test loading rag-basic preset"""
    preset = load_preset('rag-basic')
    
    assert preset.name == 'rag-basic'
    assert len(preset.probes) > 0


def test_load_preset_agent():
    """Test loading agent-tools preset"""
    preset = load_preset('agent-tools')
    
    assert preset.name == 'agent-tools'
    assert len(preset.probes) > 0


def test_preset_to_plugin_names():
    """Test converting preset to plugin names"""
    preset = load_preset('chatbot-basic')
    probe_names, detector_names = preset_to_plugin_names(preset)
    
    # Should have probes. prefix
    assert all(p.startswith('probes.') for p in probe_names)
    assert all(d.startswith('detectors.') for d in detector_names)


def test_pilot_config_validation():
    """Test pilot config validation"""
    config_data = {
        'target': {
            'type': 'null',
            'name': 'test-target',
        },
        'profile': {
            'preset': 'chatbot-basic'
        },
        'campaign': {
            'max_requests': 10
        },
        'output': {
            'results_dir': 'test_runs'
        }
    }
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        temp_path = f.name
    
    try:
        # Note: This will fail due to env var validation in auth
        # In real test would mock environment
        config = PilotConfig(**config_data)
        assert config.target.name == 'test-target'
        assert config.profile.preset == 'chatbot-basic'
    finally:
        Path(temp_path).unlink()


def test_risk_score_calculation():
    """Test risk score calculation"""
    # Mock evaluations
    evaluations = [
        {'probe': 'probes.dan.DAN', 'detector': 'detectors.dan.DAN', 'passed': False},
        {'probe': 'probes.dan.DAN', 'detector': 'detectors.dan.DAN', 'passed': False},
        {'probe': 'probes.promptinject.Test', 'detector': 'detectors.promptinject', 'passed': False},
    ]
    
    result = calculate_risk_score(evaluations, preset=None)
    
    assert 'risk_score' in result
    assert 0 <= result['risk_score'] <= 100
    assert result['total_detections'] == 3


def test_risk_score_no_failures():
    """Test risk score with no failures"""
    evaluations = [
        {'probe': 'probes.dan.DAN', 'detector': 'detectors.dan.DAN', 'passed': True},
    ]
    
    result = calculate_risk_score(evaluations, preset=None)
    
    assert result['risk_score'] == 100
    assert result['total_detections'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
