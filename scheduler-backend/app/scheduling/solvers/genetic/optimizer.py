"""Genetic algorithm optimizer for schedule generation."""
import time
from typing import List, Optional, Tuple, Dict, Any, Callable
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
        
        # Statistics tracking for experiments
        self.generations_run = 0
        self.solutions_found = 0
        self.convergence_generation = None
        self.best_fitness_history = []
        self.avg_fitness_history = []
        self.diversity_history = []
        self._start_time = 0
        self._stats_callback = None
        
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
    
    def set_stats_callback(self, callback: Callable[[int, float, float, float, float, float], None]) -> None:
        """
        Set a callback function to receive statistics during optimization.
        
        The callback will receive: (generation, best_fitness, avg_fitness, diversity, 
                                   mutation_rate, crossover_rate)
        
        Args:
            callback: Function to call with statistics for each generation
        """
        self._stats_callback = callback
    
    def _check_convergence(self, generations_without_improvement: int = 20) -> bool:
        """
        Check if the algorithm has converged based on improvement history.
        
        Args:
            generations_without_improvement: Number of generations without significant improvement
            
        Returns:
            Whether the algorithm has converged
        """
        if len(self.best_fitness_history) < generations_without_improvement:
            return False
            
        # Check for improvement over the last N generations
        recent_history = self.best_fitness_history[-generations_without_improvement:]
        start_fitness = recent_history[0]
        end_fitness = recent_history[-1]
        
        if abs(start_fitness) < 1e-10:  # Avoid division by zero
            return False
            
        improvement = (end_fitness - start_fitness) / abs(start_fitness)
        
        # If improvement is below threshold, we've converged
        if improvement < self.convergence_threshold:
            if self.convergence_generation is None:
                self.convergence_generation = self.generations_run
            return True
            
        return False
    
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
        self._start_time = time.time()
        self.generations_run = 0
        self.solutions_found = 0
        self.convergence_generation = None
        self.best_fitness_history = []
        self.avg_fitness_history = []
        self.diversity_history = []
        
        # Initialize components
        self.fitness_calculator = self.fitness_calculator or self._create_fitness_calculator(request, weights)
        self.population_manager = self.population_manager or self._create_population_manager(request)
        
        # Calculate initial fitness for population (in parallel if enabled)
        print(f"Evaluating initial population fitness (parallel={self.parallel_fitness}, workers={self.max_workers})")
        self._evaluate_fitness_parallel(self.population_manager.population)
        
        # Track best solution and its fitness
        best_solution = None
        best_fitness = float('-inf')
        generations_without_improvement = 0
        
        # Get initial population statistics
        best, avg, diversity = self.population_manager.get_population_stats()
        self.best_fitness_history.append(best)
        self.avg_fitness_history.append(avg)
        self.diversity_history.append(diversity)
        
        # Call stats callback if registered
        if self._stats_callback:
            self._stats_callback(
                0, best, avg, diversity, 
                self.population_manager.mutation_rate,
                self.population_manager.crossover_rate
            )
        
        # Evolution loop
        for generation in range(self.max_generations):
            self.generations_run = generation + 1
            
            # Check time limit
            if time.time() - self._start_time > time_limit_seconds:
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
                self.solutions_found += 1
                
                print(f"Generation {generation}: New best solution found with fitness {best_fitness}")
            else:
                generations_without_improvement += 1
            
            # Get population statistics
            best, avg, diversity = self.population_manager.get_population_stats()
            self.best_fitness_history.append(best)
            self.avg_fitness_history.append(avg)
            self.diversity_history.append(diversity)
            
            # Call stats callback if registered
            if self._stats_callback:
                self._stats_callback(
                    generation + 1, best, avg, diversity,
                    self.population_manager.mutation_rate,
                    self.population_manager.crossover_rate
                )
            
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
            if self._check_convergence(generations_without_improvement):
                print(f"Converged after {generation} generations")
                break
        
        if not best_solution:
            raise ValueError("No valid solution found")
            
        # Convert best solution to schedule response
        schedule = best_solution.decode()
        
        # Update metadata
        duration = int((time.time() - self._start_time) * 1000)  # Convert to milliseconds
        schedule.metadata = ScheduleMetadata(
            duration_ms=duration,
            solutions_found=self.solutions_found,
            score=best_fitness,
            gap=0.0,  # Not applicable for genetic algorithm
            distribution=None  # Will be populated by dashboard code if needed
        )
        
        return schedule
    
    def _create_fitness_calculator(self, request: ScheduleRequest, weights: WeightConfig) -> FitnessCalculator:
        """Create a fitness calculator for the given request and weights."""
        return FitnessCalculator(request, weights)
    
    def _create_population_manager(self, request: ScheduleRequest) -> PopulationManager:
        """Create a population manager for the given request."""
        return PopulationManager(
            size=self.population_size,
            request=request,
            elite_size=self.elite_size,
            mutation_rate=self.mutation_rate,
            crossover_rate=self.crossover_rate,
            crossover_methods=["single_point", "two_point", "uniform", "order"]
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics from the optimization process.
        
        Returns:
            Dictionary containing optimization statistics
        """
        return {
            "generations_run": self.generations_run,
            "solutions_found": self.solutions_found,
            "convergence_generation": self.convergence_generation,
            "best_fitness_history": self.best_fitness_history,
            "avg_fitness_history": self.avg_fitness_history,
            "diversity_history": self.diversity_history,
            "final_mutation_rate": self.population_manager.mutation_rate if self.population_manager else self.mutation_rate,
            "final_crossover_rate": self.population_manager.crossover_rate if self.population_manager else self.crossover_rate
        }
