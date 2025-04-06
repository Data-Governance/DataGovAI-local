#!/usr/bin/env python
"""
Script to analyze and summarize the current status of the SOTA branch development plan.
This helps developers stay aligned with the plan and track overall progress.
"""
import os
import re
import sys
from pathlib import Path
from datetime import datetime
import argparse
from typing import Dict, List, Tuple

# Define status indicators and their meanings
STATUS_INDICATORS = {
    "✅": "COMPLETED",
    "🔄": "IN PROGRESS",
    "⏳": "PENDING",
    "❌": "BLOCKED",
    "⚠️": "NEEDS REVIEW"
}

def find_development_plan() -> Path:
    """Find the development plan file."""
    # Try current directory first
    current_dir = Path.cwd()
    plan_path = current_dir / "DEVELOPMENT_PLAN_SOTA.md"
    
    if plan_path.exists():
        return plan_path
    
    # Try parent directory
    parent_dir = current_dir.parent
    plan_path = parent_dir / "DEVELOPMENT_PLAN_SOTA.md"
    
    if plan_path.exists():
        return plan_path
    
    # Try project root (assuming we're in src/knowledge_base_agent/scripts)
    if current_dir.name == "scripts" and current_dir.parent.name == "knowledge_base_agent":
        project_root = current_dir.parent.parent.parent
        plan_path = project_root / "DEVELOPMENT_PLAN_SOTA.md"
        
        if plan_path.exists():
            return plan_path
    
    raise FileNotFoundError("Could not find DEVELOPMENT_PLAN_SOTA.md")

def count_status_indicators(content: str) -> Dict[str, int]:
    """Count occurrences of each status indicator in the content."""
    counts = {}
    
    for emoji, status in STATUS_INDICATORS.items():
        counts[status] = len(re.findall(re.escape(emoji), content))
    
    return counts

def extract_tasks_by_status(content: str, status_emoji: str) -> List[str]:
    """Extract task descriptions matching a specific status."""
    # Regex pattern to match task descriptions with the specified status
    pattern = rf'\*\s+\*\*([^*]+)\*\*:.*?\n\s+\*\s+\*Status:\*\s+{re.escape(status_emoji)}'
    
    # Find all matches
    matches = re.findall(pattern, content)
    
    # Clean up the task descriptions
    return [task.strip() for task in matches]

def extract_current_section(content: str) -> str:
    """Extract the current implementation section from the plan."""
    # Look for the Implementation Plan section
    match = re.search(r'## Implementation Plan\s+(.+?)(?:##|$)', content, re.DOTALL)
    
    if not match:
        return "Implementation Plan section not found"
        
    return match.group(1).strip()

def parse_sections(content: str) -> Dict[str, List[Dict[str, str]]]:
    """Parse the development plan into structured sections."""
    sections = {}
    
    # Extract the implementation plan section
    impl_plan_match = re.search(r'## Implementation Plan\s+(.+?)(?:##|$)', content, re.DOTALL)
    
    if not impl_plan_match:
        return sections
        
    impl_plan = impl_plan_match.group(1)
    
    # Parse top-level sections
    top_level_sections = re.findall(r'\*\*(\d+)\.\s+([^*]+)\*\*:', impl_plan)
    
    for section_num, section_name in top_level_sections:
        section_id = f"{section_num}. {section_name.strip()}"
        
        # Extract the section content
        section_pattern = rf'\*\*{re.escape(section_num)}\.\s+{re.escape(section_name)}\*\*:(.*?)(?:\*\*\d+\.|$)'
        section_match = re.search(section_pattern, impl_plan, re.DOTALL)
        
        if not section_match:
            continue
            
        section_content = section_match.group(1)
        
        # Parse tasks within the section
        tasks = []
        task_matches = re.findall(r'\*\s+\*\*([^*]+)\*\*:(.*?)(?:\*\s+\*\*|$)', section_content, re.DOTALL)
        
        for task_name, task_details in task_matches:
            # Extract status
            status_match = re.search(r'\*Status:\*\s+([✅🔄⏳❌⚠️])', task_details)
            status = status_match.group(1) if status_match else "❓"
            
            # Extract action
            action_match = re.search(r'\*Action:\*\s+(.*?)(?:\*|$)', task_details, re.DOTALL)
            action = action_match.group(1).strip() if action_match else ""
            
            tasks.append({
                "name": task_name.strip(),
                "status": status,
                "action": action
            })
        
        sections[section_id] = tasks
    
    return sections

