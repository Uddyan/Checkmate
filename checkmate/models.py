"""Core domain models for LLM red-teaming scanner.

This module consolidates all domain models using Pydantic for validation and serialization.
Aligned with OWASP LLM Top-10 categories and the red-teaming product one-pager.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class OWASPCategory(str, Enum):
    """OWASP LLM Top-10 vulnerability categories"""
    
    LLM01_PROMPT_INJECTION = "LLM01_prompt_injection"
    LLM02_INSECURE_OUTPUT = "LLM02_insecure_output"
    LLM03_TRAINING_DATA_POISONING = "LLM03_training_data_poisoning"
    LLM04_MODEL_DENIAL_OF_SERVICE = "LLM04_model_denial_of_service"
    LLM05_SUPPLY_CHAIN = "LLM05_supply_chain"
    LLM06_SENSITIVE_INFO_DISCLOSURE = "LLM06_sensitive_info_disclosure"
    LLM07_INSECURE_PLUGIN_DESIGN = "LLM07_insecure_plugin_design"
    LLM08_EXCESSIVE_AGENCY = "LLM08_excessive_agency"
    LLM09_OVERRELIANCE = "LLM09_overreliance"
    LLM10_MODEL_THEFT = "LLM10_model_theft"


class Severity(str, Enum):
    """Severity levels for vulnerabilities"""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Attack(BaseModel):
    """A single attack from an attack pack
    
    Attributes:
        id: Unique identifier for the attack (e.g., "jailbreak_basic_001")
        category: OWASP LLM category this attack targets
        severity: Expected severity if successful
        description: Human-readable description of the attack
        template: Prompt template (supports Jinja2 variables)
        metadata: Optional metadata (tags, references, etc.)
    """
    
    id: str
    category: OWASPCategory
    severity: Severity
    description: str
    template: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class DetectorResult(BaseModel):
    """Result from running a detector on an interaction
    
    Attributes:
        detector_name: Name of the detector that produced this result
        matched: Whether the detector found an issue
        confidence: Confidence score (0.0-1.0)
        evidence: Optional evidence string (matched pattern, excerpt, etc.)
        metadata: Additional metadata from the detector
    """
    
    detector_name: str
    matched: bool
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class InteractionRecord(BaseModel):
    """Record of a single attack-defense interaction
    
    Attributes:
        interaction_id: Unique ID for this interaction
        attack_id: ID of the attack that was executed
        prompt: Messages sent to the target (list of dicts with role/content)
        response: Response from the target
        latency_ms: Response latency in milliseconds
        detector_results: Results from all detectors run on this interaction
        timestamp: ISO 8601 timestamp of when interaction occurred
        status: HTTP status or success indicator
        error: Error message if interaction failed
    """
    
    interaction_id: str
    attack_id: str
    prompt: list[dict[str, str]]  # [{"role": "user", "content": "..."}]
    response: dict[str, Any]
    latency_ms: float
    detector_results: list[DetectorResult] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: str = "success"
    error: Optional[str] = None
    
    def has_findings(self) -> bool:
        """Check if any detector found an issue"""
        return any(dr.matched for dr in self.detector_results)
    
    def max_confidence(self) -> float:
        """Get maximum confidence across all detector results"""
        if not self.detector_results:
            return 0.0
        return max(dr.confidence for dr in self.detector_results)


class Finding(BaseModel):
    """Aggregated finding for a specific attack pattern
    
    Attributes:
        attack_id: ID of the attack that produced this finding
        category: OWASP category
        severity: Severity level
        description: Description of the vulnerability
        interaction_ids: List of interaction IDs where this attack succeeded
        count: Number of times this attack succeeded
        max_confidence: Highest confidence score across all instances
        example_evidence: Example evidence from one instance
    """
    
    attack_id: str
    category: OWASPCategory
    severity: Severity
    description: str
    interaction_ids: list[str]
    count: int
    max_confidence: float = Field(ge=0.0, le=1.0)
    example_evidence: Optional[str] = None
    
    class Config:
        use_enum_values = True


class RunSummary(BaseModel):
    """Summary of a complete red-teaming campaign run
    
    Attributes:
        run_id: Unique identifier for this run
        target_name: Name of the target system
        target_type: Type of target (http_app, openai, etc.)
        start_time: ISO 8601 start timestamp
        end_time: ISO 8601 end timestamp
        total_attacks: Total number of attacks attempted
        total_interactions: Total interactions (some attacks may have multiple)
        successful_attacks: Number of attacks that found vulnerabilities
        risk_score: Overall risk score (0-100)
        findings: List of aggregated findings
        findings_by_category: Count of findings per OWASP category
        findings_by_severity: Count of findings per severity level
        metadata: Additional run metadata (config, versions, etc.)
    """
    
    run_id: str
    target_name: str
    target_type: str
    start_time: str
    end_time: str
    total_attacks: int
    total_interactions: int
    successful_attacks: int
    risk_score: float = Field(ge=0.0, le=100.0)
    findings: list[Finding]
    findings_by_category: dict[str, int] = Field(default_factory=dict)
    findings_by_severity: dict[str, int] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    def compute_statistics(self) -> None:
        """Compute findings_by_category and findings_by_severity from findings list"""
        self.findings_by_category = {}
        self.findings_by_severity = {}
        
        for finding in self.findings:
            # Count by category
            cat = finding.category.value if isinstance(finding.category, Enum) else finding.category
            self.findings_by_category[cat] = self.findings_by_category.get(cat, 0) + finding.count
            
            # Count by severity
            sev = finding.severity.value if isinstance(finding.severity, Enum) else finding.severity
            self.findings_by_severity[sev] = self.findings_by_severity.get(sev, 0) + finding.count


# Configuration Models (for new YAML schema)

class AuthConfig(BaseModel):
    """Authentication configuration for target
    
    Attributes:
        type: Auth type (header, bearer, api_key)
        header_name: Header name for auth (default: Authorization)
        env_var: Environment variable containing the auth value
    """
    
    type: str = "header"
    header_name: str = "Authorization"
    env_var: str


class TargetConfig(BaseModel):
    """Configuration for the target LLM system
    
    Attributes:
        type: Target type (http_app, openai, anthropic, etc.)
        name: Human-readable name for the target
        base_url: Base URL for HTTP targets
        method: HTTP method (POST, GET, etc.)
        model: Model name for API-based targets
        auth: Authentication configuration
        timeout: Request timeout in seconds
    """
    
    type: str
    name: str
    base_url: Optional[str] = None
    method: str = "POST"
    model: Optional[str] = None
    auth: Optional[AuthConfig] = None
    timeout: int = 30


class ProfileConfig(BaseModel):
    """Test profile configuration
    
    Attributes:
        app_type: Application type (chatbot, rag_support_bot, agent_tools)
        attack_packs: List of paths to attack pack YAML files
    """
    
    app_type: str
    attack_packs: list[str]


class CampaignConfig(BaseModel):
    """Campaign execution configuration
    
    Attributes:
        max_requests: Maximum number of attack requests to send
        max_rps: Maximum requests per second (rate limiting)
        concurrent_requests: Number of concurrent async requests
        use_llm_attacker: Whether to use LLM-based attack generation (future)
        use_llm_judge: Whether to use LLM-as-judge for detection
        timeout: Request timeout in seconds
    """
    
    max_requests: int = 200
    max_rps: float = 2.0
    concurrent_requests: int = 5
    use_llm_attacker: bool = False
    use_llm_judge: bool = False
    timeout: int = 30


class OutputConfig(BaseModel):
    """Output configuration
    
    Attributes:
        run_id: Unique run identifier (auto-generated if not provided)
        results_dir: Directory for all output files
        html_report: Path to HTML report (derived from results_dir if not set)
        jsonl_file: Path to JSONL interactions file
        findings_json: Path to findings JSON file
    """
    
    run_id: str = Field(default_factory=lambda: f"run-{datetime.now():%Y-%m-%d-%H%M%S}")
    results_dir: str
    html_report: Optional[str] = None
    jsonl_file: Optional[str] = None
    findings_json: Optional[str] = None
    
    def resolve_paths(self) -> None:
        """Resolve derived paths based on results_dir"""
        if not self.html_report:
            self.html_report = f"{self.results_dir}/report.html"
        if not self.jsonl_file:
            self.jsonl_file = f"{self.results_dir}/interactions.jsonl"
        if not self.findings_json:
            self.findings_json = f"{self.results_dir}/findings.json"


class ScannerConfig(BaseModel):
    """Root configuration for scanner (matches YAML schema from one-pager)
    
    This is the main configuration model that gets loaded from YAML files.
    
    Example YAML:
        target:
          type: "http_app"
          name: "my-chatbot"
          base_url: "https://api.example.com/chat"
          auth:
            env_var: "API_KEY"
        profile:
          app_type: "chatbot"
          attack_packs:
            - "attack_packs/chatbot_basic.yaml"
        campaign:
          max_requests: 100
          max_rps: 5
        output:
          run_id: "test-001"
          results_dir: "runs/test-001"
    """
    
    target: TargetConfig
    profile: ProfileConfig
    campaign: CampaignConfig = Field(default_factory=CampaignConfig)
    output: OutputConfig
    
    def model_post_init(self, __context: Any) -> None:
        """Post-initialization hook to resolve paths"""
        self.output.resolve_paths()


# Risk scoring utilities

SEVERITY_WEIGHTS = {
    Severity.CRITICAL: 25,
    Severity.HIGH: 10,
    Severity.MEDIUM: 3,
    Severity.LOW: 1,
}


def calculate_risk_score(findings: list[Finding]) -> float:
    """Calculate risk score (0-100) based on findings
    
    Uses weighted sum of findings by severity:
    - Critical: 25 points each
    - High: 10 points each
    - Medium: 3 points each
    - Low: 1 point each
    
    Capped at 100.
    
    Args:
        findings: List of findings to score
        
    Returns:
        Risk score from 0.0 to 100.0
    """
    score = 0.0
    for finding in findings:
        weight = SEVERITY_WEIGHTS.get(finding.severity, 1)
        score += weight * finding.count
    
    return min(score, 100.0)
