# SPDX-License-Identifier: Apache-2.0
"""Main Checkmate engine - orchestrates scanning."""

import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from checkmate.core.config import CheckmateConfig
from checkmate.probes.registry import get_probe
from checkmate.detectors.registry import get_detector
from checkmate.adapters import get_adapter

logger = logging.getLogger(__name__)

# Verbosity constants (match CLI)
VERBOSITY_QUIET = 0
VERBOSITY_NORMAL = 1
VERBOSITY_VERBOSE = 2


class CheckmateEngine:
    """Main engine for running Checkmate scans."""
    
    def __init__(
        self, 
        config: CheckmateConfig, 
        run_id: Optional[str] = None,
        profile: Optional[str] = None,
        verbosity: int = VERBOSITY_NORMAL,
    ):
        self.config = config
        self.run_id = run_id or str(uuid.uuid4())[:8]
        self.profile = profile or "default"
        self.verbosity = verbosity
        self.adapter = None
        self.probes = []
        self.detectors = []
        self.results = {}
        
    def setup(self) -> None:
        """Initialize adapter, probes, and detectors from config."""
        if self.verbosity >= VERBOSITY_NORMAL:
            logger.info(f"Setting up Checkmate engine (run_id: {self.run_id})...")
        
        # Configure database if enabled
        if hasattr(self.config, 'database'):
            from checkmate.db import configure_db
            configure_db({
                "enabled": self.config.database.enabled,
                "url": self.config.database.url,
            })
        
        # Initialize adapter
        target = self.config.target
        self.adapter = get_adapter(
            target.adapter,
            endpoint=target.endpoint,
            model=target.model,
            api_key=target.api_key,
            headers=target.headers,
        )
        if self.verbosity >= VERBOSITY_NORMAL:
            logger.info(f"Loaded adapter: {target.adapter}")
        
        # Initialize probes
        for probe_config in self.config.probes:
            if probe_config.enabled:
                probe = get_probe(probe_config.name, **probe_config.params)
                self.probes.append(probe)
                if self.verbosity >= VERBOSITY_VERBOSE:
                    logger.debug(f"Loaded probe: {probe_config.name} (tags: {getattr(probe, 'tags', [])})")
                elif self.verbosity >= VERBOSITY_NORMAL:
                    logger.info(f"Loaded probe: {probe_config.name}")
        
        # Initialize detectors
        for detector_config in self.config.detectors:
            if detector_config.enabled:
                detector = get_detector(detector_config.name, threshold=detector_config.threshold)
                self.detectors.append(detector)
                if self.verbosity >= VERBOSITY_VERBOSE:
                    logger.debug(f"Loaded detector: {detector_config.name} (threshold: {detector_config.threshold})")
                elif self.verbosity >= VERBOSITY_NORMAL:
                    logger.info(f"Loaded detector: {detector_config.name}")
    
    def run(self) -> Dict[str, Any]:
        """Execute the scan and return results."""
        if self.verbosity >= VERBOSITY_NORMAL:
            logger.info("Starting Checkmate scan...")
        
        start_time = datetime.now()
        
        all_results = []
        all_detections = []
        probe_stats = {}  # Track per-probe statistics
        
        for probe in self.probes:
            if self.verbosity >= VERBOSITY_NORMAL:
                logger.info(f"Running probe: {probe.name}")
            
            probe_results = probe.run(self.adapter)
            prompt_count = len(probe_results)
            detection_count = 0
            
            if self.verbosity >= VERBOSITY_VERBOSE:
                logger.debug(f"  → {probe.name} generated {prompt_count} prompts")
            
            # Run detectors on results
            for result in probe_results:
                prompt = result.get("prompt", "")
                response = result.get("response", "")
                result["detections"] = []
                
                for detector in self.detectors:
                    # Use new analyze() method with both prompt and response
                    detections = detector.analyze(prompt, response)
                    
                    for detection in detections:
                        detection_dict = detection.to_dict()
                        result["detections"].append(detection_dict)
                        all_detections.append(detection)
                        detection_count += 1
                        
                        if self.verbosity >= VERBOSITY_VERBOSE:
                            logger.debug(
                                f"  → Detection: {detection.detector_name} "
                                f"(severity={detection.severity}, score={detection.score:.2f})"
                            )
                
                all_results.append(result)
            
            # Store per-probe stats
            probe_stats[probe.name] = {
                "prompts": prompt_count,
                "detections": detection_count,
            }
            
            if self.verbosity >= VERBOSITY_VERBOSE:
                logger.debug(f"  → {probe.name}: {detection_count} detections from {prompt_count} prompts")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Compile final results with full metadata
        self.results = {
            "run_id": self.run_id,
            "profile": self.profile,
            "timestamp": start_time.isoformat(),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "target": {
                "adapter": self.config.target.adapter,
                "endpoint": self.config.target.endpoint,
                "model": self.config.target.model,
            },
            "probes_used": [p.name for p in self.probes],
            "detectors_used": [d.name for d in self.detectors],
            "probe_stats": probe_stats,
            "summary": self._compute_summary(all_results, all_detections),
            "results": all_results,
        }
        
        if self.verbosity >= VERBOSITY_NORMAL:
            logger.info(f"Scan complete. Duration: {duration:.2f}s")
        
        return self.results
    
    def _compute_summary(self, results: List[Dict], detections: List) -> Dict[str, Any]:
        """Compute summary statistics from results."""
        total = len(results)
        flagged = sum(
            1 for r in results 
            if any(d.get("flagged", False) for d in r.get("detections", []))
        )
        
        # Count detections by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        owasp_counts: Dict[str, int] = {}
        
        for detection in detections:
            severity = detection.severity
            if severity in severity_counts:
                severity_counts[severity] += 1
            
            owasp = detection.owasp_category
            if owasp:
                owasp_counts[owasp] = owasp_counts.get(owasp, 0) + 1
        
        # Risk score: fraction of flagged prompts (0-1 scale, higher = worse)
        risk_score = flagged / total if total > 0 else 0.0
        
        return {
            "total_prompts": total,
            "flagged_prompts": flagged,
            "total_detections": len(detections),
            "pass_rate": (total - flagged) / total if total > 0 else 1.0,
            "risk_score": risk_score,
            "severity_breakdown": severity_counts,
            "owasp_breakdown": owasp_counts,
        }
    
    def save_results(self) -> None:
        """Save results to output directory."""
        from checkmate.core.report import generate_json, generate_html
        
        output_dir = Path(self.config.output.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if "json" in self.config.output.formats:
            json_path = output_dir / "results.json"
            generate_json(self.results, str(json_path))
            if self.verbosity >= VERBOSITY_NORMAL:
                logger.info(f"Saved JSON report: {json_path}")
        
        if "html" in self.config.output.formats:
            html_path = output_dir / "results.html"
            generate_html(self.results, str(html_path))
            if self.verbosity >= VERBOSITY_NORMAL:
                logger.info(f"Saved HTML report: {html_path}")
        
        # Try to save to database (graceful fallback)
        try:
            from checkmate.db import get_db_client
            db = get_db_client()
            if db is not None:
                db.save_scan(self.results)
                if self.verbosity >= VERBOSITY_NORMAL:
                    logger.info("Saved results to database")
        except Exception as e:
            if self.verbosity >= VERBOSITY_VERBOSE:
                logger.debug(f"Database save skipped: {e}")
