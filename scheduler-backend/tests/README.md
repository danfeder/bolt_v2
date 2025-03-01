# Scheduler Backend Testing Infrastructure

## Overview

This testing infrastructure provides comprehensive test coverage for the scheduler backend, including:
- Core constraint validation
- Distribution optimization verification
- Performance benchmarking
- Integration testing

## Directory Structure

```
tests/
├── conftest.py           # Shared pytest fixtures
├── utils/
│   ├── generators.py     # Test data generation utilities
│   ├── assertions.py     # Custom test assertions
│   └── fixtures.py       # Common test fixtures
├── unit/
│   ├── test_constraints.py   # Core constraint tests
│   ├── test_distribution.py  # Distribution tests
│   └── test_optimization.py  # Optimization tests
├── integration/
│   └── test_scheduler.py     # End-to-end tests
└── performance/
    └── test_benchmarks.py    # Performance tests
```

## Test Categories

### Unit Tests

1. Constraint Tests (`test_constraints.py`)
   - Single assignment validation
   - Overlap prevention
   - Required period satisfaction
   - Teacher availability respect
   - Class limit enforcement
   - Consecutive class handling

2. Distribution Tests (`test_distribution.py`)
   - Weekly variance calculations
   - Period spread metrics
   - Teacher workload balance
   - Multi-objective weights

### Integration Tests (`test_scheduler.py`)
- End-to-end schedule generation
- Complex constraint interactions
- Edge cases
- Error handling
- Optimization priority verification

### Performance Tests (`test_benchmarks.py`)
- Small dataset performance (5-10 classes)
- Medium dataset performance (20-30 classes)
- Large dataset performance (50+ classes)
- Solver convergence analysis
- Memory usage tracking

## Running Tests

### Prerequisites
- Python 3.11.* (ortools requires Python 3.11, newer versions not supported)
- pytest
- psutil (for performance tests)

### Installation
```bash
# Create virtual environment with Python 3.11
python3.11 -m venv venv
source venv/bin/activate  # On Unix/macOS
# or
.\venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Running All Tests
```bash
pytest tests/
```

### Running Specific Test Categories
```bash
# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run performance tests only
pytest tests/performance/
```

### Running Individual Test Files
```bash
# Run constraint tests
pytest tests/unit/test_constraints.py

# Run distribution tests
pytest tests/unit/test_distribution.py

# Run integration tests
pytest tests/integration/test_scheduler.py

# Run performance tests
pytest tests/performance/test_benchmarks.py
```

### Test Options
```bash
# Run tests with detailed output
pytest -v

# Run tests and show print statements
pytest -s

# Run a specific test function
pytest tests/unit/test_constraints.py::test_single_assignment

# Run tests matching a pattern
pytest -k "test_daily"
```

## Test Utilities

### Data Generators (`generators.py`)
- `TimeSlotGenerator`: Create time slot patterns
- `WeeklyScheduleGenerator`: Generate weekly schedules
- `ClassGenerator`: Create test classes
- `TeacherAvailabilityGenerator`: Generate availability patterns
- `ScheduleRequestGenerator`: Create complete schedule requests

### Assertions (`assertions.py`)
- `assert_valid_assignments`: Verify assignment completeness
- `assert_no_overlaps`: Check for scheduling conflicts
- `assert_respects_conflicts`: Validate conflict handling
- `assert_respects_teacher_availability`: Check availability constraints
- `assert_respects_required_periods`: Verify required period satisfaction
- `assert_respects_class_limits`: Validate class limits
- `assert_respects_consecutive_classes`: Check consecutive class rules
- `assert_valid_schedule`: Comprehensive schedule validation

## Performance Benchmarks

The performance tests include configurable thresholds:
- Small dataset: < 5 seconds, < 100MB memory
- Medium dataset: < 15 seconds, < 250MB memory
- Large dataset: < 30 seconds, < 500MB memory

Memory and timing metrics are logged for analysis.

## Adding New Tests

1. Choose the appropriate category (unit/integration/performance)
2. Create test file in the corresponding directory
3. Use provided utilities from `utils/`
4. Follow existing patterns for consistency
5. Include docstrings and comments
6. Verify with existing test suite

## Best Practices

1. Use generators for test data creation
2. Leverage shared fixtures from `conftest.py`
3. Include clear test descriptions
4. Test edge cases and error conditions
5. Keep performance tests realistic
6. Use appropriate assertions
7. Follow naming conventions
