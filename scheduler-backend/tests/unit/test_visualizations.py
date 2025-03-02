"""Unit tests for visualization tools in the genetic algorithm."""
import os
import pytest
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from unittest.mock import patch, MagicMock, mock_open, call
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import random

from app.scheduling.solvers.genetic.visualizations import (
    PopulationVisualizer,
    ChromosomeEncoder
)
from app.scheduling.solvers.genetic.chromosome import ScheduleChromosome, Gene
from app.scheduling.solvers.genetic.population import PopulationManager
from app.models import (
    ScheduleRequest, 
    ScheduleAssignment, 
    TimeSlot, 
    Class, 
    WeeklySchedule,
    ScheduleConstraints,
    InstructorAvailability
)


# Monkey patch Gene class to add time_slot property for our tests
def time_slot_property(self):
    return TimeSlot(dayOfWeek=self.day_of_week, period=self.period)

# Add the property to the Gene class
Gene.time_slot = property(time_slot_property)


@pytest.fixture
def sample_schedule_request():
    """Create a sample schedule request for testing."""
    classes = [
        Class(
            id="class1",
            name="Math 101",
            grade="3",
            gradeGroup=2,
            equipmentNeeds=["whiteboard"],
            weeklySchedule=WeeklySchedule()
        ),
        Class(
            id="class2",
            name="Science 101",
            grade="4",
            gradeGroup=3,
            equipmentNeeds=["lab equipment"],
            weeklySchedule=WeeklySchedule()
        )
    ]
    
    # Create schedule constraints
    constraints = ScheduleConstraints(
        maxClassesPerDay=4,
        maxClassesPerWeek=16,
        minPeriodsPerWeek=8,
        maxConsecutiveClasses=2,
        consecutiveClassesRule="soft",
        startDate="2025-02-12",
        endDate="2025-02-26",
        allowConsecutiveClasses=True,
        requiredBreakPeriods=[4]  # lunch period
    )
    
    # Create schedule request
    request = ScheduleRequest(
        classes=classes,
        instructorAvailability=[],
        startDate="2025-02-12",
        endDate="2025-02-26",
        constraints=constraints
    )
    
    return request


@pytest.fixture
def real_chromosome(sample_schedule_request):
    """Create a real schedule chromosome for testing."""
    chromosome = ScheduleChromosome(sample_schedule_request)
    
    # Create genes manually instead of randomly
    genes = [
        Gene(class_id="class1", day_of_week=1, period=1, week=0),  # Monday, period 1, week 0
        Gene(class_id="class1", day_of_week=3, period=2, week=0),  # Wednesday, period 2, week 0
        Gene(class_id="class1", day_of_week=5, period=3, week=0),  # Friday, period 3, week 0
        Gene(class_id="class1", day_of_week=2, period=2, week=1),  # Tuesday, period 2, week 1
        Gene(class_id="class2", day_of_week=2, period=1, week=0),  # Tuesday, period 1, week 0
        Gene(class_id="class2", day_of_week=4, period=3, week=0),  # Thursday, period 3, week 0
        Gene(class_id="class2", day_of_week=1, period=2, week=1),  # Monday, period 2, week 1
        Gene(class_id="class2", day_of_week=3, period=1, week=1),  # Wednesday, period 1, week 1
    ]
    
    chromosome.genes = genes
    chromosome.fitness = 85.5
    chromosome.constraint_violations = []
    return chromosome


@pytest.fixture
def real_chromosome2(sample_schedule_request):
    """Create a second real chromosome with slight differences for comparison testing."""
    chromosome = ScheduleChromosome(sample_schedule_request)
    
    # Create genes with some differences from the first chromosome
    genes = [
        Gene(class_id="class1", day_of_week=1, period=2, week=0),  # Different period
        Gene(class_id="class1", day_of_week=3, period=2, week=0),  # Same
        Gene(class_id="class1", day_of_week=5, period=1, week=0),  # Different period
        Gene(class_id="class1", day_of_week=2, period=2, week=1),  # Same
        Gene(class_id="class2", day_of_week=2, period=3, week=0),  # Different period
        Gene(class_id="class2", day_of_week=4, period=3, week=0),  # Same
        Gene(class_id="class2", day_of_week=1, period=3, week=1),  # Different period
        Gene(class_id="class2", day_of_week=3, period=1, week=1),  # Same
    ]
    
    chromosome.genes = genes
    chromosome.fitness = 75.0
    chromosome.constraint_violations = []
    return chromosome


