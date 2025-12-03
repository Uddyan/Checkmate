"""Resource loading utilities for checkmate"""

from importlib.resources import files
from pathlib import Path
from typing import Union


def data_path(*parts: str) -> Path:
    """Get path to data resource within checkmate package.
    
    Args:
        *parts: Path components to append to data directory
        
    Returns:
        Path to the requested data resource
    """
    return files("checkmate") / "data" / "/".join(parts)


def resource_path(*parts: str) -> Path:
    """Get path to resource within checkmate package.
    
    Args:
        *parts: Path components to append to resources directory
        
    Returns:
        Path to the requested resource
    """
    return files("checkmate") / "resources" / "/".join(parts)


def load_text_resource(*parts: str, encoding: str = "utf-8") -> str:
    """Load a text resource from the checkmate package.
    
    Args:
        *parts: Path components to the resource
        encoding: Text encoding to use
        
    Returns:
        Contents of the text resource
    """
    path = resource_path(*parts)
    return path.read_text(encoding=encoding)


def load_data_text(*parts: str, encoding: str = "utf-8") -> str:
    """Load a text resource from the checkmate data directory.
    
    Args:
        *parts: Path components to the data resource
        encoding: Text encoding to use
        
    Returns:
        Contents of the text resource
    """
    path = data_path(*parts)
    return path.read_text(encoding=encoding)


def load_binary_resource(*parts: str) -> bytes:
    """Load a binary resource from the checkmate package.
    
    Args:
        *parts: Path components to the resource
        
    Returns:
        Contents of the binary resource
    """
    path = resource_path(*parts)
    return path.read_bytes()


def load_data_binary(*parts: str) -> bytes:
    """Load a binary resource from the checkmate data directory.
    
    Args:
        *parts: Path components to the data resource
        
    Returns:
        Contents of the binary resource
    """
    path = data_path(*parts)
    return path.read_bytes()
