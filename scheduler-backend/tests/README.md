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

# Test Coverage Improvement Plan

## Current Coverage Status

Based on the latest coverage analysis (March 3, 2025), we have significantly improved test coverage across multiple modules:

1. **meta_optimizer.py**: 93% coverage (Improved from 19%)
2. **optimizer.py**: 100% coverage (Improved from 35%)
3. **parallel.py**: 93% coverage (Improved from 27%)
4. **visualizations.py**: 80% coverage (Improved from 6%)
5. **teacher_workload.py**: 82% coverage (Improved from 10%)

All tests are now passing and the codebase maintains high test coverage across all critical modules. The significant improvements in test coverage have been achieved through:

1. Comprehensive mocking strategies for complex components
2. Better test fixtures and setup
3. More accurate simulation of actual usage patterns
4. Improved error handling in tests

## Approach for Improving Coverage

### 1. MetaOptimizer Module (meta_optimizer.py)

The MetaOptimizer is responsible for tuning weights in the scheduling system. Key functions to test:

- **WeightChromosome class**: Test serialization and conversion methods
- **MetaObjectiveCalculator**: Test evaluation of weight configurations
- **MetaOptimizer**: Test initialization, population generation, evaluation, parent selection, crossover, mutation, and optimization workflow

**Test Plan**:
- Create test fixtures for ScheduleRequest and SolverConfig
- Test WeightChromosome initialization and conversion to WeightConfig
- Test MetaObjectiveCalculator's evaluation functions with mocked solver
- Test MetaOptimizer's initialization with various parameters
- Test population initialization and evaluation
- Test parent selection logic
- Test crossover and mutation operations
- Test the complete optimization workflow with controlled randomness

### 2. GeneticOptimizer Module (optimizer.py)

The GeneticOptimizer manages the genetic algorithm optimization process. Key functions to test:

- **Initialization with various parameters**
- **Time limit handling**
- **Optimization process with and without adaptation**
- **Result conversion and metadata generation**

**Test Plan**:
- Test initialization with different parameter combinations
- Test the optimization process with a simplified problem
- Test time limit handling and early stopping
- Test adaptation integration
- Test result generation and metadata collection
- Test parallelization behavior

### 3. Parallel Processing Module (parallel.py)

The parallel.py module provides utilities for parallel processing in the genetic algorithm. Key functions to test:

- **Worker count determination**
- **Parallel mapping with exception handling**
- **Fallback to sequential processing**
- **Test mode behavior**

**Test Plan**:
- Test worker count determination with different CPU configurations
- Test parallel mapping with successful and failing functions
- Test exception handling and fallback mechanisms
- Test behavior in test mode

### 4. Visualization Module (visualizations.py) 

The Visualization module provides important insights into the genetic algorithm's operation through various visualizations. Key functions that have been tested:

- **ChromosomeEncoder**: Tests for converting chromosomes to assignment and distance matrices
- **PopulationVisualizer**: Tests for all visualization methods including diversity, fitness landscape, population evolution, chromosome comparison, and individual chromosome visualization

**Completed Testing**:
- Created test fixtures with real ScheduleChromosome, Gene, and PopulationManager instances
- Added tests for empty chromosome handling to prevent ZeroDivisionError
- Properly mocked matplotlib's savefig method to avoid actual file operations
- Validated assignment matrix and distance matrix calculations
- Tested all visualization methods with real data
- Achieved 80% code coverage (meeting our target)

**March 2, 2025 Improvements**:
- Fixed failing tests in the visualization module:
  - Corrected `test_visualize_fitness_landscape_empty` to verify `ax.text()` is called instead of `plt.text()`
  - Fixed `test_visualize_population_evolution_actual` to properly mock matplotlib axes and verify `ax1.plot()` is called
  - Updated `test_visualize_population_evolution_empty` to check for `ax.text()` instead of `plt.text()`
- Ensured tests reflect actual implementation details (axes vs. plt methods)
- Added appropriate error message validation
- Verified proper parameter passing and return values

**Key Improvements**:
- Replaced all mock-based tests with real object tests
- Added appropriate fixtures with time_slot property in Gene objects
- Fixed direct fixture calls to comply with pytest patterns
- Added robust handling of edge cases

## Implementation Strategy

1. **Start with simple unit tests** for each class and method
2. **Use mocking** extensively to isolate components
3. **Create test fixtures** for common test data
4. **Use parametrized tests** for comprehensive coverage
5. **Implement integration tests** for key workflows

## Prioritization

1. **optimizer.py** (highest priority - core functionality)
2. **parallel.py** (critical for performance)
3. **meta_optimizer.py** (important for weight tuning)
4. **visualizations.py** (useful but less critical)

## Target Coverage

Our goal is to increase the coverage of these modules to at least:

- **optimizer.py**: 80%
- **parallel.py**: 80%
- **meta_optimizer.py**: 75%
- **visualizations.py**: 80% 

This will bring our overall genetic algorithm module coverage above the 75% target.