def print_summary(counts: Dict[str, int]) -> None:
    """Print a summary of the task statuses."""
    total = sum(counts.values())
    
    if total == 0:
        print("No tasks found in the development plan")
        return
    
    print("\n=== Development Plan Status ===")
    
    for status, count in counts.items():
        percentage = (count / total) * 100 if total > 0 else 0
        print(f"{status.ljust(12)}: {count} ({percentage:.1f}%)")
    
    print(f"Total Tasks  : {total}")
    
    # Calculate overall completion percentage
    completion = (counts.get("COMPLETED", 0) / total) * 100 if total > 0 else 0
    print(f"Completion   : {completion:.1f}%")

def print_tasks_by_status(content: str, status: str) -> None:
    """Print all tasks with a specific status."""
    emoji = next((e for e, s in STATUS_INDICATORS.items() if s == status), None)
    
    if not emoji:
        print(f"Unknown status: {status}")
        return
    
    tasks = extract_tasks_by_status(content, emoji)
    
    if not tasks:
        print(f"No tasks with status '{status}'")
        return
    
    print(f"\n=== Tasks with Status: {status} ===")
    for i, task in enumerate(tasks, 1):
        print(f"{i}. {task}")

def print_detailed_report(sections: Dict[str, List[Dict[str, str]]]) -> None:
    """Print a detailed report of all sections and tasks."""
    print("\n=== Detailed Development Report ===")
    
    for section_id, tasks in sections.items():
        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks if task["status"] == "✅")
        completion = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        
        print(f"\n{section_id} - {completed_tasks}/{total_tasks} ({completion:.1f}%)")
        
        for task in tasks:
            status_text = STATUS_INDICATORS.get(task["status"], "UNKNOWN")
            print(f"  {task['status']} {task['name']} ({status_text})")

def main() -> None:
    """Main function to analyze the development plan."""
    parser = argparse.ArgumentParser(description="Analyze the SOTA development plan status")
    parser.add_argument("--in-progress", action="store_true", help="Show only in-progress tasks")
    parser.add_argument("--blocked", action="store_true", help="Show only blocked tasks")
    parser.add_argument("--pending", action="store_true", help="Show only pending tasks")
    parser.add_argument("--detailed", action="store_true", help="Show detailed report of all sections")
    args = parser.parse_args()
    
    try:
        plan_path = find_development_plan()
        print(f"Development Plan: {plan_path}")
        
        # Read the plan content
        content = plan_path.read_text()
        
        # Count status indicators
        counts = count_status_indicators(content)
        
        # Print summary
        print_summary(counts)
        
        # Parse sections
        sections = parse_sections(content)
        
        # Show specific task lists if requested
        if args.in_progress:
            print_tasks_by_status(content, "IN PROGRESS")
        
        if args.blocked:
            print_tasks_by_status(content, "BLOCKED")
        
        if args.pending:
            print_tasks_by_status(content, "PENDING")
            
        if args.detailed:
            print_detailed_report(sections)
        
        # Default: Show in-progress tasks
        if not any([args.in_progress, args.blocked, args.pending, args.detailed]):
            print_tasks_by_status(content, "IN PROGRESS")
        
        # Remind about checking the plan
        print("\n✨ REMINDER: Always check DEVELOPMENT_PLAN_SOTA.md before starting work!")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error analyzing development plan: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 