@pytest.fixture
def empty_chromosome(sample_schedule_request):
    """Create an empty chromosome for testing."""
    chromosome = ScheduleChromosome(sample_schedule_request)
    chromosome.genes = []
    chromosome.fitness = 0.0
    chromosome.constraint_violations = []
    return chromosome


@pytest.fixture
def real_population(real_chromosome, sample_schedule_request):
    """Create a real population for testing."""
    # Start with our real chromosome
    population = [real_chromosome]
    
    # Add a few more chromosomes with varying fitness
    for i in range(5):
        chromosome = ScheduleChromosome(sample_schedule_request)
        
        # Create genes with slight variations
        genes = []
        for gene in real_chromosome.genes:
            # Copy with slight modifications
            new_gene = Gene(
                class_id=gene.class_id,
                day_of_week=max(1, min(5, gene.day_of_week + random.randint(-1, 1))),
                period=max(1, min(8, gene.period + random.randint(-1, 1))),
                week=gene.week
            )
            genes.append(new_gene)
        
        chromosome.genes = genes
        chromosome.fitness = 80.0 - i * 10.0  # Decreasing fitness values
        chromosome.constraint_violations = []
        population.append(chromosome)
    
    return population


@pytest.fixture
def real_population_manager(sample_schedule_request):
    """Create a real population manager for testing."""
    # Initialize with a small population size for testing
    manager = PopulationManager(
        size=6,
        request=sample_schedule_request,
        elite_size=2,
        mutation_rate=0.1,
        crossover_rate=0.8
    )
    
    # Set up a simple evolution history for testing
    generations = 10
    manager.generation = generations
    
    # Create fitness history with an improving trend - using NumPy arrays instead of lists
    fitness_history = np.array([50.0 + i * 5 for i in range(generations)])
    avg_fitness_history = np.array([40.0 + i * 4 for i in range(generations)])
    diversity_history = np.array([0.8 - i * 0.05 for i in range(generations)])
    
    # Add these to the manager
    manager._fitness_history = fitness_history
    manager._avg_fitness_history = avg_fitness_history
    manager._diversity_history = diversity_history
    
    return manager


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Clean up after the test
    shutil.rmtree(temp_dir)


