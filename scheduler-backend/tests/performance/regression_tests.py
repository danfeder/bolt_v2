"""
Performance Regression Tests

This module contains tests that can detect performance regressions by comparing
current performance metrics against baseline values.
"""
import pytest
import json
import os
from pathlib import Path
import time
from typing import Dict, Any, Optional

from app.models import ScheduleRequest, WeightConfig
from tests.utils.generators import ScheduleRequestGenerator
from app.scheduling.solvers.genetic.optimizer import GeneticOptimizer

from .perf_utils import PerformanceTracker

# Path for storing baseline metrics
BASELINE_PATH = Path("tests/performance/baselines")


def save_baseline(name: str, metrics: Dict[str, Any]) -> None:
    """
    Save baseline metrics to disk.
    
    Args:
        name: Name of the baseline
        metrics: Dictionary of metrics to save
    """
    BASELINE_PATH.mkdir(exist_ok=True)
    
    with open(BASELINE_PATH / f"{name}.json", 'w') as f:
        json.dump(metrics, f, indent=2)


def load_baseline(name: str) -> Optional[Dict[str, Any]]:
    """
    Load baseline metrics from disk.
    
    Args:
        name: Name of the baseline
        
    Returns:
        Dictionary of baseline metrics or None if not found
    """
    baseline_file = BASELINE_PATH / f"{name}.json"
    
    if not baseline_file.exists():
        return None
    
    with open(baseline_file, 'r') as f:
        return json.load(f)


def create_standard_test_request() -> ScheduleRequest:
    """Create a standardized test request for regression testing."""
    return ScheduleRequestGenerator.create_request(
        num_classes=15,
        num_weeks=2
    )


def run_standard_optimization() -> Dict[str, Any]:
    """
    Run a standardized optimization test case.
    
    Returns:
        Dictionary of performance metrics
    """
    request = create_standard_test_request()
    weights = WeightConfig(
        required_periods=1.0,
        preferred_periods=0.7,
        consecutive_periods=0.5,
        daily_balance=0.3,
        weekly_balance=0.3,
        equipment_matching=0.8,
        instructor_availability=1.0,
        grade_mixing=0.4
    )
    
    # Set up performance tracking
    tracker = PerformanceTracker("standard_test", save_results=False)
    tracker.start()
    
    # Configure standard optimizer
    optimizer = GeneticOptimizer(
        population_size=100,
        mutation_rate=0.1,
        crossover_rate=0.8,
        max_generations=50,
        convergence_threshold=0.01,
        use_adaptive_control=True,
        parallel_fitness=True
    )
    
    # Run optimization with time limit
    response = optimizer.optimize(request, weights, time_limit_seconds=30)
    
    # Record solution metrics
    solution_metrics = {
        "score": response.metadata.score,
        "duration_ms": response.metadata.duration_ms,
        "solutions_found": response.metadata.solutions_found
    }
    tracker.record_solution_metric(solution_metrics)
    
    # Stop tracking and return metrics
    metrics = tracker.stop()
    return metrics


def compare_with_baseline(current: Dict[str, Any], baseline: Dict[str, Any], 
                         tolerance: float = 0.15) -> Dict[str, Any]:
    """
    Compare current metrics with baseline values.
    
    Args:
        current: Current metrics
        baseline: Baseline metrics
        tolerance: Fractional tolerance for regression (e.g., 0.15 = 15%)
        
    Returns:
        Dictionary of comparison results
    """
    results = {
        "exceeded_tolerance": False,
        "metrics": {}
    }
    
    # Compare key metrics
    for key, baseline_value in baseline.items():
        if key not in current:
            continue
            
        current_value = current[key]
        
        # Skip non-numeric values
        if not isinstance(baseline_value, (int, float)) or not isinstance(current_value, (int, float)):
            continue
            
        # Calculate percent change
        if baseline_value != 0:
            percent_change = (current_value - baseline_value) / baseline_value
        else:
            percent_change = float('inf') if current_value > 0 else 0
            
        # Check if change exceeds tolerance (only for metrics where higher is worse)
        is_regression = False
        if key in ["total_duration", "duration_ms", "peak_memory", "memory_increase"]:
            is_regression = percent_change > tolerance
        elif key in ["score"]:
            # For score, lower is worse (negative change beyond tolerance)
            is_regression = percent_change < -tolerance
            
        results["metrics"][key] = {
            "baseline": baseline_value,
            "current": current_value,
            "percent_change": percent_change * 100,  # Convert to percentage
            "is_regression": is_regression
        }
        
        if is_regression:
            results["exceeded_tolerance"] = True
    
    return results


