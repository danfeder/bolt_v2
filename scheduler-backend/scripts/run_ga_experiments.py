#!/usr/bin/env python
"""
Command-line script for running genetic algorithm parameter tuning experiments.

This script provides a convenient way to run experiments with different parameter
combinations and analyze the results.
"""

import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
from typing import Dict, Any, List, Optional

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent.parent))

from app.models import ScheduleRequest, WeightConfig
from app.scheduling.solvers.genetic.experiments import (
    ExperimentManager,
    ParameterGrid,
    recommended_parameter_grid
)

def load_request_from_file(file_path: str) -> ScheduleRequest:
    """
    Load schedule request from JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        ScheduleRequest object
    """
    with open(file_path, 'r') as f:
        request_data = json.load(f)
        
    return ScheduleRequest.parse_obj(request_data)

def load_weights_from_file(file_path: str) -> WeightConfig:
    """
    Load weights from JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        WeightConfig object
    """
    with open(file_path, 'r') as f:
        weights_data = json.load(f)
        
    return WeightConfig.parse_obj(weights_data)

def load_param_grid_from_file(file_path: str) -> ParameterGrid:
    """
    Load parameter grid from JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        ParameterGrid object
    """
    with open(file_path, 'r') as f:
        param_space = json.load(f)
        
    return ParameterGrid(param_space)

def parse_param_space(param_defs: List[str]) -> Dict[str, List[Any]]:
    """
    Parse parameter space from command-line arguments.
    
    Args:
        param_defs: List of parameter definitions in the format "name=val1,val2,val3"
        
    Returns:
        Parameter space dictionary
    """
    param_space = {}
    
    for param_def in param_defs:
        parts = param_def.split('=')
        if len(parts) != 2:
            raise ValueError(f"Invalid parameter definition: {param_def}")
            
        name = parts[0].strip()
        values_str = parts[1].strip()
        
        # Parse values
        values = []
        for val in values_str.split(','):
            val = val.strip()
            
            # Try to convert to appropriate type
            if val.lower() == 'true':
                values.append(True)
            elif val.lower() == 'false':
                values.append(False)
            else:
                try:
                    # Try as int
                    values.append(int(val))
                except ValueError:
                    try:
                        # Try as float
                        values.append(float(val))
                    except ValueError:
                        # Keep as string
                        values.append(val)
        
        param_space[name] = values
        
    return param_space

def main():
    """Run the experiment CLI."""
    parser = argparse.ArgumentParser(description='Run genetic algorithm parameter tuning experiments')
    
    parser.add_argument('--request', '-r', required=True,
                       help='Path to schedule request JSON file')
    
    parser.add_argument('--weights', '-w',
                       help='Path to weights JSON file')
    
    parser.add_argument('--output-dir', '-o',
                       help='Directory to store experiment results')
    
    parser.add_argument('--time-limit', '-t', type=int, default=300,
                       help='Time limit per experiment in seconds (default: 300)')
    
    parser.add_argument('--max-experiments', '-m', type=int,
                       help='Maximum number of experiments to run')
    
    # Parameter grid options
    param_group = parser.add_argument_group('Parameter Grid')
    param_group.add_argument('--param-file',
                           help='Path to parameter grid JSON file')
    
    param_group.add_argument('--param', '-p', action='append',
                           help='Parameter definition (e.g., "population_size=50,100,200")')
    
    param_group.add_argument('--recommended', action='store_true',
                           help='Use recommended parameter grid')
    
    # Analysis options
    analysis_group = parser.add_argument_group('Analysis')
    analysis_group.add_argument('--analyze-only',
                              help='Path to results file to analyze (no new experiments)')
    
    analysis_group.add_argument('--analyze-param', action='append',
                              help='Parameters to analyze (e.g., "mutation_rate")')
    
    args = parser.parse_args()
    
    # Analyze existing results if specified
    if args.analyze_only:
        results_file = args.analyze_only
        output_dir = args.output_dir or os.path.dirname(results_file)
        
        # Create dummy experiment manager
        manager = ExperimentManager(
            # Dummy request, won't be used for analysis
            request=ScheduleRequest(classes=[], instructorAvailability={}, 
                                 startDate="2025-01-01", endDate="2025-01-07"),
            results_dir=output_dir
        )
        
        # Load results
        manager.load_results(results_file)
        
        # Analyze parameters
        params_to_analyze = args.analyze_param or ['population_size', 'mutation_rate', 'crossover_rate']
        for param in params_to_analyze:
            print(f"\nAnalyzing parameter: {param}")
            analysis = manager.analyze_parameters(param)
            print(analysis)
            
        # Plot convergence for best experiments
        best_indices = []
        df = manager.get_results_dataframe()
        if not df.empty:
            # Get top 3 experiments by fitness
            best_indices = df.sort_values('fitness', ascending=False).head(3).index.tolist()
            
        manager.plot_convergence(experiment_indices=best_indices)
        
        sys.exit(0)
    
    # Load request
    request = load_request_from_file(args.request)
    
    # Load weights if specified
    weights = None
    if args.weights:
        weights = load_weights_from_file(args.weights)
    
    # Create output directory
    output_dir = args.output_dir
    if not output_dir:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"experiment_results_{timestamp}"
    
    # Create experiment manager
    manager = ExperimentManager(request, weights, output_dir)
    
    # Get parameter grid
    param_grid = None
    
    if args.param_file:
        # Load from file
        param_grid = load_param_grid_from_file(args.param_file)
    elif args.param:
        # Parse from command line
        param_space = parse_param_space(args.param)
        param_grid = ParameterGrid(param_space)
    elif args.recommended:
        # Use recommended grid
        param_grid = recommended_parameter_grid()
    else:
        # Default to recommended grid
        print("Using recommended parameter grid")
        param_grid = recommended_parameter_grid()
    
    # Run experiments
    results = manager.run_experiments(
        param_grid,
        time_limit_seconds=args.time_limit,
        max_experiments=args.max_experiments
    )
    
    # Print summary
    print("\nExperiment Summary:")
    print(f"Total experiments: {len(results)}")
    
    best_result = manager.get_best_result()
    if best_result:
        print("\nBest Result:")
        print(f"Fitness: {best_result.fitness}")
        print(f"Duration: {best_result.duration_ms}ms")
        print(f"Generations: {best_result.generations}")
        print(f"Solutions Found: {best_result.solutions_found}")
        
        print("\nParameters:")
        for key, value in best_result.parameters.items():
            print(f"  {key}: {value}")
    
    # Create analysis if experiments were run
    if results:
        # Analyze parameters
        params_to_analyze = ['population_size', 'mutation_rate', 'crossover_rate']
        if 'use_adaptive_control' in results[0].parameters:
            params_to_analyze.append('use_adaptive_control')
            
        for param in params_to_analyze:
            if any(param in result.parameters for result in results):
                print(f"\nAnalyzing parameter: {param}")
                analysis = manager.analyze_parameters(param)
                print(analysis)
        
        # Plot convergence for best experiments
        best_indices = []
        df = manager.get_results_dataframe()
        if not df.empty:
            # Get top 3 experiments by fitness
            best_indices = df.sort_values('fitness', ascending=False).head(3).index.tolist()
            
        manager.plot_convergence(experiment_indices=best_indices)

if __name__ == '__main__':
    main()
