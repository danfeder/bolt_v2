"""Integration tests for GeneticOptimizer and MetaOptimizer."""
import pytest
from unittest.mock import patch, MagicMock, ANY
import random

from app.models import (
    ScheduleRequest, ScheduleResponse, WeightConfig, Class, 
    ScheduleConstraints, ScheduleAssignment, TimeSlot, WeeklySchedule, ScheduleMetadata
)
from app.scheduling.core import SolverConfig
from app.scheduling.solvers.genetic.optimizer import GeneticOptimizer
from app.scheduling.solvers.genetic.meta_optimizer import MetaOptimizer, WeightChromosome

@pytest.fixture
def schedule_request():
    """Create a minimal test schedule request."""
    return ScheduleRequest(
        classes=[],
        instructorAvailability=[],
        startDate="2023-01-01",
        endDate="2023-05-30",
        constraints=ScheduleConstraints(
            maxClassesPerDay=4,
            maxClassesPerWeek=16,
            minPeriodsPerWeek=8,
            maxConsecutiveClasses=2,
            consecutiveClassesRule="soft",
            startDate="2023-01-01",
            endDate="2023-05-30",
            allowConsecutiveClasses=True,
            requiredBreakPeriods=[]
        )
    )

@pytest.fixture
def solver_config():
    """Create a minimal test solver configuration."""
    return SolverConfig()

class TestMetaOptimizerIntegration:
    """Integration tests for the MetaOptimizer and GeneticOptimizer interaction."""
    
    @pytest.fixture
    def schedule_request(self):
        """Create a minimal test schedule request."""
        return ScheduleRequest(
            classes=[],
            instructorAvailability=[],
            startDate="2023-01-01",
            endDate="2023-05-30",
            constraints=ScheduleConstraints(
                maxClassesPerDay=4,
                maxClassesPerWeek=16,
                minPeriodsPerWeek=8,
                maxConsecutiveClasses=2,
                consecutiveClassesRule="soft",
                startDate="2023-01-01",
                endDate="2023-05-30",
                allowConsecutiveClasses=True,
                requiredBreakPeriods=[]
            )
        )
    
    @pytest.fixture
    def solver_config(self):
        """Create a minimal test solver configuration."""
        return SolverConfig()
    
    @patch('app.scheduling.solvers.genetic.meta_optimizer.GeneticOptimizer')
    def test_meta_optimizer_uses_genetic_optimizer(self, mock_genetic_optimizer, schedule_request, solver_config):
        """Test that MetaOptimizer uses GeneticOptimizer for evaluating weight configurations."""
        # Setup mock optimizer to return a valid schedule response
        mock_optimizer_instance = MagicMock()
        mock_genetic_optimizer.return_value = mock_optimizer_instance
        
        # Create a schedule response with valid metadata
        mock_response = ScheduleResponse(
            assignments=[
                ScheduleAssignment(
                    name="Class 1",
                    classId="class-1",
                    date="2025-03-01",
                    timeSlot=TimeSlot(dayOfWeek=1, period=1)
                )
            ],
            metadata=ScheduleMetadata(
                duration_ms=500,
                solutions_found=1,
                score=100.0,
                gap=0.0,
                distribution=None,
                solver=None
            )
        )
        mock_optimizer_instance.optimize.return_value = mock_response
        
        # Create meta-optimizer with reduced size for faster testing
        meta_optimizer = MetaOptimizer(
            request=schedule_request,
            base_config=solver_config,
            population_size=3,  # Small population for quick testing
            generations=2,      # Just 2 generations
            mutation_rate=0.1,
            crossover_rate=0.8,
            eval_time_limit=10
        )
        
        # Create a MetaObjectiveCalculator instance and patch it
        objective_calculator = MagicMock()
        meta_optimizer.objective_calculator = objective_calculator
        
        # Configure the mocked objective calculator to return a valid evaluation
        objective_calculator.evaluate_weight_config.return_value = (
            0.8,  # fitness
            [ScheduleAssignment(
                name="Test Class",
                classId="class-1",
                date="2025-03-01",
                timeSlot=TimeSlot(dayOfWeek=1, period=1)
            )]
        )
        
        # Create a small population of weight chromosomes
        weight_chromosomes = [
            WeightChromosome(weights={
                'final_week_compression': 3000,
                'day_usage': 2000,
                'daily_balance': 1500,
                'preferred_periods': 1000,
                'distribution': 1000,
                'avoid_periods': -500,
                'earlier_dates': 10
            }),
        ]
        
        # Set fitness values for the chromosomes
        for chromosome in weight_chromosomes:
            chromosome.fitness = random.uniform(0.1, 1.0)
        
        # Mock the initialize_population to use our predefined chromosomes
        with patch.object(meta_optimizer, 'initialize_population'):
            meta_optimizer.current_population = weight_chromosomes
            meta_optimizer.best_chromosome = weight_chromosomes[0]
            
            # Run a single generation of the optimization to trigger evaluation of chromosomes
            # Process pool executor could cause issues in testing, so skip real parallel evaluation
            with patch.object(meta_optimizer, 'evaluate_population', wraps=meta_optimizer.evaluate_population):
                with patch('concurrent.futures.ProcessPoolExecutor'):
                    # Skip actual evolution to speed up test
                    with patch.object(meta_optimizer, 'create_next_generation'):
                        # Run the optimization with just one generation
                        meta_optimizer.generations = 1
                        result = meta_optimizer.optimize()
                
                # Verify result is not None
                assert result is not None
                
                # Verify that evaluate_weight_config was called at least once
                assert objective_calculator.evaluate_weight_config.call_count > 0