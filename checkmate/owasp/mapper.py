"""OWASP LLM Top-10 category mapping and documentation.

This module provides mappings from checkmate probes/detectors to
OWASP LLM Top-10 vulnerability categories.
"""

OWASP_CATEGORIES = {
    'LLM01': {
        'name': 'Prompt Injection',
        'description': 'Manipulating LLM via crafted inputs to override system instructions',
        'examples': ['DAN jailbreaks', 'System prompt extraction', 'Context poisoning']
    },
    'LLM02': {
        'name': 'Insecure Output Handling',
        'description': 'Insufficient validation of LLM outputs leading to XSS, SSRF, etc.',
        'examples': ['Code injection', 'XSS via generated content', 'Malware generation']
    },
    'LLM03': {
        'name': 'Training Data Poisoning',
        'description': 'Manipulation of training data or fine-tuning to introduce vulnerabilities',
        'examples': ['Backdoor attacks', 'Bias injection']
    },
    'LLM04': {
        'name': 'Model Denial of Service',
        'description': 'Resource exhaustion via expensive operations',
        'examples': ['Context overflow', 'Recursive prompts']
    },
    'LLM05': {
        'name': 'Supply Chain Vulnerabilities',
        'description': 'Vulnerabilities in third-party components, models, or datasets',
        'examples': ['Compromised models', 'Malicious plugins']
    },
    'LLM06': {
        'name': 'Sensitive Information Disclosure',
        'description': 'Unintended revelation of confidential data',
        'examples': ['Training data leakage', 'PII exposure', 'API key disclosure']
    },
    'LLM07': {
        'name': 'Insecure Plugin Design',
        'description': 'Plugins with insufficient access control or validation',
        'examples': ['Tool parameter injection', 'Unauthorized API calls']
    },
    'LLM08': {
        'name': 'Excessive Agency',
        'description': 'LLM agent with too much autonomy or permissions',
        'examples': ['Unauthorized actions', 'Privilege escalation via tools']
    },
    'LLM09': {
        'name': 'Overreliance',
        'description': 'Excessive dependence on LLM outputs without oversight',
        'examples': ['Hallucination propagation', 'Unchecked medical advice']
    },
    'LLM10': {
        'name': 'Model Theft',
        'description': 'Unauthorized access or extraction of proprietary models',
        'examples': ['Model extraction', 'Inference API abuse']
    }
}


def get_category_info(category_id: str) -> dict:
    """Get information about an OWASP category
    
    Args:
        category_id: Category ID (e.g., 'LLM01' or 'LLM01: Prompt Injection')
        
    Returns:
        Dict with category info or None if not found
    """
    # Extract ID if full string provided
    if ':' in category_id:
        category_id = category_id.split(':')[0].strip()
    
    return OWASP_CATEGORIES.get(category_id)


def format_category_name(category_id: str) -> str:
    """Format OWASP category as full name
    
    Args:
        category_id: Category ID
        
    Returns:
        Formatted string like "LLM01: Prompt Injection"
    """
    info = get_category_info(category_id)
    if info:
        return f"{category_id}: {info['name']}"
    return category_id


def list_all_categories() -> list:
    """List all OWASP LLM Top-10 categories
    
    Returns:
        List of formatted category strings
    """
    return [
        f"{cat_id}: {cat_info['name']}"
        for cat_id, cat_info in sorted(OWASP_CATEGORIES.items())
    ]
