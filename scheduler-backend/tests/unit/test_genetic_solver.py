"""Unit tests for genetic algorithm solver components."""
import pytest
from datetime import datetime, timedelta

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
    assert chromosome.validate()
    
    # Check gene properties
    for gene in chromosome.genes:
        assert 1 <= gene.day_of_week <= 5  # Monday-Friday
        assert 1 <= gene.period <= 8       # Valid periods
        assert gene.class_id in [c.id for c in request.classes]

def test_population_evolution():
    """Test population initialization and evolution."""
    request = create_test_request()
    population = PopulationManager(
        size=10,  # Small population for testing
        request=request,
        elite_size=2,
        mutation_rate=0.1,
        crossover_rate=0.8
    )
    
    # Test initial population
    assert len(population.population) == 10
    initial_best = population.get_best_solution()
    assert initial_best is not None
    
    # Evolve for a few generations
    for _ in range(5):
        population.evolve()
        
    # Test evolution happened
    final_best = population.get_best_solution()
    assert final_best is not None
    
    # Get population statistics
    best, avg, diversity = population.get_population_stats()
    assert best != 0
    assert 0 <= diversity <= 1

def test_fitness_calculation():
    """Test fitness calculation for chromosomes."""
    request = create_test_request()
    weights = WeightConfig(
        final_week_compression=3000,
        day_usage=2000,
        daily_balance=1500,
        preferred_periods=1000,
        distribution=1000,
        avoid_periods=-500,
        earlier_dates=10
    )
    
    calculator = FitnessCalculator(request, weights)
    chromosome = ScheduleChromosome(request)
    chromosome.initialize_random()
    
    fitness = calculator.calculate_fitness(chromosome)
    assert isinstance(fitness, float)
    
    # Test invalid chromosome gets worst fitness
    invalid_chromosome = ScheduleChromosome(request)  # Empty chromosome
    invalid_fitness = calculator.calculate_fitness(invalid_chromosome)
    assert invalid_fitness == float('-inf')

def test_genetic_optimizer():
    """Test complete genetic optimization process."""
    request = create_test_request()
    optimizer = GeneticOptimizer(
        population_size=20,
        elite_size=2,
        mutation_rate=0.1,
        crossover_rate=0.8,
        max_generations=10,  # Small number for testing
        convergence_threshold=0.01
    )
    
    weights = WeightConfig(
        final_week_compression=3000,
        day_usage=2000,
        daily_balance=1500,
        preferred_periods=1000,
        distribution=1000,
        avoid_periods=-500,
        earlier_dates=10
    )
    
    # Run optimization with short time limit
    response = optimizer.optimize(request, weights, time_limit_seconds=5)
    
    # Verify response
    assert response is not None
    assert len(response.assignments) > 0
    assert response.metadata is not None
    assert response.metadata.duration_ms > 0
    assert response.metadata.solutions_found > 0
    
    # Check assignments meet basic requirements
    class_counts = {}
    for assignment in response.assignments:
        class_counts[assignment.name] = class_counts.get(assignment.name, 0) + 1
        
    # Each class should have at least minPeriodsPerWeek * number_of_weeks assignments
    weeks = (
        datetime.strptime(request.endDate, "%Y-%m-%d") - 
        datetime.strptime(request.startDate, "%Y-%m-%d")
    ).days // 7 + 1
    min_assignments = request.constraints.minPeriodsPerWeek * weeks
    
    for class_id in [c.id for c in request.classes]:
        assert class_counts.get(class_id, 0) >= min_assignments

def test_genetic_crossover():
    """Test crossover operation between chromosomes."""
    request = create_test_request()
    parent1 = ScheduleChromosome(request)
    parent2 = ScheduleChromosome(request)
    
    parent1.initialize_random()
    parent2.initialize_random()
    
    child1, child2 = parent1.crossover(parent2)
    
    # Verify children are valid
    assert child1.validate()
    assert child2.validate()
    assert len(child1.genes) == len(parent1.genes)
    assert len(child2.genes) == len(parent2.genes)
    
    # Verify children have genes from both parents
    parent1_genes = set((g.class_id, g.day_of_week, g.period, g.week) for g in parent1.genes)
    parent2_genes = set((g.class_id, g.day_of_week, g.period, g.week) for g in parent2.genes)
    child1_genes = set((g.class_id, g.day_of_week, g.period, g.week) for g in child1.genes)
    
    # At least some genes should come from each parent
    assert child1_genes & parent1_genes
    assert child1_genes & parent2_genes

def test_genetic_mutation():
    """Test mutation operation on chromosomes."""
    request = create_test_request()
    chromosome = ScheduleChromosome(request)
    chromosome.initialize_random()
    
    # Copy original genes
    original_genes = [(g.class_id, g.day_of_week, g.period, g.week) 
                     for g in chromosome.genes]
    
    # Apply mutation with high rate to ensure changes
    chromosome.mutate(mutation_rate=0.5)
    
    # Verify chromosome is still valid
    assert chromosome.validate()
    
    # Check that some genes changed
    mutated_genes = [(g.class_id, g.day_of_week, g.period, g.week) 
                    for g in chromosome.genes]
    assert any(og != mg for og, mg in zip(original_genes, mutated_genes))
