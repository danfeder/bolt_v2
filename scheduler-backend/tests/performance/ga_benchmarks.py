"""Genetic Algorithm Performance Benchmarks

This module contains benchmarks specifically for the genetic algorithm components,
measuring performance across various dataset sizes and parameter combinations.
"""
import pytest
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import itertools
import pandas as pd
import matplotlib.pyplot as plt

from app.models import (
    ScheduleRequest,
    ScheduleResponse,
    WeightConfig,
    ScheduleMetadata,
    ScheduleConstraints
)
from app.scheduling.solvers.genetic.optimizer import GeneticOptimizer
from tests.utils.generators import ScheduleRequestGenerator
from tests.utils.assertions import assert_valid_schedule

from .perf_utils import (
    PerformanceTracker,
    performance_test,
    analyze_performance_results,
    visualize_performance_comparison
)


def create_test_request(
    num_classes: int, 
    num_weeks: int,
    constraints: Optional[ScheduleConstraints] = None
) -> ScheduleRequest:
    """
    Create a test schedule request with the specified parameters.
    
    Args:
        num_classes: Number of classes to include
        num_weeks: Number of weeks to schedule
        constraints: Optional constraints (uses defaults if not provided)
        
    Returns:
        ScheduleRequest for testing
    """
    start_date = datetime.now().strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=7*num_weeks)).strftime('%Y-%m-%d')
    
    if constraints is None:
        constraints = ScheduleConstraints(
            maxClassesPerDay=8,
            maxClassesPerWeek=25,
            minPeriodsPerWeek=1,
            maxConsecutiveClasses=2,
            consecutiveClassesRule="soft",
            startDate=start_date,
            endDate=end_date
        )
    
    return ScheduleRequestGenerator.create_request(
        num_classes=num_classes,
        num_weeks=num_weeks,
        constraints=constraints
    )


def get_default_weight_config() -> WeightConfig:
    """Get default weight configuration for testing."""
    return WeightConfig(
        required_periods=1.0,
        preferred_periods=0.7,
        consecutive_periods=0.5,
        daily_balance=0.3,
        weekly_balance=0.3,
        equipment_matching=0.8,
        instructor_availability=1.0,
        grade_mixing=0.4
    )


@performance_test(save_results=True)
def run_optimizer_benchmark(
    request: ScheduleRequest,
    weights: WeightConfig = None,
    population_size: int = 100,
    mutation_rate: float = 0.1,
    crossover_rate: float = 0.8,
    max_generations: int = 100,
    convergence_threshold: float = 0.01,
    use_adaptive_control: bool = True,
    parallel_fitness: bool = True,
    max_workers: int = None,
    time_limit_seconds: int = 30
) -> ScheduleResponse:
    """
    Run a benchmark test on the genetic optimizer.
    
    Args:
        request: Schedule request to optimize
        weights: Optional weight configuration
        population_size: Size of the population
        mutation_rate: Probability of mutation for each gene
        crossover_rate: Probability of crossover between chromosomes
        max_generations: Maximum number of generations to evolve
        convergence_threshold: Minimum improvement required to continue
        use_adaptive_control: Whether to use adaptive parameter control
        parallel_fitness: Whether to use parallel fitness evaluation
        max_workers: Maximum number of worker processes (None for auto)
        time_limit_seconds: Maximum time to spend optimizing
        
    Returns:
        ScheduleResponse from the optimizer
    """
    if weights is None:
        weights = get_default_weight_config()
    
    optimizer = GeneticOptimizer(
        population_size=population_size,
        mutation_rate=mutation_rate,
        crossover_rate=crossover_rate,
        max_generations=max_generations,
        convergence_threshold=convergence_threshold,
        use_adaptive_control=use_adaptive_control,
        parallel_fitness=parallel_fitness,
        max_workers=max_workers
    )
    
    response = optimizer.optimize(request, weights, time_limit_seconds)
    return response


