# SPDX-License-Identifier: Apache-2.0
"""Main Checkmate engine - orchestrates scanning."""

import logging
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

from checkmate.core.config import CheckmateConfig
from checkmate.probes.registry import get_probe
from checkmate.detectors.registry import get_detector
from checkmate.adapters import get_adapter

logger = logging.getLogger(__name__)


class CheckmateEngine:
    """Main engine for running Checkmate scans."""
    
    def __init__(self, config: CheckmateConfig):
        self.config = config
        self.adapter = None
        self.probes = []
        self.detectors = []
        self.results = []
        
    def setup(self) -> None:
        """Initialize adapter, probes, and detectors from config."""
        logger.info("Setting up Checkmate engine...")
        
        # Initialize adapter
        target = self.config.target
        self.adapter = get_adapter(
            target.adapter,
            endpoint=target.endpoint,
            model=target.model,
            api_key=target.api_key,
            headers=target.headers,
        )
        logger.info(f"Loaded adapter: {target.adapter}")
        
        # Initialize probes
        for probe_config in self.config.probes:
            if probe_config.enabled:
                probe = get_probe(probe_config.name, **probe_config.params)
                self.probes.append(probe)
                logger.info(f"Loaded probe: {probe_config.name}")
        
        # Initialize detectors
        for detector_config in self.config.detectors:
            if detector_config.enabled:
                detector = get_detector(detector_config.name, threshold=detector_config.threshold)
                self.detectors.append(detector)
                logger.info(f"Loaded detector: {detector_config.name}")
    
    def run(self) -> Dict[str, Any]:
        """Execute the scan and return results."""
        logger.info("Starting Checkmate scan...")
        start_time = datetime.now()
        
        all_results = []
        
        for probe in self.probes:
            logger.info(f"Running probe: {probe.name}")
            probe_results = probe.run(self.adapter)
            
            # Run detectors on results
            for result in probe_results:
                result["detections"] = []
                for detector in self.detectors:
                    detection = detector.detect(result["response"])
                    result["detections"].append({
                        "detector": detector.name,
                        "score": detection,
                        "flagged": detection >= detector.threshold,
                    })
                all_results.append(result)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Compile final results
        self.results = {
            "scan_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "target": {
                "adapter": self.config.target.adapter,
                "model": self.config.target.model,
            },
            "summary": self._compute_summary(all_results),
            "results": all_results,
        }
        
        logger.info(f"Scan complete. Duration: {duration:.2f}s")
        return self.results
    
    def _compute_summary(self, results: List[Dict]) -> Dict[str, Any]:
        """Compute summary statistics from results."""
        total = len(results)
        flagged = sum(
            1 for r in results 
            if any(d["flagged"] for d in r.get("detections", []))
        )
        
        return {
            "total_prompts": total,
            "flagged_prompts": flagged,
            "pass_rate": (total - flagged) / total if total > 0 else 1.0,
            "risk_score": flagged / total if total > 0 else 0.0,
        }
    
    def save_results(self) -> None:
        """Save results to output directory."""
        from checkmate.core.report import generate_json, generate_html
        
        output_dir = Path(self.config.output.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if "json" in self.config.output.formats:
            json_path = output_dir / "results.json"
            generate_json(self.results, str(json_path))
            logger.info(f"Saved JSON report: {json_path}")
        
        if "html" in self.config.output.formats:
            html_path = output_dir / "results.html"
            generate_html(self.results, str(html_path))
            logger.info(f"Saved HTML report: {html_path}")
