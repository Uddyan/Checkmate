# SPDX-License-Identifier: Apache-2.0
"""Checkmate CLI - command-line interface for LLM security scanning."""

import argparse
import logging
import sys
import uuid
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Verbosity levels
VERBOSITY_QUIET = 0
VERBOSITY_NORMAL = 1
VERBOSITY_VERBOSE = 2


def setup_logging(verbosity: int = VERBOSITY_NORMAL) -> None:
    """Configure logging based on verbosity level."""
    if verbosity == VERBOSITY_QUIET:
        level = logging.WARNING
    elif verbosity == VERBOSITY_VERBOSE:
        level = logging.DEBUG
    else:
        level = logging.INFO
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )


def main(args=None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="checkmate",
        description="Checkmate - LLM Red-Teaming Security Scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  checkmate scan --config my-config.yaml
  checkmate validate --config my-config.yaml
  checkmate demo
  checkmate list-presets
        """
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # scan command
    scan_parser = subparsers.add_parser("scan", help="Run a security scan")
    scan_parser.add_argument(
        "--config", "-c",
        required=True,
        type=str,
        help="Path to YAML config file",
    )
    scan_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging (show probe/detector details)",
    )
    scan_parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Quiet mode (only show final score and summary)",
    )
    scan_parser.add_argument(
        "--profile",
        type=str,
        default=None,
        help="Profile name for metadata tracking",
    )
    scan_parser.add_argument(
        "--min-risk-score",
        type=int,
        default=None,
        help="Minimum acceptable risk score (0-100). Exit with code 1 if below.",
    )
    scan_parser.add_argument(
        "--max-critical",
        type=int,
        default=None,
        help="Maximum allowed critical findings. Exit with code 1 if exceeded.",
    )
    
    # validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a config file")
    validate_parser.add_argument(
        "--config", "-c",
        required=True,
        type=str,
        help="Path to YAML config file to validate",
    )
    
    # demo command
    subparsers.add_parser("demo", help="Run a demo scan against a vulnerable mock endpoint")
    
    # list command
    list_parser = subparsers.add_parser("list", help="List available probes/detectors")
    list_parser.add_argument(
        "type",
        choices=["probes", "detectors"],
        help="What to list",
    )
    
    # list-presets command
    subparsers.add_parser("list-presets", help="List available security profiles")
    
    # list-runs command
    list_runs_parser = subparsers.add_parser("list-runs", help="List previous scan runs")
    list_runs_parser.add_argument(
        "--limit", "-n",
        type=int,
        default=10,
        help="Number of runs to show (default: 10)",
    )
    
    # show-run command
    show_run_parser = subparsers.add_parser("show-run", help="Show details of a specific run")
    show_run_parser.add_argument(
        "--id",
        required=True,
        type=str,
        help="Run ID to show",
    )
    
    parsed_args = parser.parse_args(args)
    
    if parsed_args.command == "scan":
        return run_scan(parsed_args)
    elif parsed_args.command == "validate":
        return run_validate(parsed_args)
    elif parsed_args.command == "demo":
        return run_demo()
    elif parsed_args.command == "list":
        return run_list(parsed_args)
    elif parsed_args.command == "list-presets":
        return run_list_presets()
    elif parsed_args.command == "list-runs":
        return run_list_runs(parsed_args)
    elif parsed_args.command == "show-run":
        return run_show_run(parsed_args)
    else:
        parser.print_help()
        return 1


def run_scan(args) -> int:
    """Execute a scan."""
    if args.quiet:
        verbosity = VERBOSITY_QUIET
    elif args.verbose:
        verbosity = VERBOSITY_VERBOSE
    else:
        verbosity = VERBOSITY_NORMAL
    
    setup_logging(verbosity)
    logger = logging.getLogger(__name__)
    
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        return 1
    
    try:
        from checkmate.core.config import CheckmateConfig
        from checkmate.core.engine import CheckmateEngine
        
        if verbosity != VERBOSITY_QUIET:
            logger.info(f"Loading config from: {config_path}")
        
        config = CheckmateConfig.from_yaml(str(config_path))
        
        run_id = str(uuid.uuid4())[:8]
        profile = args.profile or "default"
        
        engine = CheckmateEngine(config, run_id=run_id, profile=profile, verbosity=verbosity)
        engine.setup()
        results = engine.run()
        engine.save_results()
        
        # Display final summary
        summary = results.get("summary", {})
        risk_score = summary.get("risk_score", 0)
        risk_score_100 = int((1 - risk_score) * 100)
        
        total_prompts = summary.get("total_prompts", 0)
        flagged = summary.get("flagged_prompts", 0)
        severity = summary.get("severity_breakdown", {})
        
        print("\n" + "=" * 60)
        print("🛡️  CHECKMATE SCAN COMPLETE")
        print("=" * 60)
        print(f"  Run ID:       {run_id}")
        print(f"  Profile:      {profile}")
        print(f"  Risk Score:   {risk_score_100}/100", end="")
        
        if risk_score_100 >= 80:
            print(" ✅ LOW RISK")
        elif risk_score_100 >= 50:
            print(" ⚠️  MODERATE RISK")
        else:
            print(" 🚨 HIGH RISK")
        
        print(f"  Total Prompts: {total_prompts}")
        print(f"  Flagged:       {flagged}")
        print(f"  Severity:      Critical={severity.get('critical', 0)}, High={severity.get('high', 0)}, Medium={severity.get('medium', 0)}, Low={severity.get('low', 0)}")
        print("=" * 60 + "\n")
        
        # Check CI/CD thresholds
        exit_code = 0
        
        if args.min_risk_score is not None:
            if risk_score_100 < args.min_risk_score:
                logger.warning(f"Risk score {risk_score_100} is below threshold {args.min_risk_score}")
                exit_code = 1
        
        if args.max_critical is not None:
            critical_count = severity.get("critical", 0)
            if critical_count > args.max_critical:
                logger.warning(f"Critical findings ({critical_count}) exceed threshold ({args.max_critical})")
                exit_code = 1
        
        return exit_code
        
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        if verbosity == VERBOSITY_VERBOSE:
            import traceback
            traceback.print_exc()
        return 1


def run_validate(args) -> int:
    """Validate a config file with friendly error messages."""
    config_path = Path(args.config)
    
    print(f"\n🔍 Validating config: {config_path}\n")
    
    # Check file exists
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return 1
    
    try:
        import yaml
        with open(config_path) as f:
            raw_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"❌ Invalid YAML syntax: {e}")
        return 1
    except Exception as e:
        print(f"❌ Failed to read config: {e}")
        return 1
    
    errors = []
    warnings = []
    
    # Check profile
    profile_config = raw_config.get("profile", {})
    preset_name = profile_config.get("preset") if isinstance(profile_config, dict) else None
    
    if preset_name:
        try:
            from checkmate.presets.loader import load_preset
            preset = load_preset(preset_name)
            print(f"  ✅ Profile: {preset_name} ({preset.description})")
        except ValueError as e:
            from checkmate.presets.loader import list_presets
            available = [p['name'] for p in list_presets()]
            errors.append(f"Unknown profile '{preset_name}'. Available: {', '.join(available)}")
    else:
        warnings.append("No profile specified, using defaults")
    
    # Check target
    target_config = raw_config.get("target", {})
    target_type = target_config.get("type")
    base_url = target_config.get("base_url")
    target_name = target_config.get("name", "unnamed")
    
    if not target_type:
        errors.append("Missing required field: target.type")
    else:
        valid_types = ["http_local", "openai", "anthropic", "cohere", "mistral", "mock"]
        if target_type not in valid_types:
            errors.append(f"Unknown target type '{target_type}'. Valid: {', '.join(valid_types)}")
        else:
            print(f"  ✅ Target type: {target_type}")
    
    if target_type == "http_local" and not base_url:
        errors.append("Missing required field: target.base_url (required for http_local)")
    elif base_url:
        print(f"  ✅ Target URL: {base_url}")
    
    # Check probes (if explicitly listed)
    extra_probes = profile_config.get("extra_probes", []) if isinstance(profile_config, dict) else []
    if extra_probes:
        from checkmate.probes.registry import list_probes
        available_probes = list(list_probes().keys())
        for probe in extra_probes:
            if probe not in available_probes:
                errors.append(f"Unknown probe '{probe}'. Available: {', '.join(available_probes)}")
    
    # Check detectors (if explicitly listed)
    extra_detectors = profile_config.get("extra_detectors", []) if isinstance(profile_config, dict) else []
    if extra_detectors:
        from checkmate.detectors.registry import list_detectors
        available_detectors = list(list_detectors().keys())
        for detector in extra_detectors:
            if detector not in available_detectors:
                errors.append(f"Unknown detector '{detector}'. Available: {', '.join(available_detectors)}")
    
    # Check output
    output_config = raw_config.get("output", {})
    results_dir = output_config.get("results_dir")
    if results_dir:
        print(f"  ✅ Output dir: {results_dir}")
    
    # Display results
    print()
    
    if warnings:
        for warning in warnings:
            print(f"⚠️  {warning}")
    
    if errors:
        for error in errors:
            print(f"❌ {error}")
        print(f"\n❌ Validation failed with {len(errors)} error(s)")
        return 1
    
    print(f"✅ Config is valid for profile '{preset_name or 'default'}' against '{target_name}'")
    return 0


def run_demo() -> int:
    """Run a demo scan against a vulnerable mock endpoint."""
    print("\n" + "=" * 60)
    print("🎭 CHECKMATE DEMO MODE")
    print("=" * 60)
    print()
    print("This demo starts an intentionally VULNERABLE mock server")
    print("and runs Checkmate against it to show detection capabilities.")
    print()
    print("⚠️  The demo server responds with:")
    print("   • Jailbreak compliance")
    print("   • Fake API key leaks")
    print("   • Toxic content")
    print()
    
    # Start demo server
    print("🚀 Starting vulnerable demo server...")
    try:
        from checkmate.demo_server import DemoServer
        server = DemoServer(port=19999)
        base_url = server.start()
        print(f"   Server running at: {base_url}")
    except Exception as e:
        print(f"❌ Failed to start demo server: {e}")
        return 1
    
    # Create temporary config
    demo_config_content = f"""
profile:
  preset: chatbot_quick

target:
  type: http_local
  name: "Vulnerable Demo Model"
  base_url: "{base_url}"
  model_name: "vulnerable-demo-model"

campaign:
  max_requests: 15
  concurrent_requests: 1
  max_rps: 10
  generations: 1

output:
  run_id: "demo-scan"
  results_dir: "runs/demo-scan"
"""
    
    # Write temp config
    temp_dir = tempfile.mkdtemp(prefix="checkmate_demo_")
    config_path = Path(temp_dir) / "demo_config.yaml"
    config_path.write_text(demo_config_content)
    
    print(f"\n📋 Running scan with chatbot_quick profile...")
    print("-" * 60)
    
    try:
        # Import and run the enterprise scanner for richer output
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from enterprise_checkmate import run_campaign
        
        success = run_campaign(config_path, dry_run=False, verbose=False, quiet=False)
        
    except ImportError:
        # Fallback to simpler scan
        print("Running simplified demo scan...")
        
        class FakeArgs:
            config = str(config_path)
            verbose = False
            quiet = False
            profile = "chatbot_quick"
            min_risk_score = None
            max_critical = None
        
        run_scan(FakeArgs())
        success = True
    except Exception as e:
        print(f"\n❌ Demo scan failed: {e}")
        import traceback
        traceback.print_exc()
        success = False
    finally:
        # Stop demo server
        print("\n🛑 Stopping demo server...")
        server.stop()
        
        # Clean up temp config
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass
    
    print()
    print("=" * 60)
    print("📝 DEMO NOTES")
    print("=" * 60)
    print()
    print("This demo intentionally shows Checkmate finding:")
    print("  • Jailbreak compliance (mitigation bypass)")
    print("  • API key leaks (data leak detection)")
    print("  • Model complying with malicious prompts")
    print()
    print("In a real deployment, findings indicate security issues")
    print("that should be addressed before production use.")
    print()
    
    return 0 if success else 1


def run_list(args) -> int:
    """List available probes or detectors."""
    if args.type == "probes":
        from checkmate.probes.registry import list_probes
        items = list_probes()
    else:
        from checkmate.detectors.registry import list_detectors
        items = list_detectors()
    
    print(f"\nAvailable {args.type}:")
    print("-" * 50)
    for name, description in items.items():
        print(f"  {name:20} {description}")
    print()
    return 0


def run_list_presets() -> int:
    """List available security profiles/presets."""
    from checkmate.presets.loader import list_presets
    
    print("\n📦 Available Profiles:")
    print("-" * 70)
    
    presets = list_presets()
    for preset in presets:
        name = preset['name']
        desc = preset['description']
        probes = preset['num_probes']
        detectors = preset['num_detectors']
        
        # Mark quick/full variants
        if 'quick' in name:
            label = "⚡ Fast"
        elif 'full' in name:
            label = "🔍 Deep"
        else:
            label = "   "
        
        print(f"  {label} {name:18} {probes} probes, {detectors} detectors")
        print(f"       {desc}")
        print()
    
    print("Usage: Set 'profile.preset' in your config YAML to use a profile")
    print()
    return 0


def run_list_runs(args) -> int:
    """List previous scan runs from database."""
    try:
        from checkmate.db import get_db_client
        
        db = get_db_client()
        if db is None:
            print("Database not configured. Run history requires database.")
            print("Add database configuration to enable run history.")
            return 1
        
        runs = db.list_scans(limit=args.limit)
        
        if not runs:
            print("No previous runs found.")
            return 0
        
        print(f"\n{'Run ID':<12} {'Timestamp':<20} {'Profile':<15} {'Target':<20} {'Score':<8}")
        print("-" * 80)
        for run in runs:
            print(f"{run.get('run_id', 'N/A'):<12} {run.get('timestamp', 'N/A'):<20} {run.get('profile', 'N/A'):<15} {run.get('target', 'N/A'):<20} {run.get('risk_score', 'N/A'):<8}")
        print()
        return 0
        
    except Exception as e:
        print(f"Error listing runs: {e}")
        return 1


def run_show_run(args) -> int:
    """Show details of a specific run."""
    try:
        from checkmate.db import get_db_client
        
        db = get_db_client()
        if db is None:
            print("Database not configured.")
            return 1
        
        run = db.get_scan(args.id)
        if run is None:
            print(f"Run not found: {args.id}")
            return 1
        
        print(f"\n{'=' * 60}")
        print(f"Run ID: {run.get('run_id')}")
        print(f"Timestamp: {run.get('timestamp')}")
        print(f"Profile: {run.get('profile')}")
        print(f"Target: {run.get('target')}")
        print(f"Risk Score: {run.get('risk_score')}/100")
        print(f"Duration: {run.get('duration_seconds', 0):.2f}s")
        print(f"\nSeverity Breakdown:")
        for sev, count in run.get('severity_breakdown', {}).items():
            print(f"  {sev}: {count}")
        print(f"\nOWASP Breakdown:")
        for cat, count in run.get('owasp_breakdown', {}).items():
            print(f"  {cat}: {count}")
        print(f"{'=' * 60}\n")
        return 0
        
    except Exception as e:
        print(f"Error showing run: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