def benchmark_dataset_scaling(save_results: bool = True) -> Dict[str, Any]:
    """
    Benchmark how the optimizer scales with different dataset sizes.
    
    Args:
        save_results: Whether to save the results to disk
        
    Returns:
        Dictionary of benchmark results
    """
    tracker = PerformanceTracker("dataset_scaling", save_results)
    tracker.start()
    
    class_counts = [5, 10, 15, 20, 25, 30, 40, 50]
    results = []
    
    for num_classes in class_counts:
        print(f"\nBenchmarking dataset with {num_classes} classes...")
        request = create_test_request(num_classes, num_weeks=2)
        
        try:
            response = run_optimizer_benchmark(
                request=request,
                population_size=50,  # Smaller population for quicker tests
                max_generations=50,
                time_limit_seconds=60
            )
            
            # Get embedded performance metrics from the decorator
            perf_metrics = getattr(response, "_performance_metrics", {})
            
            # Record specific metrics
            result = {
                "num_classes": num_classes,
                "duration_ms": response.metadata.duration_ms,
                "score": response.metadata.score,
                "solutions_found": response.metadata.solutions_found,
                "peak_memory_mb": perf_metrics.get("peak_memory", 0),
                "avg_cpu_percent": perf_metrics.get("avg_cpu_percent", 0)
            }
            results.append(result)
            tracker.record_solution_metric(result)
            
        except Exception as e:
            print(f"Error benchmarking {num_classes} classes: {e}")
    
    tracker.stop()
    return {"class_counts": class_counts, "results": results}


def benchmark_parameter_sensitivity(save_results: bool = True) -> Dict[str, Any]:
    """
    Benchmark how different parameter combinations affect performance.
    
    Args:
        save_results: Whether to save the results to disk
        
    Returns:
        Dictionary of benchmark results
    """
    tracker = PerformanceTracker("parameter_sensitivity", save_results)
    tracker.start()
    
    # Create a medium-sized test request
    request = create_test_request(num_classes=20, num_weeks=2)
    
    # Parameter grid to test
    param_grid = {
        "population_size": [50, 100, 200],
        "mutation_rate": [0.05, 0.1, 0.2],
        "crossover_rate": [0.7, 0.8, 0.9],
        "use_adaptive_control": [False, True],
        "parallel_fitness": [False, True]
    }
    
    # Generate parameter combinations (limit total combinations to manage test time)
    all_keys = list(param_grid.keys())
    all_values = list(param_grid.values())
    all_combinations = list(itertools.product(*all_values))
    
    # Use a subset of combinations to keep test duration reasonable
    # Every 7th combination to get ~20-30 test cases
    combinations_subset = all_combinations[::7]
    
    results = []
    
    for combo in combinations_subset:
        params = dict(zip(all_keys, combo))
        param_str = ", ".join([f"{k}={v}" for k, v in params.items()])
        print(f"\nBenchmarking parameters: {param_str}")
        
        try:
            response = run_optimizer_benchmark(
                request=request,
                **params,
                time_limit_seconds=45  # Limit time to keep overall benchmark reasonable
            )
            
            # Get embedded performance metrics from the decorator
            perf_metrics = getattr(response, "_performance_metrics", {})
            
            # Record results
            result = {
                **params,
                "duration_ms": response.metadata.duration_ms,
                "score": response.metadata.score,
                "solutions_found": response.metadata.solutions_found,
                "peak_memory_mb": perf_metrics.get("peak_memory", 0),
                "avg_cpu_percent": perf_metrics.get("avg_cpu_percent", 0)
            }
            results.append(result)
            tracker.record_solution_metric(result)
            
        except Exception as e:
            print(f"Error benchmarking parameters {param_str}: {e}")
    
    tracker.stop()
    return {"param_combinations": combinations_subset, "results": results}


