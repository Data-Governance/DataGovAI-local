#!/usr/bin/env python
"""
Script to help developers find relevant documentation for their current task.
This helps ensure that developers consult documentation before making changes.
"""
import os
import re
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Set

def find_project_root() -> Path:
    """Find the project root directory."""
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

def scan_development_plan(project_root: Path) -> Dict[str, List[str]]:
    """Scan the development plan to extract components and their statuses."""
    plan_path = project_root / 'DEVELOPMENT_PLAN_SOTA.md'
    if not plan_path.exists():
        return {}
    
    content = plan_path.read_text()
    
    # Extract implementation sections
    impl_plan_match = re.search(r'## Implementation Plan\s+(.+?)(?:##|$)', content, re.DOTALL)
    if not impl_plan_match:
        return {}
    
    impl_plan = impl_plan_match.group(1)
    
    # Dictionary to store component -> [tasks]
    components = {}
    
    # Extract top-level sections
    section_matches = re.findall(r'\*\*(\d+)\.\s+([^*]+)\*\*:(.*?)(?:\*\*\d+\.|$)', impl_plan, re.DOTALL)
    
    for section_num, section_name, section_content in section_matches:
        component_name = section_name.strip()
        tasks = []
        
        # Extract tasks within the section
        task_matches = re.findall(r'\*\s+\*\*([^*]+)\*\*:(.*?)(?:\*\s+\*\*|$)', section_content, re.DOTALL)
        
        for task_name, task_details in task_matches:
            # Extract status
            status_match = re.search(r'\*Status:\*\s+([✅🔄⏳❌⚠️])', task_details)
            status = status_match.group(1) if status_match else "❓"
            
            task_info = f"{status} {task_name.strip()}"
            tasks.append(task_info)
        
        components[component_name] = tasks
    
    return components

def scan_docs_dir(project_root: Path) -> Dict[str, Path]:
    """Scan the docs directory for documentation files."""
    docs_dir = project_root / 'docs'
    if not docs_dir.is_dir():
        return {}
    
    # Dictionary to store topic -> file path
    docs = {}
    
    # Recursively scan for markdown files
    for md_file in docs_dir.glob('**/*.md'):
        # Skip README.md and index.md
        if md_file.name in ['README.md', 'index.md']:
            continue
        
        # Extract title from file
        try:
            content = md_file.read_text()
            title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else md_file.stem.replace('_', ' ').title()
            
            # Store relative path
            docs[title] = md_file.relative_to(project_root)
        except Exception:
            # Skip files that can't be read
            continue
    
    return docs

def find_relevant_docs(project_root: Path, component: str) -> List[Tuple[str, Path]]:
    """Find documentation relevant to a specific component."""
    all_docs = scan_docs_dir(project_root)
    relevant_docs = []
    
    # Normalize component name for matching
    component_norm = component.lower()
    
    for title, path in all_docs.items():
        # Check if component name appears in title or file path
        if (component_norm in title.lower() or 
            component_norm in str(path).lower()):
            relevant_docs.append((title, path))
    
    # Always include architecture overview
    arch_overview_path = project_root / 'docs' / 'architecture' / 'overview.md'
    if arch_overview_path.exists() and not any(str(p) == str(arch_overview_path.relative_to(project_root)) for _, p in relevant_docs):
        relevant_docs.append(("Architecture Overview", Path('docs/architecture/overview.md')))
    
    return relevant_docs

def find_relevant_modules(project_root: Path, component: str) -> List[Path]:
    """Find relevant code modules for a component."""
    src_dir = project_root / 'src' / 'knowledge_base_agent'
    if not src_dir.is_dir():
        return []
    
    # Normalize component name for matching
    component_norm = component.lower()
    component_words = set(component_norm.split())
    
    # List to store relevant modules
    relevant_modules = []
    
    # Recursively scan for Python files
    for py_file in src_dir.glob('**/*.py'):
        file_path = str(py_file.relative_to(project_root))
        file_name = py_file.stem.lower()
        
        # Check if component name appears in file path or name
        if (component_norm in file_name or 
            any(word in file_name for word in component_words) or
            component_norm in file_path.lower()):
            relevant_modules.append(py_file.relative_to(project_root))
    
    return relevant_modules

def print_component_info(component_name: str, tasks: List[str], 
                         relevant_docs: List[Tuple[str, Path]], 
                         relevant_modules: List[Path]) -> None:
    """Print information about a component."""
    print(f"\n{'=' * 80}")
    print(f"Component: {component_name}")
    print(f"{'=' * 80}")
    
    print("\nTasks from Development Plan:")
    for task in tasks:
        print(f"  {task}")
    
    print("\nRelevant Documentation:")
    if relevant_docs:
        for title, path in relevant_docs:
            print(f"  - {title}: {path}")
    else:
        print("  No specific documentation found for this component")
    
    print("\nRelevant Code Modules:")
    if relevant_modules:
        for module in relevant_modules:
            print(f"  - {module}")
    else:
        print("  No specific modules found for this component")

def get_component_list(components: Dict[str, List[str]]) -> None:
    """Print a list of all components from the development plan."""
    print("\nAvailable Components:")
    for i, component in enumerate(components.keys(), 1):
        print(f"  {i}. {component}")

def main() -> None:
    """Main function to find relevant documentation."""
    parser = argparse.ArgumentParser(description="Find relevant documentation for a component")
    parser.add_argument("component", nargs="?", help="Component name to find documentation for")
    parser.add_argument("--list", action="store_true", help="List all available components")
    args = parser.parse_args()
    
    try:
        project_root = find_project_root()
        components = scan_development_plan(project_root)
        
        if args.list or not args.component:
            get_component_list(components)
            return
        
        # Try to find exact match first
        component_name = args.component
        if component_name not in components:
            # Try case-insensitive match
            matches = [c for c in components.keys() if component_name.lower() in c.lower()]
            if matches:
                component_name = matches[0]
            else:
                print(f"Component '{component_name}' not found in development plan")
                get_component_list(components)
                return
        
        tasks = components[component_name]
        relevant_docs = find_relevant_docs(project_root, component_name)
        relevant_modules = find_relevant_modules(project_root, component_name)
        
        print_component_info(component_name, tasks, relevant_docs, relevant_modules)
        
        # Remind about checking documentation
        print("\n✨ REMINDER: Review documentation before making code changes!")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error finding documentation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 