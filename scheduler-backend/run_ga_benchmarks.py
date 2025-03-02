#!/usr/bin/env python
"""
Genetic Algorithm Benchmark Runner

This script runs comprehensive benchmarks for the genetic algorithm components
of the Gym Class Rotation Scheduler and generates visualizations and reports.

Usage:
    python run_ga_benchmarks.py [--dataset] [--parameters] [--parallel] [--quick]

Options:
    --dataset       Run dataset scaling benchmarks
    --parameters    Run parameter sensitivity benchmarks
    --parallel      Run parallel scaling benchmarks
    --quick         Run quick versions of benchmarks (fewer iterations)
    
If no options are specified, all benchmarks will be run.
"""
import sys
import os
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import json

# Ensure the scheduler-backend is in the Python path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from tests.performance.ga_benchmarks import (
    benchmark_dataset_scaling,
    benchmark_parameter_sensitivity,
    benchmark_parallel_scaling
)
from tests.performance.perf_utils import (
    analyze_performance_results,
    visualize_performance_comparison
)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Genetic Algorithm Benchmark Runner")
    parser.add_argument("--dataset", action="store_true", help="Run dataset scaling benchmarks")
    parser.add_argument("--parameters", action="store_true", help="Run parameter sensitivity benchmarks")
    parser.add_argument("--parallel", action="store_true", help="Run parallel scaling benchmarks")
    parser.add_argument("--quick", action="store_true", help="Run quick versions of benchmarks")
    return parser.parse_args()


