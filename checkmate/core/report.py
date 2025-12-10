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
    
    # Determine risk level color
    risk_score = summary.get("risk_score", 0)
    if risk_score < 0.3:
        risk_color = "#22c55e"  # green
        risk_level = "LOW"
    elif risk_score < 0.7:
        risk_color = "#eab308"  # yellow
        risk_level = "MEDIUM"
    else:
        risk_color = "#ef4444"  # red
        risk_level = "HIGH"
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Checkmate Scan Report</title>
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
        .subtitle {{ color: #888; margin-bottom: 2rem; }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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
        .results-section {{ margin-top: 2rem; }}
        .result-item {{
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            border-left: 4px solid #7c3aed;
        }}
        .result-item.flagged {{ border-left-color: #ef4444; }}
        .prompt {{ font-family: monospace; background: rgba(0,0,0,0.3); padding: 0.5rem; border-radius: 4px; margin: 0.5rem 0; }}
        .response {{ color: #aaa; margin-top: 0.5rem; }}
        .detection-tags {{ display: flex; gap: 0.5rem; margin-top: 0.5rem; flex-wrap: wrap; }}
        .tag {{ 
            font-size: 0.75rem; 
            padding: 0.25rem 0.5rem; 
            border-radius: 4px; 
            background: rgba(124, 58, 237, 0.3);
        }}
        .tag.flagged {{ background: rgba(239, 68, 68, 0.3); }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ Checkmate Scan Report</h1>
        <p class="subtitle">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        
        <div class="summary-grid">
            <div class="card">
                <div class="card-label">Risk Level</div>
                <span class="risk-badge">{risk_level}</span>
            </div>
            <div class="card">
                <div class="card-label">Risk Score</div>
                <div class="card-value">{risk_score:.1%}</div>
            </div>
            <div class="card">
                <div class="card-label">Total Prompts</div>
                <div class="card-value">{summary.get('total_prompts', 0)}</div>
            </div>
            <div class="card">
                <div class="card-label">Flagged</div>
                <div class="card-value" style="color: #ef4444;">{summary.get('flagged_prompts', 0)}</div>
            </div>
        </div>
        
        <div class="results-section">
            <h2 style="margin-bottom: 1rem;">Detailed Results</h2>
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
            html += f'<span class="tag {tag_class}">{detection.get("detector")}: {detection.get("score", 0):.2f}</span>'
        
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
