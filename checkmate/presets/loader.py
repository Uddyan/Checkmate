# SPDX-License-Identifier: Apache-2.0
"""Preset loader for attack pack configurations.

Loads preset YAML files that define curated combinations of probes and
detectors for specific use cases (smoke-test, chatbot_basic).
"""

import yaml
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PresetConfig:
    """Preset configuration loaded from YAML"""
    name: str
    description: str
    probes: List[str]
    detectors: List[str]
    owasp_map: Dict[str, str]
    severity_map: Dict[str, str]


def load_preset(preset_name: str) -> PresetConfig:
    """Load a preset configuration from YAML file
    
    Args:
        preset_name: Name of preset (smoke-test, chatbot_basic)
        
    Returns:
        PresetConfig object
        
    Raises:
        FileNotFoundError: If preset file doesn't exist
        ValueError: If preset YAML is invalid
    """
    # Normalize preset name (support both dash and underscore)
    normalized_name = preset_name.replace('-', '_')
    
    # Map preset name to file
    preset_files = {
        'chatbot_basic': 'chatbot_basic.yaml',
        'chatbot_quick': 'chatbot_quick.yaml',
        'chatbot_full': 'chatbot_full.yaml',
        'smoke_test': 'smoke_test.yaml',
        'agent_basic': 'agent_basic.yaml',
        'rag_basic': 'rag_basic.yaml',
    }
    
    if normalized_name not in preset_files:
        raise ValueError(
            f"Unknown preset: {preset_name}. "
            f"Must be one of {list(preset_files.keys())}"
        )
    
    # Load from package directory
    preset_dir = Path(__file__).parent
    preset_path = preset_dir / preset_files[normalized_name]
    
    if not preset_path.exists():
        raise FileNotFoundError(f"Preset file not found: {preset_path}")
    
    try:
        with open(preset_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in preset {preset_name}: {e}") from e
    
    # Validate required fields
    required_fields = ['name', 'description', 'probes', 'detectors']
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Preset {preset_name} missing required field: {field}")
    
    # Create PresetConfig
    return PresetConfig(
        name=data['name'],
        description=data['description'],
        probes=data['probes'],
        detectors=data['detectors'],
        owasp_map=data.get('owasp_map', {}),
        severity_map=data.get('severity_map', {})
    )


def preset_to_plugin_names(preset: PresetConfig, 
                           extra_probes: Optional[List[str]] = None,
                           extra_detectors: Optional[List[str]] = None) -> Tuple[List[str], List[str]]:
    """Convert preset config to fully-qualified plugin names
    
    Args:
        preset: PresetConfig object
        extra_probes: Additional probes to include
        extra_detectors: Additional detectors to include
        
    Returns:
        Tuple of (probe_names, detector_names) with 'probes.' and 'detectors.' prefixes
    """
    extra_probes = extra_probes or []
    extra_detectors = extra_detectors or []
    
    # Add 'probes.' prefix if not present
    probe_names = []
    for probe in preset.probes + extra_probes:
        if not probe.startswith('probes.'):
            probe_names.append(f'probes.{probe}')
        else:
            probe_names.append(probe)
    
    # Add 'detectors.' prefix if not present
    detector_names = []
    for detector in preset.detectors + extra_detectors:
        if not detector.startswith('detectors.'):
            detector_names.append(f'detectors.{detector}')
        else:
            detector_names.append(detector)
    
    return probe_names, detector_names


def list_presets() -> List[Dict[str, Any]]:
    """List all available presets
    
    Returns:
        List of dicts with preset info
    """
    presets = []
    for preset_name in ['smoke_test', 'chatbot_basic', 'chatbot_quick', 'chatbot_full', 'agent_basic', 'rag_basic']:
        try:
            preset = load_preset(preset_name)
            presets.append({
                'name': preset.name,
                'description': preset.description,
                'num_probes': len(preset.probes),
                'num_detectors': len(preset.detectors)
            })
        except Exception:
            continue
    return presets


def get_owasp_category_for_probe(preset: PresetConfig, probe_name: str) -> str:
    """Get OWASP category for a specific probe
    
    Args:
        preset: PresetConfig object
        probe_name: Probe name (with or without 'probes.' prefix)
        
    Returns:
        OWASP category string or "Unknown"
    """
    # Remove 'probes.' prefix if present
    clean_probe = probe_name.replace('probes.', '')
    
    # Check each key in owasp_map
    for key, category in preset.owasp_map.items():
        if clean_probe.startswith(key + '.') or clean_probe == key:
            return category
    
    return "LLM01: Prompt Injection"  # Default


def get_severity_for_probe(preset: PresetConfig, probe_name: str) -> str:
    """Get severity for a specific probe
    
    Args:
        preset: PresetConfig object
        probe_name: Probe name (with or without 'probes.' prefix)
        
    Returns:
        Severity string (critical/high/medium/low) or "medium" as default
    """
    clean_probe = probe_name.replace('probes.', '')
    
    for key, severity in preset.severity_map.items():
        if clean_probe.startswith(key + '.') or clean_probe == key:
            return severity
    
    return "medium"  # default severity
