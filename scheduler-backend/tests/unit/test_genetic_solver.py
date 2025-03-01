"""Unit tests for genetic algorithm solver components."""
import pytest
from datetime import datetime, timedelta
import random

from app.models import (
    ScheduleRequest,
    Class,
    WeeklySchedule,
    TimeSlot,
    ScheduleConstraints,
    WeightConfig
)
from app.scheduling.solvers.genetic import (
    ScheduleChromosome,
    PopulationManager,
    FitnessCalculator,
    GeneticOptimizer
)

def create_test_request() -> ScheduleRequest:
    """Create a simple schedule request for testing."""
    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    
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

def test_chromosome_initialization():
    """Test chromosome creation and validation."""
    request = create_test_request()
    chromosome = ScheduleChromosome(request)
    chromosome.initialize_random()
    
    assert len(chromosome.genes) > 0
    
    # Check gene properties are within bounds
    for gene in chromosome.genes:
        assert 1 <= gene.day_of_week <= 5  # Monday-Friday
        assert 1 <= gene.period <= 8       # Valid periods

def test_population_evolution():
    """Test population initialization and evolution."""
    random.seed(42)  # Set seed for reproducibility
    request = create_test_request()
    
    # Create population
    population = PopulationManager(
        size=20,
        request=request,
        elite_size=2,
        mutation_rate=0.1,
        crossover_rate=0.8
    )
    
    # Check initial population
    assert len(population.population) == 20
    
    # Get initial best fitness
    initial_population = population.population.copy()
    initial_best_fitness = max(chrom.fitness for chrom in initial_population)
    
    # Evolve for a few generations
    for _ in range(5):
        population.evolve()
    
    # Check population size remains constant
    assert len(population.population) == 20
    
    # Check generation counter increased
    assert population.generation == 5
    
    # Get best solution
    best_solution = population.get_best_solution()
    assert best_solution is not None
    
    # Check population statistics
    avg, best, diversity = population.get_population_stats()
    assert isinstance(avg, float)
    assert isinstance(best, float)
    assert isinstance(diversity, float)
    assert 0 <= diversity <= 1.0

def test_fitness_calculation():
    """Test fitness calculation for chromosomes."""
    request = create_test_request()
    
    # Create weight config
    weights = WeightConfig(
        required_periods=100,
        preferred_periods=50,
        avoid_periods=-25,
        distribution=30,
        consecutive_classes=-40,
        earlier_dates=10
    )
    
    # Create fitness calculator
    calculator = FitnessCalculator(request, weights)
    
    # Create and initialize chromosome
    chromosome = ScheduleChromosome(request)
    chromosome.initialize_random()
    
    # Calculate fitness
    fitness = calculator.calculate_fitness(chromosome)
    
    # Fitness should be a number
    assert isinstance(fitness, float)
    
    # Create chromosome with a conflict
    conflict_chromosome = ScheduleChromosome(request)
    conflict_chromosome.genes = [
        # class_0 has conflict on Monday period 1
        Gene(class_id="class_0", day_of_week=1, period=1, week=0)
    ]
    
    # Calculate fitness
    conflict_fitness = calculator.calculate_fitness(conflict_chromosome)
    
    # Conflict fitness should be lower
    assert conflict_fitness < fitness

def test_genetic_optimizer():
    """Test complete genetic optimization process."""
    random.seed(42)  # Set seed for reproducibility
    request = create_test_request()
    
    # Create optimizer with small population for fast testing
    optimizer = GeneticOptimizer(
        population_size=10,
        generations=5,
        mutation_rate=0.1,
        crossover_rate=0.8,
        elite_size=2
    )
    
    # Run optimization
    result = optimizer.optimize(request)
    
    # Check result
    assert result is not None
    assert hasattr(result, 'assignments')
    assert len(result.assignments) > 0
    
    # Check metadata
    assert hasattr(result, 'metadata')
    assert result.metadata.startDate == request.startDate
    assert result.metadata.endDate == request.endDate
    assert result.metadata.solverType == "GeneticAlgorithm"
    
    # Check optimizer statistics
    stats = optimizer.get_statistics()
    assert 'generations' in stats
    assert 'best_fitness' in stats
    assert 'avg_fitness' in stats
    assert 'diversity' in stats
    assert stats['generations'] == 5

def test_genetic_crossover():
    """Test crossover operation between chromosomes."""
    request = create_test_request()
    
    # Create chromosomes
    parent1 = ScheduleChromosome(request)
    parent1.initialize_random()
    
    parent2 = ScheduleChromosome(request)
    parent2.initialize_random()
    
    # Test all crossover methods
    methods = ["single_point", "two_point", "uniform", "order", "auto"]
    
    for method in methods:
        # Perform crossover
        child1, child2 = parent1.crossover(parent2, method=method)
        
        # Check children
        assert len(child1.genes) == len(parent1.genes)
        assert len(child2.genes) == len(parent2.genes)
        
        # Children should be different from parents
        assert child1.genes != parent1.genes
        assert child2.genes != parent2.genes

def test_genetic_mutation():
    """Test mutation operation on chromosomes."""
    random.seed(42)  # Set seed for reproducibility
    request = create_test_request()
    
    # Create chromosome
    chromosome = ScheduleChromosome(request)
    chromosome.initialize_random()
    
    # Store original genes
    original_genes = chromosome.genes.copy()
    
    # Perform mutation with high rate to ensure changes
    chromosome.mutate(mutation_rate=0.5)
    
    # Check some genes changed
    changes = sum(1 for i, gene in enumerate(chromosome.genes) 
                  if (gene.day_of_week != original_genes[i].day_of_week or
                      gene.period != original_genes[i].period or
                      gene.week != original_genes[i].week))
    
    # At least some genes should change with high mutation rate
    assert changes > 0
    
    # Class IDs should remain the same
    for i, gene in enumerate(chromosome.genes):
        assert gene.class_id == original_genes[i].class_id
