"""Pre-flight checks module for validating configuration and environment before campaign execution"""

import os
import sys
from pathlib import Path
from typing import Tuple, List, Dict
import logging


def check_python_version() -> Tuple[bool, str]:
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        return False, f"Python 3.10+ required, found {version.major}.{version.minor}"
    return True, f"Python {version.major}.{version.minor}.{version.micro}"


def check_dependencies() -> Tuple[bool, List[str]]:
    """Check if required dependencies are installed"""
    required = ['yaml', 'pydantic', 'colorama']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        return False, missing
    return True, []


def check_adapter_connectivity(adapter_type: str, base_url: str = None) -> Tuple[bool, str]:
    """Check if adapter can be initialized and is available"""
    try:
        if adapter_type == "mock":
            return True, "Mock adapter always available"
        
        if adapter_type == "null":
            return True, "Null adapter always available"
        
        if adapter_type in ["http_app", "http_local"]:
            if not base_url:
                return False, "HTTP adapter requires base_url"
            # Could add actual connectivity check here
            return True, f"HTTP endpoint configured: {base_url}"
        
        if adapter_type == "openai_compatible":
            if not os.getenv("OPENAI_API_KEY"):
                return False, "OPENAI_API_KEY environment variable not set"
            return True, "OpenAI API key found"
        
        return True, f"Adapter type {adapter_type} accepted"
        
    except Exception as e:
        return False, f"Adapter check failed: {e}"


def check_output_directory(results_dir: Path) -> Tuple[bool, str]:
    """Check if output directory is writable"""
    try:
        results_dir = Path(results_dir)
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to create a test file
        test_file = results_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
        
        return True, f"Output directory writable: {results_dir}"
    except Exception as e:
        return False, f"Cannot write to output directory: {e}"


def run_pre_flight_checks(pilot_config) -> Dict[str, any]:
    """Run all pre-flight checks
    
    Args:
        pilot_config: PilotConfig object
        
    Returns:
        Dict with check results and summary
    """
    results = {
        'all_passed': True,
        'checks': []
    }
    
    # Python version check
    passed, msg = check_python_version()
    results['checks'].append({
        'name': 'Python Version',
        'passed': passed,
        'message': msg
    })
    if not passed:
        results['all_passed'] = False
    
    # Dependencies check
    passed, missing = check_dependencies()
    msg = "All dependencies installed" if passed else f"Missing: {', '.join(missing)}"
    results['checks'].append({
        'name': 'Dependencies',
        'passed': passed,
        'message': msg
    })
    if not passed:
        results['all_passed'] = False
    
    # Adapter connectivity
    passed, msg = check_adapter_connectivity(
        pilot_config.target.type,
        pilot_config.target.base_url
    )
    results['checks'].append({
        'name': 'Adapter Connectivity',
        'passed': passed,
        'message': msg
    })
    if not passed:
        results['all_passed'] = False
    
    # Output directory
    passed, msg = check_output_directory(pilot_config.output.results_dir)
    results['checks'].append({
        'name': 'Output Directory',
        'passed': passed,
        'message': msg
    })
    if not passed:
        results['all_passed'] = False
    
    return results


def print_pre_flight_results(results: Dict):
    """Print pre-flight check results in a user-friendly format"""
    print("\n🔍 Pre-Flight Checks")
    print("=" * 60)
    
    for check in results['checks']:
        status = "✅" if check['passed'] else "❌"
        print(f"{status} {check['name']}: {check['message']}")
    
    print("=" * 60)
    
    if results['all_passed']:
        print("✅ All pre-flight checks passed!\n")
    else:
        print("❌ Some pre-flight checks failed. Please fix the issues above.\n")
    
    return results['all_passed']
