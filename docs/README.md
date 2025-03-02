# Documentation System

This directory contains the MkDocs-based documentation for the Gym Class Rotation Scheduler project.

## Quick Start

1. Install the documentation dependencies:
   ```bash
   pip install -r docs/requirements.txt
   ```

2. Start the documentation server:
   ```bash
   mkdocs serve
   ```

3. View the documentation at http://localhost:8000

## Building Documentation

To build the static site:
```bash
mkdocs build
```

The built documentation will be in the `site` directory.

## Directory Structure

- **docs/**: Markdown source files
  - **getting-started/**: Installation and quick start guides
  - **user-guide/**: End-user documentation
  - **architecture/**: System architecture documentation
  - **developer-guide/**: Developer-focused documentation
  - **component-reference/**: Detailed component documentation
  - **tutorials/**: Step-by-step guides
  - **project-management/**: Roadmap and project history

## Contributing to Documentation

1. All documentation is written in Markdown
2. Follow the style guide in the [Documentation Consolidation Plan](/memory-bank/review/documentation_consolidation_plan.md)
3. Preview your changes locally before committing
4. Use relative links for internal references

## Migrating Documentation

To migrate existing documentation:
```bash
python scripts/migrate_docs.py
```
