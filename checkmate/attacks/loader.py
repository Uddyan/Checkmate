"""Attack pack loader for YAML-based attack definitions.

This module loads attack packs from YAML files following the schema:

```yaml
attacks:
  - id: "jailbreak_basic_001"
    category: "LLM01_prompt_injection"
    severity: "high"
    description: "Basic jailbreak attempt"
    template: |
      Ignore all previous instructions...
```
"""

import yaml
from pathlib import Path
from typing import Union
from checkmate.models import Attack, OWASPCategory, Severity


def load_attack_pack(path: Union[str, Path]) -> list[Attack]:
    """Load attacks from a YAML attack pack file
    
    Args:
        path: Path to the YAML attack pack file
        
    Returns:
        List of Attack objects
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the YAML is invalid or missing required fields
    """
    pack_path = Path(path)
    if not pack_path.exists():
        raise FileNotFoundError(f"Attack pack not found: {pack_path}")
    
    try:
        with open(pack_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {pack_path}: {e}") from e
    
    if not isinstance(data, dict) or "attacks" not in data:
        raise ValueError(f"Attack pack must have 'attacks' key: {pack_path}")
    
    attacks = []
    for i, attack_data in enumerate(data["attacks"]):
        try:
            # Validate required fields
            required_fields = ["id", "category", "severity", "description", "template"]
            for field in required_fields:
                if field not in attack_data:
                    raise ValueError(f"Attack {i} missing required field: {field}")
            
            # Create Attack object
            attack = Attack(
                id=attack_data["id"],
                category=OWASPCategory(attack_data["category"]),
                severity=Severity(attack_data["severity"]),
                description=attack_data["description"],
                template=attack_data["template"],
                metadata=attack_data.get("metadata", {})
            )
            attacks.append(attack)
        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid attack at index {i} in {pack_path}: {e}") from e
    
    return attacks


def load_attack_packs(pack_paths: list[Union[str, Path]], base_path: Path | None = None) -> list[Attack]:
    """Load multiple attack packs
    
    Args:
        pack_paths: List of paths to attack pack YAML files
        base_path: Base path to resolve relative paths against (defaults to project root)
        
    Returns:
        Combined list of attacks from all packs
    """
    all_attacks = []
    
    # Default base path to the checkmate package directory
    if base_path is None:
        base_path = Path(__file__).parent.parent.parent  # Go up to project root
    
    for path_str in pack_paths:
        path = Path(path_str)
        
        # Resolve relative paths against base_path
        if not path.is_absolute():
            path = base_path / path
        
        attacks = load_attack_pack(path)
        all_attacks.extend(attacks)
    
    return all_attacks


def validate_attack_pack(path: Union[str, Path]) -> tuple[bool, str]:
    """Validate an attack pack without loading it
    
    Args:
        path: Path to the YAML attack pack file
        
    Returns:
        Tuple of (is_valid, error_message). error_message is empty if valid.
    """
    try:
        attacks = load_attack_pack(path)
        return True, f"Valid attack pack with {len(attacks)} attacks"
    except Exception as e:
        return False, str(e)
