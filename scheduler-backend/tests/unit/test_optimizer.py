"""Unit tests for genetic optimizer components."""
import pytest
import random
import time
from concurrent.futures import ProcessPoolExecutor
from unittest.mock import patch, MagicMock, call, PropertyMock
from typing import Dict, List, Optional, Any

from app.models import (
    ScheduleRequest,
    ScheduleResponse,
    WeightConfig,
    ScheduleAssignment,
    ScheduleMetadata,
    TimeSlot,
    Class,
    InstructorAvailability,
    ScheduleConstraints,
    WeeklySchedule
)
from app.scheduling.solvers.genetic.optimizer import GeneticOptimizer
from app.scheduling.solvers.genetic.population import PopulationManager
from app.scheduling.solvers.genetic.chromosome import ScheduleChromosome
from app.scheduling.core import SolverConfig


# Mock classes and fixtures
@pytest.fixture
def schedule_request():
    """Create a mock schedule request."""
    return ScheduleRequest(
        classes=[
            Class(
                id="class-1",
                name="Class 1",
                grade="1",
                gradeGroup=2,
                weeklySchedule=WeeklySchedule()
            ),
            Class(
                id="class-2",
                name="Class 2",
                grade="2",
                gradeGroup=3,
                weeklySchedule=WeeklySchedule()
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
    """Create a weight configuration for testing."""
    return WeightConfig(
        final_week_compression=3000,
        day_usage=2000,
        daily_balance=1500,
        distribution=1000,
        avoid_periods=-500,
        earlier_dates=10,
        preferred_periods=1000
    )


@pytest.fixture
def mock_chromosome():
    """Create a mock chromosome with a decode method that returns a valid ScheduleResponse."""
    mock = MagicMock(spec=ScheduleChromosome)
    type(mock).fitness = PropertyMock(return_value=1000.0)
    
    # Create a valid schedule response for the decode method
    schedule_response = ScheduleResponse(
        assignments=[
            ScheduleAssignment(
                name="Class 1",
                classId="class-1",
                date="2025-03-01",
                timeSlot=TimeSlot(dayOfWeek=1, period=1)
            ),
            ScheduleAssignment(
                name="Class 2",
                classId="class-2",
                date="2025-03-01",
                timeSlot=TimeSlot(dayOfWeek=1, period=2)
            )
        ],
        metadata=ScheduleMetadata(
            duration_ms=100,
            solutions_found=1,
            score=1000.0,
            gap=0.0
        )
    )
    
    mock.decode.return_value = schedule_response
    return mock


class TestGeneticOptimizer:
    """Tests for the GeneticOptimizer class."""

    def test_init(self):
        """Test initialization of genetic optimizer."""
        # Test with default parameters
        optimizer = GeneticOptimizer()
        assert optimizer.population_size == 100
        assert optimizer.elite_size == 2
        assert optimizer.mutation_rate == 0.1
        assert optimizer.crossover_rate == 0.8
        assert optimizer.max_generations == 100
        assert optimizer.convergence_threshold == 0.01
        assert optimizer.use_adaptive_control == True
        assert optimizer.parallel_fitness == True
        assert optimizer.max_workers is not None
        assert optimizer.adaptive_controller is not None
        assert optimizer.population_manager is None
        assert optimizer.fitness_calculator is None

        # Test with custom parameters
        optimizer = GeneticOptimizer(
            population_size=50,
            elite_size=5,
            mutation_rate=0.2,
            crossover_rate=0.7,
            max_generations=50,
            convergence_threshold=0.05,
            use_adaptive_control=False,
            adaptation_interval=10,
            diversity_threshold=0.2,
            adaptation_strength=0.3,
            parallel_fitness=False,
            max_workers=4
        )
        assert optimizer.population_size == 50
        assert optimizer.elite_size == 5
        assert optimizer.mutation_rate == 0.2
        assert optimizer.crossover_rate == 0.7
        assert optimizer.max_generations == 50
        assert optimizer.convergence_threshold == 0.05
        assert optimizer.use_adaptive_control == False
        assert optimizer.parallel_fitness == False
        assert optimizer.max_workers == 4
        assert optimizer.adaptive_controller is None

    def test_evaluate_fitness_sequential(self):
        """Test fitness evaluation in sequential mode."""
        optimizer = GeneticOptimizer(parallel_fitness=False)
        
        # Create mock components
        optimizer.fitness_calculator = MagicMock()
        optimizer.fitness_calculator.calculate_fitness.side_effect = lambda c: c.id * 10
        
        # Create mock chromosomes
        chromosomes = []
        for i in range(5):
            chromosome = MagicMock()
            chromosome.id = i + 1
            chromosome.fitness = 0
            chromosomes.append(chromosome)
        
        # Call the method
        optimizer._evaluate_fitness_parallel(chromosomes)
        
        # Check results
        for i, chromosome in enumerate(chromosomes):
            assert chromosome.fitness == (i + 1) * 10
            
        # Check that fitness_calculator was called for each chromosome
        assert optimizer.fitness_calculator.calculate_fitness.call_count == 5
        for i, chromosome in enumerate(chromosomes):
            optimizer.fitness_calculator.calculate_fitness.assert_any_call(chromosome)

    @patch('app.scheduling.solvers.genetic.optimizer.parallel_map')
    def test_evaluate_fitness_parallel(self, mock_parallel_map):
        """Test fitness evaluation in parallel mode."""
        # Setup parallel map mock to return fitness values
        mock_parallel_map.return_value = [10, 20, 30, 40, 50]
        
        # Create optimizer with parallel enabled
        optimizer = GeneticOptimizer(parallel_fitness=True, max_workers=2)
        
        # Create mock fitness calculator
        optimizer.fitness_calculator = MagicMock()
        
        # Create mock chromosomes
        chromosomes = []
        for i in range(5):
            chromosome = MagicMock()
            chromosome.id = i + 1
            chromosome.fitness = 0
            chromosomes.append(chromosome)
            
        # Call the method
        optimizer._evaluate_fitness_parallel(chromosomes)
        
        # Check parallel_map was called with correct arguments
        mock_parallel_map.assert_called_once()
        # Check results
        for i, chromosome in enumerate(chromosomes):
            assert chromosome.fitness == (i+1) * 10

    def test_evaluate_fitness_empty(self):
        """Test fitness evaluation with empty chromosome list."""
        optimizer = GeneticOptimizer()
        optimizer.fitness_calculator = MagicMock()
        
        # Call with empty list
        optimizer._evaluate_fitness_parallel([])
        
        # Verify fitness calculator was not called
        optimizer.fitness_calculator.calculate_fitness.assert_not_called()

    def test_optimize_with_mocks(self, schedule_request, weight_config, mock_chromosome):
        """Test optimize using comprehensive mocking approach."""
        # Create optimizer instance
        optimizer = GeneticOptimizer(
            population_size=10,
            max_generations=2,
            parallel_fitness=False, 
            use_adaptive_control=False
        )
        
        # Mock key components and methods
        with patch.object(optimizer, '_evaluate_fitness_parallel') as mock_evaluate, \
             patch('app.scheduling.solvers.genetic.optimizer.FitnessCalculator') as MockFitness, \
             patch('app.scheduling.solvers.genetic.optimizer.PopulationManager') as MockPopManager, \
             patch('time.time', side_effect=[0, 1, 2, 3, 4, 5, 6]):
            
            # Setup mock population manager
            mock_pop_manager = MockPopManager.return_value
            mock_pop_manager.population = [mock_chromosome]
            mock_pop_manager.get_best_solution.return_value = mock_chromosome
            mock_pop_manager.get_population_stats.return_value = (1000.0, 500.0, 0.5)
            
            # Call optimize
            result = optimizer.optimize(schedule_request, weight_config, time_limit_seconds=10)
            
        # Verify results
        assert isinstance(result, ScheduleResponse)
        assert len(result.assignments) == 2
        assert result.metadata.score > 0

    def test_optimize_time_limit_with_mocks(self, schedule_request, weight_config, mock_chromosome):
        """Test time limit optimization using mocks."""
        # Create optimizer instance
        optimizer = GeneticOptimizer(
            population_size=10,
            max_generations=100,  # Large number to ensure time limit is triggered
            parallel_fitness=False,
            use_adaptive_control=False
        )
        
        # Setup time values to exceed limit after first generation
        time_values = [0, 1, 2, 11, 12, 13]  # Time jumps from 2 to 11, exceeding 10s time limit
        
        # Mock components
        with patch.object(optimizer, '_evaluate_fitness_parallel') as mock_evaluate, \
             patch('app.scheduling.solvers.genetic.optimizer.FitnessCalculator') as MockFitness, \
             patch('app.scheduling.solvers.genetic.optimizer.PopulationManager') as MockPopManager, \
             patch('time.time', side_effect=time_values):
            
            # Setup mock population manager
            mock_pop_manager = MockPopManager.return_value
            mock_pop_manager.population = [mock_chromosome]
            mock_pop_manager.get_best_solution.return_value = mock_chromosome
            mock_pop_manager.get_population_stats.return_value = (1000.0, 500.0, 0.5)
            
            # Call optimize with 10 second time limit
            result = optimizer.optimize(schedule_request, weight_config, time_limit_seconds=10)
            
        # Verify results
        assert isinstance(result, ScheduleResponse)
        assert result.metadata.score > 0

    def test_optimize_adaptive_control_with_mocks(self, schedule_request, weight_config, mock_chromosome):
        """Test adaptive control optimization using mocks."""
        # Create optimizer with adaptive control enabled
        optimizer = GeneticOptimizer(
            population_size=10,
            max_generations=3,
            parallel_fitness=False,
            use_adaptive_control=True,
            adaptation_interval=1  # Adapt every generation
        )
        
        # Mock components
        with patch.object(optimizer, '_evaluate_fitness_parallel') as mock_evaluate, \
             patch('app.scheduling.solvers.genetic.optimizer.FitnessCalculator') as MockFitness, \
             patch('app.scheduling.solvers.genetic.optimizer.PopulationManager') as MockPopManager, \
             patch('app.scheduling.solvers.genetic.optimizer.AdaptiveController') as MockAdaptiveController, \
             patch('time.time', side_effect=[0, 1, 2, 3, 4, 5, 6]):
            
            # Setup mock adaptive controller
            mock_adaptive = MockAdaptiveController.return_value
            mock_adaptive.adapt_parameters.return_value = (0.15, 0.75)  # New mutation_rate, crossover_rate
            
            # Setup mock population manager
            mock_pop_manager = MockPopManager.return_value
            mock_pop_manager.population = [mock_chromosome]
            mock_pop_manager.get_best_solution.return_value = mock_chromosome
            mock_pop_manager.get_population_stats.return_value = (1000.0, 500.0, 0.5)
            
            # Set initial rates
            type(mock_pop_manager).mutation_rate = PropertyMock(return_value=0.1)
            type(mock_pop_manager).crossover_rate = PropertyMock(return_value=0.8)
            
            # Call optimize
            result = optimizer.optimize(schedule_request, weight_config, time_limit_seconds=100)
            
        # Verify results
        assert isinstance(result, ScheduleResponse)
        assert result.metadata.score > 0

    def test_optimize_no_valid_solution_with_mocks(self, schedule_request, weight_config):
        """Test no valid solution scenario using mocks."""
        # Create optimizer
        optimizer = GeneticOptimizer(
            population_size=10,
            max_generations=2,
            parallel_fitness=False,
            use_adaptive_control=False
        )
        
        # Mock components to return no solution
        with patch.object(optimizer, '_evaluate_fitness_parallel') as mock_evaluate, \
             patch('app.scheduling.solvers.genetic.optimizer.FitnessCalculator') as MockFitness, \
             patch('app.scheduling.solvers.genetic.optimizer.PopulationManager') as MockPopManager, \
             patch('time.time', side_effect=[0, 1, 2, 3, 4, 5, 6]):
            
            # Setup mock population manager to return no best solution
            mock_pop_manager = MockPopManager.return_value
            mock_pop_manager.population = []  # Empty population
            mock_pop_manager.get_best_solution.return_value = None  # No solution found
            mock_pop_manager.get_population_stats.return_value = (0.0, 0.0, 0.0)
            
            # Call optimize and check for exception
            with pytest.raises(ValueError, match="No valid solution found"):
                optimizer.optimize(schedule_request, weight_config, time_limit_seconds=10)
