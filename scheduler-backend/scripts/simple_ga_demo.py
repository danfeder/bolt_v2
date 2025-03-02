#!/usr/bin/env python
"""
Simple demonstration of genetic algorithm parameter experimentation.

This script shows how different genetic algorithm parameters affect
the performance and solution quality without requiring the full framework.
"""

import time
import random
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import os
from pathlib import Path

# Create output directory for plots
output_dir = "ga_simple_demo"
os.makedirs(output_dir, exist_ok=True)

# Simple 0-1 Knapsack problem for demonstration
class KnapsackProblem:
    def __init__(self, num_items=50):
        # Generate random items (value, weight)
        random.seed(42)  # For reproducibility
        self.items = [(random.randint(1, 30), random.randint(1, 10)) for _ in range(num_items)]
        self.capacity = sum(weight for _, weight in self.items) // 3  # Set capacity to 1/3 of total weight
        
    def evaluate(self, solution):
        """Evaluate a solution (binary string)."""
        if len(solution) != len(self.items):
            return 0
            
        total_value = 0
        total_weight = 0
        
        for i, (value, weight) in enumerate(self.items):
            if solution[i] == 1:
                total_value += value
                total_weight += weight
                
        # Apply penalty for exceeding capacity
        if total_weight > self.capacity:
            return 0
            
        return total_value


