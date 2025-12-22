"""
Checkmate: Minimal One-Probe LLM Security Scanner

Simple CLI for running security tests against LLM models.
"""

#!/usr/bin/env python3
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List, Union

# CRITICAL: Set config defaults BEFORE any checkmate imports
# This prevents AttributeError for config attributes accessed during module loading
import checkmate
from checkmate import _config

# Set critical config attributes that might be accessed during imports
if not hasattr(_config.system, 'user_agent'):
    _config.system.user_agent = "checkmate-beta-scanner/1.0"
if not hasattr(_config.run, 'user_agent'):
    _config.run.user_agent = "checkmate-beta-scanner/1.0"  # Harness uses this
if not hasattr(_config.system, 'lite'):
    _config.system.lite = False
if not hasattr(_config.system, 'show_z'):
    _config.system.show_z = False
if not hasattr(_config.system, 'narrow_output'):
    _config.system.narrow_output = False
if not hasattr(_config.system, 'parallel_attempts'):
    _config.system.parallel_attempts = False  # Probes may check this

# Rich for progress indicators
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table

# Import checkmate core (after config is set)
from checkmate import _plugins, command
from checkmate.adapters import get_adapter
from checkmate.generators.base import Generator
from checkmate.evaluators.base import Evaluator
from checkmate.attempt import Conversation, Message  # For AdapterGenerator

# Import pilot modules
from checkmate.pilot_config import (
    load_pilot_config,
    setup_checkmate_config,
    get_adapter_kwargs,
    validate_pilot_config_file
)
from checkmate.presets.loader import (
    load_preset,
    preset_to_plugin_names,
    list_presets
)
from checkmate.utils.preflight import run_pre_flight_checks, print_pre_flight_results

# Load .env file if present
from dotenv import load_dotenv
load_dotenv()

console = Console()


class AdapterGenerator(Generator):
    """Wrapper to use an adapter as a generator for harness execution"""
    
    def __init__(self, adapter):
        self.adapter = adapter
        self.name = adapter.name
        self.fullname = f"Adapter:{adapter.name}"
        self.generator_family_name = "HTTP_LOCAL"
        self.active = True
        self.generations = _config.run.generations if hasattr(_config.run, 'generations') else 1
        # Don't call super().__init__ to avoid re-initializing
    
    def _call_model(
        self, prompt: Conversation, generations_this_call: int = 1
    ) -> List[Union[Message, None]]:
        """Generate responses using the adapter
        
        Args:
            prompt: Conversation object
            generations_this_call: Number of generations
            
        Returns:
            List of Message objects
        """
        # Extract prompt text from conversation
        prompt_text = prompt.last_message().text
        
        try:
            # Call adapter with string prompt
            responses = self.adapter.generate(prompt_text, generations_this_call)
            
            # Convert string responses to Message objects
            if isinstance(responses, list):
                return [Message(str(r)) if r is not None else None for r in responses]
            else:
                # Single response
                return [Message(str(responses))] if responses is not None else [None]
                
        except Exception as e:
            logging.error(f"Adapter generation error: {e}")
            # Return error message instead of raising
            return [Message(f"ERROR: Generation failed: {e}")]


def format_error(error: Exception, context: str = "") -> str:
    """Format errors in a user-friendly way"""
    error_type = type(error).__name__
    
    friendly_messages = {
        'FileNotFoundError': f"📁 File not found: {error}",
        'ValueError': f"⚠️  Invalid value: {error}",
        'ConnectionError': f"🔌 Connection failed: {error}",
        'TimeoutError': f"⏱️  Request timed out: {error}",
        'KeyError': f"🔑 Missing required field: {error}",
        'AttributeError': f"⚙️  Configuration error: {error}",
    }
    
    if error_type in friendly_messages:
        return friendly_messages[error_type]
    
    return f"❌ Error{' in ' + context if context else ''}: {error}"


