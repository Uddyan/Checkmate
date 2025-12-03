"""Command-line interface for checkmate"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from checkmate.adapters import get_adapter, ADAPTERS
from checkmate.core.types import RunConfig
from checkmate.utils.resources import data_path


def main(args: Optional[List[str]] = None) -> None:
    """Main CLI entry point"""
    if args is None:
        args = sys.argv[1:]
    
    parser = argparse.ArgumentParser(
        prog="checkmate",
        description="Model-agnostic LLM vulnerability scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run vulnerability scans")
    run_parser.add_argument(
        "--adapters",
        nargs="+",
        default=["null"],
        help="Adapters to use (default: null)"
    )
    run_parser.add_argument(
        "--probes",
        nargs="+",
        default=["demo"],
        help="Probes to run (default: demo)"
    )
    run_parser.add_argument(
        "--detectors",
        nargs="+",
        default=["basic"],
        help="Detectors to use (default: basic)"
    )
    run_parser.add_argument(
        "--buffs",
        nargs="+",
        default=[],
        help="Buffs to apply"
    )
    run_parser.add_argument(
        "--output",
        type=str,
        default="runs",
        help="Output directory (default: runs)"
    )
    run_parser.add_argument(
        "--max-attempts",
        type=int,
        default=10,
        help="Maximum attempts per probe (default: 10)"
    )
    run_parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducibility"
    )
    run_parser.add_argument(
        "--model-name",
        type=str,
        help="Model name for adapters (e.g., deepseek/deepseek-r1-0528-qwen3-8b)"
    )
    run_parser.add_argument(
        "--base-url",
        type=str,
        help="Base URL for HTTP adapter (e.g., http://192.168.1.232:1234)"
    )
    run_parser.add_argument(
        "--generations",
        type=int,
        default=3,
        help="Number of generations per probe (default: 3)"
    )
    run_parser.add_argument(
        "--config",
        type=str,
        help="Configuration file to use"
    )
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available components")
    list_parser.add_argument(
        "component",
        choices=["adapters", "probes", "detectors", "buffs"],
        help="Component type to list"
    )
    
    # Explain command
    explain_parser = subparsers.add_parser("explain", help="Explain a component")
    explain_parser.add_argument(
        "component_id",
        help="Component ID to explain"
    )
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate reports from scan results")
    report_parser.add_argument(
        "run_dir",
        type=str,
        help="Directory containing report.jsonl from a scan"
    )
    report_parser.add_argument(
        "--out",
        type=str,
        help="Output directory for reports (default: <run_dir>/reports)"
    )
    
    parsed_args = parser.parse_args(args)
    
    if parsed_args.command == "run":
        run_command(parsed_args)
    elif parsed_args.command == "list":
        list_command(parsed_args)
    elif parsed_args.command == "explain":
        explain_command(parsed_args)
    elif parsed_args.command == "report":
        report_command(parsed_args)
    else:
        parser.print_help()


def run_command(args) -> None:
    """Handle the run command"""
    print(f"🔍 Checkmate: Running vulnerability scan")
    print(f"   Adapters: {', '.join(args.adapters)}")
    print(f"   Probes: {', '.join(args.probes)}")
    print(f"   Detectors: {', '.join(args.detectors)}")
    print(f"   Output: {args.output}")
    print(f"   Generations: {args.generations}")
    
    # Create output directory
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load base configuration
    try:
        from checkmate import _config
        if not _config.loaded:
            _config.load_base_config()
        print("   ✅ Configuration loaded")
    except Exception as e:
        print(f"   ⚠️  Config loading had issues: {e}, using defaults")
    
    # Initialize adapters with model configuration
    adapters = []
    for adapter_name in args.adapters:
        try:
            adapter_kwargs = {}
            if adapter_name == "hf_local" and args.model_name:
                adapter_kwargs["model_name"] = args.model_name
                print(f"   🔧 Using model: {args.model_name}")
            elif adapter_name == "http_local":
                if args.base_url:
                    adapter_kwargs["base_url"] = args.base_url
                    print(f"   🔧 Using endpoint: {args.base_url}")
                if args.model_name:
                    adapter_kwargs["model_name"] = args.model_name
                    print(f"   🔧 Using model: {args.model_name}")
            
            adapter = get_adapter(adapter_name, **adapter_kwargs)
            if adapter.is_available():
                adapters.append(adapter)
                print(f"   ✅ {adapter_name} adapter ready")
            else:
                print(f"   ❌ {adapter_name} adapter not available")
        except Exception as e:
            print(f"   ❌ Failed to load {adapter_name}: {e}")
    
    if not adapters:
        print("   ❌ No adapters available")
        return
    
    # Parse probe specifications
    from checkmate import _plugins
    probe_names = []
    
    for probe_spec in args.probes:
        if probe_spec.lower() == "all":
            # Get all active probes
            all_probes = _plugins.enumerate_plugins("probes")
            probe_names.extend([name for name, active in all_probes if active])
        else:
            # Parse specific probe names
            if "." not in probe_spec:
                # Try to find probes by module name
                found_probes = [name for name, active in _plugins.enumerate_plugins("probes") 
                              if name.startswith(f"probes.{probe_spec}.") and active]
                probe_names.extend(found_probes)
            else:
                # Full probe name
                probe_names.append(f"probes.{probe_spec}")
    
    if not probe_names:
        print("   ❌ No probes found")
        return
    
    print(f"   🚀 Running {len(probe_names)} probes on {len(adapters)} adapters...")
    
    # Run the actual vulnerability scan
    try:
        from checkmate.harnesses.probewise import ProbewiseHarness
        from checkmate.evaluators.base import Evaluator
        from checkmate.generators.adapter_wrapper import AdapterGenerator
        from checkmate import _config
        import json
        import os
        
        # Set up report file
        report_file_path = output_path / "report.jsonl"
        report_file = open(report_file_path, "w", encoding="utf-8")
        _config.transient.reportfile = report_file
        _config.transient.report_filename = str(report_file_path)
        
        harness = ProbewiseHarness()
        evaluator = Evaluator()
        
        for adapter in adapters:
            print(f"   📊 Testing {adapter.name}...")
            
            # Convert adapter to generator
            generator = AdapterGenerator(adapter, name=adapter.name)
            
            # Run the scan
            harness.run(generator, probe_names, evaluator)
        
        report_file.close()
        print(f"   ✅ Scan complete! Results saved to {report_file_path}")
        
    except Exception as e:
        print(f"   ❌ Scan failed: {e}")
        import traceback
        traceback.print_exc()


def list_command(args) -> None:
    """Handle the list command"""
    component = args.component
    
    if component == "adapters":
        print("Available adapters:")
        for name, adapter_class in ADAPTERS.items():
            print(f"  {name}: {adapter_class.__doc__ or 'No description'}")
    
    elif component == "probes":
        print("Available probes:")
        from checkmate import _plugins
        probes = _plugins.enumerate_plugins("probes")
        active_probes = [name for name, active in probes if active]
        print(f"  Total: {len(probes)} probes ({len(active_probes)} active)")
        print()
        
        # Group probes by category
        categories = {}
        for name, active in probes:
            if active:
                module = name.split('.')[1]  # Get module name
                if module not in categories:
                    categories[module] = []
                categories[module].append(name.split('.')[-1])  # Get class name
        
        for category, probe_classes in sorted(categories.items()):
            print(f"  {category}:")
            for probe_class in sorted(probe_classes):
                print(f"    {probe_class}")
            print()
    
    elif component == "detectors":
        print("Available detectors:")
        from checkmate import _plugins
        detectors = _plugins.enumerate_plugins("detectors")
        active_detectors = [name for name, active in detectors if active]
        print(f"  Total: {len(detectors)} detectors ({len(active_detectors)} active)")
        print()
        
        # Group detectors by category
        categories = {}
        for name, active in detectors:
            if active:
                module = name.split('.')[1]  # Get module name
                if module not in categories:
                    categories[module] = []
                categories[module].append(name.split('.')[-1])  # Get class name
        
        for category, detector_classes in sorted(categories.items()):
            print(f"  {category}:")
            for detector_class in sorted(detector_classes):
                print(f"    {detector_class}")
            print()
    
    elif component == "buffs":
        print("Available buffs:")
        print("  none: No buffs available yet")


def explain_command(args) -> None:
    """Handle the explain command"""
    print(f"Explaining: {args.component_id}")
    # TODO: Implement explain functionality


def report_command(args) -> None:
    """Handle the report command"""
    from checkmate.reporting.report import ReportGenerator
    from datetime import datetime
    
    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        print(f"❌ Error: Directory not found: {run_dir}")
        return
    
    report_jsonl = run_dir / "report.jsonl"
    if not report_jsonl.exists():
        print(f"❌ Error: report.jsonl not found in {run_dir}")
        return
    
    # Determine output directory
    if args.out:
        output_dir = Path(args.out)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = run_dir / "reports" / timestamp
    
    print(f"📊 Generating reports from {report_jsonl}")
    print(f"   Output directory: {output_dir}")
    
    try:
        generator = ReportGenerator(report_jsonl, output_dir)
        generator.load()
        results = generator.generate_all()
        
        print(f"✅ Reports generated successfully:")
        print(f"   📄 HTML: {results['html']}")
        print(f"   📊 CSV: {results['csv']}")
        print(f"   📋 JSON: {results['json']}")
    except Exception as e:
        print(f"❌ Error generating reports: {e}")
        import traceback
        traceback.print_exc()