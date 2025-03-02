# Development Environment Guide

This document provides detailed instructions for setting up and maintaining the development environment for the Gym Rotation Scheduler backend.

## Environment Requirements

### Core Requirements
- **Python 3.11** (specifically 3.11.x - required for OR-Tools compatibility)
- **Docker** (optional, for containerized development)
- **Git** (for version control)
- **Homebrew** (recommended for macOS users)

### Operating System Support
- **macOS**: Fully supported (primary development environment)
- **Linux**: Supported (Ubuntu 20.04+ or equivalent)
- **Windows**: Supported with WSL2 (Windows Subsystem for Linux)

## Setup Options

### Option 1: Local Development (Recommended for Daily Work)

1. **Install Python 3.11**

   **macOS (with Homebrew):**
   ```bash
   brew install python@3.11
   ```

   **Ubuntu/Debian:**
   ```bash
   sudo apt update
   sudo apt install software-properties-common
   sudo add-apt-repository ppa:deadsnakes/ppa
   sudo apt install python3.11 python3.11-venv python3.11-dev
   ```

   **Windows (with WSL2):**
   Follow Ubuntu instructions within your WSL2 environment.

2. **Create Virtual Environment**

   ```bash
   # Navigate to project directory
   cd scheduler-backend
   
   # Create virtual environment using Python 3.11
   # macOS:
   /opt/homebrew/bin/python3.11 -m venv venv
   
   # Linux/WSL:
   python3.11 -m venv venv
   
   # Activate virtual environment
   source venv/bin/activate
   ```

3. **Install Dependencies**

   ```bash
   # Make sure venv is activated
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Verify Setup**

   ```bash
   # Check Python version (should be 3.11.x)
   python --version
   
   # Verify OR-Tools installation
   python -c "from ortools.sat.python import cp_model; print('OR-Tools installed successfully')"
   ```

### Option 2: Containerized Development (Recommended for Consistent Testing)

1. **Install Docker**

   Follow instructions at [docker.com](https://docs.docker.com/get-docker/) for your platform.

2. **Build and Run Container**

   ```bash
   # Navigate to project directory
   cd scheduler-backend
   
   # Build Docker image
   docker build -t scheduler-backend .
   
   # Run container (mapping port 3001)
   docker run -p 3001:3001 -v $(pwd)/app:/app/app scheduler-backend
   ```

## Environment Management

### Dependency Management

When adding new dependencies:

1. **Add to requirements.txt**
   
   ```bash
   # Activate virtual environment
   source venv/bin/activate
   
   # Install new package with specific version
   pip install some-package==1.2.3
   
   # Update requirements.txt
   pip freeze > requirements.txt.new
   
   # Manually review and merge with existing requirements.txt
   # This manual step ensures we don't accidentally change versions of existing packages
   ```

2. **Update Documentation**
   
   If the new dependency requires additional setup, update this documentation.

### Environment Verification Script

We provide a script to verify your environment is correctly set up:

```bash
# Activate virtual environment
source venv/bin/activate

# Run verification script
python -m scripts.verify_environment
```

## Common Issues and Solutions

### OR-Tools Installation Problems

**Issue**: OR-Tools fails to install or import
**Solution**: 
- Ensure you're using Python 3.11.x exactly
- Try reinstalling with: `pip install --force-reinstall ortools==9.3.10497`

### Module Not Found Errors

**Issue**: Python reports missing modules
**Solution**:
- Ensure virtual environment is activated
- Reinstall all dependencies: `pip install -r requirements.txt`

### Docker Container Errors

**Issue**: Docker container fails to start
**Solution**:
- Check Docker logs: `docker logs [container_id]`
- Verify port 3001 is not in use: `lsof -i :3001`

## CI/CD Environment

Our CI/CD pipeline uses the same Docker container as defined in the Dockerfile. This ensures consistency between development and deployment environments.

### GitHub Actions Configuration

The GitHub Actions workflow uses the following environment:
- Python 3.11
- Ubuntu Latest
- Docker for containerized tests

## Performance Considerations

- OR-Tools performance is heavily dependent on CPU rather than GPU
- For large scheduling problems, ensure at least 4GB RAM is available
- Docker containers may have resource limitations - adjust as needed 