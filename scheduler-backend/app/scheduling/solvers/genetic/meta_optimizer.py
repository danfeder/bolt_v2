"""Meta-optimization system for tuning weights in the scheduling system."""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import random
import numpy as np
import time
from concurrent.futures import ProcessPoolExecutor
import logging

from ....models import ScheduleRequest, WeightConfig, ScheduleAssignment
from ...core import SolverConfig
from ..config import WEIGHTS
# Import UnifiedSolver is moved to method level to avoid circular imports
from .optimizer import GeneticOptimizer
from .fitness import FitnessCalculator
from .population import PopulationManager as Population  # Alias for backward compatibility
from .chromosome import ScheduleChromosome

logger = logging.getLogger(__name__)

@dataclass
class WeightChromosome:
    """Chromosome representation for weight configuration"""
    # Dictionary of objective name to weight value
    weights: Dict[str, int]
    # Fitness score (higher is better)
    fitness: float = 0.0
    
    def to_weight_config(self) -> WeightConfig:
        """Convert to WeightConfig model"""
        weights_dict = self.weights.copy()
        
        # Map required_periods to preferred_periods if needed
        if 'required_periods' in weights_dict and 'preferred_periods' not in weights_dict:
            weights_dict['preferred_periods'] = weights_dict.pop('required_periods')
            
        return WeightConfig(
            final_week_compression=weights_dict.get('final_week_compression', 3000),
            day_usage=weights_dict.get('day_usage', 2000),
            daily_balance=weights_dict.get('daily_balance', 1500),
            preferred_periods=weights_dict.get('preferred_periods', 1000),
            distribution=weights_dict.get('distribution', 1000),
            avoid_periods=weights_dict.get('avoid_periods', -500),
            earlier_dates=weights_dict.get('earlier_dates', 10)
        )

class MetaObjectiveCalculator:
    """Calculates meta-objective scores for weight configurations."""
    
    def __init__(self, request: ScheduleRequest, base_config: SolverConfig):
        """
        Initialize meta-objective calculator.
        
        Args:
            request: Schedule request to test weight configurations on
            base_config: Base solver configuration
        """
        self.request = request
        self.base_config = base_config
        
    def evaluate_weight_config(self, weight_chromosome: WeightChromosome, 
                              time_limit_seconds: int = 60) -> Tuple[float, Optional[List[ScheduleAssignment]]]:
        """
        Evaluate a weight configuration by running the scheduler with it.
        
        Args:
            weight_chromosome: Weight configuration to evaluate
            time_limit_seconds: Time limit for each optimization run
            
        Returns:
            Tuple of (meta score, schedule assignments if successful)
        """
        start_time = time.time()
        weight_config = weight_chromosome.to_weight_config()
        
        # Import at method level to avoid circular imports
        from ..solver import UnifiedSolver
        
        # Create solver with this weight configuration
        solver = UnifiedSolver(
            request=self.request,
            config=self.base_config,
            use_or_tools=False,  # Use only genetic algorithm for evaluation
            use_genetic=True,
            custom_weights=weight_config.weights_dict
        )
        
        # Run solver with time limit
        try:
            result = solver.solve(time_limit_seconds=time_limit_seconds)
            
            # If no solution found, return poor score
            if not result.assignments:
                return -1000.0, None
                
            # Calculate meta-score based on multiple metrics
            meta_score = self._calculate_meta_score(result.assignments, solver)
            
            return meta_score, result.assignments
            
        except Exception as e:
            logger.error(f"Error evaluating weight config: {e}")
            return -10000.0, None
        
    def _calculate_meta_score(self, assignments: List[ScheduleAssignment], solver) -> float:
        """
        Calculate meta-score for a schedule based on multiple quality metrics.
        
        Args:
            assignments: Schedule assignments to evaluate
            solver: Solver with state after optimization
            
        Returns:
            Composite quality score (higher is better)
        """
        score = 0.0
        
        # 1. Use final optimization score as baseline
        if hasattr(solver, 'genetic_optimizer') and solver.genetic_optimizer:
            best_fitness = solver.genetic_optimizer.best_fitness
            score += best_fitness * 0.01  # Scale down the raw fitness
        
        # 2. Reward constraint satisfaction (no violations)
        if hasattr(solver, 'constraint_violations') and solver.constraint_violations:
            score -= len(solver.constraint_violations) * 500
        else:
            # Bonus for fully valid solutions
            score += 1000
            
        # 3. Distribution quality metrics
        by_day = {}
        for assignment in assignments:
            day = assignment.date
            if day not in by_day:
                by_day[day] = 0
            by_day[day] += 1
            
        # Variance of classes per day (lower is better)
        if by_day:
            values = list(by_day.values())
            variance = np.var(values) if len(values) > 1 else 0
            score -= variance * 50
            
        # 4. Reward finding solution quickly
        if hasattr(solver, 'genetic_optimizer') and solver.genetic_optimizer:
            generations = solver.genetic_optimizer.current_generation
            if generations > 0:
                score += 500 * (1 - (generations / solver.genetic_optimizer.config.MAX_GENERATIONS))
        
        return score

