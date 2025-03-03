# CI/CD Pipeline Documentation

This document provides an overview of the Continuous Integration and Continuous Deployment (CI/CD) pipeline for the Gym Class Rotation Scheduler project.

## Overview

The CI/CD pipeline automates testing, quality checks, building, and deployment processes, ensuring that code changes are reliably tested and deployed. The pipeline is implemented using GitHub Actions.

## Workflow Structure

The CI/CD pipeline consists of three main workflows:

1. **Backend CI** (`backend-ci.yml`) - Runs on each pull request and push to main/develop branches:
   - Code quality checks (linting, formatting)
   - Unit tests with parallel execution
   - Integration tests
   - API tests
   - Functional tests
   - Build and package

2. **Backend CD** (`backend-cd.yml`) - Runs on pushes to main and when tags are created:
   - Validation checks
   - Build application
   - Deploy to staging environment
   - Deploy to production environment (only for tagged releases)
   - Create GitHub release (for tagged versions)

3. **Code Quality Monitoring** (`code-quality.yml`) - Runs on pull requests, pushes, and weekly schedule:
   - SonarCloud analysis
   - Dependency vulnerability audit
   - Code complexity analysis
   - Duplicate code detection
   - Quality report generation

## Development Workflow

The typical development workflow with this CI/CD pipeline is as follows:

1. Develop features in a feature branch
2. Create a pull request to the develop branch
3. CI pipeline automatically runs tests and checks
4. After approval and merging, changes are deployed to staging
5. After validation in staging, create a release tag
6. Tagged releases are automatically deployed to production

## Running Workflows Manually

You can manually trigger workflow runs from the GitHub Actions tab:

1. Go to the Actions tab in the GitHub repository
2. Select the workflow you want to run
3. Click "Run workflow"
4. Select the branch and parameters (if applicable)
5. Click "Run workflow"

## Required Secrets

The following GitHub Secrets need to be configured:

- `AWS_ACCESS_KEY_ID` - AWS access key for deployments
- `AWS_SECRET_ACCESS_KEY` - AWS secret key for deployments
- `SONAR_TOKEN` - SonarCloud API token for code quality analysis

## Quality Gates

The pipeline enforces the following quality gates:

1. **Code Quality**:
   - All linting and formatting checks must pass
   - Unit tests must have sufficient coverage (>80%)
   - No critical issues in SonarCloud analysis

2. **Build and Deployment**:
   - All tests must pass before deployment
   - Smoke tests must pass after deployment

## Environments

The pipeline supports the following environments:

1. **Staging** - Used for testing and validation
2. **Production** - Used for the live application

## Troubleshooting

Common issues and their solutions:

- **Failed linting/formatting checks**: Run the corresponding check locally and fix issues
- **Failed tests**: Check the test logs for specific failures
- **Deployment failures**: Verify AWS credentials and deployment configuration

## Monitoring

Pipeline status and results can be monitored in several ways:

1. GitHub Actions dashboard
2. SonarCloud dashboard for code quality metrics
3. Generated reports (available as workflow artifacts)

## Future Enhancements

Planned improvements to the CI/CD pipeline:

1. Automated performance regression testing
2. Blue/green deployment strategy
3. Feature flag integration
4. Enhanced monitoring and alerting
