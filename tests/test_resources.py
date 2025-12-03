"""Tests for checkmate resource loading"""

import pytest
from pathlib import Path
from checkmate.utils.resources import (
    data_path, resource_path, 
    load_text_resource, load_data_text,
    load_binary_resource, load_data_binary
)


class TestResourcePaths:
    """Test resource path utilities"""
    
    def test_data_path(self):
        """Test data path construction"""
        path = data_path("test", "file.txt")
        assert isinstance(path, Path)
        assert "data" in str(path)
        assert "test" in str(path)
        assert "file.txt" in str(path)
    
    def test_resource_path(self):
        """Test resource path construction"""
        path = resource_path("test", "file.txt")
        assert isinstance(path, Path)
        assert "resources" in str(path)
        assert "test" in str(path)
        assert "file.txt" in str(path)
    
    def test_data_path_multiple_parts(self):
        """Test data path with multiple parts"""
        path = data_path("calibration", "2024", "data.json")
        assert isinstance(path, Path)
        assert "calibration" in str(path)
        assert "2024" in str(path)
        assert "data.json" in str(path)


class TestResourceLoading:
    """Test resource loading functions"""
    
    def test_load_text_resource_nonexistent(self):
        """Test loading non-existent text resource"""
        # This should raise an exception for non-existent files
        with pytest.raises(FileNotFoundError):
            load_text_resource("nonexistent", "file.txt")
    
    def test_load_data_text_nonexistent(self):
        """Test loading non-existent data text resource"""
        # This should raise an exception for non-existent files
        with pytest.raises(FileNotFoundError):
            load_data_text("nonexistent", "file.txt")
    
    def test_load_binary_resource_nonexistent(self):
        """Test loading non-existent binary resource"""
        # This should raise an exception for non-existent files
        with pytest.raises(FileNotFoundError):
            load_binary_resource("nonexistent", "file.bin")
    
    def test_load_data_binary_nonexistent(self):
        """Test loading non-existent data binary resource"""
        # This should raise an exception for non-existent files
        with pytest.raises(FileNotFoundError):
            load_data_binary("nonexistent", "file.bin")
