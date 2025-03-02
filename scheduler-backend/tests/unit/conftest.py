"""Common test fixtures and setup for unit tests."""
import pytest
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from unittest.mock import patch
import tempfile

# Use the Agg backend for testing to avoid GUI issues
matplotlib.use('Agg')

# Work around matplotlib issue with _NoValueType
original_float = float
def safe_float(value):
    """Handle edge cases in float conversion, particularly for matplotlib."""
    if hasattr(value, '__class__') and value.__class__.__name__ == '_NoValueType':
        return 0.0
    return original_float(value)

# Patch float in matplotlib.figure to handle _NoValueType
@pytest.fixture(autouse=True)
def patch_matplotlib():
    """Patch matplotlib's float handling to work with mocks."""
    with patch('matplotlib.figure.float', safe_float):
        with patch('matplotlib.axes._base.float', safe_float):
            with patch('matplotlib.cm.float', safe_float):
                yield

@pytest.fixture(autouse=True)
def close_figures():
    """Automatically close figures after each test to prevent memory leaks and state issues."""
    yield
    plt.close('all')

@pytest.fixture
def sample_schedule_request():
    """Create a simple schedule request for testing."""
    from app.models import ScheduleRequest, Class, TimeSlot
    
    classes = [
        Class(
            id="class1",
            name="Math 101",
            grade="3",
            gradeGroup=2,
            equipmentNeeds=["whiteboard"],
            weeklyFrequency=3,
            instructorId="teacher1"
        ),
        Class(
            id="class2",
            name="Science 101",
            grade="3",
            gradeGroup=2,
            equipmentNeeds=["lab"],
            weeklyFrequency=2,
            instructorId="teacher2"
        )
    ]
    
    time_slots = [
        TimeSlot(dayOfWeek=1, period=1),
        TimeSlot(dayOfWeek=1, period=2),
        TimeSlot(dayOfWeek=2, period=1),
        TimeSlot(dayOfWeek=2, period=2),
        TimeSlot(dayOfWeek=3, period=1),
        TimeSlot(dayOfWeek=3, period=2),
    ]
    
    return ScheduleRequest(
        classes=classes,
        availableTimeSlots=time_slots,
        startPeriod=1,
        endPeriod=5,
        maxConsecutiveClassesRule="soft",
        startDate="2025-02-12",
        endDate="2025-02-26",
        allowConsecutiveClasses=True,
        requiredBreakPeriods=[4]
    )

@pytest.fixture
def real_chromosome(sample_schedule_request):
    """Create a real chromosome with genes for testing."""
    from app.scheduling.solvers.genetic.chromosome import ScheduleChromosome, Gene
    
    chromosome = ScheduleChromosome()
    chromosome.schedule_request = sample_schedule_request
    
    # Add some genes
    chromosome.genes = [
        Gene(class_id="class1", day_of_week=1, period=1),
        Gene(class_id="class1", day_of_week=2, period=2),
        Gene(class_id="class1", day_of_week=3, period=1),
        Gene(class_id="class2", day_of_week=1, period=2),
        Gene(class_id="class2", day_of_week=3, period=2)
    ]
    
    chromosome.fitness = 0.75
    chromosome.constraint_violations = ["Sample violation 1"]
    
    return chromosome

@pytest.fixture
def real_chromosome2(sample_schedule_request):
    """Create a second real chromosome with slightly different genes for testing."""
    from app.scheduling.solvers.genetic.chromosome import ScheduleChromosome, Gene
    
    chromosome = ScheduleChromosome()
    chromosome.schedule_request = sample_schedule_request
    
    # Add some genes with a different pattern
    chromosome.genes = [
        Gene(class_id="class1", day_of_week=1, period=1),
        Gene(class_id="class1", day_of_week=2, period=1),  # Changed from period 2
        Gene(class_id="class1", day_of_week=3, period=2),  # Changed from period 1
        Gene(class_id="class2", day_of_week=1, period=2),
        Gene(class_id="class2", day_of_week=2, period=2)   # Changed from day 3
    ]
    
    chromosome.fitness = 0.82
    chromosome.constraint_violations = ["Sample violation 2"]
    
    return chromosome

@pytest.fixture
def real_population(real_chromosome, real_chromosome2):
    """Create a realistic population for testing."""
    population = []
    
    # Add the fixture chromosomes
    population.append(real_chromosome)
    population.append(real_chromosome2)
    
    # Add some more variations
    for i in range(8):  # Add 8 more for a total of 10
        # Clone from the base chromosome but vary fitness
        from copy import deepcopy
        chrom = deepcopy(real_chromosome if i % 2 == 0 else real_chromosome2)
        chrom.fitness = 0.5 + (i / 20.0)  # Vary fitness from 0.5 to 0.9
        population.append(chrom)
    
    return population

@pytest.fixture
def real_population_manager(real_population):
    """Create a realistic population manager with history for testing."""
    from app.scheduling.solvers.genetic.population import PopulationManager
    import numpy as np
    
    # Create a mock population manager with actual history data
    manager = PopulationManager()
    
    # Set the current population
    manager.population = real_population
    
    # Create fake history data
    generations = 20
    manager.history = []
    manager._best_fitness_history = np.linspace(0.5, 0.9, generations).tolist()
    manager._avg_fitness_history = np.linspace(0.3, 0.7, generations).tolist()
    manager._diversity_history = np.linspace(0.8, 0.4, generations).tolist()
    
    return manager

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir
