#!/usr/bin/env python3
"""
Documentation Migration Script

This script helps with migrating existing documentation into the new MkDocs structure.
It processes markdown files, updates internal links, and copies them to the new location.
"""

import os
import re
import shutil
import argparse
from pathlib import Path

# Mapping of source files to destination files
DOC_MAPPING = {
    "scheduler-backend/README.md": "docs/getting-started/installation.md",
    "scheduler-backend/ENVIRONMENT.md": "docs/getting-started/development-setup.md",
    "memory-bank/schedulingRequirements.md": "docs/architecture/system-overview.md",
    "memory-bank/geneticOptimizationProposal.md": "docs/component-reference/backend/genetic-algorithm.md",
    "memory-bank/dashboard_overview.md": "docs/component-reference/frontend/react-components.md",
    "memory-bank/next_steps_roadmap.md": "docs/project-management/roadmap.md",
    "scheduler-backend/app/scheduling/solvers/README.md": "docs/component-reference/backend/scheduler.md",
}

def update_links(content, project_root):
    """Updates internal links in the content to match the new documentation structure."""
    
    # Pattern for markdown links: [text](url)
    link_pattern = r'\[(.*?)\]\((.*?)\)'
    
    def replace_link(match):
        text, url = match.groups()
        
        # Skip external links, anchors, or mailto links
        if (url.startswith(('http://', 'https://', '#', 'mailto:')) or 
            not url.endswith(('.md', '.markdown'))):
            return match.group(0)
        
        # Normalize the path
        source_path = Path(url)
        
        # Try to find the target in our mapping
        source_abs = str(source_path)
        if source_abs in DOC_MAPPING:
            new_url = DOC_MAPPING[source_abs].replace("docs/", "")
            return f"[{text}]({new_url})"
        
        # If not in mapping, keep the original
        return match.group(0)
    
    # Replace all links in the content
    updated_content = re.sub(link_pattern, replace_link, content)
    return updated_content

def migrate_file(source_file, target_file, project_root, overwrite=False):
    """Migrates a single file from source to target with link updates."""
    source_path = os.path.join(project_root, source_file)
    target_path = os.path.join(project_root, target_file)
    
    if not os.path.exists(source_path):
        print(f"Source file not found: {source_path}")
        return False
    
    if os.path.exists(target_path) and not overwrite:
        print(f"Target file already exists: {target_path}")
        return False
    
    # Create target directory if it doesn't exist
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    # Read source content
    with open(source_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update links
    updated_content = update_links(content, project_root)
    
    # Write to target
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"Migrated: {source_file} -> {target_file}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Migrate documentation files to MkDocs structure")
    parser.add_argument("--project-root", type=str, default=".", help="Path to the project root")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()
    
    success_count = 0
    for source, target in DOC_MAPPING.items():
        if migrate_file(source, target, args.project_root, args.overwrite):
            success_count += 1
    
    print(f"\nMigration complete: {success_count}/{len(DOC_MAPPING)} files migrated")

if __name__ == "__main__":
    main()
