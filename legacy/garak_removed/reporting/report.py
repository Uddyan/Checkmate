"""Main report generator that coordinates HTML, CSV, and JSON report generation"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from checkmate.reporting.html import HTMLReportGenerator
from checkmate.reporting.csv import CSVReportGenerator
from checkmate.reporting.json_summary import JSONSummaryGenerator


class ReportGenerator:
    """Main report generator that creates HTML, CSV, and JSON reports from JSONL scan results"""

    def __init__(self, report_jsonl_path: Path, output_dir: Path):
        """Initialize report generator.

        Args:
            report_jsonl_path: Path to the report.jsonl file from a scan
            output_dir: Directory where reports will be written
        """
        self.report_jsonl_path = Path(report_jsonl_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load report data
        self.records: List[Dict[str, Any]] = []
        self.attempts: List[Dict[str, Any]] = []
        self.evaluations: List[Dict[str, Any]] = []
        self.config: Optional[Dict[str, Any]] = None

    def load(self) -> "ReportGenerator":
        """Load report.jsonl file and parse records."""
        if not self.report_jsonl_path.exists():
            raise FileNotFoundError(f"Report file not found: {self.report_jsonl_path}")

        with open(self.report_jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    self.records.append(record)

                    entry_type = record.get("entry_type")
                    if entry_type == "attempt":
                        self.attempts.append(record)
                    elif entry_type == "eval":
                        self.evaluations.append(record)
                    elif entry_type == "config":
                        self.config = record
                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping invalid JSON line: {e}")

        return self

    def generate_all(self) -> Dict[str, Path]:
        """Generate all report formats (HTML, CSV, JSON summary).

        Returns:
            Dictionary mapping report type to output path
        """
        results = {}

        # Generate HTML report
        html_gen = HTMLReportGenerator(self.records, self.attempts, self.evaluations, self.config)
        html_path = self.output_dir / "report.html"
        html_gen.generate(html_path)
        results["html"] = html_path

        # Generate CSV report
        csv_gen = CSVReportGenerator(self.attempts, self.evaluations)
        csv_path = self.output_dir / "findings.csv"
        csv_gen.generate(csv_path)
        results["csv"] = csv_path

        # Generate JSON summary
        json_gen = JSONSummaryGenerator(self.records, self.attempts, self.evaluations, self.config)
        json_path = self.output_dir / "summary.json"
        json_gen.generate(json_path)
        results["json"] = json_path

        return results

    def generate_html(self) -> Path:
        """Generate HTML report only."""
        html_gen = HTMLReportGenerator(self.records, self.attempts, self.evaluations, self.config)
        html_path = self.output_dir / "report.html"
        html_gen.generate(html_path)
        return html_path

    def generate_csv(self) -> Path:
        """Generate CSV report only."""
        csv_gen = CSVReportGenerator(self.attempts, self.evaluations)
        csv_path = self.output_dir / "findings.csv"
        csv_gen.generate(csv_path)
        return csv_path

    def generate_json_summary(self) -> Path:
        """Generate JSON summary only."""
        json_gen = JSONSummaryGenerator(self.records, self.attempts, self.evaluations, self.config)
        json_path = self.output_dir / "summary.json"
        json_gen.generate(json_path)
        return json_path

