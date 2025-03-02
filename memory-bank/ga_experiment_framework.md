# Genetic Algorithm Experiment Framework Reference

This document provides a reference to the Genetic Algorithm Experiment Framework that was implemented on March 1, 2025.

## Framework Overview

The GA Experiment Framework provides tools for systematically testing and tuning genetic algorithm parameters to optimize scheduling solution quality. It is a key component in enhancing the performance of our genetic algorithm-based scheduler.

## Documentation Location

Full documentation for the experiment framework can be found at:
- **Primary README**: `/scheduler-backend/app/scheduling/solvers/genetic/experiments/README.md`
- This document provides comprehensive information on usage, parameter tuning guidelines, and future work.

## Key Components

The framework consists of:

1. **Parameter Grid System**: Creates combinations of parameters for systematic testing
2. **Statistics Collection**: Tracks per-generation metrics for algorithm performance analysis
3. **Experiment Management**: Runs experiments and analyzes results
4. **Visualization Tools**: Generates plots to understand parameter impact
5. **Command-Line Interface**: Provides easy-to-use scripts for running experiments
6. **Enhanced GeneticOptimizer**: Includes statistics tracking capabilities

## Demo Scripts

For demonstration purposes, the following scripts are available:
- `scripts/run_ga_experiments.py`: Full-featured CLI tool for running experiments
- `scripts/demo_ga_experiments.py`: Demo showing how to use the framework
- `scripts/simple_ga_demo.py`: Simplified demo showing parameter effects on a knapsack problem

## Future Work

Future enhancements planned for the experiment framework include:
1. Real data experimentation with various scheduling scenarios
2. System integration for automatic parameter selection
3. Framework extensions for additional parameters and operators
4. Automated parameter tuning based on problem characteristics
5. Meta-optimization using GA to find optimal GA parameters

## Related Documentation

For more information about the genetic algorithm implementation, refer to:
- The implementation phases documentation in `memory-bank/implementationPhases/`
- The genetic optimization proposal in `memory-bank/geneticOptimizationProposal.md`
