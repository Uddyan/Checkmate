"""PostgreSQL client for Checkmate runs and findings storage.

This module provides optional database persistence. If the database is unavailable
or disabled, the scanner continues to function normally using file-based reports.
"""

import psycopg2
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def get_connection(db_url: str):
    """
    Get PostgreSQL database connection.
    
    Args:
        db_url: PostgreSQL connection string (e.g., "postgresql://user:pass@host:5432/dbname")
        
    Returns:
        psycopg2 connection object
        
    Raises:
        psycopg2.Error: If connection fails
    """
    return psycopg2.connect(db_url)


def init_schema_if_needed(conn) -> None:
    """
    Create database tables if they don't exist (idempotent).
    
    Tables created:
    - runs: Stores campaign run summaries
    - findings: Stores vulnerability findings per run
    
    Args:
        conn: psycopg2 connection object
    """
    with conn.cursor() as cur:
        # Create runs table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                target_name TEXT,
                model_name TEXT,
                preset TEXT,
                risk_score REAL,
                duration_seconds REAL,
                total_probes INT,
                total_interactions INT,
                total_detections INT
            )
        """)
        
        # Create findings table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                id SERIAL PRIMARY KEY,
                run_id TEXT REFERENCES runs(id) ON DELETE CASCADE,
                probe_name TEXT,
                detector_name TEXT,
                owasp_category TEXT,
                severity TEXT,
                count INT,
                attack_id TEXT
            )
        """)
        
        # Create indexes for faster queries
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_findings_run_id 
            ON findings(run_id)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_findings_owasp 
            ON findings(owasp_category)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_findings_severity 
            ON findings(severity)
        """)
        
        conn.commit()
        logger.info("Database schema initialized successfully")


def insert_run(conn, run_summary: Dict) -> None:
    """
    Insert run summary into the runs table.
    
    Args:
        conn: psycopg2 connection object
        run_summary: Dictionary with run summary data from summary.json
    """
    with conn.cursor() as cur:
        # Calculate duration
        start_time = datetime.fromisoformat(run_summary.get('start_time', ''))
        end_time = datetime.fromisoformat(run_summary.get('end_time', ''))
        duration_seconds = (end_time - start_time).total_seconds()
        
        cur.execute("""
            INSERT INTO runs (
                id, target_name, model_name, preset, risk_score, 
                duration_seconds, total_probes, total_interactions, total_detections
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                risk_score = EXCLUDED.risk_score,
                total_detections = EXCLUDED.total_detections
        """, (
            run_summary['run_id'],
            run_summary.get('target_name', 'unknown'),
            run_summary.get('model_name', 'unknown'),
            run_summary.get('preset', 'unknown'),
            run_summary.get('risk_score', 0.0),
            duration_seconds,
            run_summary.get('total_probes', 0),
            run_summary.get('total_attempts', 0),
            run_summary.get('total_detections', 0)
        ))
        
        conn.commit()
        logger.info(f"Run {run_summary['run_id']} inserted into database")


def insert_findings(conn, run_id: str, findings_data: Dict) -> None:
    """
    Insert findings into the findings table.
    
    Args:
        conn: psycopg2 connection object
        run_id: Run ID to associate findings with
        findings_data: Dictionary with findings data from findings.json
    """
    findings_list = findings_data.get('findings', [])
    
    if not findings_list:
        logger.warning(f"No findings to insert for run {run_id}")
        return
    
    with conn.cursor() as cur:
        for finding in findings_list:
            # Extract detector name from probe name (if format is probe.detector)
            probe_name = finding.get('probe', '')
            detector_name = finding.get('detector', '')
            
            cur.execute("""
                INSERT INTO findings (
                    run_id, probe_name, detector_name, owasp_category, 
                    severity, count, attack_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                run_id,
                probe_name,
                detector_name,
                finding.get('owasp_category', 'Unknown'),
                finding.get('severity', 'medium'),
                finding.get('count', 0),
                finding.get('attack_id')  # May be None
            ))
        
        conn.commit()
        logger.info(f"Inserted {len(findings_list)} findings for run {run_id}")


def query_runs(conn, limit: int = 10) -> List[Dict]:
    """
    Query recent runs from the database.
    
    Args:
        conn: psycopg2 connection object
        limit: Maximum number of runs to return
        
    Returns:
        List of run dictionaries
    """
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, created_at, target_name, model_name, preset,
                   risk_score, duration_seconds, total_detections
            FROM runs
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))
        
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]


def query_findings_by_run(conn, run_id: str) -> List[Dict]:
    """
    Query findings for a specific run.
    
    Args:
        conn: psycopg2 connection object
        run_id: Run ID to query findings for
        
    Returns:
        List of finding dictionaries
    """
    with conn.cursor() as cur:
        cur.execute("""
            SELECT probe_name, detector_name, owasp_category, severity, count
            FROM findings
            WHERE run_id = %s
            ORDER BY severity DESC, count DESC
        """, (run_id,))
        
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]
