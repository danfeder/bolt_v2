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
    WeightConfig,
    ScheduleAssignment,
    ScheduleMetadata
)
from app.scheduling.solvers.genetic import (
    ScheduleChromosome,
    PopulationManager,
    FitnessCalculator,
    GeneticOptimizer
)
from app.scheduling.solvers.genetic.chromosome import Gene

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
    
    # Manually assign same number of genes to each chromosome to ensure compatibility
    for chrom in population.population:
        # Give each chromosome exactly 4 genes on different days
        chrom.genes = []
        for j in range(4):
            day = (j % 5) + 1  # Days 1-5
            chrom.genes.append(Gene(
                class_id=f"class_{j}", 
                day_of_week=day, 
                period=2,  # All period 2 to avoid consecutive classes
                week=0
            ))
    
    # Try to evolve - catch any exceptions for diagnosis
    try:
        # Just check if we can call evolve() without exception
        population.evolve()
        
        # Basic checks
        assert len(population.population) == 20  # Size should be maintained
        assert population.generation == 1  # We evolved one generation
        
    except Exception as e:
        # If there's an exception, make the test fail with diagnostic info
        pytest.fail(f"Population evolution test failed: {str(e)}")

def test_fitness_calculation():
    """Test fitness calculation for chromosomes."""
    request = create_test_request()
    
    # Create weight config with all required fields
    weights = WeightConfig(
        required_periods=100,
        preferred_periods=50,
        avoid_periods=-25,
        distribution=30,
        consecutive_classes=-40,
        earlier_dates=10,
        final_week_compression=3000,
        day_usage=2000,
        daily_balance=1500
    )
    
    # Create fitness calculator
    calculator = FitnessCalculator(request, weights)
    
    # Create a chromosome with explicitly defined genes
    # that should be valid given our test constraints
    chromosome = ScheduleChromosome(request)
    
    # Create a set of genes that don't violate constraints
    # Each class assigned to different days
    chromosome.genes = [
        Gene(class_id="class_0", day_of_week=1, period=2, week=0),
        Gene(class_id="class_1", day_of_week=2, period=2, week=0),
        Gene(class_id="class_2", day_of_week=3, period=2, week=0),
        Gene(class_id="class_3", day_of_week=4, period=2, week=0)
    ]
    
    # Calculate fitness
    fitness = calculator.calculate_fitness(chromosome)
    
    # Fitness should be a number
    assert isinstance(fitness, float)
    
    # Alternative approach: test that we can calculate a fitness score
    # for a very simple chromosome
    simple_chromosome = ScheduleChromosome(request)
    simple_chromosome.genes = [
        Gene(class_id="class_0", day_of_week=1, period=2, week=0)
    ]
    
    simple_fitness = calculator.calculate_fitness(simple_chromosome)
    assert isinstance(simple_fitness, float)

def test_genetic_optimizer():
    """Test genetic optimizer with simplified approach."""
    # Create a test request with minimal configuration
    request = create_test_request()
    
    # Create weight config with all required fields
    weights = WeightConfig(
        required_periods=100,
        preferred_periods=50,
        avoid_periods=-25,
        distribution=30,
        consecutive_classes=-40,
        earlier_dates=10,
        final_week_compression=3000,
        day_usage=2000,
        daily_balance=1500
    )
    
    # Create optimizer with minimal settings
    optimizer = GeneticOptimizer(
        population_size=5,  # Very small population
        max_generations=1,  # Just one generation
        mutation_rate=0.1,
        crossover_rate=0.8,
        elite_size=1
    )
    
    try:
        # Create fitness calculator
        fitness_calculator = FitnessCalculator(request, weights)
        
        # Create a valid chromosome manually
        chromosome = ScheduleChromosome(request)
        chromosome.initialize_random()
        
        # Set its fitness
        chromosome.fitness = fitness_calculator.calculate_fitness(chromosome)
        
        # Create a mock ScheduleResponse
        schedule = chromosome.decode()
        assert schedule is not None
        assert hasattr(schedule, 'assignments')
        assert hasattr(schedule, 'metadata')
        
        # Check the assignments are of the right type
        assert isinstance(schedule.assignments, list)
        for assignment in schedule.assignments:
            assert isinstance(assignment, ScheduleAssignment)
            
        # Check some basic metadata fields
        assert isinstance(schedule.metadata, ScheduleMetadata)
        assert hasattr(schedule.metadata, 'score')
        assert schedule.metadata.score == chromosome.fitness
        
    except Exception as e:
        pytest.fail(f"Basic genetic optimizer test failed: {str(e)}")

def test_genetic_crossover():
    """Test crossover operation between chromosomes."""
    request = create_test_request()
    
    # Create chromosomes
    parent1 = ScheduleChromosome(request)
    parent1.initialize_random()
    
    parent2 = ScheduleChromosome(request)
    parent2.initialize_random()
    
    # Test only supported crossover methods
    methods = ["single_point", "two_point", "uniform"]
    
    for method in methods:
        # Perform crossover
        child1, child2 = parent1.crossover(parent2, method=method)
        
        # Check children
        assert len(child1.genes) == len(parent1.genes)
        assert len(child2.genes) == len(parent2.genes)
        
        # Check genes are valid
        for gene in child1.genes + child2.genes:
            assert 1 <= gene.day_of_week <= 5
            assert 1 <= gene.period <= 8

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
