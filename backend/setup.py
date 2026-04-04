"""
SocialSpace Agent - Setup Configuration
========================================

Package setup and installation configuration for the SocialSpace Agent.

This file enables the package to be installed in development mode using:
    pip install -e .

Author: Dheeraj Mishra
Created: February 6, 2026
License: MIT
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements from requirements.txt
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, 'r', encoding='utf-8') as f:
        requirements = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith('#')
        ]

setup(
    # ============================================
    # PACKAGE METADATA
    # ============================================
    name="socialspace-agent",
    version="0.1.0",
    description="Unified AI-powered social media management platform built on Hive framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    # ============================================
    # AUTHOR INFO
    # ============================================
    author="Dheeraj Mishra",
    author_email="your.email@example.com",  # Update with your email
    url="https://github.com/yourusername/socialspace-agent",  # Update when created
    
    # ============================================
    # LICENSE & CLASSIFIERS
    # ============================================
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    
    # ============================================
    # PACKAGE DISCOVERY
    # ============================================
    packages=find_packages(exclude=["tests", "tests.*", "docs"]),
    package_dir={"": "."},
    
    # ============================================
    # DEPENDENCIES
    # ============================================
    python_requires=">=3.11",
    install_requires=requirements,
    
    # Optional dependencies for different features
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.12.0",
            "flake8>=7.0.0",
            "mypy>=1.7.0",
            "isort>=5.13.0",
        ],
        "docs": [
            "sphinx>=7.2.0",
            "sphinx-rtd-theme>=2.0.0",
        ],
        "monitoring": [
            "sentry-sdk>=1.39.0",
            "prometheus-client>=0.19.0",
        ],
    },
    
    # ============================================
    # PACKAGE DATA
    # ============================================
    include_package_data=True,
    package_data={
        "socialspace_agent": [
            "py.typed",  # PEP 561 - type hints
        ],
    },
    
    # ============================================
    # ENTRY POINTS
    # ============================================
    # CLI commands (we'll add these later)
    entry_points={
        "console_scripts": [
            "socialspace=socialspace_agent.cli:main",  # Future CLI
        ],
    },
    
    # ============================================
    # KEYWORDS
    # ============================================
    keywords=[
        "ai-agent",
        "social-media",
        "automation",
        "whatsapp",
        "instagram",
        "twitter",
        "telegram",
        "facebook",
        "linkedin",
        "hive-framework",
    ],
    
    # ============================================
    # PROJECT URLS
    # ============================================
    project_urls={
        "Documentation": "https://socialspace-agent.readthedocs.io",  # Future
        "Source": "https://github.com/yourusername/socialspace-agent",  # Update
        "Bug Reports": "https://github.com/yourusername/socialspace-agent/issues",  # Update
    },
)
