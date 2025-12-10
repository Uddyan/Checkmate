# SPDX-License-Identifier: Apache-2.0
"""Checkmate CLI - minimal command-line interface."""

import argparse
import logging
import sys
from pathlib import Path


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )


def main(args=None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="checkmate",
        description="Checkmate - LLM Red-Teaming Scanner",
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
        help="Enable verbose logging",
    )
    
    # list command
    list_parser = subparsers.add_parser("list", help="List available probes/detectors")
    list_parser.add_argument(
        "type",
        choices=["probes", "detectors"],
        help="What to list",
    )
    
    parsed_args = parser.parse_args(args)
    
    if parsed_args.command == "scan":
        return run_scan(parsed_args)
    elif parsed_args.command == "list":
        return run_list(parsed_args)
    else:
        parser.print_help()
        return 1


def run_scan(args) -> int:
    """Execute a scan."""
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        return 1
    
    try:
        from checkmate.core.config import CheckmateConfig
        from checkmate.core.engine import CheckmateEngine
        
        logger.info(f"Loading config from: {config_path}")
        config = CheckmateConfig.from_yaml(str(config_path))
        
        engine = CheckmateEngine(config)
        engine.setup()
        engine.run()
        engine.save_results()
        
        logger.info("✅ Scan complete!")
        return 0
        
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def run_list(args) -> int:
    """List available probes or detectors."""
    if args.type == "probes":
        from checkmate.probes.registry import list_probes
        items = list_probes()
    else:
        from checkmate.detectors.registry import list_detectors
        items = list_detectors()
    
    print(f"\nAvailable {args.type}:")
    print("-" * 40)
    for name, description in items.items():
        print(f"  {name}: {description}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
