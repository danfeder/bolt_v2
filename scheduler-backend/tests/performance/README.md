# Performance Testing Framework

This directory contains the performance testing framework for the Gym Class Rotation Scheduler, focusing on the genetic algorithm implementation.

## Overview

The performance testing framework provides tools to:

1. Measure execution time, memory usage, and CPU utilization
2. Benchmark different dataset sizes and parameter configurations
3. Detect performance regressions
4. Visualize performance metrics

## Components

### Core Utilities (`perf_utils.py`)

The `PerformanceTracker` class provides mechanisms to measure and record performance metrics during test execution. It also includes utilities for analyzing and visualizing results.

Key features:
- Measuring execution time, memory usage, and CPU utilization
- Recording solution quality metrics
- Saving results to disk for later analysis
- Performance test decorator for easy instrumentation

### Benchmark Tests (`ga_benchmarks.py`)

Comprehensive benchmark tests for different aspects of the genetic algorithm:

1. **Dataset Scaling**: Tests how performance scales with different dataset sizes
2. **Parameter Sensitivity**: Analyzes the impact of different parameter combinations
3. **Parallel Processing**: Evaluates scaling with different worker counts

### Regression Tests (`regression_tests.py`)

Tests that compare current performance against baseline metrics to detect regressions:

- Compares execution time, memory usage, and solution quality
- Fails CI/CD pipeline if performance degrades beyond tolerance threshold
- Includes utilities for updating baselines

## Usage

### Running Benchmarks

```bash
# Run all benchmarks
python run_ga_benchmarks.py

# Run specific benchmark types
python run_ga_benchmarks.py --dataset
python run_ga_benchmarks.py --parameters
python run_ga_benchmarks.py --parallel

# Run quick version of benchmarks (fewer iterations)
python run_ga_benchmarks.py --quick
```

### Managing Baselines

```bash
# List all existing baselines
python update_performance_baselines.py --list

# Update standard test baseline
python update_performance_baselines.py --create-standard
```

### Running Regression Tests

```bash
# Run all performance regression tests
pytest tests/performance/regression_tests.py -v
```

## Results

Benchmark results are saved in the `perf_results` directory in JSON format. Visualizations are saved in `perf_results/visualizations`.

See `examples/benchmark_report_example.md` for an example of a benchmark report.

## Continuous Integration

Performance tests are automatically run in CI/CD pipeline for:
- Pushes to main/develop branches that modify genetic algorithm code
- Pull requests to main/develop that modify genetic algorithm code

The pipeline will flag performance regressions beyond the specified tolerance threshold.

## Extending the Framework

To add new performance tests:
1. Use the `PerformanceTracker` class to measure performance metrics
2. Use the `@performance_test` decorator for automatic instrumentation
3. Add visualization code for new metrics

To adjust regression detection sensitivity:
- Modify the tolerance parameter in `compare_with_baseline()` function
- Update baseline values as needed