def run_campaign(config_path: Path, dry_run: bool = False, verbose: bool = False, quiet: bool = False) -> bool:
    """Run a red-teaming campaign against an LLM target
    
    Args:
        config_path: Path to config file
        dry_run: If True, validate only without running
        verbose: If True, show detailed probe/detector info
        quiet: If True, show only final score and summary
    """
    
    if not quiet:
        console.print("\n[bold blue]🚀 Checkmate: LLM Security Scanner[/bold blue]")
        console.print("=" * 60)
    
    # Load and validate config
    if not quiet:
        console.print(f"📋 Loading config: [yellow]{config_path}[/yellow]")
    try:
        pilot_config = load_pilot_config(config_path)
    except Exception as e:
        console.print(f"\n{format_error(e, 'config loading')}")
        return False
    
    # Generate run_id early for tracking
    run_id = pilot_config.output.get_run_id()
    
    if not quiet:
        console.print(f"✅ Config loaded: [green]{pilot_config.target.name}[/green]")
        console.print(f"   Run ID: [cyan]{run_id}[/cyan]")
        console.print(f"   Target: {pilot_config.target.type}")
        console.print(f"   Profile: {pilot_config.profile.preset}")
    
    # Run pre-flight checks
    if not quiet:
        console.print("\n[bold]Running Pre-Flight Checks...[/bold]")
    preflight_results = run_pre_flight_checks(pilot_config)
    if not print_pre_flight_results(preflight_results, quiet=quiet):
        console.print("[bold red]❌ Pre-flight checks failed. Please fix the issues above.[/bold red]")
        return False
    
    # Load preset
    if not quiet:
        console.print(f"📦 Loading preset: [yellow]{pilot_config.profile.preset}[/yellow]")
    try:
        preset = load_preset(pilot_config.profile.preset)
        probe_names, detector_names = preset_to_plugin_names(
            preset,
            pilot_config.profile.extra_probes,
            pilot_config.profile.extra_detectors
        )
    except Exception as e:
        console.print(f"\n{format_error(e, 'preset loading')}")
        return False
    
    if not quiet:
        console.print(f"✅ Preset loaded: [green]{preset.description}[/green]")
        console.print(f"   Probes: {len(probe_names)}")
        console.print(f"   Detectors: {len(detector_names)}")
    
    # Verbose mode: show probe details
    if verbose:
        console.print("\n[bold cyan]📋 Probe Details:[/bold cyan]")
        for probe_name in probe_names:
            console.print(f"   • {probe_name}")
        console.print("[bold cyan]🔍 Detector Details:[/bold cyan]")
        for det_name in detector_names:
            console.print(f"   • {det_name}")
    
    # DRY RUN MODE
    if dry_run:
        console.print("\n[bold yellow]🔍 DRY RUN MODE - No actual attacks will be sent[/bold yellow]")
        
        table = Table(title="Campaign Plan")
        table.add_column("Component", style="cyan")
        table.add_column("Details", style="green")
        
        table.add_row("Target", f"{pilot_config.target.type} - {pilot_config.target.name}")
        table.add_row("Endpoint", pilot_config.target.base_url or "N/A")
        table.add_row("Preset", pilot_config.profile.preset)
        table.add_row("Total Probes", str(len(probe_names)))
        table.add_row("Total Detectors", str(len(detector_names)))
        table.add_row("Max Requests", str(pilot_config.campaign.max_requests))
        table.add_row("Rate Limit", f"{pilot_config.campaign.max_rps} req/s")
        table.add_row("Concurrent", str(pilot_config.campaign.concurrent_requests))
        table.add_row("Output Dir", str(pilot_config.output.get_results_path()))
        
        console.print(table)
        console.print("\n✅ [green]Dry run complete - configuration is valid![/green]")
        return True
    
    # Setup checkmate environment FIRST (before creating adapter)
    console.print("\n⚙️  Configuring checkmate environment...")
    try:
        setup_checkmate_config(pilot_config)
    except Exception as e:
        console.print(f"\n{format_error(e, 'environment setup')}")
        return False
    
    # Initialize adapter AFTER config is set
    console.print(f"🔌 Initializing adapter: [yellow]{pilot_config.target.type}[/yellow]")
    try:
        adapter_kwargs = get_adapter_kwargs(pilot_config.target)
        adapter = get_adapter(pilot_config.target.type, **adapter_kwargs)
        
        if not adapter.is_available():
            console.print(f"[bold red]❌ Adapter {pilot_config.target.type} not available[/bold red]")
            return False
            
        console.print(f"✅ Adapter ready: [green]{adapter.name}[/green]")
    except Exception as e:
        console.print(f"\n{format_error(e, 'adapter initialization')}")
        logging.exception(e)
        return False
    
    # Create generator wrapper
    generator = AdapterGenerator(adapter)
    
    # Create evaluator
    evaluator = Evaluator()
    
    # Start checkmate run (sets up JSONL reporting)
    console.print("\n📝 Starting campaign run...")
    command.start_logging()
    command.start_run()
    
    console.print(f"   Report dir: {_config.reporting.report_dir}")
    console.print(f"   Run ID: {_config.transient.run_id}")
    
    # Execute campaign with progress indicators
    console.print(f"\n[bold]🔍 Executing vulnerability scans...[/bold]")
    console.print(f"   Testing {len(probe_names)} probes with {len(detector_names)} detectors\n")
    
    try:
        # Use progress bar for campaign execution
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task(
                "[cyan]Running security probes...",
                total=len(probe_names)
            )
            
            # Use pxd harness if we have explicit detectors
            if detector_names:
                progress.update(task, description="[cyan]Using PxD (Probe x Detector) harness")
                command.pxd_run(
                    generator=generator,
                    probe_names=probe_names,
                    detector_names=detector_names,
                    evaluator=evaluator,
                    buffs=[]
                )
            else:
                progress.update(task, description="[cyan]Using Probewise harness")
                command.probewise_run(
                    generator=generator,
                    probe_names=probe_names,
                    evaluator=evaluator,
                    buffs=[]
                )
            
            progress.update(task, completed=len(probe_names))
            
    except Exception as e:
        console.print(f"\n{format_error(e, 'campaign execution')}")
        logging.exception(e)
        # Still try to generate reports
    
    # End run (generates HTML report)
    if not quiet:
        console.print("\n📊 Generating reports...")
    command.end_run()
    
    # Enhance with risk scoring and OWASP mapping
    if not quiet:
        console.print("🎯 Calculating risk score...")
    summary_data = None
    try:
        from checkmate.scoring.risk_scorer import enhance_reports_with_scoring
        report_path = Path(_config.transient.report_filename)
        results_dir = report_path.parent
        
        summary_data, _ = enhance_reports_with_scoring(
            report_jsonl_path=report_path,
            results_dir=results_dir,
            preset=preset,
            target_name=pilot_config.target.name,
            target_url=pilot_config.target.base_url,
            profile_name=pilot_config.profile.preset,
            quiet=quiet
        )
        if not quiet:
            console.print("✅ [green]Risk scoring complete[/green]")
    except Exception as e:
        console.print(f"⚠️  {format_error(e, 'risk scoring')}")
        logging.exception(e)
    
    # Generate executive HTML report
    if not quiet:
        console.print("📄 Generating executive HTML report...")
    try:
        from checkmate.reporting.renderer import render_html_report
        
        summary_path = results_dir / "summary.json"
        findings_path = results_dir / "findings.json"
        html_path = results_dir / "report.html"
        
        if summary_path.exists() and findings_path.exists():
            render_html_report(summary_path, findings_path, html_path)
            if not quiet:
                console.print(f"   ✅ HTML report: [cyan]{html_path}[/cyan]")
        else:
            if not quiet:
                console.print("   ⚠️  JSON files not found, skipping HTML generation")
    except Exception as e:
        console.print(f"   ⚠️  HTML generation failed: {e}")
        logging.error(f"HTML generation error: {e}", exc_info=True)
    
    # Final Summary - Always show this
    console.print("\n" + "=" * 60)
    console.print("[bold green]✅ Checkmate Scan Complete[/bold green]")
    console.print("=" * 60)
    
    # Show run_id and risk score prominently
    console.print(f"\n   [cyan]Run ID:[/cyan]     {run_id}")
    if summary_data:
        risk_score = summary_data.get('risk_score', 'N/A')
        # Color code risk score
        if isinstance(risk_score, (int, float)):
            if risk_score >= 80:
                score_color = "green"
            elif risk_score >= 50:
                score_color = "yellow"
            else:
                score_color = "red"
            console.print(f"   [cyan]Risk Score:[/cyan]  [{score_color}]{risk_score:.1f}/100[/{score_color}]")
        else:
            console.print(f"   [cyan]Risk Score:[/cyan]  {risk_score}")
        
        total_detections = summary_data.get('total_detections', 0)
        console.print(f"   [cyan]Detections:[/cyan]  {total_detections}")
    
    console.print(f"\n   [cyan]Results:[/cyan]    {results_dir}")
    console.print(f"   [cyan]HTML:[/cyan]       {results_dir / 'report.html'}")
    console.print()
    
    return True


