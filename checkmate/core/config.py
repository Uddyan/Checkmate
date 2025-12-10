# SPDX-License-Identifier: Apache-2.0
"""Pydantic configuration models for Checkmate."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class TargetConfig(BaseModel):
    """Configuration for the target LLM."""
    adapter: str = Field(description="Adapter type (e.g., 'openai_compatible', 'http_local')")
    endpoint: Optional[str] = Field(default=None, description="API endpoint URL")
    model: Optional[str] = Field(default=None, description="Model name/identifier")
    api_key: Optional[str] = Field(default=None, description="API key (if required)")
    headers: Dict[str, str] = Field(default_factory=dict, description="Custom headers")
    timeout: int = Field(default=30, description="Request timeout in seconds")


class ProbeConfig(BaseModel):
    """Configuration for a probe."""
    name: str = Field(description="Probe name (e.g., 'smoke_test')")
    enabled: bool = Field(default=True, description="Whether probe is enabled")
    params: Dict[str, Any] = Field(default_factory=dict, description="Probe-specific parameters")


class DetectorConfig(BaseModel):
    """Configuration for a detector."""
    name: str = Field(description="Detector name (e.g., 'mitigation_bypass')")
    enabled: bool = Field(default=True, description="Whether detector is enabled")
    threshold: float = Field(default=0.5, description="Detection threshold")


class OutputConfig(BaseModel):
    """Configuration for output."""
    output_dir: str = Field(default="./results", description="Output directory")
    formats: List[str] = Field(default=["json", "html"], description="Output formats")


class SystemConfig(BaseModel):
    """System-level configuration."""
    parallel: bool = Field(default=False, description="Run probes in parallel")
    max_workers: int = Field(default=4, description="Max parallel workers")
    verbose: bool = Field(default=False, description="Verbose logging")
    seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")


class CheckmateConfig(BaseModel):
    """Top-level Checkmate configuration."""
    target: TargetConfig = Field(description="Target LLM configuration")
    probes: List[ProbeConfig] = Field(default_factory=list, description="Probes to run")
    detectors: List[DetectorConfig] = Field(default_factory=list, description="Detectors to use")
    output: OutputConfig = Field(default_factory=OutputConfig, description="Output settings")
    system: SystemConfig = Field(default_factory=SystemConfig, description="System settings")
    
    @classmethod
    def from_yaml(cls, path: str) -> "CheckmateConfig":
        """Load configuration from a YAML file."""
        import yaml
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls(**data)
