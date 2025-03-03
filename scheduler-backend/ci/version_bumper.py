#!/usr/bin/env python
"""
Version Bumper

This script increments version numbers in appropriate files based on semantic versioning rules.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Tuple


def get_current_version(version_file: str) -> Tuple[int, int, int]:
    """
    Extract the current version from the version file.
    
    Args:
        version_file: Path to the file containing version information
        
    Returns:
        Tuple containing major, minor, and patch version numbers
    """
    try:
        content = Path(version_file).read_text()
        # Look for version pattern like "__version__ = '1.2.3'" or "VERSION = '1.2.3'"
        pattern = r"(?:__version__|VERSION)\s*=\s*['\"](\d+)\.(\d+)\.(\d+)['\"]"
        match = re.search(pattern, content)
        
        if match:
            major, minor, patch = map(int, match.groups())
            return major, minor, patch
        else:
            print(f"Error: Could not find version pattern in {version_file}")
            sys.exit(1)
    except Exception as e:
        print(f"Error reading version file: {e}")
        sys.exit(1)


def bump_version(
    version_file: str,
    bump_type: str
) -> Tuple[str, str]:
    """
    Bump the version in the specified file according to semantic versioning.
    
    Args:
        version_file: Path to the file containing version information
        bump_type: Type of bump (major, minor, or patch)
        
    Returns:
        Tuple containing the old and new version strings
    """
    major, minor, patch = get_current_version(version_file)
    old_version = f"{major}.{minor}.{patch}"
    
    # Increment version based on bump type
    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    elif bump_type == 'patch':
        patch += 1
    else:
        print(f"Error: Invalid bump type '{bump_type}'. Must be major, minor, or patch.")
        sys.exit(1)
    
    new_version = f"{major}.{minor}.{patch}"
    
    # Update the version file
    content = Path(version_file).read_text()
    new_content = re.sub(
        r"(__version__|VERSION)\s*=\s*['\"]\d+\.\d+\.\d+['\"]",
        f"\\1 = '{new_version}'",
        content
    )
    
    Path(version_file).write_text(new_content)
    
    return old_version, new_version


def update_changelog(changelog_file: str, new_version: str) -> None:
    """
    Update the changelog with a new version entry.
    
    Args:
        changelog_file: Path to the changelog file
        new_version: The new version string to add
    """
    if not Path(changelog_file).exists():
        print(f"Warning: Changelog file {changelog_file} does not exist. Creating a new one.")
        changelog_content = "# Changelog\n\n"
    else:
        changelog_content = Path(changelog_file).read_text()
    
    # Create a new version entry
    import datetime
    today = datetime.date.today().strftime("%Y-%m-%d")
    new_entry = f"## [{new_version}] - {today}\n\n"
    new_entry += "### Added\n- \n\n"
    new_entry += "### Changed\n- \n\n"
    new_entry += "### Fixed\n- \n\n"
    
    # Insert after the header
    if "# Changelog" in changelog_content:
        changelog_content = changelog_content.replace(
            "# Changelog\n\n",
            f"# Changelog\n\n{new_entry}",
            1
        )
    else:
        changelog_content = f"# Changelog\n\n{new_entry}\n{changelog_content}"
    
    Path(changelog_file).write_text(changelog_content)


def main():
    parser = argparse.ArgumentParser(description="Bump version numbers based on semantic versioning")
    parser.add_argument("--type", required=True, choices=['major', 'minor', 'patch'],
                        help="Type of version bump")
    parser.add_argument("--version-file", default="../app/__init__.py",
                        help="File containing the version string")
    parser.add_argument("--changelog", default="../CHANGELOG.md",
                        help="Path to the changelog file")
    parser.add_argument("--no-changelog", action="store_true",
                        help="Skip updating the changelog")
    
    args = parser.parse_args()
    
    # Check if version file exists
    if not Path(args.version_file).exists():
        print(f"Error: Version file {args.version_file} does not exist")
        sys.exit(1)
    
    # Bump the version
    old_version, new_version = bump_version(args.version_file, args.type)
    print(f"Version bumped from {old_version} to {new_version}")
    
    # Update the changelog if needed
    if not args.no_changelog:
        update_changelog(args.changelog, new_version)
        print(f"Updated changelog at {args.changelog}")
    
    # Return the new version for use in CI scripts
    print(f"::set-output name=new_version::{new_version}")


if __name__ == "__main__":
    main()
