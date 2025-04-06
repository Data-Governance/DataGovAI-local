"""
DataGovAI - Utah GRS Knowledge Base Agent
Copyright (c) 2025 Utah Office of Data Privacy (ODP). All Rights Reserved.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements files
def read_requirements(filename: str) -> list:
    """Read requirements from file."""
    with open(filename, "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith('#')]

# Core requirements
install_requires = read_requirements('requirements.txt')

# Development requirements
dev_requires = [
    'pytest>=7.4.3',
    'pytest-asyncio>=0.21.1',
    'pytest-cov>=4.1.0',
    'pytest-mock>=3.10.0',
    'black>=23.11.0',
    'isort>=5.12.0',
    'flake8>=6.0.0',
    'mypy>=1.7.0',
]

setup(
    name="datagovai",
    version="1.0.0",
    author="Utah Office of Data Privacy",
    author_email="privacy@utah.gov",  # Replace with actual ODP email
    description="A proprietary knowledge base agent for Utah GRS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://privacy.utah.gov",  # Replace with actual ODP website
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Government",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.10",
        "Topic :: Text Processing :: Indexing",
        "Private :: Do Not Upload",  # Indicates this is not for public distribution
    ],
    python_requires=">=3.10",
    install_requires=[
        "flask>=2.0.0",
        "sentence-transformers>=4.0.0",
        "transformers>=4.35.0",
        "torch>=2.0.0",
        "pymupdf>=1.23.0",
        "python-dotenv>=1.0.0",
        "psycopg2-binary>=2.9.0",
        "pgvector>=0.2.0",
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "tqdm>=4.65.0",
        "plotly>=5.16.0",
    ],
    extras_require={
        "dev": dev_requires,
        "docs": [
            "sphinx>=7.1.2",
            "sphinx-rtd-theme>=1.3.0",
            "myst-parser>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "datagovai=app.app:main",
        ],
    },
    include_package_data=True,
    package_data={
        "datagovai": [
            "app/templates/*",
            "app/static/*",
        ],
    },
) 