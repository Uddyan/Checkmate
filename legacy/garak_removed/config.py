"""Unified configuration system with TOML support and pydantic validation"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback for Python < 3.11
    except ImportError:
        tomllib = None

try:
    from pydantic import BaseModel, Field, field_validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object  # Fallback


# Pydantic models for config validation
if PYDANTIC_AVAILABLE:
    class AdapterConfig(BaseModel):
        """Adapter configuration"""
        name: str
        api_key: Optional[str] = None
        base_url: Optional[str] = None
        model: Optional[str] = None
        timeout: int = 30
        max_retries: int = 3
    
    class RunConfig(BaseModel):
        """Run configuration"""
        adapters: list[str] = Field(default_factory=lambda: ["null"])
        probes: list[str] = Field(default_factory=lambda: ["demo"])
        detectors: list[str] = Field(default_factory=lambda: ["basic"])
        buffs: list[str] = Field(default_factory=list)
        output_dir: str = "runs"
        max_attempts: int = 10
        generations: int = 3
        seed: Optional[int] = None
    
    class Config(BaseModel):
        """Main configuration model"""
        adapters: Dict[str, AdapterConfig] = Field(default_factory=dict)
        run: RunConfig = Field(default_factory=RunConfig)
        reporting: Dict[str, Any] = Field(default_factory=dict)
        
        @field_validator('adapters', mode='before')
        @classmethod
        def parse_adapters(cls, v):
            if isinstance(v, dict):
                return {k: AdapterConfig(**v) if isinstance(v, dict) else v 
                       for k, v in v.items()}
            return v
else:
    # Fallback dataclasses if pydantic not available
    @dataclass
    class AdapterConfig:
        name: str
        api_key: Optional[str] = None
        base_url: Optional[str] = None
        model: Optional[str] = None
        timeout: int = 30
        max_retries: int = 3
    
    @dataclass
    class RunConfig:
        adapters: list = field(default_factory=lambda: ["null"])
        probes: list = field(default_factory=lambda: ["demo"])
        detectors: list = field(default_factory=lambda: ["basic"])
        buffs: list = field(default_factory=list)
        output_dir: str = "runs"
        max_attempts: int = 10
        generations: int = 3
        seed: Optional[int] = None
    
    @dataclass
    class Config:
        adapters: Dict[str, AdapterConfig] = field(default_factory=dict)
        run: RunConfig = field(default_factory=RunConfig)
        reporting: Dict[str, Any] = field(default_factory=dict)


class ConfigManager:
    """Manages configuration with precedence: CLI > ENV > config file"""
    
    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or self._find_config_file()
        self._config: Optional[Config] = None
    
    def _find_config_file(self) -> Optional[Path]:
        """Find config file in standard locations"""
        # Check current directory
        for filename in ["checkmate.toml", "scanner.toml", "pyproject.toml"]:
            path = Path.cwd() / filename
            if path.exists():
                return path
        
        # Check project root (where setup.py/pyproject.toml is)
        project_root = self._find_project_root()
        if project_root:
            for filename in ["checkmate.toml", "scanner.toml"]:
                path = project_root / filename
                if path.exists():
                    return path
        
        return None
    
    def _find_project_root(self) -> Optional[Path]:
        """Find project root by looking for setup.py or pyproject.toml"""
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            if (parent / "setup.py").exists() or (parent / "pyproject.toml").exists():
                return parent
        return None
    
    def load(self) -> Config:
        """Load configuration from file, environment, and CLI args"""
        # Start with defaults
        config_dict: Dict[str, Any] = {
            "adapters": {},
            "run": {
                "adapters": ["null"],
                "probes": ["demo"],
                "detectors": ["basic"],
                "buffs": [],
                "output_dir": "runs",
                "max_attempts": 10,
                "generations": 3,
            },
            "reporting": {},
        }
        
        # Load from config file
        if self.config_file and self.config_file.exists():
            file_config = self._load_file(self.config_file)
            if file_config:
                config_dict = self._merge_dicts(config_dict, file_config)
        
        # Override with environment variables
        env_config = self._load_env()
        if env_config:
            config_dict = self._merge_dicts(config_dict, env_config)
        
        # Convert to Config object
        if PYDANTIC_AVAILABLE:
            try:
                self._config = Config(**config_dict)
            except Exception as e:
                print(f"Warning: Config validation failed: {e}, using defaults")
                self._config = Config()
        else:
            # Manual construction without pydantic
            run_config = RunConfig(**config_dict.get("run", {}))
            adapters = {
                k: AdapterConfig(**v) if isinstance(v, dict) else v
                for k, v in config_dict.get("adapters", {}).items()
            }
            self._config = Config(
                adapters=adapters,
                run=run_config,
                reporting=config_dict.get("reporting", {})
            )
        
        return self._config
    
    def _load_file(self, path: Path) -> Optional[Dict[str, Any]]:
        """Load configuration from TOML file"""
        if tomllib is None:
            print("Warning: TOML support not available. Install tomli for Python < 3.11")
            return None
        
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
                # Extract [tool.checkmate] section if in pyproject.toml
                if "tool" in data and "checkmate" in data["tool"]:
                    return data["tool"]["checkmate"]
                return data
        except Exception as e:
            print(f"Warning: Failed to load config file {path}: {e}")
            return None
    
    def _load_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        env_config: Dict[str, Any] = {}
        
        # Adapter configs from env
        adapter_keys = {
            "ANTHROPIC_API_KEY": "anthropic",
            "COHERE_API_KEY": "cohere",
            "MISTRAL_API_KEY": "mistral",
            "OPENAI_API_KEY": "openai_compatible",
        }
        
        for env_key, adapter_name in adapter_keys.items():
            api_key = os.getenv(env_key)
            if api_key:
                if "adapters" not in env_config:
                    env_config["adapters"] = {}
                env_config["adapters"][adapter_name] = {"api_key": api_key}
        
        # Run config from env
        if os.getenv("CHECKMATE_OUTPUT_DIR"):
            if "run" not in env_config:
                env_config["run"] = {}
            env_config["run"]["output_dir"] = os.getenv("CHECKMATE_OUTPUT_DIR")
        
        if os.getenv("CHECKMATE_SEED"):
            if "run" not in env_config:
                env_config["run"] = {}
            try:
                env_config["run"]["seed"] = int(os.getenv("CHECKMATE_SEED"))
            except ValueError:
                pass
        
        return env_config
    
    def _merge_dicts(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge two dictionaries"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_dicts(result[key], value)
            else:
                result[key] = value
        return result
    
    def apply_cli_overrides(self, cli_args: Dict[str, Any]) -> None:
        """Apply CLI argument overrides to config"""
        if self._config is None:
            self.load()
        
        # Override run config with CLI args
        if "adapters" in cli_args:
            self._config.run.adapters = cli_args["adapters"]
        if "probes" in cli_args:
            self._config.run.probes = cli_args["probes"]
        if "detectors" in cli_args:
            self._config.run.detectors = cli_args["detectors"]
        if "output" in cli_args:
            self._config.run.output_dir = cli_args["output"]
        if "seed" in cli_args and cli_args["seed"] is not None:
            self._config.run.seed = cli_args["seed"]
        if "generations" in cli_args:
            self._config.run.generations = cli_args["generations"]
    
    @property
    def config(self) -> Config:
        """Get current configuration"""
        if self._config is None:
            self.load()
        return self._config


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config(config_file: Optional[Path] = None) -> Config:
    """Get configuration instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_file)
    return _config_manager.config