class TestPopulationVisualizer:
    """Tests for the PopulationVisualizer class."""
    
    def test_init(self):
        """Test initialization of the visualizer."""
        output_dir = "test_output"
        visualizer = PopulationVisualizer(output_dir=output_dir)
        assert visualizer.output_dir == output_dir
        
        # Clean up
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
    
    def test_init_creates_directory(self, temp_output_dir):
        """Test that initialization creates output directory if it doesn't exist."""
        test_dir = os.path.join(temp_output_dir, "test_output")
        visualizer = PopulationVisualizer(output_dir=test_dir)
        assert os.path.exists(test_dir)
    
    def test_save_figure(self, temp_output_dir):
        """Test saving a figure to file."""
        visualizer = PopulationVisualizer(output_dir=temp_output_dir)
        
        # Create a simple figure using a mock
        with patch('matplotlib.pyplot.subplots', autospec=True) as mock_subplots:
            fig = MagicMock()
            ax = MagicMock()
            mock_subplots.return_value = (fig, ax)
            
            # Mock the savefig method
            with patch.object(fig, 'savefig') as mock_savefig:
                # Call the method under test
                test_filename = "test_figure.png"
                visualizer._save_figure(fig, test_filename)
                
                # Verify the mock was called correctly
                full_path = os.path.join(temp_output_dir, test_filename)
                mock_savefig.assert_called_once_with(full_path, dpi=300, bbox_inches='tight')
    
    @patch('matplotlib.pyplot.subplots', autospec=True)
    def test_visualize_diversity_actual(self, mock_subplots, real_population):
        """Test actual diversity visualization with real population."""
        # Setup mocks
        fig = MagicMock()
        ax1 = MagicMock()
        ax2 = MagicMock()
        axs = (ax1, ax2)
        mock_subplots.return_value = (fig, axs)
        
        # Mock all the dependencies that could cause issues
        with patch('seaborn.histplot', autospec=True) as mock_histplot, \
             patch('seaborn.heatmap', autospec=True) as mock_heatmap, \
             patch('numpy.tril', autospec=True) as mock_tril, \
             patch('matplotlib.pyplot.colorbar', autospec=True) as mock_colorbar:
            
            # Setup the mocks with appropriate returns
            mock_histplot.return_value = ax1
            mock_heatmap.return_value = ax2
            mock_tril.return_value = np.zeros((5, 5))
            mock_colorbar.return_value = MagicMock()
            
            # Ensure all chromosomes have valid fitness values
            for chrom in real_population:
                if not hasattr(chrom, 'fitness') or chrom.fitness is None:
                    chrom.fitness = 100.0
            
            visualizer = PopulationVisualizer()
            
            # Run the method
            result = visualizer.visualize_diversity(real_population)
            
            # Assertions
            assert result is fig
    
    @patch('matplotlib.pyplot.subplots', autospec=True)
    @patch('sklearn.decomposition.PCA')
    def test_visualize_fitness_landscape_actual(self, mock_pca, mock_subplots, real_population):
        """Test actual fitness landscape visualization."""
        # Setup mocks
        fig = MagicMock()
        ax = MagicMock()
        mock_subplots.return_value = (fig, ax)
        
        # Mock PCA
        pca_instance = MagicMock()
        mock_pca.return_value = pca_instance
        pca_instance.fit_transform.return_value = np.array([[0, 0], [1, 1], [2, 2], [3, 3], [4, 4], [5, 5]])
        
        # Make sure each chromosome has genes with the required attributes
        for chrom in real_population:
            if not hasattr(chrom, 'fitness') or chrom.fitness is None:
                chrom.fitness = 100.0
                
            for gene in chrom.genes:
                if not hasattr(gene, 'class_id'):
                    gene.class_id = "class1"  # Default class ID
                
                # Ensure time_slot is properly mocked
                if not hasattr(gene, 'time_slot'):
                    gene.time_slot = MagicMock()
                    gene.time_slot.dayOfWeek = gene.day_of_week
                    gene.time_slot.period = gene.period
        
        # Patch both dimensionality reduction methods
        with patch('sklearn.manifold.TSNE', autospec=True) as mock_tsne, \
             patch('matplotlib.pyplot.scatter', autospec=True) as mock_scatter, \
             patch('matplotlib.pyplot.colorbar', autospec=True) as mock_colorbar:
            
            tsne_instance = MagicMock()
            mock_tsne.return_value = tsne_instance
            tsne_instance.fit_transform.return_value = np.array([[0, 0], [1, 1], [2, 2], [3, 3], [4, 4], [5, 5]])
            mock_scatter.return_value = MagicMock()
            mock_colorbar.return_value = MagicMock()
            
            visualizer = PopulationVisualizer()
            
            # Run the method
            result = visualizer.visualize_fitness_landscape(real_population)
            
            # Assertions
            assert result is fig
    
    @patch('matplotlib.pyplot.subplots', autospec=True)
    def test_visualize_fitness_landscape_empty(self, mock_subplots):
        """Test fitness landscape visualization with insufficient population."""
        # Setup mocks for a simple figure
        fig = MagicMock()
        ax = MagicMock()
        mock_subplots.return_value = (fig, ax)
        
        visualizer = PopulationVisualizer()
        
        # Create a small population (less than 3 chromosomes)
        small_population = []
        for _ in range(2):
            chrom = MagicMock(spec=ScheduleChromosome)
            chrom.fitness = 50.0  # Set a concrete number
            chrom.genes = []  # Ensure genes are empty
            small_population.append(chrom)
        
        # We need to actually patch the text method on the axes, not on plt directly
        result = visualizer.visualize_fitness_landscape(small_population)
        
        # Assertions
        assert result is fig
        
        # Since we're using ax.text() in the code not plt.text(),
        # verify that our ax mock's text method was called
        ax.text.assert_called_once_with(
            0.5, 0.5,
            "Insufficient chromosomes for fitness landscape analysis (need at least 3)",
            horizontalalignment='center', verticalalignment='center',
            transform=ax.transAxes, fontsize=12
        )
    
    @patch('matplotlib.pyplot.subplots', autospec=True)
    def test_visualize_chromosome_empty(self, mock_subplots, real_chromosome):
        """Test chromosome visualization with empty genes."""
        # Setup mocks
        fig = MagicMock()
        ax1 = MagicMock()
        ax2 = MagicMock()
        axs = (ax1, ax2)
        mock_subplots.return_value = (fig, axs)
        
        # Create an empty chromosome
        empty_chrom = real_chromosome
        empty_chrom.genes = []
        
        visualizer = PopulationVisualizer()
        
        # Run the method
        result = visualizer.visualize_chromosome(empty_chrom)
        
        # Assertions
        assert result is fig
    
    @patch('matplotlib.pyplot.subplots', autospec=True)
    def test_visualize_chromosome_actual(self, mock_subplots, real_chromosome, temp_output_dir):
        """Test chromosome visualization with actual data."""
        # Setup mocks
        fig = MagicMock()
        ax1 = MagicMock()
        ax2 = MagicMock()
        axs = (ax1, ax2)
        mock_subplots.return_value = (fig, axs)
        
        visualizer = PopulationVisualizer(output_dir=temp_output_dir)
        
        # Run the method with the correct parameter (save_path instead of save)
        save_path = os.path.join(temp_output_dir, "test_chromosome.png")
        result = visualizer.visualize_chromosome(real_chromosome, save_path=save_path)
        
        # Assertions
        assert result is fig
    
    @patch('matplotlib.pyplot.subplots', autospec=True)
    def test_visualize_chromosome_comparison_empty(self, mock_subplots, real_chromosome):
        """Test chromosome comparison visualization with empty genes."""
        # Setup mocks
        fig = MagicMock()
        ax = MagicMock()
        mock_subplots.return_value = (fig, ax)
        
        # Create empty chromosomes by starting with real_chromosome but emptying genes
        chrom1 = real_chromosome
        chrom1.genes = []
        chrom2 = real_chromosome
        chrom2.genes = []
        
        visualizer = PopulationVisualizer()
        
        # Run the method
        result = visualizer.visualize_chromosome_comparison(chrom1, chrom2)
        
        # Assertions
        assert result is fig
    
    @patch('matplotlib.pyplot.subplots', autospec=True)
    def test_visualize_chromosome_comparison_actual(self, mock_subplots, real_chromosome, real_chromosome2):
        """Test chromosome comparison visualization with actual data."""
        # Setup mocks
        fig = MagicMock()
        ax1 = MagicMock()
        ax2 = MagicMock()
        ax3 = MagicMock()
        axs = (ax1, ax2, ax3)
        mock_subplots.return_value = (fig, axs)
        
        visualizer = PopulationVisualizer()
        
        # Run the method
        result = visualizer.visualize_chromosome_comparison(real_chromosome, real_chromosome2)
        
        # Assertions
        assert result is fig
    
    def test_visualize_population_evolution_actual(self):
        """Test population evolution visualization with actual data."""
        # Create a mock for the figure and axes
        with patch('matplotlib.figure.Figure') as mock_figure_class, \
             patch('matplotlib.gridspec.GridSpec') as mock_gridspec, \
             patch('matplotlib.pyplot.figure', return_value=MagicMock()) as mock_figure, \
             patch('matplotlib.pyplot.subplot') as mock_subplot:
            
            # Create mock axes with plot method
            ax1 = MagicMock()
            ax2 = MagicMock()  
            ax3 = MagicMock()
            
            # Configure subplot to return our mocked axes
            mock_subplot.side_effect = [ax1, ax2, ax3]
            
            # Patch other plt methods that might be called
            with patch('matplotlib.pyplot.suptitle') as mock_suptitle, \
                 patch('matplotlib.pyplot.tight_layout') as mock_tight_layout:
                
                visualizer = PopulationVisualizer()
                
                # Create non-zero test data
                fitness_history = [10.0, 11.0, 12.0, 13.0, 14.0]
                avg_fitness_history = [5.0, 6.0, 7.0, 8.0, 9.0]
                diversity_history = [0.1, 0.2, 0.3, 0.4, 0.5]
                
                # Call the method
                result = visualizer.visualize_population_evolution(
                    fitness_history=fitness_history,
                    avg_fitness_history=avg_fitness_history,
                    diversity_history=diversity_history
                )
                
                # Verify that ax1.plot was called (not plt.plot)
                assert ax1.plot.called, "Expected ax1.plot to be called"
                assert ax2.plot.called, "Expected ax2.plot to be called"
    
    def test_visualize_population_evolution_empty(self):
        """Test population evolution visualization with empty history."""
        visualizer = PopulationVisualizer()
        
        # Create empty history data
        fitness_history = []
        avg_fitness = []
        diversity = []
        
        # Mock plt.subplots to properly test this case
        with patch('matplotlib.pyplot.subplots', autospec=True) as mock_subplots:
            
            # Setup mocks
            fig = MagicMock()
            ax = MagicMock()
            mock_subplots.return_value = (fig, ax)
            
            # Run the method with the corrected parameter names
            result = visualizer.visualize_population_evolution(
                fitness_history=fitness_history,
                avg_fitness_history=avg_fitness,
                diversity_history=diversity
            )
            
            # Assertions
            assert result is fig
            # Verify that ax.text was called (note: not plt.text)
            assert ax.text.called, "Expected ax.text to be called with an empty data message"


