#!/usr/bin/env python
"""
Installs Git hooks to help maintain development practices.
This script sets up:
1. pre-commit hook to remind about checking the development plan
2. post-merge hook to notify about development plan changes

Run this script after cloning the repository.
"""
import os
import sys
from pathlib import Path

# Pre-commit hook content
PRE_COMMIT_HOOK = """#!/bin/bash
# Knowledge Base Agent pre-commit hook

# Output colors
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}⚠️  REMINDER: Have you checked DEVELOPMENT_PLAN_SOTA.md before this commit?${NC}"
echo -e "${YELLOW}    Run 'python -m src.knowledge_base_agent.scripts.check_plan' to view the current status.${NC}"

# Check if the commit modifies code files
python_files=$(git diff --cached --name-only | grep -E '\\.py$' | wc -l)

if [ "$python_files" -gt 0 ]; then
    echo -e "${YELLOW}ℹ️  This commit contains Python code changes.${NC}"
    
    # Check if development plan is also being updated
    dev_plan_updated=$(git diff --cached --name-only | grep -E 'DEVELOPMENT_PLAN_SOTA\\.md$' | wc -l)
    
    if [ "$dev_plan_updated" -eq 0 ]; then
        echo -e "${RED}❗ WARNING: You're changing code but not updating DEVELOPMENT_PLAN_SOTA.md${NC}"
        echo -e "${YELLOW}   If your changes complete or modify a task, please update the plan.${NC}"
        
        read -p "Continue with commit anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}Commit aborted. Please update the development plan first.${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✅ Good job! You're updating the development plan along with your code changes.${NC}"
    fi
fi

exit 0
"""

# Post-merge hook content
POST_MERGE_HOOK = """#!/bin/bash
# Knowledge Base Agent post-merge hook

# Output colors
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Check if the development plan was updated
dev_plan_updated=$(git diff ORIG_HEAD HEAD --name-only | grep -E 'DEVELOPMENT_PLAN_SOTA\\.md$' | wc -l)

if [ "$dev_plan_updated" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  NOTICE: DEVELOPMENT_PLAN_SOTA.md was updated in the merge/pull${NC}"
    echo -e "${YELLOW}   Please review the changes to stay up-to-date with the development plan.${NC}"
    echo -e "${YELLOW}   Run 'python -m src.knowledge_base_agent.scripts.check_plan --detailed' to see the current status.${NC}"
fi

exit 0
"""

def find_git_root() -> Path:
    """Find the Git repository root directory."""
    current_dir = Path.cwd()
    
    # Check if .git directory exists in current or parent directories
    while current_dir != Path('/'):
        if (current_dir / '.git').is_dir():
            return current_dir
        current_dir = current_dir.parent
    
    raise FileNotFoundError("Not in a Git repository")

def install_hooks() -> None:
    """Install Git hooks for the project."""
    try:
        # Find the Git repository root
        git_root = find_git_root()
        git_hooks_dir = git_root / '.git' / 'hooks'
        
        if not git_hooks_dir.is_dir():
            print(f"Error: Git hooks directory not found at {git_hooks_dir}")
            return
        
        # Install pre-commit hook
        pre_commit_path = git_hooks_dir / 'pre-commit'
        with open(pre_commit_path, 'w') as f:
            f.write(PRE_COMMIT_HOOK)
        
        # Make executable
        os.chmod(pre_commit_path, 0o755)
        print(f"✅ Installed pre-commit hook to {pre_commit_path}")
        
        # Install post-merge hook
        post_merge_path = git_hooks_dir / 'post-merge'
        with open(post_merge_path, 'w') as f:
            f.write(POST_MERGE_HOOK)
        
        # Make executable
        os.chmod(post_merge_path, 0o755)
        print(f"✅ Installed post-merge hook to {post_merge_path}")
        
        print("\nGit hooks installed successfully!")
        print("The hooks will remind you about checking the development plan when committing and pulling.")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error installing Git hooks: {e}")
        sys.exit(1)

if __name__ == "__main__":
    install_hooks() 