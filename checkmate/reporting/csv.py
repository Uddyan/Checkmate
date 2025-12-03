"""CSV report generator for findings"""

import csv
from pathlib import Path
from typing import Dict, List, Any


class CSVReportGenerator:
    """Generates a CSV report with all findings"""

    def __init__(
        self,
        attempts: List[Dict[str, Any]],
        evaluations: List[Dict[str, Any]],
    ):
        self.attempts = attempts
        self.evaluations = evaluations

    def generate(self, output_path: Path) -> None:
        """Generate CSV report with findings."""
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(
                [
                    "attempt_id",
                    "probe",
                    "detector",
                    "score",
                    "severity",
                    "prompt",
                    "output",
                    "status",
                ]
            )

            # Write findings
            for attempt in self.attempts:
                attempt_id = attempt.get("uuid", "unknown")
                probe_name = attempt.get("probe_classname", "unknown")
                prompt_text = ""
                if "prompt" in attempt:
                    prompt_obj = attempt["prompt"]
                    if isinstance(prompt_obj, dict):
                        # Extract text from prompt structure
                        turns = prompt_obj.get("turns", [])
                        if turns:
                            prompt_text = turns[0].get("content", {}).get("text", "")
                    else:
                        prompt_text = str(prompt_obj)

                outputs = attempt.get("outputs", [])
                output_text = ""
                if outputs:
                    output_text = outputs[0].get("text", "") if isinstance(outputs[0], dict) else str(outputs[0])

                detector_results = attempt.get("detector_results", {})
                status = attempt.get("status", 0)

                # Write one row per detector score
                for detector_name, scores in detector_results.items():
                    for idx, score in enumerate(scores):
                        if score is not None and score > 0.0:  # Only write vulnerabilities
                            severity = (
                                "critical"
                                if score >= 0.8
                                else "high"
                                if score >= 0.6
                                else "medium"
                                if score >= 0.4
                                else "low"
                            )

                            writer.writerow(
                                [
                                    attempt_id,
                                    probe_name,
                                    detector_name,
                                    f"{score:.4f}",
                                    severity,
                                    prompt_text[:200],  # Truncate long prompts
                                    output_text[:200] if idx == 0 else "",  # Only first output
                                    status,
                                ]
                            )