@pytest.mark.performance
def test_performance_against_baseline():
    """Test that performance hasn't regressed from baseline."""
    # Run standard test
    current_metrics = run_standard_optimization()
    
    # Extract key metrics for simpler comparison
    key_metrics = {
        "total_duration": current_metrics.get("total_duration", 0),
        "peak_memory": current_metrics.get("peak_memory", 0),
        "score": current_metrics.get("solution_metrics", [{}])[0].get("score", 0) 
                  if current_metrics.get("solution_metrics") else 0,
        "duration_ms": current_metrics.get("solution_metrics", [{}])[0].get("duration_ms", 0)
                        if current_metrics.get("solution_metrics") else 0,
    }
    
    # Load baseline
    baseline = load_baseline("standard_test")
    
    # If no baseline exists, create one
    if baseline is None:
        print("No baseline found. Creating new baseline.")
        save_baseline("standard_test", key_metrics)
        pytest.skip("Created new baseline, skipping comparison")
        
    # Compare with baseline
    comparison = compare_with_baseline(key_metrics, baseline)
    
    # Report results
    print("\nPerformance Comparison with Baseline:")
    for metric, result in comparison["metrics"].items():
        change_str = f"{result['percent_change']:.2f}%"
        status = "REGRESSION" if result["is_regression"] else "OK"
        print(f"{metric}: {result['current']} vs baseline {result['baseline']} ({change_str}) - {status}")
    
    # Fail if performance regressed
    assert not comparison["exceeded_tolerance"], \
        "Performance has regressed beyond tolerance threshold. See details above."


@pytest.mark.performance
def test_execution_time():
    """Test optimizer execution time is within acceptable limits."""
    # Create a small test case
    request = ScheduleRequestGenerator.create_request(num_classes=10, num_weeks=1)
    weights = WeightConfig(
        required_periods=1.0, preferred_periods=0.7, consecutive_periods=0.5,
        daily_balance=0.3, weekly_balance=0.3, equipment_matching=0.8,
        instructor_availability=1.0, grade_mixing=0.4
    )
    
    # Configure optimizer
    optimizer = GeneticOptimizer(
        population_size=50,
        max_generations=50,
        time_limit_seconds=15  # Maximum time limit
    )
    
    # Measure execution time
    start_time = time.time()
    response = optimizer.optimize(request, weights)
    execution_time = time.time() - start_time
    
    # Verify execution time is reasonable
    assert execution_time <= 15, f"Execution time ({execution_time:.2f}s) exceeds maximum (15s)"
    
    # Check that solution quality is reasonable
    assert response.metadata.score > 0.5, f"Solution score ({response.metadata.score}) is too low"


def update_baseline():
    """Command-line utility to update the performance baseline."""
    print("Running standard optimization to update baseline...")
    metrics = run_standard_optimization()
    
    # Extract key metrics
    key_metrics = {
        "total_duration": metrics.get("total_duration", 0),
        "peak_memory": metrics.get("peak_memory", 0),
        "score": metrics.get("solution_metrics", [{}])[0].get("score", 0) 
                  if metrics.get("solution_metrics") else 0,
        "duration_ms": metrics.get("solution_metrics", [{}])[0].get("duration_ms", 0)
                        if metrics.get("solution_metrics") else 0,
    }
    
    # Save as new baseline
    save_baseline("standard_test", key_metrics)
    print(f"Baseline updated with values: {key_metrics}")


if __name__ == "__main__":
    update_baseline()
