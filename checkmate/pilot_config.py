"""Pilot-friendly YAML configuration loader for beta customers.

This module provides a simplified configuration system that translates
to the internal checkmate/_config structure while maintaining backward
compatibility with existing TOML configs.
"""

import os
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, model_validator


class AuthConfig(BaseModel):
    """Authentication configuration for target"""
    type: str = "header"
    header_name: str = "Authorization"
    env_var: str
    
    @validator('env_var')
    def validate_env_var(cls, v):
        """Ensure env var is set"""
        if not os.getenv(v):
            raise ValueError(f"Environment variable {v} is not set")
        return v


class TargetConfig(BaseModel):
    """Target LLM system configuration"""
    type: str = Field(..., description="Adapter type: http_app, openai_compatible, openai, etc.")
    name: str = Field(..., description="Human-readable target name")
    base_url: Optional[str] = None
    method: str = "POST"
    model: Optional[str] = None
    auth: Optional[AuthConfig] = None
    timeout: int = 30
    
    @validator('type')
    def validate_type(cls, v):
        """Validate adapter type"""
        valid_types = ['http_app', 'http_local', 'openai_compatible', 'openai', 
                      'hf_local', 'anthropic', 'cohere', 'null', 'mock']
        if v not in valid_types:
            raise ValueError(f"Invalid adapter type: {v}. Must be one of {valid_types}")
        return v


class ProfileConfig(BaseModel):
    """Test profile configuration"""
    preset: str = Field(..., description="Preset attack pack: chatbot-basic, rag-basic, agent-tools")
    extra_probes: List[str] = Field(default_factory=list)
    extra_detectors: List[str] = Field(default_factory=list)
    
    @validator('preset')
    def validate_preset(cls, v):
        """Validate preset name"""
        valid_presets = ['chatbot-basic', 'rag-basic', 'agent-tools', 'smoke-test']
        if v not in valid_presets:
            raise ValueError(f"Invalid preset: {v}. Must be one of {valid_presets}")
        return v


class CampaignConfig(BaseModel):
    """Campaign execution configuration"""
    max_requests: int = Field(200, description="Maximum total requests to send", ge=1)
    max_rps: float = Field(2.0, description="Maximum requests per second", ge=0.1)
    concurrent_requests: int = Field(5, ge=1, le=50)
    use_llm_judge: bool = False
    generations: int = Field(3, description="Generations per probe", ge=1)


class OutputConfig(BaseModel):
    """Output configuration for results and reports"""
    run_id: Optional[str] = None
    results_dir: str = "runs"
    
    def get_run_id(self) -> str:
        """Get or generate run ID"""
        if self.run_id:
            return self.run_id
        import uuid
        return str(uuid.uuid4())
    
    def get_results_path(self) -> Path:
        """Get full results directory path"""
        run_id = self.get_run_id()
        return Path(self.results_dir) / run_id


class DatabaseConfig(BaseModel):
    """Optional database configuration for persisting runs and findings"""
    enabled: bool = False
    url: Optional[str] = None  # e.g., "postgresql://user:pass@host:5432/checkmate"
    
    @model_validator(mode='after')
    def validate_url_if_enabled(self):
        if self.enabled and not self.url:
            raise ValueError("database.url is required when database.enabled is true")
        return self


class PilotConfig(BaseModel):
    """Main configuration object for Checkmate pilot/enterprise runs"""
    target: TargetConfig
    profile: ProfileConfig
    campaign: CampaignConfig = CampaignConfig()
    output: OutputConfig = OutputConfig()
    database: Optional[DatabaseConfig] = None


def load_pilot_config(config_path: Path) -> PilotConfig:
    """Load and validate pilot configuration from YAML file
    
    Args:
        config_path: Path to YAML config file
        
    Returns:
        Validated PilotConfig object
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")
    
    try:
        with open(config_file) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in config file: {e}") from e
    
    if not data:
        raise ValueError("Config file is empty")
    
    try:
        pilot_config = PilotConfig(**data)
        return pilot_config
    except Exception as e:
        raise ValueError(f"Invalid pilot config: {e}") from e


def setup_checkmate_config(pilot_config: PilotConfig):
    """Translate pilot config to checkmate internal _config structure
    
    This function modifies the global checkmate._config object to match
    the pilot configuration, allowing the existing harnesses to work
    without modification.
    
    Args:
        pilot_config: Validated pilot configuration
    """
    from checkmate import _config
    import argparse
    import datetime
    
    # Set run configuration
    _config.run.generations = pilot_config.campaign.generations
    _config.run.interactive = False
    
    # Set reporting configuration
    results_path = pilot_config.output.get_results_path()
    results_path.mkdir(parents=True, exist_ok=True)
    
    _config.reporting.report_dir = str(results_path)
    _config.reporting.report_prefix = pilot_config.target.name.replace(" ", "-").lower()
    
    # Set system configuration  
    _config.system.verbose = 2
    _config.system.parallel_requests = pilot_config.campaign.concurrent_requests
    _config.system.show_z = False  # Disable z-score calibration for beta
    _config.system.narrow_output = False  # Use wide output format
    _config.system.lite = False  # Not using lite mode
    _config.system.user_agent = "checkmate-beta-scanner/1.0"  # User agent for HTTP requests
    
    # Set plugins configuration
    _config.plugins.extended_detectors = False  # Use primary detectors only by default
    _config.plugins.target_type = pilot_config.target.type
    _config.plugins.target_name = pilot_config.target.name
    
    # Set transient run ID and timing
    _config.transient.run_id = pilot_config.output.get_run_id()
    _config.transient.starttime = datetime.datetime.now()  # Track campaign start
    _config.transient.starttime_iso = _config.transient.starttime.isoformat()
    _config.transient.data_dir = Path.home() / ".local" / "share" / "checkmate"
    
    # Create mock CLI args for compatibility
    cli_args = argparse.Namespace()
    cli_args.list_probes = False
    cli_args.list_detectors = False
    cli_args.list_generators = False
    cli_args.list_buffs = False
    cli_args.list_config = False
    cli_args.plugin_info = False
    _config.transient.cli_args = cli_args
    
    # Store pilot config for later use
    _config.transient.pilot_config = pilot_config



def get_adapter_kwargs(target_config: TargetConfig) -> Dict[str, Any]:
    """Extract adapter keyword arguments from target config
    
    Args:
        target_config: Target configuration
        
    Returns:
        Dictionary of kwargs to pass to adapter constructor
    """
    kwargs = {}
    
    if target_config.base_url:
        kwargs['base_url'] = target_config.base_url
    
    if target_config.model:
        kwargs['model_name'] = target_config.model
    
    if target_config.method:
        kwargs['http_method'] = target_config.method
    
    if target_config.auth:
        auth_value = os.getenv(target_config.auth.env_var)
        if target_config.auth.type == "header":
            kwargs['headers'] = {
                target_config.auth.header_name: auth_value
            }
    
    if target_config.timeout:
        kwargs['timeout'] = target_config.timeout
    
    return kwargs


def validate_pilot_config_file(config_path: Path) -> tuple[bool, str]:
    """Validate a pilot config file without fully loading it
    
    Args:
        config_path: Path to config file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        pilot_config = load_pilot_config(config_path)
        return True, f"Valid pilot config: {pilot_config.target.name}"
    except Exception as e:
        return False, str(e)
