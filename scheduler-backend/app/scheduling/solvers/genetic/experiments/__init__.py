"""
Experiment framework for genetic algorithm parameter tuning.

This module provides tools for systematically exploring different 
genetic algorithm parameter combinations to identify optimal settings
for various scheduling scenarios.
"""

from typing import Dict, List, Any, Callable, Optional, Tuple
import time
import json
import os
from datetime import datetime
import itertools
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from app.models import ScheduleRequest, ScheduleResponse, WeightConfig
from ..optimizer import GeneticOptimizer
from ..chromosome import ScheduleChromosome
from ... import config

@dataclass
class ExperimentResult:
    """Results from a single experiment run."""
    parameters: Dict[str, Any]
    fitness: float
    duration_ms: int
    generations: int
    solutions_found: int
    convergence_gen: Optional[int] = None
    generation_stats: List[Dict[str, float]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        result = {
            "parameters": self.parameters,
            "fitness": self.fitness,
            "duration_ms": self.duration_ms,
            "generations": self.generations,
            "solutions_found": self.solutions_found
        }
        
        if self.convergence_gen is not None:
            result["convergence_gen"] = self.convergence_gen
            
        if self.generation_stats:
            result["generation_stats"] = self.generation_stats
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExperimentResult':
        """Create result instance from dictionary."""
        return cls(
            parameters=data["parameters"],
            fitness=data["fitness"],
            duration_ms=data["duration_ms"],
            generations=data["generations"],
            solutions_found=data["solutions_found"],
            convergence_gen=data.get("convergence_gen"),
            generation_stats=data.get("generation_stats", [])
        )


class ParameterGrid:
    """Generate combinations of parameters for experiments."""
    
    def __init__(self, param_space: Dict[str, List[Any]]):
        """
        Initialize with parameter search space.
        
        Args:
            param_space: Dictionary mapping parameter names to lists of possible values
        """
        self.param_space = param_space
        
    def generate_combinations(self, max_combinations: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Generate parameter combinations from the parameter space.
        
        Args:
            max_combinations: Optional maximum number of combinations to generate
            
        Returns:
            List of parameter dictionaries
        """
        param_names = list(self.param_space.keys())
        param_values = list(self.param_space.values())
        
        # Generate all combinations
        combinations = list(itertools.product(*param_values))
        
        # Convert to list of dictionaries
        result = [dict(zip(param_names, combo)) for combo in combinations]
        
        # Limit if needed
        if max_combinations and max_combinations < len(result):
            return result[:max_combinations]
            
        return result


class StatsCollector:
    """Collect and process experiment statistics."""
    
    def __init__(self):
        """Initialize stats collector."""
        self.stats = []
        
    def add_generation_stats(self, 
                             generation: int, 
                             best_fitness: float, 
                             avg_fitness: float, 
                             diversity: float,
                             mutation_rate: Optional[float] = None,
                             crossover_rate: Optional[float] = None):
        """
        Add statistics for a generation.
        
        Args:
            generation: Generation number
            best_fitness: Best fitness in generation
            avg_fitness: Average fitness in generation
            diversity: Population diversity
            mutation_rate: Current mutation rate if adaptive
            crossover_rate: Current crossover rate if adaptive
        """
        stat = {
            "generation": generation,
            "best_fitness": best_fitness,
            "avg_fitness": avg_fitness,
            "diversity": diversity
        }
        
        if mutation_rate is not None:
            stat["mutation_rate"] = mutation_rate
            
        if crossover_rate is not None:
            stat["crossover_rate"] = crossover_rate
            
        self.stats.append(stat)
        
    def get_stats(self) -> List[Dict[str, float]]:
        """Get all collected statistics."""
        return self.stats
        
    def get_convergence_generation(self, 
                                  window_size: int = 5, 
                                  threshold: float = 0.001) -> Optional[int]:
        """
        Determine the generation at which the algorithm converged.
        
        Args:
            window_size: Size of the window to check for improvement
            threshold: Minimum improvement threshold
            
        Returns:
            Generation at which convergence occurred, or None if it didn't converge
        """
        if len(self.stats) < window_size + 1:
            return None
            
        # Check for convergence based on best fitness improvement
        for i in range(len(self.stats) - window_size):
            # Calculate improvement over window
            start_fitness = self.stats[i]["best_fitness"]
            end_fitness = self.stats[i + window_size]["best_fitness"]
            
            # Skip if we have negative or zero start fitness
            if start_fitness <= 0:
                continue
                
            improvement = (end_fitness - start_fitness) / abs(start_fitness)
            
            # If improvement is below threshold, we've converged
            if improvement < threshold:
                return i + window_size
                
        return None


class ExperimentManager:
    """
    Manage genetic algorithm parameter tuning experiments.
    
    This class allows running experiments with different parameter combinations,
    collecting results, and analyzing experiment outcomes.
    """
    
    def __init__(self, 
                 request: ScheduleRequest, 
                 weights: Optional[WeightConfig] = None,
                 results_dir: Optional[str] = None):
        """
        Initialize experiment manager.
        
        Args:
            request: Schedule request to use for experiments
            weights: Optional weight configuration
            results_dir: Directory to store experiment results
        """
        self.request = request
        self.weights = weights
        
        # Create results directory if specified
        if results_dir:
            self.results_dir = Path(results_dir)
            os.makedirs(self.results_dir, exist_ok=True)
        else:
            # Default to a timestamped directory in current path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.results_dir = Path(f"experiment_results_{timestamp}")
            os.makedirs(self.results_dir, exist_ok=True)
        
        self.results = []
        
    def run_single_experiment(self, 
                             params: Dict[str, Any], 
                             time_limit_seconds: int = 300,
                             collect_generation_stats: bool = True) -> ExperimentResult:
        """
        Run a single experiment with the given parameters.
        
        Args:
            params: Parameter dictionary for the experiment
            time_limit_seconds: Time limit for optimization
            collect_generation_stats: Whether to collect per-generation statistics
            
        Returns:
            Experiment result
        """
        # Create optimizer with experiment parameters
        optimizer = GeneticOptimizer(**params)
        
        # Setup stats collector if needed
        stats_collector = None
        if collect_generation_stats:
            stats_collector = StatsCollector()
            
            # Monkey patch the optimizer to collect stats
            original_optimize = optimizer.optimize
            
            def optimize_with_stats(request, weights, time_limit_seconds=300):
                # Initialize components first (copied from original optimize)
                optimizer.fitness_calculator = optimizer.fitness_calculator or optimizer._create_fitness_calculator(request, weights)
                optimizer.population_manager = optimizer.population_manager or optimizer._create_population_manager()
                
                # Calculate initial fitness
                optimizer._evaluate_fitness_parallel(optimizer.population_manager.population)
                
                # Track statistics
                best, avg, diversity = optimizer.population_manager.get_population_stats()
                stats_collector.add_generation_stats(
                    0, best, avg, diversity, 
                    optimizer.mutation_rate, 
                    optimizer.crossover_rate
                )
                
                # Evolution loop
                for generation in range(optimizer.max_generations):
                    # Standard optimization logic (simplified)
                    optimizer.population_manager.evolve()
                    optimizer._evaluate_fitness_parallel(optimizer.population_manager.population)
                    
                    # Collect stats after each generation
                    best, avg, diversity = optimizer.population_manager.get_population_stats()
                    stats_collector.add_generation_stats(
                        generation + 1, best, avg, diversity,
                        optimizer.population_manager.mutation_rate,
                        optimizer.population_manager.crossover_rate
                    )
                    
                    # Check time limit
                    if time.time() - optimizer._start_time > time_limit_seconds:
                        break
                        
                    # Check convergence
                    if optimizer._check_convergence():
                        break
                
                # Return the result
                return original_optimize(request, weights, time_limit_seconds)
            
            # Replace optimize method
            optimizer.optimize = optimize_with_stats
        
        # Run experiment
        start_time = time.time()
        response = optimizer.optimize(self.request, self.weights, time_limit_seconds)
        
        # Create result object
        result = ExperimentResult(
            parameters=params,
            fitness=response.metadata.score,
            duration_ms=response.metadata.duration_ms,
            generations=optimizer.generations_run if hasattr(optimizer, "generations_run") else 0,
            solutions_found=response.metadata.solutions_found if hasattr(response.metadata, "solutions_found") else 0
        )
        
        # Add generation stats if collected
        if stats_collector:
            result.generation_stats = stats_collector.get_stats()
            result.convergence_gen = stats_collector.get_convergence_generation()
            
        return result
    
    def run_experiments(self, 
                       param_grid: ParameterGrid, 
                       time_limit_seconds: int = 300,
                       max_experiments: Optional[int] = None,
                       collect_generation_stats: bool = True) -> List[ExperimentResult]:
        """
        Run experiments for multiple parameter combinations.
        
        Args:
            param_grid: Parameter grid with combinations to test
            time_limit_seconds: Time limit per experiment
            max_experiments: Maximum number of experiments to run
            collect_generation_stats: Whether to collect per-generation statistics
            
        Returns:
            List of experiment results
        """
        # Generate parameter combinations
        combinations = param_grid.generate_combinations(max_experiments)
        
        # Run experiments for each combination
        results = []
        for i, params in enumerate(combinations):
            print(f"Running experiment {i+1}/{len(combinations)} with parameters:")
            for key, value in params.items():
                print(f"  {key}: {value}")
                
            # Run experiment
            result = self.run_single_experiment(
                params, 
                time_limit_seconds,
                collect_generation_stats
            )
            
            # Add to results
            results.append(result)
            self.results.append(result)
            
            # Save results after each experiment
            self._save_results()
            
            print(f"  Result: fitness={result.fitness}, duration={result.duration_ms}ms")
            print(f"  Generations: {result.generations}, Solutions: {result.solutions_found}")
            if result.convergence_gen is not None:
                print(f"  Converged at generation: {result.convergence_gen}")
            print()
            
        return results
    
    def get_best_result(self) -> Optional[ExperimentResult]:
        """
        Get the best result from all experiments.
        
        Returns:
            Best experiment result by fitness
        """
        if not self.results:
            return None
            
        return max(self.results, key=lambda r: r.fitness)
    
    def get_results_dataframe(self) -> pd.DataFrame:
        """
        Convert results to pandas DataFrame for analysis.
        
        Returns:
            DataFrame containing experiment results
        """
        # Extract basic parameters and results
        data = []
        for result in self.results:
            row = {
                "fitness": result.fitness,
                "duration_ms": result.duration_ms,
                "generations": result.generations,
                "solutions_found": result.solutions_found
            }
            
            if result.convergence_gen is not None:
                row["convergence_gen"] = result.convergence_gen
                
            # Add parameters
            for param, value in result.parameters.items():
                row[param] = value
                
            data.append(row)
            
        return pd.DataFrame(data)
    
    def _save_results(self) -> None:
        """Save experiment results to disk."""
        results_file = self.results_dir / "results.json"
        
        # Convert results to dictionaries
        results_dict = [result.to_dict() for result in self.results]
        
        # Save as JSON
        with open(results_file, 'w') as f:
            json.dump(results_dict, f, indent=2)
    
    def load_results(self, file_path: str) -> None:
        """
        Load experiment results from file.
        
        Args:
            file_path: Path to results file
        """
        with open(file_path, 'r') as f:
            results_dict = json.load(f)
            
        # Convert dictionaries to result objects
        self.results = [ExperimentResult.from_dict(r) for r in results_dict]
    
    def analyze_parameters(self,
                          param_name: str,
                          metric: str = "fitness",
                          show_plot: bool = True,
                          save_plot: bool = True) -> pd.DataFrame:
        """
        Analyze the impact of a parameter on a metric.
        
        Args:
            param_name: Name of parameter to analyze
            metric: Metric to analyze (fitness, duration_ms, generations, solutions_found)
            show_plot: Whether to display the plot
            save_plot: Whether to save the plot
            
        Returns:
            DataFrame with parameter value and average metric value
        """
        # Get results dataframe
        df = self.get_results_dataframe()
        
        # Group by parameter and calculate statistics
        grouped = df.groupby(param_name)[metric].agg(['mean', 'std', 'min', 'max']).reset_index()
        
        # Plot results
        if show_plot or save_plot:
            plt.figure(figsize=(10, 6))
            plt.errorbar(
                grouped[param_name], 
                grouped['mean'], 
                yerr=grouped['std'],
                marker='o',
                linestyle='-'
            )
            plt.xlabel(param_name)
            plt.ylabel(metric)
            plt.title(f"Effect of {param_name} on {metric}")
            plt.grid(True)
            
            if save_plot:
                plot_file = self.results_dir / f"param_analysis_{param_name}_{metric}.png"
                plt.savefig(plot_file)
                
            if show_plot:
                plt.show()
            else:
                plt.close()
                
        return grouped
    
    def plot_convergence(self, 
                        experiment_indices: Optional[List[int]] = None,
                        show_plot: bool = True,
                        save_plot: bool = True) -> None:
        """
        Plot convergence curves for selected experiments.
        
        Args:
            experiment_indices: Indices of experiments to plot (None for all)
            show_plot: Whether to display the plot
            save_plot: Whether to save the plot
        """
        if not self.results or not any(r.generation_stats for r in self.results):
            print("No generation statistics available for convergence plot")
            return
            
        # Select experiments to plot
        results_to_plot = self.results
        if experiment_indices is not None:
            results_to_plot = [self.results[i] for i in experiment_indices if i < len(self.results)]
            
        # Create plot
        plt.figure(figsize=(12, 8))
        
        for i, result in enumerate(results_to_plot):
            if not result.generation_stats:
                continue
                
            # Extract generations and fitness values
            generations = [stat['generation'] for stat in result.generation_stats]
            best_fitness = [stat['best_fitness'] for stat in result.generation_stats]
            
            # Create label from key parameters
            params = result.parameters
            label = f"Exp {i}: "
            for key in ['population_size', 'mutation_rate', 'crossover_rate']:
                if key in params:
                    label += f"{key.split('_')[0]}={params[key]}, "
            label = label.rstrip(', ')
            
            # Plot convergence curve
            plt.plot(generations, best_fitness, marker='o', linestyle='-', label=label)
            
            # Mark convergence point if available
            if result.convergence_gen is not None:
                conv_gen = result.convergence_gen
                # Find the closest generation in our data
                closest_idx = min(range(len(generations)), 
                                key=lambda i: abs(generations[i] - conv_gen))
                plt.axvline(x=generations[closest_idx], linestyle='--', alpha=0.5)
                
        plt.xlabel('Generation')
        plt.ylabel('Best Fitness')
        plt.title('Convergence Curves for Experiments')
        plt.grid(True)
        plt.legend()
        
        if save_plot:
            plot_file = self.results_dir / "convergence_plot.png"
            plt.savefig(plot_file)
            
        if show_plot:
            plt.show()
        else:
            plt.close()


def recommended_parameter_grid() -> ParameterGrid:
    """
    Return a recommended parameter grid for experimentation.
    
    Returns:
        ParameterGrid with recommended parameter combinations
    """
    param_space = {
        "population_size": [50, 100, 200],
        "elite_size": [2, 5, 10],
        "mutation_rate": [0.05, 0.1, 0.2],
        "crossover_rate": [0.7, 0.8, 0.9],
        "use_adaptive_control": [True, False],
        "diversity_threshold": [0.1, 0.15, 0.2],
        "adaptation_strength": [0.3, 0.5, 0.7]
    }
    
    return ParameterGrid(param_space)