def generate_visualizations(results_dir: Path = Path("perf_results")):
    """
    Generate visualizations from benchmark results.
    
    Args:
        results_dir: Directory containing benchmark results
    """
    # Create visualizations directory
    vis_dir = results_dir / "visualizations"
    vis_dir.mkdir(exist_ok=True)
    
    # Load all result files
    result_files = list(results_dir.glob("*.json"))
    if not result_files:
        print("No benchmark results found. Run benchmarks first.")
        return
    
    # Group results by benchmark type
    dataset_files = [f for f in result_files if "dataset_scaling" in f.name]
    param_files = [f for f in result_files if "parameter_sensitivity" in f.name]
    parallel_files = [f for f in result_files if "parallel_scaling" in f.name]
    
    # Generate dataset scaling visualizations
    if dataset_files:
        results = []
        for file in dataset_files:
            with open(file, 'r') as f:
                data = json.load(f)
                if "solution_metrics" in data:
                    for metric in data["solution_metrics"]:
                        if "num_classes" in metric:
                            results.append(metric)
        
        if results:
            df = pd.DataFrame(results)
            
            # Duration vs Classes
            plt.figure(figsize=(10, 6))
            plt.plot(df["num_classes"], df["duration_ms"], marker='o', linestyle='-')
            plt.xlabel("Number of Classes")
            plt.ylabel("Duration (ms)")
            plt.title("Execution Time vs Dataset Size")
            plt.grid(True)
            plt.savefig(vis_dir / "dataset_scaling_duration.png")
            
            # Memory vs Classes
            plt.figure(figsize=(10, 6))
            plt.plot(df["num_classes"], df["peak_memory_mb"], marker='o', linestyle='-')
            plt.xlabel("Number of Classes")
            plt.ylabel("Peak Memory (MB)")
            plt.title("Memory Usage vs Dataset Size")
            plt.grid(True)
            plt.savefig(vis_dir / "dataset_scaling_memory.png")
            
            # Score vs Classes
            plt.figure(figsize=(10, 6))
            plt.plot(df["num_classes"], df["score"], marker='o', linestyle='-')
            plt.xlabel("Number of Classes")
            plt.ylabel("Solution Score")
            plt.title("Solution Quality vs Dataset Size")
            plt.grid(True)
            plt.savefig(vis_dir / "dataset_scaling_score.png")
    
    # Generate parameter sensitivity visualizations
    if param_files:
        results = []
        for file in param_files:
            with open(file, 'r') as f:
                data = json.load(f)
                if "solution_metrics" in data:
                    solutions = data["solution_metrics"]
                    for metric in solutions:
                        # Add parameters if they exist
                        if "parameters" in data:
                            params = data["parameters"]
                            metric.update({k: v for k, v in params.items() if k not in metric})
                        results.append(metric)
        
        if results:
            df = pd.DataFrame(results)
            
            # Effect of population size on score
            if "population_size" in df.columns:
                plt.figure(figsize=(10, 6))
                sizes = sorted(df["population_size"].unique())
                scores = [df[df["population_size"] == size]["score"].mean() for size in sizes]
                plt.plot(sizes, scores, marker='o', linestyle='-')
                plt.xlabel("Population Size")
                plt.ylabel("Average Score")
                plt.title("Effect of Population Size on Solution Quality")
                plt.grid(True)
                plt.savefig(vis_dir / "param_population_size.png")
            
            # Effect of mutation rate on score
            if "mutation_rate" in df.columns:
                plt.figure(figsize=(10, 6))
                rates = sorted(df["mutation_rate"].unique())
                scores = [df[df["mutation_rate"] == rate]["score"].mean() for rate in rates]
                plt.plot(rates, scores, marker='o', linestyle='-')
                plt.xlabel("Mutation Rate")
                plt.ylabel("Average Score")
                plt.title("Effect of Mutation Rate on Solution Quality")
                plt.grid(True)
                plt.savefig(vis_dir / "param_mutation_rate.png")
            
            # Compare adaptive vs non-adaptive
            if "use_adaptive_control" in df.columns:
                plt.figure(figsize=(10, 6))
                adaptive_scores = df[df["use_adaptive_control"] == True]["score"]
                non_adaptive_scores = df[df["use_adaptive_control"] == False]["score"]
                
                plt.boxplot([non_adaptive_scores, adaptive_scores], labels=["Non-Adaptive", "Adaptive"])
                plt.ylabel("Solution Score")
                plt.title("Effect of Adaptive Control on Solution Quality")
                plt.grid(True)
                plt.savefig(vis_dir / "param_adaptive_control.png")
    
    # Generate parallel scaling visualizations
    if parallel_files:
        results = []
        for file in parallel_files:
            with open(file, 'r') as f:
                data = json.load(f)
                if "solution_metrics" in data:
                    for metric in data["solution_metrics"]:
                        if "workers" in metric:
                            results.append(metric)
        
        if results:
            df = pd.DataFrame(results)
            
            # Convert 'auto' to a numeric value for plotting
            df["workers_num"] = df["workers"].apply(lambda x: -1 if x == "auto" else x)
            
            # Worker count vs duration
            plt.figure(figsize=(10, 6))
            workers = df["workers"].tolist()
            durations = df["duration_ms"].tolist()
            
            # Sort by worker count (with "auto" at the end)
            sorted_indices = sorted(range(len(workers)), 
                                  key=lambda i: float('inf') if workers[i] == "auto" else workers[i])
            sorted_workers = [workers[i] for i in sorted_indices]
            sorted_durations = [durations[i] for i in sorted_indices]
            
            plt.bar(range(len(sorted_workers)), sorted_durations)
            plt.xticks(range(len(sorted_workers)), sorted_workers)
            plt.xlabel("Worker Count")
            plt.ylabel("Duration (ms)")
            plt.title("Effect of Worker Count on Execution Time")
            plt.grid(True, axis='y')
            plt.savefig(vis_dir / "parallel_scaling_duration.png")
            
            # Worker count vs CPU utilization
            plt.figure(figsize=(10, 6))
            cpu_util = df["avg_cpu_percent"].tolist()
            sorted_cpu = [cpu_util[i] for i in sorted_indices]
            
            plt.bar(range(len(sorted_workers)), sorted_cpu)
            plt.xticks(range(len(sorted_workers)), sorted_workers)
            plt.xlabel("Worker Count")
            plt.ylabel("Average CPU Utilization (%)")
            plt.title("Effect of Worker Count on CPU Utilization")
            plt.grid(True, axis='y')
            plt.savefig(vis_dir / "parallel_scaling_cpu.png")
    
    print(f"Visualizations generated in {vis_dir}")


def main():
    """Run benchmarks based on command-line arguments."""
    args = parse_args()
    
    # Determine which benchmarks to run
    run_all = not (args.dataset or args.parameters or args.parallel)
    
    if run_all or args.dataset:
        print("\n=== Running Dataset Scaling Benchmark ===\n")
        benchmark_dataset_scaling()
    
    if run_all or args.parameters:
        print("\n=== Running Parameter Sensitivity Benchmark ===\n")
        benchmark_parameter_sensitivity()
    
    if run_all or args.parallel:
        print("\n=== Running Parallel Scaling Benchmark ===\n")
        benchmark_parallel_scaling()
    
    # Generate visualizations from results
    print("\n=== Generating Visualizations ===\n")
    generate_visualizations()
    
    print("\nBenchmarks complete! Results are in the perf_results directory.")


if __name__ == "__main__":
    main()
