# CI Scripts

This directory contains custom scripts used in the CI/CD pipeline for the Gym Class Rotation Scheduler project.

## Scripts

### `coverage_report.py`

Generates a formatted coverage report from coverage data, with highlighting of areas that need improvement.

```bash
python ci/coverage_report.py --input coverage.xml --output coverage_report.md
```

### `version_bumper.py`

Script to automatically increment version numbers based on semantic versioning rules.

```bash
python ci/version_bumper.py --type [major|minor|patch]
```

### `deploy.py`

Handles deployment to different environments with proper configuration.

```bash
python ci/deploy.py --env [staging|production] --package dist/scheduler_backend-1.0.0-py3-none-any.whl
```

### `quality_gate.py`

Enforces quality gates by checking test results, coverage, and other metrics.

```bash
python ci/quality_gate.py --coverage-threshold 80 --test-results junit.xml
```

## Usage in CI/CD Pipeline

These scripts are used in the GitHub Actions workflows to automate various tasks. See the workflow files in `.github/workflows/` for details on how they are integrated.
