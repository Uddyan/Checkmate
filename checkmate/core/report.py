# SPDX-License-Identifier: Apache-2.0
"""Report generation for Checkmate - JSON and HTML outputs."""

import json
from typing import Dict, Any
from datetime import datetime


def generate_json(results: Dict[str, Any], path: str = "results.json") -> None:
    """Generate JSON report from scan results.
    
    Args:
        results: Scan results dictionary
        path: Output file path
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)


def generate_html(results: Dict[str, Any], path: str = "results.html") -> None:
    """Generate HTML report from scan results.
    
    Args:
        results: Scan results dictionary
        path: Output file path
    """
    summary = results.get("summary", {})
    scan_results = results.get("results", [])
    
    # Metadata
    run_id = results.get("run_id", "N/A")
    profile = results.get("profile", "default")
    timestamp = results.get("timestamp", datetime.now().isoformat())
    target = results.get("target", {})
    model = target.get("model", "N/A")
    endpoint = target.get("endpoint", "N/A")
    duration = results.get("duration_seconds", 0)
    
    # Severity breakdown
    severity = summary.get("severity_breakdown", {})
    owasp = summary.get("owasp_breakdown", {})
    
    # Determine risk level color (score is 0-1 where higher = more issues)
    risk_score = summary.get("risk_score", 0)
    # Convert to 0-100 scale (100 = safe, 0 = unsafe)
    risk_score_100 = int((1 - risk_score) * 100)
    
    if risk_score_100 >= 80:
        risk_color = "#22c55e"  # green
        risk_level = "LOW"
    elif risk_score_100 >= 50:
        risk_color = "#eab308"  # yellow
        risk_level = "MODERATE"
    else:
        risk_color = "#ef4444"  # red
        risk_level = "HIGH"
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Checkmate Scan Report - {run_id}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 2rem;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ 
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(90deg, #00d4ff, #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .meta-bar {{
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1.5rem;
            display: flex;
            flex-wrap: wrap;
            gap: 2rem;
            font-size: 0.9rem;
        }}
        .meta-item {{ display: flex; flex-direction: column; }}
        .meta-label {{ color: #888; font-size: 0.75rem; text-transform: uppercase; }}
        .meta-value {{ color: #fff; font-weight: 500; }}
        .subtitle {{ color: #888; margin-bottom: 2rem; }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .card {{
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 1.5rem;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .card-label {{ font-size: 0.875rem; color: #888; margin-bottom: 0.5rem; }}
        .card-value {{ font-size: 2rem; font-weight: bold; }}
        .risk-badge {{
            display: inline-block;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: bold;
            background: {risk_color};
            color: white;
        }}
        .section {{ margin-top: 2rem; }}
        .section-title {{ font-size: 1.25rem; margin-bottom: 1rem; color: #fff; }}
        .breakdown-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 0.75rem;
        }}
        .breakdown-item {{
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        }}
        .breakdown-count {{ font-size: 1.5rem; font-weight: bold; }}
        .breakdown-label {{ font-size: 0.75rem; color: #888; margin-top: 0.25rem; }}
        .severity-critical {{ color: #ef4444; }}
        .severity-high {{ color: #f97316; }}
        .severity-medium {{ color: #eab308; }}
        .severity-low {{ color: #22c55e; }}
        .legend {{
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
            padding: 1rem;
            margin-top: 1rem;
            font-size: 0.85rem;
        }}
        .legend-title {{ font-weight: 600; margin-bottom: 0.5rem; }}
        .legend-item {{ display: flex; align-items: center; gap: 0.5rem; margin: 0.25rem 0; }}
        .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; }}
        .results-section {{ margin-top: 2rem; }}
        .result-item {{
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            border-left: 4px solid #7c3aed;
        }}
        .result-item.flagged {{ border-left-color: #ef4444; }}
        .prompt {{ font-family: monospace; background: rgba(0,0,0,0.3); padding: 0.5rem; border-radius: 4px; margin: 0.5rem 0; font-size: 0.85rem; }}
        .response {{ color: #aaa; margin-top: 0.5rem; font-size: 0.9rem; }}
        .detection-tags {{ display: flex; gap: 0.5rem; margin-top: 0.5rem; flex-wrap: wrap; }}
        .tag {{ 
            font-size: 0.75rem; 
            padding: 0.25rem 0.5rem; 
            border-radius: 4px; 
            background: rgba(124, 58, 237, 0.3);
        }}
        .tag.flagged {{ background: rgba(239, 68, 68, 0.3); }}
        .owasp-section {{ margin-top: 2rem; }}
        .owasp-item {{
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
            padding: 0.75rem 1rem;
            margin-bottom: 0.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .owasp-name {{ font-weight: 500; }}
        .owasp-count {{ 
            background: rgba(124, 58, 237, 0.3);
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ Checkmate Scan Report</h1>
        
        <div class="meta-bar">
            <div class="meta-item">
                <span class="meta-label">Run ID</span>
                <span class="meta-value">{run_id}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Profile</span>
                <span class="meta-value">{profile}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Model</span>
                <span class="meta-value">{model or 'N/A'}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Timestamp</span>
                <span class="meta-value">{timestamp}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Duration</span>
                <span class="meta-value">{duration:.2f}s</span>
            </div>
        </div>
        
        <div class="summary-grid">
            <div class="card">
                <div class="card-label">Risk Level</div>
                <span class="risk-badge">{risk_level}</span>
            </div>
            <div class="card">
                <div class="card-label">Risk Score</div>
                <div class="card-value">{risk_score_100}/100</div>
            </div>
            <div class="card">
                <div class="card-label">Total Prompts</div>
                <div class="card-value">{summary.get('total_prompts', 0)}</div>
            </div>
            <div class="card">
                <div class="card-label">Flagged</div>
                <div class="card-value" style="color: #ef4444;">{summary.get('flagged_prompts', 0)}</div>
            </div>
            <div class="card">
                <div class="card-label">Total Detections</div>
                <div class="card-value">{summary.get('total_detections', 0)}</div>
            </div>
        </div>
        
        <div class="section">
            <h3 class="section-title">Severity Breakdown</h3>
            <div class="breakdown-grid">
                <div class="breakdown-item">
                    <div class="breakdown-count severity-critical">{severity.get('critical', 0)}</div>
                    <div class="breakdown-label">Critical</div>
                </div>
                <div class="breakdown-item">
                    <div class="breakdown-count severity-high">{severity.get('high', 0)}</div>
                    <div class="breakdown-label">High</div>
                </div>
                <div class="breakdown-item">
                    <div class="breakdown-count severity-medium">{severity.get('medium', 0)}</div>
                    <div class="breakdown-label">Medium</div>
                </div>
                <div class="breakdown-item">
                    <div class="breakdown-count severity-low">{severity.get('low', 0)}</div>
                    <div class="breakdown-label">Low</div>
                </div>
            </div>
        </div>
"""
    
    # OWASP Breakdown section
    if owasp:
        html += """
        <div class="owasp-section">
            <h3 class="section-title">OWASP LLM Top 10 Breakdown</h3>
"""
        for cat, count in sorted(owasp.items()):
            html += f"""
            <div class="owasp-item">
                <span class="owasp-name">{_escape_html(cat)}</span>
                <span class="owasp-count">{count} findings</span>
            </div>
"""
        html += """
        </div>
"""
    
    # Risk score explanation and legend
    html += f"""
        <div class="legend">
            <div class="legend-title">📊 Risk Score Explanation</div>
            <p style="margin-bottom: 0.75rem; color: #aaa;">
                Score is based on the number and severity of findings across OWASP categories. 
                A higher score indicates better security posture.
            </p>
            <div class="legend-item">
                <span class="legend-dot" style="background: #22c55e;"></span>
                <span><strong>80-100:</strong> Low Risk - Strong security posture</span>
            </div>
            <div class="legend-item">
                <span class="legend-dot" style="background: #eab308;"></span>
                <span><strong>50-79:</strong> Moderate Risk - Some vulnerabilities detected</span>
            </div>
            <div class="legend-item">
                <span class="legend-dot" style="background: #ef4444;"></span>
                <span><strong>0-49:</strong> High Risk - Significant security concerns</span>
            </div>
        </div>
        
        <div class="results-section">
            <h2 class="section-title">Detailed Results</h2>
"""
    
    for i, result in enumerate(scan_results[:50], 1):  # Limit to 50 results
        flagged = any(d.get("flagged", False) for d in result.get("detections", []))
        flagged_class = "flagged" if flagged else ""
        
        html += f"""
            <div class="result-item {flagged_class}">
                <strong>#{i} - {result.get('probe', 'unknown')}</strong>
                <div class="prompt">{_escape_html(result.get('prompt', '')[:200])}</div>
                <div class="response"><strong>Response:</strong> {_escape_html(str(result.get('response', ''))[:300])}</div>
                <div class="detection-tags">
"""
        for detection in result.get("detections", []):
            tag_class = "flagged" if detection.get("flagged") else ""
            owasp_cat = detection.get("owasp_category", "")
            owasp_short = owasp_cat.split(":")[0] if owasp_cat else ""
            html += f'<span class="tag {tag_class}">{detection.get("detector")}: {detection.get("score", 0):.2f} {owasp_short}</span>'
        
        html += """
                </div>
            </div>
"""
    
    html += """
        </div>
    </div>
</body>
</html>
"""
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