class TestChromosomeEncoder:
    """Tests for the ChromosomeEncoder class."""
    
    def test_chromosome_to_assignment_matrix_empty(self, sample_schedule_request):
        """Test conversion of an empty chromosome to assignment matrix."""
        encoder = ChromosomeEncoder()
        
        # Create a chromosome with no genes
        empty_chromosome = ScheduleChromosome(sample_schedule_request)
        empty_chromosome.genes = []
        
        # Should return an empty array
        matrix = encoder.chromosome_to_assignment_matrix(empty_chromosome)
        assert isinstance(matrix, np.ndarray)
        assert matrix.size == 0
    
    def test_chromosome_to_assignment_matrix(self, real_chromosome):
        """Test conversion of a chromosome to class-timeslot assignment matrix."""
        encoder = ChromosomeEncoder()
        
        # Normalized matrix
        matrix = encoder.chromosome_to_assignment_matrix(real_chromosome)
        assert isinstance(matrix, np.ndarray)
        assert matrix.shape[0] > 0  # Should have rows for classes
        assert matrix.shape[1] > 0  # Should have columns for time slots
        assert np.max(matrix) <= 1.0  # Should be normalized to [0,1]
        assert np.min(matrix) >= 0.0  # No negative values
        
        # Unnormalized matrix
        matrix_unnormalized = encoder.chromosome_to_assignment_matrix(real_chromosome, normalize=False)
        assert isinstance(matrix_unnormalized, np.ndarray)
        assert matrix_unnormalized.shape == matrix.shape
        assert np.max(matrix_unnormalized) == 1.0  # Binary values only
        assert np.min(matrix_unnormalized) == 0.0  # Binary values only
        
        # Check specific assignments
        # We know there should be at least two assignments from our test data
        assert matrix_unnormalized[0, 0] == 1.0
        assert matrix_unnormalized[1, 1] == 1.0
    
    def test_chromosome_to_distance_matrix(self, real_chromosome, sample_schedule_request):
        """Test chromosome_to_distance_matrix with two different chromosomes."""
        encoder = ChromosomeEncoder()
        
        # Create a second chromosome with different time slots
        chromosome2 = ScheduleChromosome(sample_schedule_request)
        
        # Create genes with some differences from the first chromosome
        genes2 = [
            Gene(class_id="class1", day_of_week=2, period=2, week=0),  # Different from real_chromosome
            Gene(class_id="class2", day_of_week=3, period=3, week=0)   # Different from real_chromosome
        ]
        
        chromosome2.genes = genes2
        
        # Calculate distance matrix
        distance_matrix = encoder.chromosome_to_distance_matrix(real_chromosome, chromosome2)
        
        # Should be a square matrix with size equal to the number of unique classes
        assert distance_matrix.shape == (2, 2)  # 2 classes in our test data
        
        # The distance should be >= 0 for different assignments
        assert distance_matrix[0, 0] >= 0  # Distance between same class across chromosomes
        assert distance_matrix[1, 1] >= 0  # Distance between same class across chromosomes
        assert distance_matrix[0, 1] >= 0  # Distance between different classes
        assert distance_matrix[1, 0] >= 0  # Distance between different classes
        assert np.isclose(distance_matrix[0, 1], distance_matrix[1, 0])  # Should be symmetric
    
    def test_chromosome_to_distance_matrix_identical(self, real_chromosome):
        """Test distance matrix with identical chromosomes."""
        encoder = ChromosomeEncoder()
        
        # Distance between the same chromosome should be zero
        distance_matrix = encoder.chromosome_to_distance_matrix(real_chromosome, real_chromosome)
        
        # Should be a square matrix with size equal to the number of unique classes
        assert distance_matrix.shape == (2, 2)  # 2 classes in our test data
        
        # The diagonal elements should be zero (distance from class to itself)
        assert distance_matrix[0, 0] == 0
        assert distance_matrix[1, 1] == 0
        
        # The off-diagonal elements represent distances between different classes
        # These might not be zero, since they represent relationships between different classes
        assert distance_matrix[0, 1] == distance_matrix[1, 0]  # Should be symmetric
    
    def test_chromosome_to_distance_matrix_empty(self, empty_chromosome):
        """Test distance matrix with empty chromosomes."""
        encoder = ChromosomeEncoder()
        
        # Distance matrix for empty chromosomes should be empty
        distance_matrix = encoder.chromosome_to_distance_matrix(empty_chromosome, empty_chromosome)
        assert distance_matrix.size == 0
