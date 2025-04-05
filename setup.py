"""
Setup configuration for the Generic AI Agent package.
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
    name="knowledge-base-agent",
    version="0.1.0",
    author="Knowledge Base Agent Contributors",
    author_email="your.email@example.com",
    description="A hybrid knowledge base agent combining vector embeddings and knowledge graphs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/knowledge-base-agent",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn>=0.24.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.2",
        "pinecone-client>=3.0.0",
        "pymongo>=4.6.1",
        "neo4j>=5.14.0",
        "sentence-transformers>=2.2.2",
        "spacy>=3.7.2",
        "torch>=2.1.0",
        "transformers>=4.36.0",
        "numpy>=1.24.0",
        "pandas>=2.1.3",
        "tqdm>=4.66.1",
        "PyYAML>=6.0.1",
        "python-multipart>=0.0.6",
        "aiofiles>=23.2.1",
        "tenacity>=8.2.3",
        "openai>=1.12.0",
        "tiktoken>=0.6.0",
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
            "knowledge-base-agent=knowledge_base_agent.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 