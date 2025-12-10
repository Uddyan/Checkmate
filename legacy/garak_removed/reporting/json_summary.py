"""JSON summary report generator"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict


class JSONSummaryGenerator:
    """Generates a JSON summary with KPIs and statistics"""

    def __init__(
        self,
        records: List[Dict[str, Any]],
        attempts: List[Dict[str, Any]],
        evaluations: List[Dict[str, Any]],
        config: Optional[Dict[str, Any]],
    ):
        self.records = records
        self.attempts = attempts
        self.evaluations = evaluations
        self.config = config

    def _calculate_kpis(self) -> Dict[str, Any]:
        """Calculate key performance indicators."""
        total_attempts = len(self.attempts)
        total_evaluations = len(self.evaluations)

        # Calculate attack success rate (ASR)
        # ASR = (attempts with score > 0) / total attempts
        vulnerable_attempts = 0
        total_scores = 0.0
        score_count = 0

        for attempt in self.attempts:
            detector_results = attempt.get("detector_results", {})
            for detector_name, scores in detector_results.items():
                for score in scores:
                    if score is not None:
                        total_scores += score
                        score_count += 1
                        if score > 0.0:
                            vulnerable_attempts += 1

        asr = (vulnerable_attempts / total_attempts * 100) if total_attempts > 0 else 0.0
        avg_score = (total_scores / score_count) if score_count > 0 else 0.0

        # Severity distribution
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for attempt in self.attempts:
            detector_results = attempt.get("detector_results", {})
            for detector_name, scores in detector_results.items():
                for score in scores:
                    if score is not None:
                        if score >= 0.8:
                            severity_counts["critical"] += 1
                        elif score >= 0.6:
                            severity_counts["high"] += 1
                        elif score >= 0.4:
                            severity_counts["medium"] += 1
                        elif score > 0.0:
                            severity_counts["low"] += 1

        # Top probes by vulnerability count
        probe_vulnerabilities: Dict[str, int] = defaultdict(int)
        for attempt in self.attempts:
            probe_name = attempt.get("probe_classname", "unknown")
            detector_results = attempt.get("detector_results", {})
            has_vulnerability = False
            for scores in detector_results.values():
                if any(s is not None and s > 0.0 for s in scores):
                    has_vulnerability = True
                    break
            if has_vulnerability:
                probe_vulnerabilities[probe_name] += 1

        top_probes = sorted(
            probe_vulnerabilities.items(), key=lambda x: x[1], reverse=True
        )[:10]

        return {
            "total_attempts": total_attempts,
            "total_evaluations": total_evaluations,
            "attack_success_rate": round(asr, 2),
            "average_score": round(avg_score, 4),
            "vulnerable_attempts": vulnerable_attempts,
            "severity_distribution": severity_counts,
            "top_probes": [{"probe": k, "vulnerabilities": v} for k, v in top_probes],
        }

    def _calculate_by_category(self) -> Dict[str, Any]:
        """Calculate statistics by category."""
        # Group by probe category if available
        category_stats: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"attempts": 0, "vulnerabilities": 0}
        )

        for attempt in self.attempts:
            probe_name = attempt.get("probe_classname", "unknown")
            # Extract category from probe name (e.g., "dan.Ablation" -> "dan")
            category = probe_name.split(".")[0] if "." in probe_name else "other"

            category_stats[category]["attempts"] += 1

            detector_results = attempt.get("detector_results", {})
            for scores in detector_results.values():
                if any(s is not None and s > 0.0 for s in scores):
                    category_stats[category]["vulnerabilities"] += 1
                    break

        return dict(category_stats)

    def generate(self, output_path: Path) -> None:
        """Generate JSON summary report."""
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "report_metadata": {
                "total_records": len(self.records),
                "total_attempts": len(self.attempts),
                "total_evaluations": len(self.evaluations),
            },
            "config": self.config or {},
            "kpis": self._calculate_kpis(),
            "by_category": self._calculate_by_category(),
            "evaluations": [
                {
                    "probe": eval_record.get("probe", "unknown"),
                    "passed": eval_record.get("passed", 0),
                    "total": eval_record.get("total", 0),
                    "score": eval_record.get("score", 0.0)
                    if "score" in eval_record
                    else (
                        (eval_record.get("passed", 0) / eval_record.get("total", 1) * 100)
                        if eval_record.get("total", 0) > 0
                        else 0.0
                    ),
                }
                for eval_record in self.evaluations
            ],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

