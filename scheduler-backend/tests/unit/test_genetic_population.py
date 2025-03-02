"""Unit tests for genetic algorithm population manager."""
import pytest
from datetime import datetime, timedelta
import random

from app.models import (
    ScheduleRequest,
    Class,
    WeeklySchedule,
    TimeSlot,
    ScheduleConstraints
)
from app.scheduling.solvers.genetic.population import PopulationManager
from app.scheduling.solvers.genetic.chromosome import ScheduleChromosome


def create_test_request(days=14) -> ScheduleRequest:
    """Create a simple schedule request for testing."""
    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    
    # Create some test classes
    classes = [
        Class(
            id=f"class_{i}",
            name=f"Class {i}",
            grade="Grade 1",
            weeklySchedule=WeeklySchedule()
        )
        for i in range(3)  # 3 classes for simple testing
    ]
    
    # Add some conflicts and preferences
    classes[0].weeklySchedule.conflicts = [
        TimeSlot(dayOfWeek=1, period=1)  # Monday first period
    ]
    classes[1].weeklySchedule.preferredPeriods = [
        TimeSlot(dayOfWeek=2, period=3)  # Tuesday third period
    ]
    
    # Create constraints
    constraints = ScheduleConstraints(
        maxClassesPerDay=2,
        maxClassesPerWeek=6,
        minPeriodsPerWeek=2,
        maxConsecutiveClasses=2,
        consecutiveClassesRule="soft",
        startDate=start_date,
        endDate=end_date
    )
    
    return ScheduleRequest(
        classes=classes,
        instructorAvailability=[],
        startDate=start_date,
        endDate=end_date,
        constraints=constraints
    )


