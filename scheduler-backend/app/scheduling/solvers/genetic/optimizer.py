"""Genetic algorithm optimizer for schedule generation."""
import time
from typing import List, Optional, Tuple, Dict, Any
import multiprocessing

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
from .parallel import parallel_map, determine_worker_count

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
        adaptation_strength: float = 0.5,
        parallel_fitness: bool = True,
        max_workers: int = None
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
            parallel_fitness: Whether to use parallel fitness evaluation
            max_workers: Maximum number of worker processes (None for auto)
        """
        self.population_size = population_size
        self.elite_size = elite_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.max_generations = max_generations
        self.convergence_threshold = convergence_threshold
        self.use_adaptive_control = use_adaptive_control
        self.parallel_fitness = parallel_fitness
        
        # Determine worker count if using parallel processing
        self.max_workers = max_workers
        if parallel_fitness and max_workers is None:
            self.max_workers = determine_worker_count()
        
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
        
    def _evaluate_fitness_parallel(self, chromosomes: List[ScheduleChromosome]) -> None:
        """
        Evaluate fitness for a list of chromosomes in parallel.
        
        Args:
            chromosomes: List of chromosomes to evaluate
        """
        if not chromosomes:
            return
            
        # Use serial processing for small batches or if parallel is disabled
        if len(chromosomes) <= 4 or not self.parallel_fitness:
            for chromosome in chromosomes:
                chromosome.fitness = self.fitness_calculator.calculate_fitness(chromosome)
            return
        
        # Create a worker function that can be pickled for multiprocessing
        def evaluate_fitness(chromosome):
            return self.fitness_calculator.calculate_fitness(chromosome)
        
        # Run fitness evaluation in parallel
        fitness_values = parallel_map(
            evaluate_fitness, 
            chromosomes,
            max_workers=self.max_workers
        )
        
        # Update chromosome fitness values
        for chromosome, fitness in zip(chromosomes, fitness_values):
            chromosome.fitness = fitness
    
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
            crossover_rate=self.crossover_rate,
            crossover_methods=["single_point", "two_point", "uniform", "order"]
        )
        
        # Calculate initial fitness for population (in parallel if enabled)
        print(f"Evaluating initial population fitness (parallel={self.parallel_fitness}, workers={self.max_workers})")
        self._evaluate_fitness_parallel(self.population_manager.population)
        
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
            
            # Update fitness for new population (in parallel if enabled)
            self._evaluate_fitness_parallel(self.population_manager.population)
            
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
            
            # Output generation statistics
            print(f"Generation {generation}: Best = {best:.2f}, Avg = {avg:.2f}, Diversity = {diversity:.2f}")
            
            # Every 10 generations, print method statistics
            if generation > 0 and generation % 10 == 0:
                method_weights = self.population_manager.crossover_method_weights
                print(f"  Crossover method weights: " + 
                      ", ".join([f"{m}={w:.2f}" for m, w in method_weights.items()]))
            
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
            gap=0.0,  # Not applicable for genetic algorithm
            distribution=None  # Will be populated by dashboard code if needed
        )
        
        return schedule
