"""Tests for configuration system"""

import pytest
import tempfile
from pathlib import Path
import os

from checkmate.config import ConfigManager, load_config


def test_config_manager_defaults():
    """Test config manager with defaults"""
    manager = ConfigManager()
    config = manager.load()
    
    assert config.run.adapters == ["null"]
    assert config.run.probes == ["demo"]
    assert config.run.output_dir == "runs"


def test_config_manager_from_file(tmp_path):
    """Test loading config from TOML file"""
    config_file = tmp_path / "test.toml"
    config_file.write_text("""
[run]
adapters = ["null", "http_local"]
probes = ["dan"]
output_dir = "test_output"
max_attempts = 20
""")
    
    manager = ConfigManager(config_file=config_file)
    config = manager.load()
    
    assert "null" in config.run.adapters
    assert "http_local" in config.run.adapters
    assert config.run.probes == ["dan"]
    assert config.run.output_dir == "test_output"
    assert config.run.max_attempts == 20


def test_config_env_override(tmp_path):
    """Test environment variable overrides"""
    config_file = tmp_path / "test.toml"
    config_file.write_text("""
[run]
output_dir = "file_output"
""")
    
    # Set env var
    os.environ["CHECKMATE_OUTPUT_DIR"] = "env_output"
    
    try:
        manager = ConfigManager(config_file=config_file)
        config = manager.load()
        
        # Env should override file
        assert config.run.output_dir == "env_output"
    finally:
        # Cleanup
        if "CHECKMATE_OUTPUT_DIR" in os.environ:
            del os.environ["CHECKMATE_OUTPUT_DIR"]


def test_config_cli_override(tmp_path):
    """Test CLI argument overrides"""
    config_file = tmp_path / "test.toml"
    config_file.write_text("""
[run]
adapters = ["null"]
probes = ["demo"]
""")
    
    manager = ConfigManager(config_file=config_file)
    config = manager.load()
    
    # Apply CLI overrides
    cli_args = {
        "adapters": ["anthropic"],
        "probes": ["dan", "promptinject"],
        "output": "cli_output",
    }
    manager.apply_cli_overrides(cli_args)
    
    assert config.run.adapters == ["anthropic"]
    assert config.run.probes == ["dan", "promptinject"]
    assert config.run.output_dir == "cli_output"


def test_config_precedence(tmp_path):
    """Test config precedence: CLI > ENV > file"""
    config_file = tmp_path / "test.toml"
    config_file.write_text("""
[run]
output_dir = "file_output"
seed = 42
""")
    
    os.environ["CHECKMATE_OUTPUT_DIR"] = "env_output"
    
    try:
        manager = ConfigManager(config_file=config_file)
        config = manager.load()
        
        # ENV should override file
        assert config.run.output_dir == "env_output"
        
        # CLI should override ENV
        manager.apply_cli_overrides({"output": "cli_output"})
        assert config.run.output_dir == "cli_output"
    finally:
        if "CHECKMATE_OUTPUT_DIR" in os.environ:
            del os.environ["CHECKMATE_OUTPUT_DIR"]

