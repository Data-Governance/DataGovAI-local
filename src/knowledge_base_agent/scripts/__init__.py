"""
Knowledge Base Agent - Scripts Package

This package contains utility scripts for development and project management.

Available scripts:
- check_plan: Analyzes and summarizes the current status of the SOTA branch development plan
- check_docs: Helps find relevant documentation for specific components
"""

from pathlib import Path

__version__ = "1.0.0"

# Expose key functions from scripts
try:
    from .check_plan import count_status_indicators, extract_tasks_by_status
    from .check_docs import find_relevant_docs, find_relevant_modules
except ImportError:
    # These will be available when scripts are installed
    pass

def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path to the project root directory.
    """
    current_dir = Path.cwd()
    
    # Look for src/knowledge_base_agent
    while current_dir != Path('/'):
        if (current_dir / 'src' / 'knowledge_base_agent').is_dir():
            return current_dir
        current_dir = current_dir.parent
    
    # If not found, try looking for docs and DEVELOPMENT_PLAN_SOTA.md
    current_dir = Path.cwd()
    while current_dir != Path('/'):
        if (current_dir / 'docs').is_dir() and (current_dir / 'DEVELOPMENT_PLAN_SOTA.md').is_file():
            return current_dir
        current_dir = current_dir.parent
    
    raise FileNotFoundError("Could not find project root")