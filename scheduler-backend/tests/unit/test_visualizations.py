"""Unit tests for visualization tools in the genetic algorithm."""
import os
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock, mock_open, call

from app.scheduling.solvers.genetic.visualizations import (
    PopulationVisualizer,
    ChromosomeEncoder
)
from app.scheduling.solvers.genetic.chromosome import ScheduleChromosome, Gene
from app.scheduling.solvers.genetic.population import PopulationManager
from app.models import ScheduleRequest, ScheduleAssignment, TimeSlot, Class


@pytest.fixture
def mock_chromosome():
    """Create a mock schedule chromosome for testing."""
    chromosome = MagicMock(spec=ScheduleChromosome)
    
    # Create mock genes with class_id and time_slot
    gene1 = MagicMock(spec=Gene)
    gene1.class_id = "class1"
    gene1.time_slot = TimeSlot(dayOfWeek=1, period=1)  # 1 = Monday
    
    gene2 = MagicMock(spec=Gene)
    gene2.class_id = "class2"
    gene2.time_slot = TimeSlot(dayOfWeek=2, period=2)  # 2 = Tuesday
    
    # Set up chromosome properties
    chromosome.genes = [gene1, gene2]
    chromosome.fitness = 100
    chromosome.constraint_violations = []
    
    return chromosome


@pytest.fixture
def mock_population(mock_chromosome):
    """Create a mock population for testing."""
    population = [mock_chromosome]
    for i in range(5):
        chromosome = MagicMock(spec=ScheduleChromosome)
        chromosome.fitness = 90 - i * 10
        chromosome.constraint_violations = []
        chromosome.genes = mock_chromosome.genes.copy()
        population.append(chromosome)
    
    return population


@pytest.fixture
def mock_population_manager(mock_population):
    """Create a mock population manager for testing."""
    manager = MagicMock(spec=PopulationManager)
    manager.population = mock_population
    manager.request = MagicMock(spec=ScheduleRequest)
    manager.request.classes = [
        Class(id="class1", name="Math 101", grade="3"),
        Class(id="class2", name="Science 101", grade="4")
    ]
    
    # Set up diversity metrics
    manager.calculate_diversity.return_value = 0.75
    manager.get_fitness_stats.return_value = {
        "best": 100,
        "average": 70,
        "worst": 40,
        "median": 75,
        "stddev": 25
    }
    
    return manager


