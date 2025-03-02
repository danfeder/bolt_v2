"""Extended unit tests for the GeneticOptimizer class."""
import pytest
import time
from unittest.mock import patch, MagicMock, ANY

from app.models import (
    ScheduleRequest, ScheduleResponse, WeightConfig, Class, 
    ScheduleConstraints, ScheduleAssignment, TimeSlot, WeeklySchedule
)
from app.scheduling.solvers.genetic.optimizer import GeneticOptimizer
from app.scheduling.solvers.genetic.chromosome import ScheduleChromosome
from app.scheduling.solvers.genetic.adaptation import AdaptiveController

@pytest.fixture
def schedule_request():
    """Create a minimal test schedule request."""
    return ScheduleRequest(
        classes=[
            Class(
                id="class-1",
                name="Class 1",
                grade="1",
                gradeGroup=2,
                equipmentNeeds=[],
                weeklySchedule=WeeklySchedule(
                    conflicts=[],
                    preferredPeriods=[],
                    requiredPeriods=[],
                    avoidPeriods=[],
                    preferenceWeight=1.5,
                    avoidanceWeight=1.2
                )
            ),
            Class(
                id="class-2",
                name="Class 2",
                grade="2",
                gradeGroup=3,
                equipmentNeeds=[],
                weeklySchedule=WeeklySchedule(
                    conflicts=[],
                    preferredPeriods=[],
                    requiredPeriods=[],
                    avoidPeriods=[],
                    preferenceWeight=1.5,
                    avoidanceWeight=1.2
                )
            )
        ],
        instructorAvailability=[],
        startDate="2025-03-01",
        endDate="2025-03-31",
        constraints=ScheduleConstraints(
            maxClassesPerDay=4,
            maxClassesPerWeek=16,
            minPeriodsPerWeek=8,
            maxConsecutiveClasses=2,
            consecutiveClassesRule="soft",
            startDate="2025-03-01",
            endDate="2025-03-31",
            allowConsecutiveClasses=True,
            requiredBreakPeriods=[]
        )
    )

@pytest.fixture
def weight_config():
    """Create a test weight configuration."""
    return WeightConfig(
        final_week_compression=3000,
        day_usage=2000,
        daily_balance=1500,
        preferred_periods=50,
        distribution=30,
        avoid_periods=-25,
        earlier_dates=10
    )

@pytest.fixture
def mock_fitness_calculator(monkeypatch):
    """Mock fitness calculator for testing."""
    mock = MagicMock()
    monkeypatch.setattr('app.scheduling.solvers.genetic.optimizer.FitnessCalculator', mock)
    return mock

@pytest.fixture
def mock_schedule_chromosome(monkeypatch):
    """Mock schedule chromosome for testing."""
    mock = MagicMock()
    monkeypatch.setattr('app.scheduling.solvers.genetic.optimizer.ScheduleChromosome', mock)
    return mock

