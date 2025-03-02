"""Utilities for performance testing of genetic algorithm scheduling."""
import time
import psutil
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Callable, Optional
import numpy as np
import platform
from functools import wraps
from pathlib import Path

# Set up base directory for performance results
PERF_RESULTS_DIR = Path("perf_results")


class PerformanceTracker:
    """
    Tracks performance metrics for benchmarking.
    
    This class provides tools to measure and record:
    - Execution time
    - Memory usage
    - CPU utilization
    - Solution quality metrics
    """
    
    def __init__(self, test_name: str, save_results: bool = True):
        """
        Initialize performance tracker.
        
        Args:
            test_name: Identifier for this test run
            save_results: Whether to save results to disk
        """
        self.test_name = test_name
        self.save_results = save_results
        self.start_time = None
        self.start_memory = None
        self.metrics = {
            "test_name": test_name,
            "timestamps": [],
            "memory_usage": [],
            "cpu_percent": [],
            "solution_metrics": [],
            "system_info": self._get_system_info(),
            "parameters": {},
        }
        
        # Create results directory if it doesn't exist
        if save_results:
            PERF_RESULTS_DIR.mkdir(exist_ok=True)
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Collect system information for context."""
        return {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(logical=False),
            "logical_cpu_count": psutil.cpu_count(logical=True),
            "total_memory": psutil.virtual_memory().total / (1024 * 1024),  # MB
            "timestamp": datetime.now().isoformat(),
        }
    
    def start(self) -> None:
        """Start performance tracking."""
        self.start_time = time.time()
        self.start_memory = self._get_memory_usage()
        self.metrics["start_time"] = datetime.now().isoformat()
        self._record_point()
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)  # Convert bytes to MB
    
    def _record_point(self) -> None:
        """Record a single measurement point."""
        elapsed = time.time() - self.start_time if self.start_time else 0
        memory = self._get_memory_usage()
        cpu = psutil.cpu_percent(interval=None)
        
        self.metrics["timestamps"].append(elapsed)
        self.metrics["memory_usage"].append(memory)
        self.metrics["cpu_percent"].append(cpu)
    
    def record_solution_metric(self, metrics: Dict[str, Any]) -> None:
        """
        Record metrics about a specific solution.
        
        Args:
            metrics: Dictionary of solution metrics
        """
        metrics["elapsed_time"] = time.time() - self.start_time if self.start_time else 0
        self.metrics["solution_metrics"].append(metrics)
        self._record_point()
    
    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        """
        Record test parameters for context.
        
        Args:
            parameters: Dictionary of test parameters
        """
        self.metrics["parameters"] = parameters
    
    def stop(self) -> Dict[str, Any]:
        """
        Stop performance tracking and return metrics.
        
        Returns:
            Dictionary of collected metrics
        """
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        # Record final point
        self._record_point()
        
        # Calculate summary statistics
        self.metrics["end_time"] = datetime.now().isoformat()
        self.metrics["total_duration"] = end_time - self.start_time if self.start_time else 0
        self.metrics["peak_memory"] = max(self.metrics["memory_usage"])
        self.metrics["memory_increase"] = end_memory - self.start_memory if self.start_memory else 0
        self.metrics["avg_cpu_percent"] = sum(self.metrics["cpu_percent"]) / len(self.metrics["cpu_percent"]) if self.metrics["cpu_percent"] else 0
        
        # Save results if requested
        if self.save_results:
            self._save_results()
        
        return self.metrics
    
    def _save_results(self) -> None:
        """Save performance results to disk."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.test_name}_{timestamp}.json"
        filepath = PERF_RESULTS_DIR / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        print(f"Performance results saved to {filepath}")


def performance_test(save_results: bool = True):
    """
    Decorator for performance testing a function.
    
    Args:
        save_results: Whether to save results to disk
    
    Returns:
        Decorated function that tracks performance
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create test name from function name
            test_name = f"perf_{func.__name__}"
            
            # Initialize tracker
            tracker = PerformanceTracker(test_name, save_results)
            
            # Record parameters
            params = {**kwargs}
            tracker.set_parameters(params)
            
            # Start tracking
            tracker.start()
            
            # Call the function
            result = func(*args, **kwargs)
            
            # Record result metrics if available
            if hasattr(result, "metadata") and result.metadata:
                solution_metrics = {
                    "score": getattr(result.metadata, "score", None),
                    "duration_ms": getattr(result.metadata, "duration_ms", None),
                    "solutions_found": getattr(result.metadata, "solutions_found", None),
                }
                tracker.record_solution_metric(solution_metrics)
            
            # Stop tracking
            metrics = tracker.stop()
            
            # Add metrics to result if it's a dictionary or similar
            if hasattr(result, "__dict__"):
                result._performance_metrics = metrics
            
            return result
        return wrapper
    return decorator


def analyze_performance_results(pattern: str = "*") -> pd.DataFrame:
    """
    Analyze performance results from disk.
    
    Args:
        pattern: File pattern to match result files
        
    Returns:
        DataFrame of performance results
    """
    result_files = list(PERF_RESULTS_DIR.glob(f"{pattern}.json"))
    if not result_files:
        print(f"No performance results found matching pattern '{pattern}'")
        return pd.DataFrame()
    
    results = []
    for file in result_files:
        with open(file, 'r') as f:
            results.append(json.load(f))
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(results)
    return df


def visualize_performance_comparison(df: pd.DataFrame, x_column: str, y_column: str, 
                                    group_by: str = None, title: str = None,
                                    save_path: Optional[str] = None) -> None:
    """
    Create visualization comparing performance metrics.
    
    Args:
        df: DataFrame of performance results
        x_column: Column to use for x-axis
        y_column: Column to use for y-axis
        group_by: Column to group results by
        title: Plot title
        save_path: Path to save visualization to (optional)
    """
    plt.figure(figsize=(10, 6))
    
    if group_by:
        for name, group in df.groupby(group_by):
            plt.plot(group[x_column], group[y_column], marker='o', linestyle='-', label=name)
        plt.legend()
    else:
        plt.plot(df[x_column], df[y_column], marker='o', linestyle='-')
    
    plt.xlabel(x_column)
    plt.ylabel(y_column)
    plt.title(title or f"{y_column} vs {x_column}")
    plt.grid(True)
    
    if save_path:
        plt.savefig(save_path)
    
    plt.show()