def benchmark_parallel_scaling(save_results: bool = True) -> Dict[str, Any]:
    """
    Benchmark how performance scales with different worker counts.
    
    Args:
        save_results: Whether to save the results to disk
        
    Returns:
        Dictionary of benchmark results
    """
    tracker = PerformanceTracker("parallel_scaling", save_results)
    tracker.start()
    
    # Create a large test request to make parallelization meaningful
    request = create_test_request(num_classes=40, num_weeks=2)
    
    # Test with different worker counts
    worker_counts = [1, 2, 4, 8, None]  # None = automatic based on CPU count
    results = []
    
    for workers in worker_counts:
        worker_label = "auto" if workers is None else workers
        print(f"\nBenchmarking with {worker_label} workers...")
        
        try:
            response = run_optimizer_benchmark(
                request=request,
                population_size=100,
                parallel_fitness=True,
                max_workers=workers,
                time_limit_seconds=60
            )
            
            # Get embedded performance metrics from the decorator
            perf_metrics = getattr(response, "_performance_metrics", {})
            
            # Record results
            result = {
                "workers": worker_label,
                "duration_ms": response.metadata.duration_ms,
                "score": response.metadata.score,
                "peak_memory_mb": perf_metrics.get("peak_memory", 0),
                "avg_cpu_percent": perf_metrics.get("avg_cpu_percent", 0)
            }
            results.append(result)
            tracker.record_solution_metric(result)
            
        except Exception as e:
            print(f"Error benchmarking with {worker_label} workers: {e}")
    
    tracker.stop()
    return {"worker_counts": worker_counts, "results": results}


def run_all_benchmarks():
    """Run all benchmarks and generate summary report."""
    print("\n=== Running Genetic Algorithm Performance Benchmarks ===\n")
    
    print("\n--- Dataset Scaling Benchmark ---")
    dataset_results = benchmark_dataset_scaling()
    
    print("\n--- Parameter Sensitivity Benchmark ---")
    param_results = benchmark_parameter_sensitivity()
    
    print("\n--- Parallel Scaling Benchmark ---")
    parallel_results = benchmark_parallel_scaling()
    
    # Generate summary report
    report_path = Path("perf_results/ga_benchmark_summary.md")
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w') as f:
        f.write("# Genetic Algorithm Performance Benchmark Summary\n\n")
        f.write(f"Benchmark run on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Dataset scaling summary
        f.write("## Dataset Scaling Results\n\n")
        f.write("| Classes | Duration (ms) | Score | Solutions Found | Peak Memory (MB) | Avg CPU (%) |\n")
        f.write("|---------|--------------|-------|-----------------|-----------------|------------|\n")
        for result in dataset_results.get("results", []):
            f.write(f"| {result.get('num_classes')} | {result.get('duration_ms')} | {result.get('score', 0):.2f} | {result.get('solutions_found')} | {result.get('peak_memory_mb', 0):.1f} | {result.get('avg_cpu_percent', 0):.1f} |\n")
        
        # Parameter sensitivity summary (showing top 5 by score)
        f.write("\n## Top 5 Parameter Combinations by Score\n\n")
        param_results_list = param_results.get("results", [])
        param_results_list.sort(key=lambda x: x.get('score', 0), reverse=True)
        top_results = param_results_list[:5]
        
        f.write("| Population | Mutation | Crossover | Adaptive | Parallel | Duration (ms) | Score | Memory (MB) |\n")
        f.write("|------------|----------|-----------|----------|----------|--------------|-------|------------|\n")
        for result in top_results:
            f.write(f"| {result.get('population_size')} | {result.get('mutation_rate')} | {result.get('crossover_rate')} | {result.get('use_adaptive_control')} | {result.get('parallel_fitness')} | {result.get('duration_ms')} | {result.get('score', 0):.2f} | {result.get('peak_memory_mb', 0):.1f} |\n")
        
        # Parallel scaling summary
        f.write("\n## Parallel Scaling Results\n\n")
        f.write("| Workers | Duration (ms) | Score | Peak Memory (MB) | Avg CPU (%) |\n")
        f.write("|---------|--------------|-------|-----------------|------------|\n")
        for result in parallel_results.get("results", []):
            f.write(f"| {result.get('workers')} | {result.get('duration_ms')} | {result.get('score', 0):.2f} | {result.get('peak_memory_mb', 0):.1f} | {result.get('avg_cpu_percent', 0):.1f} |\n")
    
    print(f"\nBenchmark summary report generated at: {report_path}")


if __name__ == "__main__":
    run_all_benchmarks()
