# GitHub Configuration and Workflows

This directory contains GitHub-specific configuration files and workflows for the Gym Class Rotation Scheduler project.

## Workflows

### Backend CI (`workflows/backend-ci.yml`)

This workflow runs continuous integration processes for the backend:
- Code quality checks (linting, formatting)
- Unit, integration, API, and functional tests
- Code coverage reporting
- Build and packaging

### Backend CD (`workflows/backend-cd.yml`)

This workflow handles continuous deployment:
- Validation tests
- Building the application
- Deploying to staging and production environments
- Creating GitHub releases for tagged versions

### Code Quality Monitoring (`workflows/code-quality.yml`)

This workflow monitors code quality:
- SonarCloud analysis for code quality metrics
- Dependency vulnerability scanning
- Code complexity analysis
- Duplicate code detection

### Performance Tests (`workflows/performance-tests.yml`)

This workflow runs performance tests to detect regressions:
- Performance regression tests
- Genetic algorithm benchmarks
- Performance results reporting

## How to Use

1. Workflows run automatically based on their trigger configuration
2. Manual workflow runs can be triggered from the GitHub Actions tab
3. Configuration changes should be tested in a feature branch before merging to main

## Required Secrets

These workflows require the following GitHub Secrets:
- `AWS_ACCESS_KEY_ID` - AWS access key for deployments
- `AWS_SECRET_ACCESS_KEY` - AWS secret key for deployments
- `SONAR_TOKEN` - SonarCloud API token for code quality analysis

## Documentation

For more detailed information, see the [CI/CD Pipeline Documentation](/docs/ci-cd-pipeline.md).
