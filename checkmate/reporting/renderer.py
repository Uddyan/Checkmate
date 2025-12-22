# SPDX-License-Identifier: Apache-2.0
"""HTML report renderer for Checkmate.

Generates a clean, professional HTML report with:
1. Summary header - target, profile, risk score
2. Findings by detector - grouped by detector and severity
3. Metadata - run info and links
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


def render_html_report(summary_path: Path, findings_path: Path, output_path: Path) -> None:
    """Render HTML report from summary and findings JSON files.
    
    Args:
        summary_path: Path to summary.json
        findings_path: Path to findings.json
        output_path: Path to write HTML report
    """
    # Load data
    with open(summary_path) as f:
        summary = json.load(f)
    
    with open(findings_path) as f:
        findings_data = json.load(f)
    
    findings = findings_data.get('findings', [])
    
    # Generate HTML
    html = _generate_html(summary, findings)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


def _get_risk_level(score: float) -> tuple:
    """Get risk level label and color from score."""
    if score >= 90:
        return "EXCELLENT", "#22c55e"  # green
    elif score >= 80:
        return "GOOD", "#84cc16"  # lime
    elif score >= 70:
        return "FAIR", "#eab308"  # yellow
    elif score >= 50:
        return "MODERATE", "#f97316"  # orange
    else:
        return "HIGH RISK", "#ef4444"  # red


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    if not text:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _truncate(text: str, max_length: int = 200) -> str:
    """Truncate text with ellipsis."""
    if not text:
        return ""
    text = str(text)
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def _severity_color(severity: str) -> str:
    """Get color for severity level."""
    colors = {
        'critical': '#dc2626',
        'high': '#ea580c',
        'medium': '#ca8a04',
        'low': '#65a30d'
    }
    return colors.get(severity.lower(), '#6b7280')


def _generate_html(summary: Dict[str, Any], findings: List[Dict]) -> str:
    """Generate the complete HTML report."""
    risk_score = summary.get('risk_score', 0)
    risk_level, risk_color = _get_risk_level(risk_score)
    
    # Severity breakdown
    severity = summary.get('severity_breakdown', {})
    critical = severity.get('critical', 0)
    high = severity.get('high', 0)
    medium = severity.get('medium', 0)
    low = severity.get('low', 0)
    
    # Detector breakdown
    detector_breakdown = summary.get('detector_breakdown', {})
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Checkmate Security Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #e2e8f0;
            min-height: 100vh;
            line-height: 1.6;
        }}
        .container {{ max-width: 1000px; margin: 0 auto; padding: 2rem; }}
        
        /* Header */
        .header {{ 
            text-align: center; 
            margin-bottom: 2rem; 
            padding: 2rem;
            background: rgba(255,255,255,0.03);
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .logo {{ font-size: 2.5rem; margin-bottom: 0.5rem; }}
        h1 {{ 
            font-size: 1.75rem; 
            font-weight: 600;
            background: linear-gradient(90deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.25rem;
        }}
        .subtitle {{ color: #94a3b8; font-size: 0.875rem; }}
        
        /* Risk Score Card */
        .risk-card {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 2rem;
            margin: 2rem 0;
            padding: 2rem;
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .risk-score {{
            text-align: center;
        }}
        .risk-number {{
            font-size: 4rem;
            font-weight: 700;
            color: {risk_color};
            line-height: 1;
        }}
        .risk-label {{
            font-size: 0.875rem;
            color: #94a3b8;
            margin-top: 0.25rem;
        }}
        .risk-badge {{
            display: inline-block;
            padding: 0.5rem 1.5rem;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 0.875rem;
            background: {risk_color};
            color: white;
        }}
        
        /* Summary Cards */
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin: 2rem 0;
        }}
        .summary-card {{
            background: rgba(255,255,255,0.03);
            border-radius: 12px;
            padding: 1.25rem;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.08);
        }}
        .summary-value {{ font-size: 1.75rem; font-weight: 700; }}
        .summary-label {{ font-size: 0.75rem; color: #94a3b8; margin-top: 0.25rem; text-transform: uppercase; letter-spacing: 0.05em; }}
        .critical {{ color: #dc2626; }}
        .high {{ color: #ea580c; }}
        .medium {{ color: #ca8a04; }}
        .low {{ color: #65a30d; }}
        
        /* Sections */
        .section {{
            background: rgba(255,255,255,0.03);
            border-radius: 16px;
            padding: 1.5rem;
            margin: 1.5rem 0;
            border: 1px solid rgba(255,255,255,0.08);
        }}
        .section-title {{
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        /* Detector Breakdown */
        .detector-list {{
            display: grid;
            gap: 0.75rem;
        }}
        .detector-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 1rem;
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
        }}
        .detector-name {{ font-weight: 500; }}
        .detector-count {{
            background: rgba(239, 68, 68, 0.2);
            color: #fca5a5;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 600;
        }}
        
        /* Findings */
        .finding {{
            background: rgba(255,255,255,0.02);
            border-radius: 12px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            border-left: 4px solid;
        }}
        .finding-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.75rem;
        }}
        .finding-title {{ font-weight: 600; font-size: 1rem; }}
        .finding-severity {{
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            text-transform: uppercase;
        }}
        .finding-meta {{
            display: flex;
            gap: 1rem;
            font-size: 0.875rem;
            color: #94a3b8;
            margin-bottom: 0.75rem;
        }}
        .finding-example {{
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
            padding: 1rem;
            font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
            font-size: 0.8rem;
            overflow-x: auto;
        }}
        .finding-example-label {{
            font-size: 0.75rem;
            color: #64748b;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }}
        .prompt {{ color: #fbbf24; margin-bottom: 0.5rem; }}
        .response {{ color: #a5b4fc; }}
        
        /* Metadata */
        .metadata {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
            font-size: 0.875rem;
        }}
        .metadata-item {{
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        .metadata-label {{ color: #94a3b8; }}
        .metadata-value {{ font-weight: 500; }}
        
        /* Footer */
        .footer {{
            text-align: center;
            padding: 2rem;
            color: #64748b;
            font-size: 0.875rem;
        }}
        
        @media (max-width: 768px) {{
            .summary-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .risk-card {{ flex-direction: column; gap: 1rem; }}
            .metadata {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="logo">🛡️</div>
            <h1>Checkmate Security Report</h1>
            <p class="subtitle">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        
        <!-- Risk Score -->
        <div class="risk-card">
            <div class="risk-score">
                <div class="risk-number">{risk_score:.0f}</div>
                <div class="risk-label">Risk Score (0-100)</div>
            </div>
            <div>
                <span class="risk-badge">{risk_level}</span>
            </div>
        </div>
        
        <!-- Detection Summary -->
        <div class="summary-grid">
            <div class="summary-card">
                <div class="summary-value critical">{critical}</div>
                <div class="summary-label">Critical</div>
            </div>
            <div class="summary-card">
                <div class="summary-value high">{high}</div>
                <div class="summary-label">High</div>
            </div>
            <div class="summary-card">
                <div class="summary-value medium">{medium}</div>
                <div class="summary-label">Medium</div>
            </div>
            <div class="summary-card">
                <div class="summary-value low">{low}</div>
                <div class="summary-label">Low</div>
            </div>
        </div>
'''
    
    # Detector Breakdown Section
    if detector_breakdown:
        html += '''
        <div class="section">
            <h2 class="section-title">🔍 Detections by Detector</h2>
            <div class="detector-list">
'''
        for detector, count in sorted(detector_breakdown.items(), key=lambda x: -x[1]):
            detector_display = detector.replace('detectors.', '').replace('.', ' › ')
            html += f'''
                <div class="detector-item">
                    <span class="detector-name">{_escape_html(detector_display)}</span>
                    <span class="detector-count">{count} detection{"s" if count != 1 else ""}</span>
                </div>
'''
        html += '''
            </div>
        </div>
'''
    
    # Findings Section
    if findings:
        html += '''
        <div class="section">
            <h2 class="section-title">⚠️ Security Findings</h2>
'''
        # Show top 10 findings
        for finding in findings[:10]:
            severity = finding.get('severity', 'medium')
            color = _severity_color(severity)
            probe = finding.get('probe', 'Unknown').replace('probes.', '')
            owasp = finding.get('owasp_category', 'Unknown')
            count = finding.get('count', 0)
            example = finding.get('example', {})
            
            html += f'''
            <div class="finding" style="border-left-color: {color};">
                <div class="finding-header">
                    <span class="finding-title">{_escape_html(probe)}</span>
                    <span class="finding-severity" style="background: {color}20; color: {color};">{severity}</span>
                </div>
                <div class="finding-meta">
                    <span>📋 {_escape_html(owasp)}</span>
                    <span>🔢 {count} occurrence{"s" if count != 1 else ""}</span>
                </div>
'''
            if example and (example.get('prompt') or example.get('response')):
                html += '''
                <div class="finding-example">
                    <div class="finding-example-label">Example Exchange</div>
'''
                if example.get('prompt'):
                    html += f'                    <div class="prompt"><strong>Prompt:</strong> {_escape_html(_truncate(example["prompt"], 150))}</div>\n'
                if example.get('response'):
                    html += f'                    <div class="response"><strong>Response:</strong> {_escape_html(_truncate(example["response"], 200))}</div>\n'
                html += '''
                </div>
'''
            html += '''
            </div>
'''
        
        if len(findings) > 10:
            html += f'''
            <p style="text-align: center; color: #94a3b8; padding: 1rem;">
                ... and {len(findings) - 10} more findings. See findings.json for complete list.
            </p>
'''
        html += '''
        </div>
'''
    else:
        html += '''
        <div class="section">
            <h2 class="section-title">✅ No Security Findings</h2>
            <p style="color: #22c55e; text-align: center; padding: 2rem;">
                No vulnerabilities detected during this scan.
            </p>
        </div>
'''
    
    # Metadata Section
    html += f'''
        <div class="section">
            <h2 class="section-title">📊 Scan Metadata</h2>
            <div class="metadata">
                <div class="metadata-item">
                    <span class="metadata-label">Run ID</span>
                    <span class="metadata-value">{_escape_html(summary.get('run_id', 'N/A'))}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">Total Attempts</span>
                    <span class="metadata-value">{summary.get('total_attempts', 0)}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">Total Detections</span>
                    <span class="metadata-value">{summary.get('total_detections', 0)}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">Total Evaluations</span>
                    <span class="metadata-value">{summary.get('total_evaluations', 0)}</span>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by Checkmate LLM Security Scanner</p>
            <p>See summary.json and findings.json for detailed data</p>
        </div>
    </div>
</body>
</html>
'''
    
    return html
