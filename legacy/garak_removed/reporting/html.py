"""HTML report generator with embedded charts"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict


class HTMLReportGenerator:
    """Generates an HTML report with charts and visualizations"""

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

    def _calculate_statistics(self) -> Dict[str, Any]:
        """Calculate statistics for the report."""
        total_attempts = len(self.attempts)
        vulnerable_attempts = 0
        total_scores = 0.0
        score_count = 0

        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "none": 0}
        probe_vulnerabilities: Dict[str, int] = defaultdict(int)
        detector_vulnerabilities: Dict[str, int] = defaultdict(int)

        for attempt in self.attempts:
            detector_results = attempt.get("detector_results", {})
            has_vulnerability = False

            for detector_name, scores in detector_results.items():
                for score in scores:
                    if score is not None:
                        total_scores += score
                        score_count += 1

                        if score > 0.0:
                            has_vulnerability = True
                            detector_vulnerabilities[detector_name] += 1

                            if score >= 0.8:
                                severity_counts["critical"] += 1
                            elif score >= 0.6:
                                severity_counts["high"] += 1
                            elif score >= 0.4:
                                severity_counts["medium"] += 1
                            else:
                                severity_counts["low"] += 1

            if has_vulnerability:
                vulnerable_attempts += 1
                probe_name = attempt.get("probe_classname", "unknown")
                probe_vulnerabilities[probe_name] += 1
            else:
                severity_counts["none"] += 1

        asr = (vulnerable_attempts / total_attempts * 100) if total_attempts > 0 else 0.0
        avg_score = (total_scores / score_count) if score_count > 0 else 0.0

        top_probes = sorted(
            probe_vulnerabilities.items(), key=lambda x: x[1], reverse=True
        )[:10]

        top_detectors = sorted(
            detector_vulnerabilities.items(), key=lambda x: x[1], reverse=True
        )[:10]

        return {
            "total_attempts": total_attempts,
            "vulnerable_attempts": vulnerable_attempts,
            "attack_success_rate": round(asr, 2),
            "average_score": round(avg_score, 4),
            "severity_distribution": severity_counts,
            "top_probes": top_probes,
            "top_detectors": top_detectors,
        }

    def _generate_html(self, stats: Dict[str, Any]) -> str:
        """Generate HTML content with embedded charts."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        model_name = "Unknown"
        if self.config:
            model_name = self.config.get("target_name", "Unknown")

        # Prepare chart data
        severity_labels = list(stats["severity_distribution"].keys())
        severity_values = list(stats["severity_distribution"].values())
        severity_colors = {
            "critical": "#dc3545",
            "high": "#fd7e14",
            "medium": "#ffc107",
            "low": "#0dcaf0",
            "none": "#6c757d",
        }

        probe_labels = [p[0] for p in stats["top_probes"]]
        probe_values = [p[1] for p in stats["top_probes"]]

        detector_labels = [d[0] for d in stats["top_detectors"]]
        detector_values = [d[1] for d in stats["top_detectors"]]

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Checkmate Security Scan Report</title>
    <!-- Using inline SVG charts for offline compatibility -->
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        header {{
            border-bottom: 3px solid #007bff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        h1 {{
            color: #007bff;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .metadata {{
            color: #666;
            font-size: 0.9em;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .kpi-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .kpi-card h3 {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
        }}
        .kpi-card .value {{
            font-size: 2.5em;
            font-weight: bold;
        }}
        .kpi-card.warning {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        .kpi-card.success {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }}
        .chart-container {{
            margin: 30px 0;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 8px;
        }}
        .chart-container h2 {{
            margin-bottom: 20px;
            color: #333;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #007bff;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .severity-critical {{ color: #dc3545; font-weight: bold; }}
        .severity-high {{ color: #fd7e14; font-weight: bold; }}
        .severity-medium {{ color: #ffc107; }}
        .severity-low {{ color: #0dcaf0; }}
        .chart-bars {{
            margin: 20px 0;
        }}
        .bar-item {{
            margin: 15px 0;
        }}
        .bar-label {{
            font-size: 0.9em;
            margin-bottom: 5px;
            color: #555;
        }}
        .bar-wrapper {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .bar-fill {{
            height: 30px;
            border-radius: 4px;
            transition: width 0.3s ease;
            min-width: 2px;
        }}
        .bar-value {{
            font-weight: bold;
            color: #333;
            min-width: 40px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🛡️ Checkmate Security Scan Report</h1>
            <div class="metadata">
                <p><strong>Model:</strong> {model_name}</p>
                <p><strong>Generated:</strong> {timestamp}</p>
                <p><strong>Total Attempts:</strong> {stats['total_attempts']}</p>
            </div>
        </header>

        <section class="kpi-grid">
            <div class="kpi-card {'warning' if stats['attack_success_rate'] > 50 else 'success'}">
                <h3>Attack Success Rate</h3>
                <div class="value">{stats['attack_success_rate']}%</div>
            </div>
            <div class="kpi-card">
                <h3>Vulnerable Attempts</h3>
                <div class="value">{stats['vulnerable_attempts']}</div>
            </div>
            <div class="kpi-card">
                <h3>Average Score</h3>
                <div class="value">{stats['average_score']:.2f}</div>
            </div>
            <div class="kpi-card">
                <h3>Total Attempts</h3>
                <div class="value">{stats['total_attempts']}</div>
            </div>
        </section>

        <section class="chart-container">
            <h2>Severity Distribution</h2>
            <div class="chart-bars">
"""
        
        # Add severity bars using CSS
        max_severity = max(severity_values) if severity_values else 1
        for label, value in zip(severity_labels, severity_values):
            percentage = (value / max_severity * 100) if max_severity > 0 else 0
            color = severity_colors.get(label, "#6c757d")
            html += f"""
                <div class="bar-item">
                    <div class="bar-label">{label.title()}</div>
                    <div class="bar-wrapper">
                        <div class="bar-fill" style="width: {percentage}%; background: {color};" data-value="{value}"></div>
                        <span class="bar-value">{value}</span>
                    </div>
                </div>
"""
        
        html += """
            </div>
        </section>

        <section class="chart-container">
            <h2>Top Vulnerable Probes</h2>
            <div class="chart-bars">
"""
        
        # Add probe bars
        max_probe = max(probe_values) if probe_values else 1
        for label, value in zip(probe_labels, probe_values):
            percentage = (value / max_probe * 100) if max_probe > 0 else 0
            # Truncate long probe names
            display_label = label.split('.')[-1] if '.' in label else label
            if len(display_label) > 40:
                display_label = display_label[:37] + "..."
            html += f"""
                <div class="bar-item">
                    <div class="bar-label" title="{label}">{display_label}</div>
                    <div class="bar-wrapper">
                        <div class="bar-fill" style="width: {percentage}%;" data-value="{value}"></div>
                        <span class="bar-value">{value}</span>
                    </div>
                </div>
"""
        
        html += """
            </div>
        </section>

        <section class="chart-container">
            <h2>Top Detectors (Vulnerabilities Found)</h2>
            <div class="chart-bars">
"""
        
        # Add detector bars
        max_detector = max(detector_values) if detector_values else 1
        for label, value in zip(detector_labels, detector_values):
            percentage = (value / max_detector * 100) if max_detector > 0 else 0
            display_label = label.split('.')[-1] if '.' in label else label
            if len(display_label) > 40:
                display_label = display_label[:37] + "..."
            html += f"""
                <div class="bar-item">
                    <div class="bar-label" title="{label}">{display_label}</div>
                    <div class="bar-wrapper">
                        <div class="bar-fill" style="width: {percentage}%; background: rgba(220, 53, 69, 0.8);" data-value="{value}"></div>
                        <span class="bar-value">{value}</span>
                    </div>
                </div>
"""
        
        html += """
            </div>
        </section>

        <section>
            <h2>Evaluation Summary</h2>
            <table>
                <thead>
                    <tr>
                        <th>Probe</th>
                        <th>Passed</th>
                        <th>Total</th>
                        <th>Score %</th>
                    </tr>
                </thead>
                <tbody>
"""

        # Add evaluation rows
        for eval_record in self.evaluations[:20]:  # Limit to first 20
            probe = eval_record.get("probe", "unknown")
            passed = eval_record.get("passed", 0)
            total = eval_record.get("total", 0)
            score = (
                eval_record.get("score", 0.0)
                if "score" in eval_record
                else ((passed / total * 100) if total > 0 else 0.0)
            )

            html += f"""
                    <tr>
                        <td>{probe}</td>
                        <td>{passed}</td>
                        <td>{total}</td>
                        <td>{score:.2f}%</td>
                    </tr>
"""

        html += """
                </tbody>
            </table>
        </section>
    </div>
</body>
</html>
"""

        return html

    def generate(self, output_path: Path) -> None:
        """Generate HTML report file."""
        stats = self._calculate_statistics()
        html_content = self._generate_html(stats)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

