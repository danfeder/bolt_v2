#!/usr/bin/env python
"""
Demonstration script for the genetic algorithm experiment framework.

This script shows how to use the experiment framework to:
1. Run experiments with different parameter combinations
2. Analyze the impact of parameters on performance
3. Visualize convergence and parameter effects
"""

import os
import sys
from pathlib import Path
import json
import time
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Add parent directory to path to import app modules
current_dir = Path(__file__).resolve().parent
scheduler_backend_dir = current_dir.parent
sys.path.insert(0, str(scheduler_backend_dir))

from app.models import ScheduleRequest, WeightConfig
from app.scheduling.solvers.genetic.experiments import (
    ExperimentManager,
    ParameterGrid,
    StatsCollector
)

def load_sample_request():
    """Load a sample schedule request for demonstration."""
    # First, check for existing sample requests in the test_data directory
    test_data_dir = Path(__file__).resolve().parent.parent / 'tests' / 'test_data'
    
    if test_data_dir.exists():
        # Look for schedule request files
        request_files = list(test_data_dir.glob('*request*.json'))
        if request_files:
            # Use the first available request file
            request_file = request_files[0]
            print(f"Using sample request file: {request_file}")
            
            with open(request_file, 'r') as f:
                request_data = json.load(f)
                return ScheduleRequest.parse_obj(request_data)
    
    # If no sample requests found, create a minimal example
    print("Creating minimal sample request")
    
    # Create a simple request with a few classes and instructors
    return ScheduleRequest(
        classes=[
            {
                "id": "class1",
                "name": "Math 101",
                "sessions": 3,
                "instructorIds": ["inst1", "inst2"],
                "groupSize": 20
            },
            {
                "id": "class2",
                "name": "Science 101",
                "sessions": 2,
                "instructorIds": ["inst2", "inst3"],
                "groupSize": 15
            },
            {
                "id": "class3",
                "name": "History 101",
                "sessions": 2,
                "instructorIds": ["inst1", "inst3"],
                "groupSize": 25
            }
        ],
        instructorAvailability={
            "inst1": ["MWF-AM", "MWF-PM"],
            "inst2": ["MWF-AM", "TR-AM"],
            "inst3": ["TR-AM", "TR-PM"]
        },
        startDate="2025-01-01",
        endDate="2025-01-07"
    )

def load_default_weights():
    """Load default weights for the fitness function."""
    return WeightConfig(
        constraint_violation=-100.0,
        instructor_preferences=2.0,
        balance_sessions=1.0,
        instructor_load=1.0
    )

def run_demo_experiments(output_dir="ga_experiment_demo"):
    """Run demonstration experiments with the genetic algorithm."""
    print("\n=== Genetic Algorithm Experiment Framework Demo ===\n")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load sample data
    request = load_sample_request()
    weights = load_default_weights()
    
    print(f"Loaded sample schedule request with {len(request.classes)} classes")
    
    # Create experiment manager
    manager = ExperimentManager(
        request=request,
        weights=weights,
        results_dir=output_dir
    )
    
    # Create parameter grid for the demo
    # Using a subset of parameters to keep the demo fast
    param_space = {
        "population_size": [50, 100],
        "mutation_rate": [0.05, 0.1, 0.2],
        "crossover_rate": [0.7, 0.9],
        "use_adaptive_control": [True, False]
    }
    param_grid = ParameterGrid(param_space)
    
    # Run experiments (with shorter time limit for demo)
    print("\nRunning experiments (this may take a few minutes)...\n")
    start_time = time.time()
    results = manager.run_experiments(
        param_grid=param_grid,
        time_limit_seconds=60,  # Short time limit for demonstration
        max_experiments=8,      # Limit number of experiments for the demo
        collect_generation_stats=True
    )
    
    # Print summary
    duration = time.time() - start_time
    print(f"\nExperiments completed in {duration:.1f} seconds")
    print(f"Total experiments: {len(results)}")
    
    # Print best result
    best_result = manager.get_best_result()
    if best_result:
        print("\nBest Result:")
        print(f"Fitness: {best_result.fitness}")
        print(f"Duration: {best_result.duration_ms}ms")
        print(f"Generations: {best_result.generations}")
        
        print("\nParameters:")
        for key, value in best_result.parameters.items():
            print(f"  {key}: {value}")
    
    # Analyze results
    print("\n=== Parameter Analysis ===\n")
    
    # Convert results to DataFrame for analysis
    df = manager.get_results_dataframe()
    
    # Basic statistics
    print("\nBasic statistics:")
    print(df.describe())
    
    # Analyze each parameter
    for param in ["population_size", "mutation_rate", "crossover_rate", "use_adaptive_control"]:
        if param in df.columns:
            print(f"\nAnalyzing parameter: {param}")
            analysis = manager.analyze_parameters(param, show_plot=False)
            print(analysis)
    
    # Plot convergence for the best experiments
    print("\n=== Convergence Analysis ===\n")
    
    if df.empty:
        print("No results available for convergence analysis")
    else:
        # Get top 3 experiments by fitness
        best_indices = df.sort_values('fitness', ascending=False).head(3).index.tolist()
        
        print(f"Plotting convergence for top {len(best_indices)} experiments")
        manager.plot_convergence(experiment_indices=best_indices, show_plot=False)
        
        print(f"Plots saved to {output_dir} directory")
    
    print("\n=== Demo Complete ===\n")
    print(f"Results and plots saved to '{output_dir}' directory")
    print("You can analyze the results further using the experiment framework API")

if __name__ == "__main__":
    run_demo_experiments()
