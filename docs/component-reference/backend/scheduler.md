# Gym Class Rotation Scheduler - Solver Architecture

## Overview

The scheduler now uses a unified solver architecture that combines both production-ready and experimental features. Features can be enabled or disabled through configuration, allowing for flexible deployment and testing of new optimizations.

## Components

### UnifiedSolver

The `UnifiedSolver` class (`solver.py`) is the main implementation that:
- Handles all scheduling operations
- Supports metrics tracking
- Enables solution comparison
- Allows experimental features to be toggled

### Configuration

Configuration is managed through the `SolverConfig` class in `config.py`. It provides:

1. **Feature Flags**
   - `ENABLE_METRICS`: Enable/disable performance metrics tracking
   - `ENABLE_SOLUTION_COMPARISON`: Enable/disable solution comparison functionality
   - `ENABLE_EXPERIMENTAL_DISTRIBUTION`: Enable/disable experimental distribution optimization

2. **Optimization Parameters**
   - `TIME_LIMIT_SECONDS`: Maximum solving time (default: 300 seconds)
   - `OPTIMIZATION_TOLERANCE`: Optimization convergence tolerance (default: 0.01)

3. **Weights**
   - Configurable weights for different optimization objectives
   - Defaults provided but can be modified at runtime

## Usage

### Basic Usage

```python
from app.scheduling.solvers import UnifiedSolver, config

# Create solver instance
solver = UnifiedSolver()

# Create schedule
response = solver.create_schedule(request)
```

### Configuration

#### Environment Variables

The solver can be configured through environment variables:
```bash
ENABLE_METRICS=1
ENABLE_SOLUTION_COMPARISON=1
ENABLE_EXPERIMENTAL_DISTRIBUTION=0
SOLVER_TIME_LIMIT=300
OPTIMIZATION_TOLERANCE=0.01
```

#### Runtime Configuration

Weights can be modified at runtime:
```python
from app.scheduling.solvers import update_weights, reset_weights

# Update specific weights
update_weights({
    'final_week_compression': 4000,
    'day_usage': 2500
})

# Reset to defaults if needed
reset_weights()
```

## Feature Details

### Metrics Tracking

When enabled (`ENABLE_METRICS=1`), tracks:
- Solving duration
- Solution score
- Number of solutions found
- Optimization gap
- Distribution metrics

### Solution Comparison

When enabled (`ENABLE_SOLUTION_COMPARISON=1`), provides:
- Detailed comparison between solutions
- Assignment differences
- Metric differences including scores and distribution changes

### Experimental Distribution

When enabled (`ENABLE_EXPERIMENTAL_DISTRIBUTION=1`):
- Adds distribution optimization to the solver
- Attempts to balance class distribution across time periods

## Legacy Code

Previous solver implementations (`stable.py` and `dev.py`) have been archived in the `legacy/` directory for reference.
