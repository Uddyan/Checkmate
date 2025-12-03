"""Tests for ReportGenerator"""

import json
import tempfile
from pathlib import Path
import pytest

from checkmate.reporting import ReportGenerator


@pytest.fixture
def sample_report_jsonl(tmp_path):
    """Create a sample report.jsonl file for testing"""
    report_file = tmp_path / "report.jsonl"
    
    # Sample attempt record
    attempt = {
        "entry_type": "attempt",
        "uuid": "test-uuid-1",
        "probe_classname": "dan.Ablation_Dan_11_0",
        "prompt": {
            "turns": [
                {"role": "user", "content": {"text": "Test prompt"}}
            ]
        },
        "outputs": [
            {"text": "Test output", "lang": "en"}
        ],
        "detector_results": {
            "dan": [1.0, 0.0, 0.0]
        },
        "status": 1,
        "goal": "test goal"
    }
    
    # Sample eval record
    eval_record = {
        "entry_type": "eval",
        "probe": "dan.Ablation_Dan_11_0",
        "passed": 1,
        "total": 3,
        "score": 33.33
    }
    
    # Sample config record
    config_record = {
        "entry_type": "config",
        "target_name": "test-model",
        "target_type": "test"
    }
    
    with open(report_file, "w") as f:
        f.write(json.dumps(attempt) + "\n")
        f.write(json.dumps(eval_record) + "\n")
        f.write(json.dumps(config_record) + "\n")
    
    return report_file


def test_report_generator_load(sample_report_jsonl, tmp_path):
    """Test loading a report file"""
    output_dir = tmp_path / "reports"
    generator = ReportGenerator(sample_report_jsonl, output_dir)
    generator.load()
    
    assert len(generator.records) == 3
    assert len(generator.attempts) == 1
    assert len(generator.evaluations) == 1
    assert generator.config is not None


def test_report_generator_html(sample_report_jsonl, tmp_path):
    """Test HTML report generation"""
    output_dir = tmp_path / "reports"
    generator = ReportGenerator(sample_report_jsonl, output_dir)
    generator.load()
    
    html_path = generator.generate_html()
    assert html_path.exists()
    assert html_path.suffix == ".html"
    
    # Check HTML content
    content = html_path.read_text()
    assert "Checkmate Security Scan Report" in content
    assert "Attack Success Rate" in content


def test_report_generator_csv(sample_report_jsonl, tmp_path):
    """Test CSV report generation"""
    output_dir = tmp_path / "reports"
    generator = ReportGenerator(sample_report_jsonl, output_dir)
    generator.load()
    
    csv_path = generator.generate_csv()
    assert csv_path.exists()
    assert csv_path.suffix == ".csv"
    
    # Check CSV content
    content = csv_path.read_text()
    assert "attempt_id" in content
    assert "probe" in content
    assert "detector" in content


def test_report_generator_json_summary(sample_report_jsonl, tmp_path):
    """Test JSON summary generation"""
    output_dir = tmp_path / "reports"
    generator = ReportGenerator(sample_report_jsonl, output_dir)
    generator.load()
    
    json_path = generator.generate_json_summary()
    assert json_path.exists()
    assert json_path.name == "summary.json"
    
    # Check JSON content
    data = json.loads(json_path.read_text())
    assert "kpis" in data
    assert "attack_success_rate" in data["kpis"]
    assert "total_attempts" in data["kpis"]


def test_report_generator_all(sample_report_jsonl, tmp_path):
    """Test generating all report formats"""
    output_dir = tmp_path / "reports"
    generator = ReportGenerator(sample_report_jsonl, output_dir)
    generator.load()
    
    results = generator.generate_all()
    
    assert "html" in results
    assert "csv" in results
    assert "json" in results
    
    assert results["html"].exists()
    assert results["csv"].exists()
    assert results["json"].exists()