class TestGeneticOptimizer:
    """Test the GeneticOptimizer class."""
    
    def test_initialization(self, schedule_request, weight_config):
        """Test that optimizer initializes with correct parameters."""
        optimizer = GeneticOptimizer(
            population_size=150,
            elite_size=5,
            mutation_rate=0.15,
            crossover_rate=0.85,
            max_generations=200,
            convergence_threshold=0.005,
            use_adaptive_control=True,
            parallel_fitness=True,
            max_workers=4
        )
        
        # Test that parameters are correctly set
        assert optimizer.population_size == 150
        assert optimizer.elite_size == 5
        assert optimizer.mutation_rate == 0.15
        assert optimizer.crossover_rate == 0.85
        assert optimizer.max_generations == 200
        assert optimizer.convergence_threshold == 0.005
        assert optimizer.use_adaptive_control is True
        assert optimizer.parallel_fitness is True
        assert optimizer.max_workers == 4
        assert optimizer.adaptive_controller is not None
    
    @patch('app.scheduling.solvers.genetic.optimizer.PopulationManager')
    @patch('app.scheduling.solvers.genetic.optimizer.FitnessCalculator')
    def test_time_limit_handling(self, mock_fitness_calc, mock_pop_manager, schedule_request, weight_config):
        """Test that optimizer respects time limits."""
        # Setup mocks
        mock_pop = MagicMock()
        mock_pop_manager.return_value = mock_pop
        
        # Setup default population stats return value
        mock_pop.get_population_stats.return_value = (100, 80, 0.3)
    
        # Create a mock chromosome with fitness value
        mock_chromosome = MagicMock()
        mock_chromosome.fitness = 100
        
        # Mock decode method to return a valid schedule response
        mock_schedule = ScheduleResponse(
            assignments=[],
            metadata={
                "generations": 5,
                "best_fitness": 100,
                "time_taken": 1.0,
                "duration_ms": 1000,
                "solutions_found": 1,
                "score": 100,
                "gap": 0.0,
                "generation_stats": []
            }
        )
        mock_chromosome.decode.return_value = mock_schedule
    
        # Make get_best_solution return the mock chromosome
        mock_pop.get_best_solution.return_value = mock_chromosome
    
        # Set up time limit behavior by patching time.time to simulate passing time
        start_time = 100.0
        # Add more time values to prevent StopIteration
        times = [start_time, start_time + 10.0, start_time + 301.0, start_time + 302.0, start_time + 303.0]
        
        with patch('time.time', side_effect=times):
            optimizer = GeneticOptimizer(
                max_generations=1000,  # Large value to ensure time limit is hit
                use_adaptive_control=False,
                parallel_fitness=False
            )
            result = optimizer.optimize(schedule_request, weight_config, time_limit_seconds=300)
        
        # Verify we stopped because of time limit
        assert mock_pop.evolve.call_count < optimizer.max_generations
        # Access score directly from metadata
        assert result.metadata.score > 0
    
    @patch('app.scheduling.solvers.genetic.optimizer.AdaptiveController')
    @patch('app.scheduling.solvers.genetic.optimizer.PopulationManager')
    @patch('app.scheduling.solvers.genetic.optimizer.FitnessCalculator')
    def test_adaptive_control(self, mock_fitness_calc, mock_pop_manager,
                             mock_adaptive_controller, schedule_request, weight_config):
        """Test that optimizer uses adaptive control when enabled."""
        # Setup mocks
        mock_pop = MagicMock()
        mock_pop_manager.return_value = mock_pop
        mock_pop.get_population_stats.return_value = (100, 80, 0.3)  # fitness, avg, diversity
    
        # Create a mock chromosome with fitness value
        mock_chromosome = MagicMock()
        mock_chromosome.fitness = 100
        
        # Mock decode method to return a valid schedule response
        mock_schedule = ScheduleResponse(
            assignments=[],
            metadata={
                "generations": 5,
                "best_fitness": 100,
                "time_taken": 1.0,
                "duration_ms": 1000,
                "solutions_found": 1,
                "score": 100,
                "gap": 0.0,
                "generation_stats": []
            }
        )
        mock_chromosome.decode.return_value = mock_schedule
    
        # Make get_best_solution return the mock chromosome
        mock_pop.get_best_solution.return_value = mock_chromosome
    
        mock_controller = MagicMock()
        mock_adaptive_controller.return_value = mock_controller
        mock_controller.adapt_parameters.return_value = (0.2, 0.8)  # New mutation, crossover rates
    
        # Set up time for a short optimization run
        times = [100.0, 100.1, 100.2, 100.3]  # Start and subsequent times
        
        with patch('time.time', side_effect=times + [100.4]):  # Add extra time value for final check
            optimizer = GeneticOptimizer(
                use_adaptive_control=True,
                max_generations=3  # Just run a few generations
            )
            optimizer.optimize(schedule_request, weight_config)
        
        # Check that adapt_parameters was called
        mock_controller.adapt_parameters.assert_called()
        
        # Check that parameters were updated
        assert mock_pop.mutation_rate == 0.2
        assert mock_pop.crossover_rate == 0.8
    
    @patch('app.scheduling.solvers.genetic.optimizer.parallel_map')
    @patch('app.scheduling.solvers.genetic.optimizer.PopulationManager')
    @patch('app.scheduling.solvers.genetic.optimizer.FitnessCalculator')
    def test_parallel_fitness_evaluation(self, mock_fitness_calc, mock_pop_manager,
                                       mock_parallel_map, schedule_request, weight_config):
        """Test that parallel fitness evaluation is used when enabled."""
        # Setup mocks
        mock_fitness = MagicMock()
        mock_fitness_calc.return_value = mock_fitness
        
        # Just return a fixed value for fitness calculation
        mock_fitness.calculate_fitness.return_value = 100

        # Mock population
        mock_pop = MagicMock()
        mock_pop_manager.return_value = mock_pop
        
        # Create fake chromosomes
        mock_chromosomes = [MagicMock() for _ in range(5)]
        mock_pop.get_population.return_value = mock_chromosomes

        # Setup default population stats return value
        mock_pop.get_population_stats.return_value = (100, 80, 0.3)
    
        # Create a mock chromosome with fitness value
        mock_chromosome = MagicMock()
        mock_chromosome.fitness = 100
        
        # Mock decode method to return a valid schedule response
        mock_schedule = ScheduleResponse(
            assignments=[],
            metadata={
                "generations": 1,
                "best_fitness": 100,
                "time_taken": 0.1,
                "duration_ms": 100,
                "solutions_found": 1,
                "score": 100,
                "gap": 0.0,
                "generation_stats": []
            }
        )
        mock_chromosome.decode.return_value = mock_schedule
    
        # Make get_best_solution return the mock chromosome
        mock_pop.get_best_solution.return_value = mock_chromosome
    
        # Set up mock for parallel_map to return fitness values
        mock_parallel_map.return_value = [100] * 5  # Return same fitness for all chromosomes
    
        # Set up time for a minimal optimization run
        times = [100.0, 100.1, 100.2, 100.3, 100.4, 100.5]

        with patch('time.time', side_effect=times):
            # Create optimizer with parallel fitness enabled
            optimizer = GeneticOptimizer(
                parallel_fitness=True,  # This is critical - must be True to use parallel
                max_generations=1,      # Run just one generation
                max_workers=6           # Set max_workers explicitly
            )
            
            # Run the optimization
            result = optimizer.optimize(schedule_request, weight_config)

        # Verify the result
        assert result.metadata.score > 0
        
        # Debug: check if parallel_map was called at all
        assert mock_parallel_map.call_count > 0, "parallel_map was not called"
        
        # Check that parallel_map was called with correct arguments
        # Note: The optimizer uses max_workers parameter, not num_workers
        mock_parallel_map.assert_called_with(
            ANY,                # First arg should be a function (could be a local function, so use ANY)
            mock_chromosomes,   # Second arg should be chromosomes
            max_workers=6       # The parameter name is max_workers, not num_workers
        )
    
    @patch('app.scheduling.solvers.genetic.optimizer.PopulationManager')
    @patch('app.scheduling.solvers.genetic.optimizer.FitnessCalculator')
    def test_early_convergence(self, mock_fitness_calc, mock_pop_manager, schedule_request, weight_config):
        """Test that optimization stops when convergence is reached."""
        # Setup mocks
        mock_pop = MagicMock()
        mock_pop_manager.return_value = mock_pop
    
        # Initially return improving fitness values, then plateau
        best_fitness_values = [50, 75, 90, 100, 100.001, 100.0015]
        population_stats = [(v, v-10, 0.3) for v in best_fitness_values]
    
        # Make sure we have enough population stats values for all optimizer calls
        extended_stats = population_stats.copy()
        # Add extra values for any additional iterations
        for _ in range(30):  # More than we expect to need
            extended_stats.append((100.0015, 90.0015, 0.3))
            
        mock_pop.get_population_stats.side_effect = extended_stats
    
        # Create mock chromosomes with improving fitness values
        chromosomes = [MagicMock(fitness=v) for v in best_fitness_values]
        
        # Mock decode methods
        for i, chrom in enumerate(chromosomes):
            mock_schedule = ScheduleResponse(
                assignments=[],
                metadata={
                    "generations": i+1,
                    "best_fitness": chrom.fitness,
                    "time_taken": 0.1,
                    "duration_ms": 100,
                    "solutions_found": 1,
                    "score": chrom.fitness,
                    "gap": 0.0,
                    "generation_stats": []
                }
            )
            chrom.decode.return_value = mock_schedule
    
        # Make get_best_solution return chromosomes in sequence plus extras for additional iterations
        extended_chromosomes = chromosomes.copy()
        for _ in range(30):  # More than we expect to need
            extended_chromosomes.append(chromosomes[-1])
            
        mock_pop.get_best_solution.side_effect = extended_chromosomes
    
        # Setup time values with plenty of values
        time_values = [100.0]
        for i in range(50):  # More than we expect to need
            time_values.append(time_values[-1] + 0.1)
        
        with patch('time.time', side_effect=time_values):
            optimizer = GeneticOptimizer(
                use_adaptive_control=False,
                parallel_fitness=False,
                max_generations=100  # More than we expect to use
            )
            result = optimizer.optimize(schedule_request, weight_config)
        
        # Check that we stopped before max_generations due to convergence
        assert mock_pop.evolve.call_count < optimizer.max_generations
        
        # Make sure we got expected values in the result - access score directly
        assert result.metadata.score > 0
        # We don't need to check stdout content, just verify result is valid
    
    @patch('app.scheduling.solvers.genetic.chromosome.ScheduleChromosome')
    @patch('app.scheduling.solvers.genetic.optimizer.PopulationManager')
    @patch('app.scheduling.solvers.genetic.optimizer.FitnessCalculator')
    def test_complete_optimization_workflow(self, mock_fitness_calc, mock_pop_manager,
                                            mock_chromosome, schedule_request, weight_config):
        """Test a complete optimization workflow with small population."""
        # Setup mocks to avoid actual optimization which might be slow or fail
        mock_pop = MagicMock()
        mock_pop_manager.return_value = mock_pop
        
        # Setup default population stats return value
        mock_pop.get_population_stats.return_value = (100, 80, 0.3)
    
        # Mock chromosome with a fitness value
        mock_chrom = MagicMock()
        mock_chrom.fitness = 100
    
        # Mock chromosomes decode method to return a valid schedule with assignments
        assignments = [
            ScheduleAssignment(
                name="Class 1",
                classId="class-1",
                date="2025-03-01",
                timeSlot=TimeSlot(dayOfWeek=1, period=1)
            )
        ]
    
        # Create a complete, valid ScheduleResponse with all required metadata fields
        mock_chrom.decode.return_value = ScheduleResponse(
            assignments=assignments,
            metadata={
                "generations": 3,
                "best_fitness": 100,
                "time_taken": 0.5,
                "duration_ms": 500,
                "solutions_found": 1,
                "score": 100,
                "gap": 0.0,
                "generation_stats": []
            }
        )
    
        # Mock get_best_solution to return our mock chromosome
        mock_pop.get_best_solution.return_value = mock_chrom
    
        # Set up time for a minimal optimization run - add extra time values
        times = [100.0, 100.5, 101.0, 101.5, 102.0]  # Add more time values
        
        with patch('time.time', side_effect=times):
            optimizer = GeneticOptimizer(
                population_size=10,  # Small population for quick test
                max_generations=2,
                use_adaptive_control=False
            )
            result = optimizer.optimize(schedule_request, weight_config)
        
        # Check that we have the expected output structure
        assert isinstance(result, ScheduleResponse)
        assert len(result.assignments) == 1
        assert result.assignments[0].classId == "class-1"
        assert result.metadata is not None
        # Access score directly
        assert result.metadata.score == 100.0

    def test_parallel_fitness_evaluation(self, monkeypatch):
        """Test that parallel fitness evaluation works correctly."""
        # Mock the fitness calculator
        mock_fitness_calculator = MagicMock()
        monkeypatch.setattr('app.scheduling.solvers.genetic.optimizer.FitnessCalculator', mock_fitness_calculator)
        
        # Create mock chromosomes
        chromosomes = []
        for _ in range(10):
            chromosome = MagicMock()
            chromosome.fitness = None
            chromosomes.append(chromosome)
        
        # Create a fitness function to spy on
        def spy_fitness(chromosome):
            return 100
        
        # Set up mock fitness calculator
        mock_fitness_calculator.return_value.calculate_fitness.side_effect = spy_fitness
        
        # Create optimizer with parallel fitness enabled
        optimizer = GeneticOptimizer(
            population_size=10,
            elite_size=2,
            mutation_rate=0.1,
            crossover_rate=0.8,
            max_generations=100,
            parallel_fitness=True,
            max_workers=4  # Explicitly set max_workers
        )
        
        # Mock the parallel_map function
        mock_parallel_map = MagicMock()
        mock_parallel_map.side_effect = lambda func, items, max_workers: [func(item) for item in items]
        monkeypatch.setattr('app.scheduling.solvers.genetic.optimizer.parallel_map', mock_parallel_map)
        
        # Execute the method
        optimizer.fitness_calculator = mock_fitness_calculator.return_value
        optimizer._evaluate_fitness_parallel(chromosomes)
        
        # Check that parallel_map was called
        mock_parallel_map.assert_called_once()
        
        # Check that the fitness calculator was called for each chromosome
        assert mock_fitness_calculator.return_value.calculate_fitness.call_count == 10
        
        # Check that all chromosomes received a fitness value
        for chromosome in chromosomes:
            assert chromosome.fitness == 100
            
    def test_parallel_fitness_evaluation_small_batch(self, monkeypatch):
        """Test that parallel fitness evaluation correctly handles small batches."""
        # Mock the fitness calculator
        mock_fitness_calculator = MagicMock()
        monkeypatch.setattr('app.scheduling.solvers.genetic.optimizer.FitnessCalculator', mock_fitness_calculator)
        
        # Create a small batch of chromosomes (≤4)
        chromosomes = []
        for _ in range(3):  # Small batch of 3 chromosomes
            chromosome = MagicMock()
            chromosome.fitness = None
            chromosomes.append(chromosome)
        
        # Create a fitness function to spy on
        def spy_fitness(chromosome):
            return 100
        
        # Set up mock fitness calculator
        mock_fitness_calculator.return_value.calculate_fitness.side_effect = spy_fitness
        
        # Create optimizer with parallel fitness enabled
        optimizer = GeneticOptimizer(
            population_size=10,
            elite_size=2,
            mutation_rate=0.1,
            crossover_rate=0.8,
            max_generations=100,
            parallel_fitness=True,  # Even though parallel is enabled
            max_workers=4  # Explicitly set max_workers
        )
        
        # Mock the parallel_map function
        mock_parallel_map = MagicMock()
        monkeypatch.setattr('app.scheduling.solvers.genetic.optimizer.parallel_map', mock_parallel_map)
        
        # Execute the method with small batch
        optimizer.fitness_calculator = mock_fitness_calculator.return_value
        optimizer._evaluate_fitness_parallel(chromosomes)
        
        # Check that parallel_map was NOT called (should use serial processing)
        mock_parallel_map.assert_not_called()
        
        # Check that the fitness calculator was still called for each chromosome
        assert mock_fitness_calculator.return_value.calculate_fitness.call_count == 3
        
        # Check that all chromosomes received a fitness value
        for chromosome in chromosomes:
            assert chromosome.fitness == 100

    def test_no_valid_solution_error(self, monkeypatch, schedule_request, weight_config):
        """Test that an error is raised when no valid solution is found."""
        # Mock the population manager
        mock_pop_manager = MagicMock()
        monkeypatch.setattr('app.scheduling.solvers.genetic.optimizer.PopulationManager', mock_pop_manager)
        
        # Setup mock population
        mock_pop = MagicMock()
        mock_pop_manager.return_value = mock_pop
        
        # Set up get_best_solution to return None, simulating no valid solution found
        mock_pop.get_best_solution.return_value = None
        
        # Setup population stats
        mock_pop.get_population_stats.return_value = (0, 0, 0)
        
        # Create optimizer
        optimizer = GeneticOptimizer(
            max_generations=5,  # Make it smaller
            use_adaptive_control=False
        )
        
        # Mock time.time to avoid StopIteration error
        original_time = time.time
        time_values = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0]
        time_iter = iter(time_values)
        
        def mock_time():
            try:
                return next(time_iter)
            except StopIteration:
                # If we run out of mock values, just return a large value
                return 1000.0
        
        # Apply the mock
        monkeypatch.setattr(time, 'time', mock_time)
        
        # Verify that ValueError is raised
        with pytest.raises(ValueError, match="No valid solution found"):
            optimizer.optimize(schedule_request, weight_config)

    def test_parallel_fitness_disabled(self, monkeypatch):
        """Test that parallel fitness evaluation is not used when disabled."""
        # Mock the fitness calculator
        mock_fitness_calculator = MagicMock()
        monkeypatch.setattr('app.scheduling.solvers.genetic.optimizer.FitnessCalculator', mock_fitness_calculator)
        
        # Create mock chromosomes
        chromosomes = []
        for _ in range(10):  # More than 4 chromosomes to ensure we'd use parallel if enabled
            chromosome = MagicMock()
            chromosome.fitness = None
            chromosomes.append(chromosome)
        
        # Create a fitness function to spy on
        def spy_fitness(chromosome):
            return 100
        
        # Set up mock fitness calculator
        mock_fitness_calculator.return_value.calculate_fitness.side_effect = spy_fitness
        
        # Create optimizer with parallel fitness DISABLED
        optimizer = GeneticOptimizer(
            population_size=10,
            elite_size=2,
            mutation_rate=0.1,
            crossover_rate=0.8,
            max_generations=100,
            parallel_fitness=False,  # Explicitly disabled
            max_workers=4
        )
        
        # Mock the parallel_map function
        mock_parallel_map = MagicMock()
        monkeypatch.setattr('app.scheduling.solvers.genetic.optimizer.parallel_map', mock_parallel_map)
        
        # Execute the method
        optimizer.fitness_calculator = mock_fitness_calculator.return_value
        optimizer._evaluate_fitness_parallel(chromosomes)
        
        # Check that parallel_map was NOT called
        mock_parallel_map.assert_not_called()
        
        # Check that the fitness calculator was called for each chromosome
        assert mock_fitness_calculator.return_value.calculate_fitness.call_count == 10
        
        # Check that all chromosomes received a fitness value
        for chromosome in chromosomes:
            assert chromosome.fitness == 100

    def test_parallel_fitness_empty_list(self, monkeypatch):
        """Test that parallel fitness evaluation correctly handles empty chromosome list."""
        # Mock the fitness calculator
        mock_fitness_calculator = MagicMock()
        monkeypatch.setattr('app.scheduling.solvers.genetic.optimizer.FitnessCalculator', mock_fitness_calculator)
        
        # Empty chromosome list
        chromosomes = []
        
        # Create optimizer
        optimizer = GeneticOptimizer(
            parallel_fitness=True,
            max_workers=4
        )
        
        # Mock the parallel_map function
        mock_parallel_map = MagicMock()
        monkeypatch.setattr('app.scheduling.solvers.genetic.optimizer.parallel_map', mock_parallel_map)
        
        # Execute the method with empty list
        optimizer.fitness_calculator = mock_fitness_calculator.return_value
        optimizer._evaluate_fitness_parallel(chromosomes)
        
        # Check that parallel_map was NOT called
        mock_parallel_map.assert_not_called()
        
        # Check that the fitness calculator was not called at all
        mock_fitness_calculator.return_value.calculate_fitness.assert_not_called() 