# Genetic Algorithm Experiment Framework

This framework provides tools for systematically exploring different genetic algorithm parameter combinations to identify optimal settings for various scheduling scenarios.

## Features

- **Parameter Grid**: Generate combinations of parameters for testing different configurations
- **Experiment Management**: Run and track experiments with different parameter combinations
- **Statistics Collection**: Gather per-generation statistics to analyze algorithm performance
- **Convergence Analysis**: Determine when the algorithm converges for different parameter settings
- **Result Visualization**: Analyze and visualize experiment results to identify optimal parameters

## Usage

### Running Experiments from Command Line

The `run_ga_experiments.py` script in the `scripts` directory provides a convenient way to run experiments from the command line:

```bash
# Run with recommended parameter grid
python scripts/run_ga_experiments.py --request path/to/request.json

# Run with custom parameters
python scripts/run_ga_experiments.py --request path/to/request.json \
    --param "population_size=50,100,200" \
    --param "mutation_rate=0.05,0.1,0.2" \
    --time-limit 120

# Analyze existing results
python scripts/run_ga_experiments.py --analyze-only path/to/results.json
```

### Programmatic Usage

```python
from app.scheduling.solvers.genetic.experiments import ExperimentManager, ParameterGrid

# Create parameter grid
param_space = {
    "population_size": [50, 100, 200],
    "mutation_rate": [0.05, 0.1, 0.2],
    "crossover_rate": [0.7, 0.8, 0.9],
    "use_adaptive_control": [True, False]
}
param_grid = ParameterGrid(param_space)

# Create experiment manager
manager = ExperimentManager(
    request=schedule_request,
    weights=weight_config,
    results_dir="experiment_results"
)

# Run experiments
results = manager.run_experiments(
    param_grid,
    time_limit_seconds=300,
    collect_generation_stats=True
)

# Analyze results
best_result = manager.get_best_result()
print(f"Best parameters: {best_result.parameters}")
print(f"Best fitness: {best_result.fitness}")

# Analyze specific parameters
manager.analyze_parameters("population_size")
manager.analyze_parameters("mutation_rate")

# Plot convergence curves
manager.plot_convergence()
```

## Parameter Tuning Guidelines

When tuning genetic algorithm parameters, consider the following guidelines:

1. **Population Size**: Larger populations explore more of the search space but require more computational resources. For complex scheduling problems, starting with 100-200 is recommended.

2. **Mutation Rate**: Controls exploration vs. exploitation tradeoff. Higher values (0.1-0.2) promote exploration, while lower values (0.01-0.05) focus on exploitation. Consider using adaptive mutation.

3. **Crossover Rate**: Controls how frequently chromosomes exchange genetic material. Values between 0.7-0.9 are typically effective.

4. **Elite Size**: The number of best individuals to preserve unchanged. Usually set to 5-10% of the population size.

5. **Adaptive Control**: Enables dynamic adjustment of mutation and crossover rates based on population diversity. Often improves performance on complex problems.

## Output Files

The experiment framework creates the following output files:

- `results.json`: Raw experiment results in JSON format
- `param_analysis_*.png`: Parameter analysis plots showing the impact of each parameter on metrics
- `convergence_plot.png`: Convergence curves for the best experiments

## Adding New Parameters

To add new parameters to the experiment framework:

1. Update the parameter space in `recommended_parameter_grid()` function
2. Ensure the parameters are properly passed to the `GeneticOptimizer` class
3. Update the analysis code in `ExperimentManager.analyze_parameters()` to include the new parameters

## Future Work

The following enhancements are planned for the experiment framework:

1. **Real Data Experimentation**: Run experiments with various real-world scheduling requests to establish optimal parameter profiles for different types of scheduling problems.

2. **System Integration**: Create a mechanism to automatically apply optimized parameters to the production scheduler based on characteristics of the scheduling request.

3. **Framework Extensions**: Add support for additional genetic algorithm parameters, chromosome representation variants, and crossover/mutation operator types.

4. **Automated Parameter Tuning**: Develop a system that automatically identifies optimal parameter values based on problem characteristics without requiring manual experimentation.

5. **Meta-Optimization**: Use the genetic algorithm itself to find optimal parameters for the genetic algorithm, implementing a meta-evolutionary optimization approach.
