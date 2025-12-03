"""Parallel harness with rate limiting and determinism"""

import json
import logging
from typing import List, Optional
from colorama import Fore, Style

import checkmate.attempt
from checkmate.detectors.base import Detector
from checkmate.harnesses.probewise import ProbewiseHarness
from checkmate.execution.parallel import ParallelExecutor, get_adapter_rate_limiter

from checkmate import _config, _plugins


class ParallelProbewiseHarness(ProbewiseHarness):
    """Enhanced ProbewiseHarness with parallel execution support"""
    
    def __init__(self, config_root=_config, max_workers: Optional[int] = None, seed: Optional[int] = None):
        """Initialize parallel harness.
        
        Args:
            config_root: Configuration root
            max_workers: Maximum worker threads (default: auto-detect)
            seed: Random seed for determinism
        """
        super().__init__(config_root)
        self.max_workers = max_workers
        self.seed = seed
        self.parallel_executor: Optional[ParallelExecutor] = None
    
    def _get_executor(self, adapter_name: str) -> ParallelExecutor:
        """Get or create parallel executor for adapter"""
        if self.parallel_executor is None:
            rate_limiter = get_adapter_rate_limiter(adapter_name)
            self.parallel_executor = ParallelExecutor(
                max_workers=self.max_workers,
                rate_limiter=rate_limiter,
                seed=self.seed,
            )
        return self.parallel_executor
    
    def run(self, model, probenames, evaluator, buff_names=None):
        """Execute probes with parallel attempt execution where possible"""
        
        if buff_names is None:
            buff_names = []

        if not probenames:
            msg = "No probes, nothing to do"
            logging.warning(msg)
            if hasattr(_config.system, "verbose") and _config.system.verbose >= 2:
                print(msg)
            raise ValueError(msg)

        self._load_buffs(buff_names)

        probenames = sorted(probenames)  # Deterministic ordering
        print(
            f"🕵️  queue of {Style.BRIGHT}{Fore.LIGHTYELLOW_EX}probes:{Style.RESET_ALL} "
            + ", ".join([name.replace("probes.", "") for name in probenames])
        )
        logging.info("probe queue: %s", " ".join(probenames))
        
        # Get adapter name for rate limiting
        adapter_name = getattr(model, 'name', 'unknown')
        if hasattr(model, 'adapter'):
            adapter_name = getattr(model.adapter, 'name', adapter_name)
        
        executor = self._get_executor(adapter_name)
        
        for probename in probenames:
            try:
                probe = _plugins.load_plugin(probename)
            except Exception as e:
                print(f"failed to load probe {probename}")
                logging.warning("failed to load probe %s:", repr(e))
                continue
            if not probe:
                continue
            detectors = []

            if probe.primary_detector:
                d = self._load_detector(probe.primary_detector)
                if d:
                    detectors = [d]
                if _config.plugins.extended_detectors is True:
                    for detector_name in sorted(probe.extended_detectors):
                        d = self._load_detector(detector_name)
                        if d:
                            detectors.append(d)

            else:
                logging.debug(
                    "deprecation warning - probe %s using recommend_detector instead of primary_detector",
                    probename,
                )
                for detector_name in sorted(probe.recommended_detectors):
                    d = self._load_detector(detector_name)
                    if d:
                        detectors.append(d)

            if not detectors:
                logging.warning("no detectors for probe %s, skipping", probename)
                continue

            # Enable parallel execution in probe if supported
            if hasattr(probe, 'parallel_attempts') and probe.parallelisable_attempts:
                # Set parallel attempts based on executor workers
                probe.parallel_attempts = executor.max_workers
                probe.max_workers = executor.max_workers

            # Run probe (it will use parallel execution internally if enabled)
            attempt_results = probe.probe(model)
            
            # Run detectors in parallel where possible
            for d in detectors:
                logging.debug("harness: run detector %s", d.detectorname)
                detector_probe_name = d.detectorname.replace("checkmate.detectors.", "")
                
                # Collect attempts for parallel detection
                attempt_list = list(attempt_results)
                
                # Execute detection in parallel
                def detect_attempt(attempt):
                    if d.skip:
                        return None
                    return (attempt, list(d.detect(attempt)))
                
                detection_tasks = [lambda a=att: detect_attempt(a) for att in attempt_list]
                detection_results = executor.execute(detection_tasks, preserve_order=True)
                
                # Apply detection results
                for result in detection_results:
                    if result is not None:
                        attempt, scores = result
                        attempt.detector_results[detector_probe_name] = scores

            # Write results
            for attempt in attempt_results:
                attempt.status = checkmate.attempt.ATTEMPT_COMPLETE
                _config.transient.reportfile.write(
                    json.dumps(attempt.as_dict(), ensure_ascii=False) + "\n"
                )

            if len(attempt_results) == 0:
                logging.warning(
                    "zero attempt results: probe %s",
                    probename,
                )
            else:
                evaluator.evaluate(attempt_results)

