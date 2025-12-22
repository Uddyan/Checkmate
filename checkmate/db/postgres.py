# SPDX-License-Identifier: Apache-2.0
"""PostgreSQL database client for Checkmate.

This module provides persistent storage of scan results in PostgreSQL.
Install with: pip install checkmate[postgres]
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from checkmate.db.client import DatabaseClient

logger = logging.getLogger(__name__)


class PostgresClient(DatabaseClient):
    """PostgreSQL implementation of the database client.
    
    Stores scan runs and findings in PostgreSQL for history tracking
    and trend analysis.
    """
    
    def __init__(self, connection_url: str):
        """Initialize PostgreSQL client.
        
        Args:
            connection_url: PostgreSQL connection URL
                e.g., postgresql://user:pass@host:5432/checkmate
        """
        self.connection_url = connection_url
        self.conn = None
        self._tables_created = False
    
    def connect(self) -> None:
        """Establish connection to PostgreSQL."""
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            self.conn = psycopg2.connect(self.connection_url)
            self.conn.autocommit = False
            
            # Create tables if they don't exist
            if not self._tables_created:
                self._create_tables()
                self._tables_created = True
            
            logger.debug("Connected to PostgreSQL database")
            
        except ImportError:
            raise ImportError(
                "psycopg2 is required for PostgreSQL support. "
                "Install it with: pip install checkmate[postgres]"
            )
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def disconnect(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.debug("Disconnected from PostgreSQL database")
    
    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        if not self.conn:
            self.connect()
        
        with self.conn.cursor() as cur:
            # Runs table - stores scan metadata
            cur.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id SERIAL PRIMARY KEY,
                    run_id VARCHAR(32) UNIQUE NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    target VARCHAR(255),
                    model VARCHAR(255),
                    profile VARCHAR(64),
                    risk_score FLOAT,
                    total_prompts INTEGER,
                    flagged_prompts INTEGER,
                    total_detections INTEGER,
                    duration_seconds FLOAT,
                    metadata JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_runs_run_id ON runs(run_id);
                CREATE INDEX IF NOT EXISTS idx_runs_timestamp ON runs(timestamp);
                CREATE INDEX IF NOT EXISTS idx_runs_profile ON runs(profile);
            """)
            
            # Findings table - stores individual detections
            cur.execute("""
                CREATE TABLE IF NOT EXISTS findings (
                    id SERIAL PRIMARY KEY,
                    run_id VARCHAR(32) NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
                    probe VARCHAR(64),
                    detector VARCHAR(64),
                    severity VARCHAR(16),
                    owasp VARCHAR(64),
                    score FLOAT,
                    message TEXT,
                    prompt_snippet TEXT,
                    response_snippet TEXT,
                    tags JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_findings_run_id ON findings(run_id);
                CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings(severity);
                CREATE INDEX IF NOT EXISTS idx_findings_owasp ON findings(owasp);
            """)
            
            self.conn.commit()
            logger.debug("Database tables created/verified")
    
    def save_scan(self, scan_data: Dict[str, Any]) -> str:
        """Save scan results to database.
        
        Args:
            scan_data: Scan results dictionary from CheckmateEngine
            
        Returns:
            The run_id of the saved scan
        """
        if not self.conn:
            self.connect()
        
        try:
            run_id = scan_data.get("run_id", "unknown")
            summary = scan_data.get("summary", {})
            target = scan_data.get("target", {})
            
            with self.conn.cursor() as cur:
                # Insert run record
                cur.execute("""
                    INSERT INTO runs (
                        run_id, timestamp, target, model, profile,
                        risk_score, total_prompts, flagged_prompts,
                        total_detections, duration_seconds, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (run_id) DO UPDATE SET
                        metadata = EXCLUDED.metadata,
                        risk_score = EXCLUDED.risk_score
                """, (
                    run_id,
                    scan_data.get("timestamp", datetime.now().isoformat()),
                    target.get("endpoint"),
                    target.get("model"),
                    scan_data.get("profile"),
                    summary.get("risk_score", 0),
                    summary.get("total_prompts", 0),
                    summary.get("flagged_prompts", 0),
                    summary.get("total_detections", 0),
                    scan_data.get("duration_seconds", 0),
                    json.dumps({
                        "severity_breakdown": summary.get("severity_breakdown", {}),
                        "owasp_breakdown": summary.get("owasp_breakdown", {}),
                        "probes_used": scan_data.get("probes_used", []),
                        "detectors_used": scan_data.get("detectors_used", []),
                    })
                ))
                
                # Insert findings from results
                for result in scan_data.get("results", []):
                    probe = result.get("probe", "unknown")
                    prompt = result.get("prompt", "")[:500]  # Truncate
                    response = str(result.get("response", ""))[:500]
                    
                    for detection in result.get("detections", []):
                        cur.execute("""
                            INSERT INTO findings (
                                run_id, probe, detector, severity, owasp,
                                score, message, prompt_snippet, response_snippet, tags
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            run_id,
                            probe,
                            detection.get("detector"),
                            detection.get("severity"),
                            detection.get("owasp_category"),
                            detection.get("score", 0),
                            detection.get("message"),
                            prompt,
                            response,
                            json.dumps(detection.get("tags", []))
                        ))
                
                self.conn.commit()
                logger.info(f"Saved scan {run_id} to database")
                return run_id
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to save scan to database: {e}")
            raise
    
    def get_scan(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve scan results by ID.
        
        Args:
            scan_id: Unique scan ID
            
        Returns:
            Scan data dictionary or None if not found
        """
        if not self.conn:
            self.connect()
        
        try:
            from psycopg2.extras import RealDictCursor
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get run metadata
                cur.execute("""
                    SELECT * FROM runs WHERE run_id = %s
                """, (scan_id,))
                
                run = cur.fetchone()
                if not run:
                    return None
                
                run = dict(run)
                
                # Get findings
                cur.execute("""
                    SELECT detector, severity, owasp, COUNT(*) as count
                    FROM findings
                    WHERE run_id = %s
                    GROUP BY detector, severity, owasp
                """, (scan_id,))
                
                findings = [dict(f) for f in cur.fetchall()]
                
                # Parse metadata
                metadata = run.get("metadata", {})
                if isinstance(metadata, str):
                    metadata = json.loads(metadata)
                
                return {
                    "run_id": run["run_id"],
                    "timestamp": run["timestamp"].isoformat() if run["timestamp"] else None,
                    "target": run["target"],
                    "model": run["model"],
                    "profile": run["profile"],
                    "risk_score": int((1 - (run["risk_score"] or 0)) * 100),
                    "total_prompts": run["total_prompts"],
                    "flagged_prompts": run["flagged_prompts"],
                    "total_detections": run["total_detections"],
                    "duration_seconds": run["duration_seconds"],
                    "severity_breakdown": metadata.get("severity_breakdown", {}),
                    "owasp_breakdown": metadata.get("owasp_breakdown", {}),
                    "findings": findings,
                }
                
        except Exception as e:
            logger.error(f"Failed to get scan from database: {e}")
            raise
    
    def list_scans(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List recent scans.
        
        Args:
            limit: Maximum number of scans to return
            
        Returns:
            List of scan metadata dictionaries
        """
        if not self.conn:
            self.connect()
        
        try:
            from psycopg2.extras import RealDictCursor
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT run_id, timestamp, target, model, profile, risk_score,
                           total_prompts, flagged_prompts, total_detections
                    FROM runs
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (limit,))
                
                runs = []
                for row in cur.fetchall():
                    row = dict(row)
                    runs.append({
                        "run_id": row["run_id"],
                        "timestamp": row["timestamp"].strftime("%Y-%m-%d %H:%M") if row["timestamp"] else "N/A",
                        "target": row["target"] or "N/A",
                        "profile": row["profile"] or "default",
                        "risk_score": f"{int((1 - (row['risk_score'] or 0)) * 100)}/100",
                    })
                
                return runs
                
        except Exception as e:
            logger.error(f"Failed to list scans from database: {e}")
            raise