class TestPopulationManager:
    """Test suite for the PopulationManager class."""

    def test_initialization(self):
        """Test population manager initialization."""
        random.seed(42)  # Set seed for reproducibility
        request = create_test_request()
        
        # Create population manager
        population = PopulationManager(
            size=20,
            request=request,
            elite_size=2,
            mutation_rate=0.1,
            crossover_rate=0.8,
            crossover_methods=["single_point", "two_point"]
        )
        
        # Check properties
        assert population.size == 20
        assert population.request == request
        assert population.elite_size == 2
        assert population.mutation_rate == 0.1
        assert population.crossover_rate == 0.8
        assert population.crossover_methods == ["single_point", "two_point"]
        assert len(population.population) == 20
        assert population.generation == 0
        
        # Check all chromosomes are initialized
        for chromosome in population.population:
            assert isinstance(chromosome, ScheduleChromosome)
            assert len(chromosome.genes) > 0
            
    def test_initialize_population(self):
        """Test population initialization."""
        random.seed(42)  # Set seed for reproducibility
        request = create_test_request()
        
        # Create population manager
        population = PopulationManager(
            size=10,
            request=request
        )
        
        # Clear population and reinitialize
        population.population = []
        population._initialize_population()
        
        # Check population is initialized
        assert len(population.population) == 10
        for chromosome in population.population:
            assert isinstance(chromosome, ScheduleChromosome)
            assert len(chromosome.genes) > 0
            
    def test_select_parent(self):
        """Test parent selection."""
        random.seed(42)  # Set seed for reproducibility
        request = create_test_request()
        
        # Create population manager
        population = PopulationManager(
            size=10,
            request=request
        )
        
        # Manually set fitness values to test selection
        for i, chromosome in enumerate(population.population):
            chromosome.fitness = i * 10
            
        # Select parent multiple times
        selected_parents = [population.select_parent() for _ in range(10)]
        
        # Check that parents are selected (some higher fitness parents should be selected)
        high_fitness_selections = sum(1 for parent in selected_parents 
                                      if parent.fitness >= 50)  # Top half
        
        # Tournament selection should favor higher fitness individuals
        assert high_fitness_selections > 0
        
    def test_select_crossover_method(self):
        """Test crossover method selection."""
        random.seed(42)  # Set seed for reproducibility
        request = create_test_request()
        
        # Create population manager with specific crossover methods
        population = PopulationManager(
            size=10,
            request=request,
            crossover_methods=["single_point", "two_point"]  # Make sure we only include methods that exist
        )
        
        # Select method (should be random in early generations)
        method = population._select_crossover_method()
        assert method in ["single_point", "two_point"]  # Only check for methods we've included
        
        # Test adaptive selection after multiple generations
        population.generation = 20
        
        # Set weights to favor a specific method
        population.crossover_method_weights = {
            "single_point": 5.0,
            "two_point": 1.0,
        }
        
        # Select method multiple times
        method_counts = {}
        for _ in range(100):
            method = population._select_crossover_method()
            method_counts[method] = method_counts.get(method, 0) + 1
            
        # The method with highest weight should be selected most often
        assert method_counts["single_point"] > method_counts["two_point"]

    def test_update_crossover_weights(self):
        """Test updating crossover method weights."""
        random.seed(42)  # Set seed for reproducibility
        request = create_test_request()
        
        # Create population manager
        population = PopulationManager(
            size=10,
            request=request,
            crossover_methods=["single_point", "two_point"]
        )
        
        # Set statistics
        population.generation = 10  # Beyond adaptation threshold
        population.crossover_stats = {
            "single_point": {"uses": 100, "improvements": 80},  # 80% success
            "two_point": {"uses": 100, "improvements": 20},     # 20% success
        }
        
        # Update weights
        population._update_crossover_weights()
        
        # Check weights reflect success rates
        assert population.crossover_method_weights["single_point"] > population.crossover_method_weights["two_point"]
        
        # Check stats are reset
        assert population.crossover_stats["single_point"]["uses"] == 0
        assert population.crossover_stats["single_point"]["improvements"] == 0
        
    def test_evolution(self):
        """Test population evolution."""
        random.seed(42)  # Set seed for reproducibility
        request = create_test_request()
        
        # Create population with small size for faster testing
        population = PopulationManager(
            size=10,
            request=request,
            elite_size=2,
            mutation_rate=0.1,
            crossover_rate=0.8,
            crossover_methods=["single_point", "two_point"]  # Explicitly include only supported methods
        )
        
        # Initialize the population first if not already done
        if len(population.population) == 0:
            population.initialize_population()
            
        # Store initial population 
        initial_population = population.population.copy()
        
        # Make sure we have fitness values before evolving
        # If any chromosome doesn't have a fitness value, set a default
        for chrom in population.population:
            if not hasattr(chrom, 'fitness') or chrom.fitness is None:
                chrom.fitness = 0.0
        
        # Evolve for multiple generations with error handling
        try:
            for _ in range(5):
                population.evolve()
                
            # Check population has evolved
            assert population.generation == 5
            assert len(population.population) == 10  # Size maintained
            
            # Check if population contains chromosomes
            assert len(population.population) > 0
            
            # Basic check that population evolution completed
            assert True
        except Exception as e:
            # If there's an error during evolution, we'll print it but not fail the test
            # This allows us to continue with other tests while we're fixing this test
            print(f"Evolution test encountered an error: {str(e)}")
            assert "Evolution test should be fixed" == ""  # This will fail the test with a clear message
        
    def test_get_best_solution(self):
        """Test retrieving best solution."""
        random.seed(42)  # Set seed for reproducibility
        request = create_test_request()
        
        # Create population
        population = PopulationManager(
            size=10,
            request=request
        )
        
        # Manually set fitness values
        for i, chromosome in enumerate(population.population):
            chromosome.fitness = i * 10
            
        # Get best solution
        best = population.get_best_solution()
        
        # Best solution should have highest fitness
        assert best is not None
        assert best.fitness == 90  # Highest fitness (9 * 10)
        
        # Test empty population
        empty_population = PopulationManager(
            size=0,
            request=request
        )
        empty_population.population = []
        
        # Should return None for empty population
        assert empty_population.get_best_solution() is None
        
    def test_get_population_stats(self):
        """Test population statistics calculation."""
        random.seed(42)  # Set seed for reproducibility
        request = create_test_request()
        
        # Create population
        population = PopulationManager(
            size=10,
            request=request
        )
        
        # Manually set fitness values
        for i, chromosome in enumerate(population.population):
            chromosome.fitness = i * 10
            
        # Calculate statistics
        best, avg, diversity = population.get_population_stats()
        
        # Calculate the expected average manually to avoid floating point comparison issues
        expected_avg = sum(i * 10 for i in range(10)) / 10
        
        # Check statistics with proper floating point comparison
        assert abs(avg - expected_avg) < 0.0001  # Average of 0, 10, 20, ..., 90
        assert abs(best - 90.0) < 0.0001  # Highest fitness
        assert 0.0 <= diversity <= 1.0
