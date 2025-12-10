# Checkmate Architecture

## Overview

Checkmate is a modular LLM red-teaming scanner. It uses a probe-detector architecture to test language models for security vulnerabilities.

## Directory Structure

```
checkmate/
├── cli/              # Command-line interface
│   └── main.py       # Entry point: `checkmate scan --config ...`
├── core/             # Core engine and configuration
│   ├── config.py     # Pydantic config models
│   ├── engine.py     # Main scan orchestration
│   └── report.py     # JSON + HTML report generation
├── probes/           # Security test probes
│   ├── base.py       # BaseProbe abstract class
│   ├── smoke_probe.py # One-probe MVP with templates
│   └── registry.py   # Probe lookup registry
├── detectors/        # Response analyzers
│   ├── base.py       # BaseDetector abstract class
│   ├── mitigation.py # Refusal pattern detector
│   └── registry.py   # Detector lookup registry
├── adapters/         # LLM API adapters
│   ├── base.py       # Adapter interface
│   ├── openai_compatible.py
│   └── ...
├── db/               # Database integration (stub)
└── vector/           # Vector database integration (stub)
```

## Key Components

### 1. CheckmateConfig (core/config.py)
Pydantic models for type-safe YAML configuration.

### 2. CheckmateEngine (core/engine.py)
Orchestrates the scan:
1. Loads adapter, probes, detectors from config
2. Runs each probe against the target model
3. Analyzes responses with detectors
4. Computes risk scores
5. Generates reports

### 3. Probes (probes/)
Generate adversarial prompts to test model security.
- Inherit from `BaseProbe`
- Implement `generate_prompts()` method
- Register via `probes/registry.py`

### 4. Detectors (detectors/)
Analyze model responses for security issues.
- Inherit from `BaseDetector`
- Implement `detect(response) -> float` method
- Register via `detectors/registry.py`

### 5. Adapters (adapters/)
Interface with different LLM APIs.
- Inherit from `Adapter`
- Implement `generate()` method

## Data Flow

```
Config (YAML)
    ↓
CheckmateEngine
    ↓
┌─────────────────┐
│    Adapter      │ ← Target LLM
└────────┬────────┘
         ↓
┌─────────────────┐
│     Probes      │ → Generate prompts
└────────┬────────┘
         ↓
┌─────────────────┐
│   Detectors     │ → Score responses
└────────┬────────┘
         ↓
    Report (JSON/HTML)
```

## Adding New Components

### New Probe
```python
# checkmate/probes/my_probe.py
from checkmate.probes.base import BaseProbe

class MyProbe(BaseProbe):
    name = "my_probe"
    description = "My custom probe"
    
    def generate_prompts(self):
        return ["prompt1", "prompt2"]

# Register in probes/registry.py
register_probe("my_probe", MyProbe)
```

### New Detector
```python
# checkmate/detectors/my_detector.py
from checkmate.detectors.base import BaseDetector

class MyDetector(BaseDetector):
    name = "my_detector"
    
    def detect(self, response: str) -> float:
        # Return 0.0 (safe) to 1.0 (vulnerable)
        return 0.5

# Register in detectors/registry.py
register_detector("my_detector", MyDetector)
```
