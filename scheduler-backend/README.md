# Scheduler Backend

## Requirements

- Python 3.11 (required for OR-Tools compatibility)
- Homebrew (recommended for Python installation on macOS)

## Setup Instructions

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

## Development

Always ensure you're using the virtual environment when running the scheduler:

```bash
# Activate virtual environment (if not already activated)
source venv/bin/activate

# Run tests
python -m app.test_class_limits

# Run server
uvicorn app.main:app --reload
```

## Common Issues

1. OR-Tools Installation Fails:
   - Make sure you're using Python 3.11
   - Check your Python version: `python --version`
   - If using wrong version, deactivate and recreate venv with Python 3.11

2. Module Not Found Errors:
   - Ensure virtual environment is activated
   - Verify all dependencies are installed: `pip list`
   - If needed, reinstall dependencies: `pip install -r requirements.txt`
