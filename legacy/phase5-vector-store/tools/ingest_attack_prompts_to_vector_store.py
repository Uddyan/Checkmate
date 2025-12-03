#!/usr/bin/env python3
"""
Ingest attack prompts into vector store.

This script is separate from the scanning pipeline and should be run
periodically to populate the vector database with attack prompts.

Usage:
    python tools/ingest_attack_prompts_to_vector_store.py --config vector_config.yaml --source prompts.json
"""

import argparse
import json
import logging
import yaml
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from checkmate.vector_store.factory import create_vector_store

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_prompts_from_json(source_path: Path) -> list:
    """
    Load attack prompts from JSON file.
    
    Expected format:
    [
        {
            "text": "Ignore all previous instructions...",
            "metadata": {
                "category": "LLM01_prompt_injection",
                "severity": "high",
                "tags": ["jailbreak", "DAN"],
                "probe_family": "dan"
            }
        },
        ...
    ]
    """
    with open(source_path) as f:
        return json.load(f)


def load_prompts_from_yaml(source_path: Path) -> list:
    """Load attack prompts from YAML file (same format as JSON)"""
    with open(source_path) as f:
        return yaml.safe_load(f)


def ingest_prompts(vector_store, prompts: list):
    """
    Ingest prompts into vector store.
    
    Note: This is a placeholder. Actual implementation would:
    1. Generate embeddings for each prompt
    2. Insert into vector database with metadata
    
    Args:
        vector_store: VectorStore instance
        prompts: List of prompt dicts
    """
    logger.info(f"Ingesting {len(prompts)} prompts into vector store...")
    
    # TODO: Implement actual ingestion
    # For each prompt:
    #   1. Generate embedding (using OpenAI API or local model)
    #   2. Insert into database with text, embedding, and metadata
    
    logger.warning("Ingestion not fully implemented - this is a placeholder")
    logger.info("To implement:")
    logger.info("1. Add embedding generation (OpenAI, SentenceTransformers, etc.)")
    logger.info("2. Implement insert method in vector store")
    logger.info("3. Handle duplicates and updates")


def main():
    parser = argparse.ArgumentParser(description='Ingest attack prompts into vector store')
    parser.add_argument('--config', required=True, help='Vector store config YAML file')
    parser.add_argument('--source', required=True, help='Source file with prompts (JSON or YAML)')
    parser.add_argument('--dry-run', action='store_true', help='Parse but do not ingest')
    
    args = parser.parse_args()
    
    # Load vector store config
    config_path = Path(args.config)
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Create vector store
    vector_store = create_vector_store(config.get('vector_store', {}))
    
    if not vector_store:
        logger.error("Failed to create vector store from config")
        return 1
    
    # Load prompts
    source_path = Path(args.source)
    if source_path.suffix == '.json':
        prompts = load_prompts_from_json(source_path)
    elif source_path.suffix in ['.yaml', '.yml']:
        prompts = load_prompts_from_yaml(source_path)
    else:
        logger.error(f"Unsupported source format: {source_path.suffix}")
        return 1
    
    logger.info(f"Loaded {len(prompts)} prompts from {source_path}")
    
    if args.dry_run:
        logger.info("Dry run - not ingesting")
        for i, prompt in enumerate(prompts[:5]):
            logger.info(f"Sample {i+1}: {prompt.get('text', '')[:100]}...")
        return 0
    
    # Ingest prompts
    ingest_prompts(vector_store, prompts)
    
    # Cleanup
    vector_store.close()
    
    logger.info("Ingestion complete")
    return 0


if __name__ == '__main__':
    sys.exit(main())