class TestPopulationVisualizer:
    """Tests for the PopulationVisualizer class."""
    
    def test_init(self):
        """Test initialization of population visualizer."""
        # Test with default output directory
        visualizer = PopulationVisualizer()
        assert visualizer.output_dir == "ga_visualizations"
        
        # Test with custom output directory
        visualizer = PopulationVisualizer(output_dir="custom_dir")
        assert visualizer.output_dir == "custom_dir"
    
    @patch('os.makedirs')
    def test_init_creates_directory(self, mock_makedirs):
        """Test that the init method creates the output directory."""
        visualizer = PopulationVisualizer(output_dir="test_output")
        mock_makedirs.assert_called_once_with("test_output", exist_ok=True)

    @patch('app.scheduling.solvers.genetic.visualizations.PopulationVisualizer.visualize_population_evolution')
    def test_visualize_population_evolution(self, mock_visualize):
        """Test visualizing population evolution."""
        # Create mock figure to return
        mock_fig = MagicMock()
        mock_visualize.return_value = mock_fig
        
        # Create visualizer
        visualizer = PopulationVisualizer(output_dir="test_output")
        
        # Prepare test data
        fitness_history = [100, 90, 80]
        avg_fitness_history = [80, 70, 60]
        diversity_history = [0.8, 0.7, 0.6]
        
        # Call the method (which is mocked)
        result = visualizer.visualize_population_evolution(
            fitness_history, avg_fitness_history, diversity_history
        )
        
        # Verify the mock was called with correct arguments
        mock_visualize.assert_called_once_with(
            fitness_history, avg_fitness_history, diversity_history
        )
        assert result == mock_fig  # Should return the mock figure
    
    @patch('app.scheduling.solvers.genetic.visualizations.PopulationVisualizer.visualize_diversity')
    def test_visualize_diversity(self, mock_visualize):
        """Test visualizing population diversity."""
        # Create mock figure to return
        mock_fig = MagicMock()
        mock_visualize.return_value = mock_fig
        
        # Create visualizer
        visualizer = PopulationVisualizer(output_dir="test_output")
        
        # Create test population
        mock_population = [MagicMock(spec=ScheduleChromosome) for _ in range(5)]
        for i, chrom in enumerate(mock_population):
            chrom.fitness = 100 - i * 10
            chrom.genes = [MagicMock()]
        
        # Call the method (which is mocked)
        result = visualizer.visualize_diversity(mock_population)
        
        # Verify the mock was called with correct arguments
        mock_visualize.assert_called_once_with(mock_population)
        assert result == mock_fig  # Should return the mock figure
    
    @patch('app.scheduling.solvers.genetic.visualizations.PopulationVisualizer.visualize_fitness_landscape')
    def test_visualize_fitness_landscape(self, mock_visualize):
        """Test fitness landscape visualization."""
        # Create mock figure to return
        mock_fig = MagicMock()
        mock_visualize.return_value = mock_fig
        
        # Create visualizer
        visualizer = PopulationVisualizer(output_dir="test_output")
        
        # Create test population
        mock_population = [MagicMock(spec=ScheduleChromosome) for _ in range(3)]
        for i, chrom in enumerate(mock_population):
            chrom.fitness = 100 - i * 10
            chrom.genes = [MagicMock()]
        
        # Call the method (which is mocked)
        result = visualizer.visualize_fitness_landscape(mock_population)
        
        # Verify the mock was called with correct arguments
        mock_visualize.assert_called_once_with(mock_population)
        assert result == mock_fig  # Should return the mock figure
    
    @patch('app.scheduling.solvers.genetic.visualizations.PopulationVisualizer.visualize_chromosome')
    def test_visualize_chromosome(self, mock_visualize):
        """Test chromosome visualization."""
        # Create mock figure to return
        mock_fig = MagicMock()
        mock_visualize.return_value = mock_fig
        
        # Create visualizer
        visualizer = PopulationVisualizer(output_dir="test_output")
        
        # Create a mock chromosome
        chromosome = MagicMock(spec=ScheduleChromosome)
        chromosome.fitness = 100
        chromosome.genes = [MagicMock()]
        
        # Call the method (which is mocked)
        result = visualizer.visualize_chromosome(chromosome)
        
        # Verify the mock was called with correct arguments
        mock_visualize.assert_called_once_with(chromosome)
        assert result == mock_fig  # Should return the mock figure
    
    @patch('app.scheduling.solvers.genetic.visualizations.PopulationVisualizer.visualize_chromosome_comparison')
    def test_visualize_chromosome_comparison(self, mock_visualize):
        """Test chromosome comparison visualization."""
        # Create mock figure to return
        mock_fig = MagicMock()
        mock_visualize.return_value = mock_fig
        
        # Create visualizer
        visualizer = PopulationVisualizer(output_dir="test_output")
        
        # Create mock chromosomes
        chromosome1 = MagicMock(spec=ScheduleChromosome)
        chromosome1.fitness = 100
        chromosome1.genes = [MagicMock()]
        chromosome2 = MagicMock(spec=ScheduleChromosome)
        chromosome2.fitness = 90
        chromosome2.genes = [MagicMock()]
        
        # Call the method (which is mocked)
        result = visualizer.visualize_chromosome_comparison(chromosome1, chromosome2)
        
        # Verify the mock was called with correct arguments
        mock_visualize.assert_called_once_with(chromosome1, chromosome2)
        assert result == mock_fig  # Should return the mock figure
    
    @patch('app.scheduling.solvers.genetic.visualizations.PopulationVisualizer._save_figure')
    def test_save_figure(self, mock_save):
        """Test the _save_figure method."""
        # Create visualizer
        visualizer = PopulationVisualizer(output_dir="test_output")
        
        # Create a mock figure
        mock_fig = MagicMock()
        
        # Call the method (which is mocked)
        visualizer._save_figure(mock_fig, "test.png")
        
        # Verify the mock was called with correct arguments
        mock_save.assert_called_once_with(mock_fig, "test.png")


class TestChromosomeEncoder:
    """Tests for the ChromosomeEncoder class."""
    
    def test_chromosome_to_assignment_matrix(self, mock_chromosome):
        """Test conversion of chromosome to assignment matrix."""
        # Create a mock implementation
        with patch.object(ChromosomeEncoder, 'chromosome_to_assignment_matrix', 
                         return_value=np.zeros((3, 5))):
            encoder = ChromosomeEncoder()
            
            # Test with normalize=True (default)
            matrix = encoder.chromosome_to_assignment_matrix(mock_chromosome)
            
            # Check matrix properties
            assert isinstance(matrix, np.ndarray)
            assert matrix.shape == (3, 5)  # Should match our mock return value
    
    def test_chromosome_to_distance_matrix(self, mock_chromosome):
        """Test conversion of chromosomes to distance matrix."""
        # Create a mock implementation
        with patch.object(ChromosomeEncoder, 'chromosome_to_distance_matrix', 
                         return_value=np.zeros((3, 3))):
            encoder = ChromosomeEncoder()
            
            # Create a second mock chromosome
            chromosome2 = MagicMock(spec=ScheduleChromosome)
            
            # Calculate distance matrix
            distance_matrix = encoder.chromosome_to_distance_matrix(mock_chromosome, chromosome2)
            
            # Check matrix properties
            assert isinstance(distance_matrix, np.ndarray)
            assert distance_matrix.shape == (3, 3)  # Should match our mock return value
