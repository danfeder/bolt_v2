"""Population management for genetic algorithm scheduling."""
from typing import List, Optional, Tuple, Dict, Any
import random
import numpy as np
from collections import Counter

from ....models import ScheduleRequest
from .chromosome import ScheduleChromosome

class PopulationManager:
    """Manages a population of schedule chromosomes."""
    
    def __init__(
        self,
        size: int,
        request: ScheduleRequest,
        elite_size: int = 2,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.8,
        crossover_methods: List[str] = None
    ):
        """
        Initialize population manager.
        
        Args:
            size: Number of chromosomes in population
            request: Schedule request containing classes and constraints
            elite_size: Number of best solutions to preserve between generations
            mutation_rate: Probability of mutation for each gene
            crossover_rate: Probability of crossover between pairs
            crossover_methods: List of crossover methods to use (or None for auto)
        """
        self.size = size
        self.request = request
        self.elite_size = elite_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.population: List[ScheduleChromosome] = []
        self.generation = 0
        
        # Set up crossover methods
        self.crossover_methods = crossover_methods or ["single_point", "two_point", "uniform", "order"]
        self.crossover_method_weights = {method: 1.0 for method in self.crossover_methods}
        self.crossover_stats = {method: {"uses": 0, "improvements": 0} for method in self.crossover_methods}
        
        # Initialize population
        self._initialize_population()
    
    def _initialize_population(self) -> None:
        """Create initial random population."""
        self.population = []
        for _ in range(self.size):
            chromosome = ScheduleChromosome(self.request)
            chromosome.initialize_random()
            self.population.append(chromosome)
    
    def select_parent(self) -> ScheduleChromosome:
        """
        Select a parent chromosome using tournament selection.
        
        Tournament selection provides good selection pressure while
        maintaining diversity.
        """
        # Select random candidates for tournament
        tournament_size = 3
        candidates = random.sample(self.population, tournament_size)
        
        # Return the one with best fitness
        return max(candidates, key=lambda x: x.fitness)
    
    def _select_crossover_method(self) -> str:
        """
        Select a crossover method using adaptive weighting.
        
        Returns:
            Selected crossover method
        """
        # Use weighted selection based on historical performance
        if self.generation > 10:  # Only start adapting after 10 generations
            # Normalize weights to sum to 1.0
            total_weight = sum(self.crossover_method_weights.values())
            if total_weight > 0:
                # Select method using roulette wheel selection
                r = random.random() * total_weight
                cumulative = 0
                for method, weight in self.crossover_method_weights.items():
                    cumulative += weight
                    if r <= cumulative:
                        return method
        
        # Fallback to random selection
        return random.choice(self.crossover_methods)
        
    def _update_crossover_weights(self) -> None:
        """Update crossover method weights based on performance."""
        # Skip during early generations
        if self.generation < 10:
            return
            
        # Calculate success rate for each method
        success_rates = {}
        for method, stats in self.crossover_stats.items():
            if stats["uses"] == 0:
                success_rates[method] = 0.5  # Default rate
            else:
                success_rates[method] = stats["improvements"] / stats["uses"]
        
        # Reset stats for next adaptation period
        for method in self.crossover_stats:
            self.crossover_stats[method] = {"uses": 0, "improvements": 0}
            
        # Update weights
        for method, rate in success_rates.items():
            # Increase weight for successful methods
            self.crossover_method_weights[method] = max(0.1, min(5.0, rate * 2.5))
    
    def evolve(self) -> None:
        """
        Evolve the population one generation.
        
        Uses elitism to preserve best solutions while creating new ones
        through selection, crossover, and mutation with adaptive operators.
        """
        # Sort population by fitness
        self.population.sort(key=lambda x: x.fitness, reverse=True)
        
        # Keep track of previous best fitness for method evaluation
        previous_best = self.population[0].fitness if self.population else float('-inf')
        
        # Keep elite solutions
        new_population = self.population[:self.elite_size]
        
        # Update crossover weights every 5 generations
        if self.generation % 5 == 0:
            self._update_crossover_weights()
        
        # Track improvements by method
        method_children: Dict[str, List[ScheduleChromosome]] = {
            method: [] for method in self.crossover_methods
        }
        
        # Fill rest of population with offspring
        while len(new_population) < self.size:
            if random.random() < self.crossover_rate:
                # Crossover with selected method
                parent1 = self.select_parent()
                parent2 = self.select_parent()
                
                # Select crossover method
                method = self._select_crossover_method()
                self.crossover_stats[method]["uses"] += 1
                
                # Apply crossover
                child1, child2 = parent1.crossover(parent2, method=method)
                
                # Mutate children
                child1.mutate(self.mutation_rate)
                child2.mutate(self.mutation_rate)
                
                # Add valid children to population and track method
                if child1.validate():
                    new_population.append(child1)
                    method_children[method].append(child1)
                    
                if len(new_population) < self.size and child2.validate():
                    new_population.append(child2)
                    method_children[method].append(child2)
            else:
                # Just clone a parent with mutation
                parent = self.select_parent()
                child = ScheduleChromosome(self.request)
                child.genes = parent.genes.copy()
                child.mutate(self.mutation_rate)
                if child.validate():
                    new_population.append(child)
        
        # Ensure population size remains constant
        self.population = new_population[:self.size]
        self.generation += 1
        
        # Evaluate improvements from each method
        if self.population:
            best_fitness = self.population[0].fitness
            if best_fitness > previous_best:
                # Find methods that contributed to improvement
                for method, children in method_children.items():
                    # If any child from this method has fitness better than previous best
                    for child in children:
                        if child.fitness > previous_best:
                            self.crossover_stats[method]["improvements"] += 1
                            break
    
    def get_best_solution(self) -> Optional[ScheduleChromosome]:
        """Return the chromosome with highest fitness."""
        if not self.population:
            return None
        return max(self.population, key=lambda x: x.fitness)
    
    def get_population_stats(self) -> Tuple[float, float, float]:
        """
        Calculate population statistics.
        
        Returns:
            Tuple containing (best_fitness, average_fitness, diversity)
        """
        if not self.population:
            return (0.0, 0.0, 0.0)
            
        fitnesses = [c.fitness for c in self.population]
        best_fitness = max(fitnesses)
        avg_fitness = sum(fitnesses) / len(fitnesses)
        
        # Calculate diversity as average distance between chromosomes
        distances = []
        for i in range(len(self.population)):
            for j in range(i + 1, len(self.population)):
                distance = self._chromosome_distance(
                    self.population[i],
                    self.population[j]
                )
                distances.append(distance)
        diversity = sum(distances) / len(distances) if distances else 0.0
        
        return (best_fitness, avg_fitness, diversity)
    
    def _chromosome_distance(
        self,
        chromosome1: ScheduleChromosome,
        chromosome2: ScheduleChromosome
    ) -> float:
        """
        Calculate distance between two chromosomes.
        
        Uses Hamming distance normalized by chromosome length.
        """
        if len(chromosome1.genes) != len(chromosome2.genes):
            return 1.0  # Maximum distance for different lengths
            
        differences = 0
        for gene1, gene2 in zip(chromosome1.genes, chromosome2.genes):
            if (gene1.class_id != gene2.class_id or
                gene1.day_of_week != gene2.day_of_week or
                gene1.period != gene2.period or
                gene1.week != gene2.week):
                differences += 1
                
        return differences / len(chromosome1.genes)
