#!/usr/bin/env python3
"""Setup script for checkmate"""

from setuptools import setup, find_packages

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements from pyproject.toml
with open("pyproject.toml", "r", encoding="utf-8") as fh:
    content = fh.read()

setup(
    name="checkmate",
    version="0.1.0",
    author="Checkmate Team",
    author_email="team@checkmate.ai",
    description="Model-agnostic LLM vulnerability scanner",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/checkmate-ai/checkmate",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Security",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "checkmate=checkmate.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "checkmate": [
            "data/**/*",
            "resources/**/*",
        ],
    },
)