def load_config(config_file: Optional[Path] = None, cli_args: Optional[Dict[str, Any]] = None) -> Config:
    """Load and return configuration with CLI overrides"""
    global _config_manager
    _config_manager = ConfigManager(config_file)
    config = _config_manager.load()
    if cli_args:
        _config_manager.apply_cli_overrides(cli_args)
    return config


def load_scanner_config(config_file: Path) -> "ScannerConfig":
    """Load new scanner configuration from YAML file
    
    This loads the new YAML schema format from the one-pager:
        target:
          type: "http_app"
          name: "my-bot"
          ...
        profile:
          app_type: "chatbot"
          attack_packs: [...]
        campaign:
          max_requests: 100
          ...
        output:
          run_id: "test-001"
          results_dir: "runs/test-001"
    
    Args:
        config_file: Path to YAML config file
        
    Returns:
        ScannerConfig instance
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValidationError: If config is invalid
    """
    from checkmate.models import ScannerConfig
    import yaml
    
    config_path = Path(config_file)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    if tomllib is None:
        # Fallback to yaml if tomllib not available
        import yaml
        with open(config_path) as f:
            data = yaml.safe_load(f)
    else:
        # Try TOML first, fallback to YAML
        try:
            with open(config_path, "rb") as f:
                data = tomllib.load(f)
        except Exception:
            # Not TOML, try YAML
            import yaml
            with open(config_path) as f:
                data = yaml.safe_load(f)
    
    # Validate and create ScannerConfig
    try:
        scanner_config = ScannerConfig(**data)
        return scanner_config
    except Exception as e:
        raise ValueError(f"Invalid scanner config: {e}") from e

