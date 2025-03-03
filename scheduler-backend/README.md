# Scheduler Backend

## Requirements

- Python 3.11 (required for OR-Tools compatibility)
- Homebrew (recommended for Python installation on macOS)
- Docker (optional, for containerized development)

## Quick Start

### Option 1: Local Development

1. Install Python 3.11 using Homebrew:
```bash
brew install python@3.11
```

2. Create and activate a virtual environment:
```bash
# Create virtual environment using Python 3.11
/opt/homebrew/bin/python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Verify your environment:
```bash
# Run environment verification script
python -m scripts.verify_environment
```

5. Run the server:
```bash
uvicorn app.main:app --reload
```

### Option 2: Docker Development

1. Build and run with Docker Compose:
```bash
# Build and start the container
docker-compose up --build

# Or run in background
docker-compose up -d
```

2. Run tests in Docker:
```bash
# Run all tests in the test container
docker-compose run scheduler-tests

# Run specific tests
docker-compose run scheduler-tests pytest -xvs tests/path/to/test.py
```

## Detailed Documentation

For comprehensive setup instructions and development guidelines, see:

- [Environment Setup Guide](ENVIRONMENT.md) - Detailed environment configuration
- [Dockerfile](Dockerfile) - Container configuration
- [Docker Compose](docker-compose.yml) - Multi-container setup

## Development

When working on the scheduler backend:

```bash
# Activate virtual environment (if not already activated)
source venv/bin/activate

# Run tests
pytest -xvs tests/

# Run server
uvicorn app.main:app --reload
```

## Constraint System

The scheduler uses an enhanced constraint system for defining and enforcing scheduling rules. The constraint system supports:

### Key Features

1. **Auto-Registration of Constraints**
   - Constraints are automatically discovered and registered
   - Factory pattern for easy constraint creation
   - Support for constraint metadata

2. **Constraint Categories**
   - Constraints are organized by category (e.g., schedule, instructor, classroom)
   - Filtering and validation by category
   - Hierarchical constraint management

3. **Constraint Compatibility**
   - Define incompatible constraints
   - Specify required dependencies between constraints
   - Automatic validation of constraint configurations

4. **Rich Validation**
   - Detailed violation reporting with context
   - Multiple severity levels (INFO, WARNING, ERROR, CRITICAL)
   - Support for relaxable constraints with adjustable enforcement

### Usage Example

```python
# Create a constraint factory
factory = get_constraint_factory()

# Register all default constraints
register_default_constraints()

# Create a constraint manager
manager = EnhancedConstraintManager(factory)

# Add constraints by category
manager.create_and_add_constraints_by_category("schedule")

# Validate assignments
is_valid, violations = manager.validate_all(assignments, context)

# Handle violations
for violation in violations:
    print(f"{violation.severity}: {violation.message}")
    if violation.context:
        print(f"Context: {violation.context}")
```

### Creating Custom Constraints

```python
class MyCustomConstraint(BaseConstraint):
    def __init__(self, name="my_custom_constraint", enabled=True):
        super().__init__(name, enabled)
        self.category = "custom"
        
    def apply(self, context):
        # Apply constraint logic
        pass
        
    def validate(self, assignments, context):
        violations = []
        # Validation logic
        if violation_detected:
            violations.append(self.create_error_violation(
                "Detailed error message",
                context={...}
            ))
        return violations
```

> **Detailed Documentation**: For comprehensive documentation on the constraint system, see the [Constraints System Documentation](/docs/component-reference/backend/constraints.md) in the project documentation.

## Common Issues

1. OR-Tools Installation Fails:
   - Make sure you're using Python 3.11
   - Check your Python version: `python --version`
   - If using wrong version, deactivate and recreate venv with Python 3.11

2. Module Not Found Errors:
   - Ensure virtual environment is activated
   - Verify all dependencies are installed: `pip list`
   - If needed, reinstall dependencies: `pip install -r requirements.txt`

3. Docker Container Errors:
   - Check Docker logs: `docker logs scheduler-backend`
   - Verify port 3001 is not in use: `lsof -i :3001`

## Environment Verification

Run our verification script to ensure your environment is properly set up:

```bash
python -m scripts.verify_environment
```

This will check:
- Python version
- Required packages
- OR-Tools functionality
- Project structure

## Testing

```bash
# Run all tests
pytest -xvs

# Run with coverage report
pytest --cov=app tests/

# Run specific test file
pytest -xvs tests/path/to/test.py

# Run tests in Docker container
docker-compose run scheduler-tests
```

## API Documentation

When running the server, access the API documentation at:
- http://localhost:3001/docs (Swagger UI)
- http://localhost:3001/redoc (ReDoc)