class MetaOptimizer:
    """Meta-genetic algorithm for optimizing weights."""
    
    def __init__(self, request: ScheduleRequest, base_config: SolverConfig,
                 population_size: int = 20, generations: int = 10,
                 mutation_rate: float = 0.2, crossover_rate: float = 0.7, 
                 eval_time_limit: int = 60):
        """
        Initialize meta-optimizer.
        
        Args:
            request: Schedule request to optimize weights for
            base_config: Base solver configuration
            population_size: Size of meta-population (weight configs)
            generations: Number of meta-generations
            mutation_rate: Probability of mutating weights
            crossover_rate: Probability of crossover
            eval_time_limit: Time limit for each inner optimization run
        """
        self.request = request
        self.base_config = base_config
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.eval_time_limit = eval_time_limit
        
        self.objective_calculator = MetaObjectiveCalculator(request, base_config)
        self.current_population: List[WeightChromosome] = []
        self.best_chromosome: Optional[WeightChromosome] = None
        self.best_assignments: Optional[List[ScheduleAssignment]] = None
        
    def initialize_population(self):
        """Initialize population of weight configurations."""
        self.current_population = []
        
        # Always include the default weights
        default = WeightChromosome(weights=WEIGHTS.copy(), fitness=0.0)
        self.current_population.append(default)
        
        # Generate random variations
        weight_keys = list(WEIGHTS.keys())
        
        for _ in range(self.population_size - 1):
            weights = WEIGHTS.copy()
            
            # Randomly adjust some weights
            for key in weight_keys:
                original = weights[key]
                # Introduce variation by scaling by a random factor
                if original >= 0:
                    scale = random.uniform(0.5, 2.0)
                    weights[key] = int(original * scale)
                else:
                    scale = random.uniform(0.5, 2.0)
                    weights[key] = int(original * scale)
            
            self.current_population.append(WeightChromosome(weights=weights, fitness=0.0))
    
    def evaluate_population(self, parallel: bool = True):
        """
        Evaluate fitness of all chromosomes in population.
        
        Args:
            parallel: Whether to use parallel evaluation
        """
        if parallel and len(self.current_population) > 1:
            # Parallel evaluation using process pool
            with ProcessPoolExecutor() as executor:
                futures = []
                for chromosome in self.current_population:
                    future = executor.submit(
                        self.objective_calculator.evaluate_weight_config,
                        chromosome,
                        self.eval_time_limit
                    )
                    futures.append((chromosome, future))
                
                # Collect results
                for chromosome, future in futures:
                    try:
                        fitness, assignments = future.result()
                        chromosome.fitness = fitness
                        
                        # Update best if better
                        if self.best_chromosome is None or fitness > self.best_chromosome.fitness:
                            self.best_chromosome = chromosome
                            self.best_assignments = assignments
                    except Exception as e:
                        logger.error(f"Error in parallel evaluation: {e}")
                        chromosome.fitness = -10000.0
        else:
            # Sequential evaluation
            for chromosome in self.current_population:
                fitness, assignments = self.objective_calculator.evaluate_weight_config(
                    chromosome, self.eval_time_limit
                )
                chromosome.fitness = fitness
                
                # Update best if better
                if self.best_chromosome is None or fitness > self.best_chromosome.fitness:
                    self.best_chromosome = chromosome
                    self.best_assignments = assignments
    
    def select_parents(self) -> List[WeightChromosome]:
        """
        Select parents for reproduction using tournament selection.
        
        Returns:
            List of selected parents
        """
        parents = []
        
        # If population is empty, return an empty list
        if not self.current_population:
            return []
        
        # Always include the best chromosome
        if self.best_chromosome:
            parents.append(self.best_chromosome)
        
        # Tournament selection for the rest
        while len(parents) < self.population_size // 2:
            # Select candidates for tournament
            # Handle case where population might be too small
            tournament_size = min(3, len(self.current_population))
            if tournament_size == 0:
                break
                
            candidates = random.sample(self.current_population, k=tournament_size)
            
            # Get the best
            if candidates:
                tournament_winner = max(candidates, key=lambda x: x.fitness)
                parents.append(tournament_winner)
            
        return parents
    
    def crossover(self, parent1: WeightChromosome, parent2: WeightChromosome) -> WeightChromosome:
        """
        Perform crossover between two parent chromosomes.
        
        Args:
            parent1: First parent
            parent2: Second parent
            
        Returns:
            Child chromosome
        """
        child_weights = {}
        
        for key in parent1.weights:
            # Randomly select from either parent or blend
            if random.random() < 0.5:
                child_weights[key] = parent1.weights[key]
            else:
                child_weights[key] = parent2.weights[key]
                
            # Small chance of blending instead
            if random.random() < 0.2:
                avg = (parent1.weights[key] + parent2.weights[key]) // 2
                child_weights[key] = avg
        
        return WeightChromosome(weights=child_weights, fitness=0.0)
    
    def mutate(self, chromosome: WeightChromosome) -> WeightChromosome:
        """
        Mutate a chromosome.
        
        Args:
            chromosome: Chromosome to mutate
            
        Returns:
            Mutated chromosome
        """
        mutated_weights = chromosome.weights.copy()
        
        for key in mutated_weights:
            # Apply mutation with probability
            if random.random() < self.mutation_rate:
                original = mutated_weights[key]
                
                # Different mutation based on weight type
                if original >= 0:
                    # For positive weights, scale up or down
                    scale = random.uniform(0.7, 1.3)
                    mutated_weights[key] = int(original * scale)
                else:
                    # For negative weights (penalties), scale up or down
                    scale = random.uniform(0.7, 1.3)
                    mutated_weights[key] = int(original * scale)
        
        return WeightChromosome(weights=mutated_weights, fitness=0.0)
    
    def create_next_generation(self):
        """Create the next generation of chromosomes."""
        # Select parents
        parents = self.select_parents()
        new_population = []
        
        # Always keep the best chromosome (elitism)
        if self.best_chromosome:
            new_population.append(self.best_chromosome)
        
        # If no parents found, we can't create a new generation
        if not parents or len(parents) < 2:
            # If we couldn't select enough parents, just keep the current population
            return
        
        # Generate children to fill the population
        while len(new_population) < self.population_size:
            # Select parents (ensure we have at least 2)
            parent1, parent2 = random.sample(parents, 2)
            
            # Crossover with probability
            if random.random() < self.crossover_rate:
                child = self.crossover(parent1, parent2)
            else:
                # Clone a parent if no crossover
                child = WeightChromosome(
                    weights=random.choice([parent1, parent2]).weights.copy(),
                    fitness=0.0
                )
            
            # Mutate
            child = self.mutate(child)
            
            new_population.append(child)
        
        self.current_population = new_population
    
    def optimize(self, parallel: bool = True) -> Tuple[WeightConfig, float]:
        """
        Run meta-optimization to find optimal weights.
        
        Args:
            parallel: Whether to use parallel evaluation
            
        Returns:
            Tuple of (best weight config, best fitness score)
        """
        logger.info(f"Starting meta-optimization with {self.population_size} weight configurations...")
        
        try:
            # Initialize population
            self.initialize_population()
            
            # Evaluate initial population
            logger.info("Evaluating initial population...")
            self.evaluate_population(parallel=parallel)
            
            # Run generations
            for generation in range(self.generations):
                logger.info(f"Meta-optimization generation {generation+1}/{self.generations}")
                
                # Create next generation
                self.create_next_generation()
                
                # Evaluate new population
                self.evaluate_population(parallel=parallel)
                
                # Log progress
                if self.best_chromosome:
                    logger.info(f"Current best fitness: {self.best_chromosome.fitness}")
                    logger.info(f"Best weights: {self.best_chromosome.weights}")
            
            # Return the best weight configuration
            if self.best_chromosome:
                # Ensure we never return a fitness of 0.0, use a small positive value instead
                fitness = max(self.best_chromosome.fitness, 0.1)
                return self.best_chromosome.to_weight_config(), fitness
            else:
                # Fallback to default if no solution found
                logger.warning("No valid weight configuration found, using defaults")
                # Create a weight config using mapped weights to ensure compatibility
                weights_dict = WEIGHTS.copy()
                # Map required_periods to preferred_periods if needed
                if 'required_periods' in weights_dict and 'preferred_periods' not in weights_dict:
                    weights_dict['preferred_periods'] = weights_dict.pop('required_periods')
                
                # Return a small positive fitness value instead of 0.0
                return WeightConfig(**weights_dict), 0.1
                
        except Exception as e:
            # Log the error and return default weights
            logger.error(f"Error during meta-optimization: {e}")
            # Create a weight config using mapped weights to ensure compatibility
            weights_dict = WEIGHTS.copy()
            # Map required_periods to preferred_periods if needed
            if 'required_periods' in weights_dict and 'preferred_periods' not in weights_dict:
                weights_dict['preferred_periods'] = weights_dict.pop('required_periods')
            
            # Return a small positive fitness value instead of 0.0
            return WeightConfig(**weights_dict), 0.1