def list_components(component_type: str):
    """List available components with rich formatting"""
    if component_type == "presets":
        console.print("\n[bold]Available Presets:[/bold]\n")
        presets = list_presets()
        
        table = Table()
        table.add_column("Preset", style="cyan")
        table.add_column("Description", style="green")
        table.add_column("Probes", justify="right", style="yellow")
        table.add_column("Detectors", justify="right", style="yellow")
        
        for preset in presets:
            table.add_row(
                preset['name'],
                preset['description'],
                str(preset['num_probes']),
                str(preset['num_detectors'])
            )
        
        console.print(table)
        
    elif component_type == "probes":
        command.print_probes()
    elif component_type == "detectors":
        command.print_detectors()
    else:
        console.print(f"[red]Unknown component type: {component_type}[/red]")


def validate_config(config_path: Path):
    """Validate a pilot config file"""
    console.print(f"\n[bold]Validating config:[/bold] {config_path}")
    is_valid, message = validate_pilot_config_file(config_path)
    if is_valid:
        console.print(f"✅ [green]{message}[/green]")
        return True
    else:
        console.print(f"❌ [red]{message}[/red]")
        return False


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="enterprise-checkmate",
        description="Enterprise LLM Red-Teaming Scanner for Beta Customers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Run a campaign:
    python3 enterprise_checkmate.py run --config config.yaml
  
  Dry run (validate without executing):
    python3 enterprise_checkmate.py run --config config.yaml --dry-run
  
  List presets:
    python3 enterprise_checkmate.py list presets
  
  Validate config:
    python3 enterprise_checkmate.py validate --config config.yaml
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run a red-teaming campaign")
    run_parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to pilot YAML config file"
    )
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate config and show plan without executing"
    )
    run_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed probe/detector info during execution"
    )
    run_parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Show only final risk score and summary"
    )
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available components")
    list_parser.add_argument(
        "component",
        choices=["presets", "probes", "detectors"],
        help="Component type to list"
    )
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a config file")
    validate_parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to config file to validate"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    # Execute command
    if args.command == "run":
        success = run_campaign(
            args.config, 
            dry_run=args.dry_run,
            verbose=getattr(args, 'verbose', False),
            quiet=getattr(args, 'quiet', False)
        )
        return 0 if success else 1
    
    elif args.command == "list":
        list_components(args.component)
        return 0
    
    elif args.command == "validate":
        is_valid = validate_config(args.config)
        return 0 if is_valid else 1
    
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