# Simple Genetic Algorithm implementation
class SimpleGeneticAlgorithm:
    def __init__(self, 
                problem,
                population_size=100,
                mutation_rate=0.1,
                crossover_rate=0.8,
                elite_size=2,
                max_generations=100):
        self.problem = problem
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_size = elite_size
        self.max_generations = max_generations
        self.chromosome_length = len(problem.items)
        
        # Statistics
        self.best_fitness_history = []
        self.avg_fitness_history = []
        self.diversity_history = []
        
    def initialize_population(self):
        """Create initial random population."""
        return [self._random_chromosome() for _ in range(self.population_size)]
        
    def _random_chromosome(self):
        """Create a random chromosome."""
        return [random.randint(0, 1) for _ in range(self.chromosome_length)]
        
    def calculate_fitness(self, chromosome):
        """Calculate fitness of a chromosome."""
        return self.problem.evaluate(chromosome)
        
    def select_parent(self, population, fitnesses):
        """Select a parent using tournament selection."""
        # Tournament selection
        tournament_size = 3
        tournament = random.sample(range(len(population)), tournament_size)
        return population[max(tournament, key=lambda i: fitnesses[i])]
        
    def crossover(self, parent1, parent2):
        """Perform crossover between two parents."""
        if random.random() > self.crossover_rate:
            return parent1[:]  # Return copy of parent1
            
        # Single-point crossover
        crossover_point = random.randint(1, len(parent1) - 1)
        child = parent1[:crossover_point] + parent2[crossover_point:]
        return child
        
    def mutate(self, chromosome):
        """Mutate a chromosome."""
        for i in range(len(chromosome)):
            if random.random() < self.mutation_rate:
                chromosome[i] = 1 - chromosome[i]  # Flip bit
        return chromosome
        
    def calculate_diversity(self, population):
        """Calculate population diversity (average Hamming distance)."""
        if len(population) <= 1:
            return 0.0
            
        total_distance = 0
        count = 0
        
        # Sample pairs to calculate average distance
        num_samples = min(100, len(population) * (len(population) - 1) // 2)
        for _ in range(num_samples):
            i = random.randint(0, len(population) - 1)
            j = random.randint(0, len(population) - 1)
            while j == i:
                j = random.randint(0, len(population) - 1)
                
            # Calculate Hamming distance
            distance = sum(a != b for a, b in zip(population[i], population[j]))
            total_distance += distance / len(population[i])  # Normalize
            count += 1
            
        return total_distance / count if count > 0 else 0.0
        
    def run(self):
        """Run the genetic algorithm."""
        # Initialize
        population = self.initialize_population()
        
        # Main loop
        for generation in range(self.max_generations):
            # Calculate fitness for all chromosomes
            fitnesses = [self.calculate_fitness(chrom) for chrom in population]
            
            # Get best and average fitness
            best_fitness = max(fitnesses) if fitnesses else 0
            avg_fitness = sum(fitnesses) / len(fitnesses) if fitnesses else 0
            diversity = self.calculate_diversity(population)
            
            # Store statistics
            self.best_fitness_history.append(best_fitness)
            self.avg_fitness_history.append(avg_fitness)
            self.diversity_history.append(diversity)
            
            # Print progress
            print(f"Generation {generation}: Best = {best_fitness}, Avg = {avg_fitness:.2f}, Diversity = {diversity:.2f}")
            
            # Check for convergence
            if generation > 20 and all(self.best_fitness_history[-10] == best_fitness for _ in range(10)):
                print(f"Converged after {generation} generations")
                break
                
            # Create next generation
            next_population = []
            
            # Elitism: Keep best chromosomes
            elite_indices = sorted(range(len(fitnesses)), key=lambda i: fitnesses[i], reverse=True)[:self.elite_size]
            for i in elite_indices:
                next_population.append(population[i])
                
            # Fill the rest of the population
            while len(next_population) < self.population_size:
                # Select parents
                parent1 = self.select_parent(population, fitnesses)
                parent2 = self.select_parent(population, fitnesses)
                
                # Create child
                child = self.crossover(parent1, parent2)
                child = self.mutate(child)
                
                next_population.append(child)
                
            population = next_population
            
        # Return best solution
        final_fitnesses = [self.calculate_fitness(chrom) for chrom in population]
        best_index = max(range(len(final_fitnesses)), key=lambda i: final_fitnesses[i])
        best_solution = population[best_index]
        best_fitness = final_fitnesses[best_index]
        
        return best_solution, best_fitness
        
    def get_convergence_generation(self):
        """Determine at which generation the algorithm converged."""
        if len(self.best_fitness_history) < 10:
            return None
            
        for i in range(10, len(self.best_fitness_history)):
            # Check if fitness hasn't improved in 10 generations
            if all(self.best_fitness_history[i-j] == self.best_fitness_history[i] for j in range(1, 10)):
                return i
                
        return None


def plot_convergence(runs, param_name, param_values, output_dir):
    """Plot convergence curves for multiple runs."""
    plt.figure(figsize=(12, 6))
    
    for i, param_value in enumerate(param_values):
        plt.plot(runs[param_value]['best_fitness'], 
                 label=f"{param_name}={param_value}",
                 marker='o' if i % 2 == 0 else 's',  # Alternate markers
                 markersize=4,
                 markevery=5)  # Mark every 5th generation
    
    plt.xlabel('Generation')
    plt.ylabel('Best Fitness')
    plt.title(f'Effect of {param_name} on Convergence')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Save plot
    plt.savefig(f"{output_dir}/convergence_{param_name}.png")
    plt.show()
    
    
def plot_parameter_effect(param_values, fitnesses, param_name, output_dir):
    """Plot the effect of a parameter on final fitness."""
    plt.figure(figsize=(10, 6))
    
    plt.plot(param_values, fitnesses, marker='o', linestyle='-')
    
    plt.xlabel(param_name)
    plt.ylabel('Best Fitness')
    plt.title(f'Effect of {param_name} on Solution Quality')
    plt.grid(True, alpha=0.3)
    
    # Save plot
    plt.savefig(f"{output_dir}/effect_{param_name}.png")
    plt.show()


def run_parameter_experiment(problem, param_name, param_values):
    """Run experiments for different values of a parameter."""
    runs = {}
    best_fitnesses = []
    
    for value in param_values:
        print(f"\nRunning with {param_name}={value}")
        
        # Create GA with this parameter value
        params = {
            'problem': problem,
            'population_size': 100,
            'mutation_rate': 0.1,
            'crossover_rate': 0.8,
            'elite_size': 2,
            'max_generations': 50
        }
        
        # Set the parameter we're experimenting with
        params[param_name] = value
        
        # Run the algorithm
        ga = SimpleGeneticAlgorithm(**params)
        best_solution, best_fitness = ga.run()
        
        # Store results
        runs[value] = {
            'best_solution': best_solution,
            'best_fitness': ga.best_fitness_history,
            'avg_fitness': ga.avg_fitness_history,
            'diversity': ga.diversity_history,
            'convergence_gen': ga.get_convergence_generation()
        }
        
        best_fitnesses.append(best_fitness)
        
        # Print results
        print(f"Best fitness: {best_fitness}")
        if runs[value]['convergence_gen']:
            print(f"Converged at generation: {runs[value]['convergence_gen']}")
    
    return runs, best_fitnesses


def main():
    """Run the demonstration."""
    print("\n=== Simple Genetic Algorithm Parameter Experimentation Demo ===\n")
    
    # Create the problem
    problem = KnapsackProblem(num_items=50)
    print(f"Created knapsack problem with {len(problem.items)} items and capacity {problem.capacity}")
    
    # Experiment 1: Population Size
    print("\n=== Experiment 1: Effect of Population Size ===")
    population_sizes = [20, 50, 100, 200]
    pop_runs, pop_fitnesses = run_parameter_experiment(
        problem, 'population_size', population_sizes
    )
    plot_convergence(pop_runs, 'Population Size', population_sizes, output_dir)
    plot_parameter_effect(population_sizes, pop_fitnesses, 'Population Size', output_dir)
    
    # Experiment 2: Mutation Rate
    print("\n=== Experiment 2: Effect of Mutation Rate ===")
    mutation_rates = [0.01, 0.05, 0.1, 0.2, 0.3]
    mut_runs, mut_fitnesses = run_parameter_experiment(
        problem, 'mutation_rate', mutation_rates
    )
    plot_convergence(mut_runs, 'Mutation Rate', mutation_rates, output_dir)
    plot_parameter_effect(mutation_rates, mut_fitnesses, 'Mutation Rate', output_dir)
    
    # Experiment 3: Crossover Rate
    print("\n=== Experiment 3: Effect of Crossover Rate ===")
    crossover_rates = [0.6, 0.7, 0.8, 0.9]
    cross_runs, cross_fitnesses = run_parameter_experiment(
        problem, 'crossover_rate', crossover_rates
    )
    plot_convergence(cross_runs, 'Crossover Rate', crossover_rates, output_dir)
    plot_parameter_effect(crossover_rates, cross_fitnesses, 'Crossover Rate', output_dir)
    
    print("\n=== Demo Complete ===")
    print(f"Results and plots saved to '{output_dir}' directory")

if __name__ == "__main__":
    main()
