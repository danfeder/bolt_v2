"""Genetic algorithm optimizer for schedule generation."""
import time
from typing import Optional

from ....models import (
    ScheduleRequest,
    ScheduleResponse,
    WeightConfig,
    ScheduleMetadata
)
from .chromosome import ScheduleChromosome
from .population import PopulationManager
from .fitness import FitnessCalculator
from .adaptation import AdaptiveController

class GeneticOptimizer:
    """Main genetic algorithm optimizer class."""
    
    def __init__(
        self,
        population_size: int = 100,
        elite_size: int = 2,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.8,
        max_generations: int = 100,
        convergence_threshold: float = 0.01,
        use_adaptive_control: bool = True,
        adaptation_interval: int = 5,
        diversity_threshold: float = 0.15,
        adaptation_strength: float = 0.5
    ):
        """
        Initialize genetic optimizer.
        
        Args:
            population_size: Size of the population
            elite_size: Number of best solutions to preserve
            mutation_rate: Probability of mutation for each gene
            crossover_rate: Probability of crossover between pairs
            max_generations: Maximum number of generations to evolve
            convergence_threshold: Minimum improvement required to continue
            use_adaptive_control: Whether to use adaptive parameter control
            adaptation_interval: Generations between parameter adjustments
            diversity_threshold: Diversity threshold for adaptation
            adaptation_strength: How strongly to adapt parameters (0.0-1.0)
        """
        self.population_size = population_size
        self.elite_size = elite_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.max_generations = max_generations
        self.convergence_threshold = convergence_threshold
        self.use_adaptive_control = use_adaptive_control
        
        # Initialize adaptive controller if enabled
        self.adaptive_controller = None
        if use_adaptive_control:
            self.adaptive_controller = AdaptiveController(
                base_mutation_rate=mutation_rate,
                base_crossover_rate=crossover_rate,
                diversity_threshold=diversity_threshold,
                adaptation_strength=adaptation_strength,
                adaptation_interval=adaptation_interval
            )
        
        # These will be set when optimize is called
        self.population_manager: Optional[PopulationManager] = None
        self.fitness_calculator: Optional[FitnessCalculator] = None
        
    def optimize(
        self,
        request: ScheduleRequest,
        weights: WeightConfig,
        time_limit_seconds: int = 300
    ) -> ScheduleResponse:
        """
        Generate an optimized schedule using genetic algorithm.
        
        Args:
            request: Schedule request containing classes and constraints
            weights: Configuration of weights for different objectives
            time_limit_seconds: Maximum time to spend optimizing
            
        Returns:
            ScheduleResponse containing the best schedule found
        """
        start_time = time.time()
        
        # Initialize components
        self.fitness_calculator = FitnessCalculator(request, weights)
        self.population_manager = PopulationManager(
            size=self.population_size,
            request=request,
            elite_size=self.elite_size,
            mutation_rate=self.mutation_rate,
            crossover_rate=self.crossover_rate
        )
        
        # Calculate initial fitness for population
        for chromosome in self.population_manager.population:
            chromosome.fitness = self.fitness_calculator.calculate_fitness(chromosome)
        
        # Track best solution and its fitness
        best_solution = None
        best_fitness = float('-inf')
        generations_without_improvement = 0
        solutions_found = 0
        
        # Evolution loop
        for generation in range(self.max_generations):
            # Check time limit
            if time.time() - start_time > time_limit_seconds:
                print(f"Time limit reached after {generation} generations")
                break
                
            # Evolve population
            self.population_manager.evolve()
            
            # Update fitness for new population
            for chromosome in self.population_manager.population:
                chromosome.fitness = self.fitness_calculator.calculate_fitness(chromosome)
            
            # Get current best solution
            current_best = self.population_manager.get_best_solution()
            if current_best and current_best.fitness > best_fitness:
                best_solution = current_best
                
                # Calculate improvement
                improvement = (current_best.fitness - best_fitness) / abs(best_fitness) if best_fitness != 0 else float('inf')
                best_fitness = current_best.fitness
                generations_without_improvement = 0
                solutions_found += 1
                
                print(f"Generation {generation}: New best solution found with fitness {best_fitness}")
            else:
                generations_without_improvement += 1
            
            # Get population statistics
            best, avg, diversity = self.population_manager.get_population_stats()
            print(f"Generation {generation}: Best = {best:.2f}, Avg = {avg:.2f}, Diversity = {diversity:.2f}")
            
            # Apply adaptive parameter control if enabled
            if self.use_adaptive_control and self.adaptive_controller:
                # Update parameters based on population metrics
                new_mutation_rate, new_crossover_rate = self.adaptive_controller.adapt_parameters(
                    generation, best, avg, diversity
                )
                
                # Apply new parameters to population manager
                if self.population_manager.mutation_rate != new_mutation_rate or \
                   self.population_manager.crossover_rate != new_crossover_rate:
                    self.population_manager.mutation_rate = new_mutation_rate
                    self.population_manager.crossover_rate = new_crossover_rate
            
            # Check convergence
            if generations_without_improvement >= 20:  # No improvement in 20 generations
                print(f"Converged after {generation} generations")
                break
        
        if not best_solution:
            raise ValueError("No valid solution found")
            
        # Convert best solution to schedule response
        schedule = best_solution.decode()
        
        # Update metadata
        duration = int((time.time() - start_time) * 1000)  # Convert to milliseconds
        schedule.metadata = ScheduleMetadata(
            duration_ms=duration,
            solutions_found=solutions_found,
            score=best_fitness,
            gap=0.0  # Not applicable for genetic algorithm
        )
        
        return schedule
