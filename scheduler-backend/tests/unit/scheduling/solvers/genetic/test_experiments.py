"""Unit tests for genetic algorithm experiment framework."""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.models import ScheduleRequest, ScheduleResponse, WeightConfig, ScheduleMetadata
from app.scheduling.solvers.genetic.experiments import (
    ExperimentManager,
    ParameterGrid,
    ExperimentResult,
    StatsCollector,
    recommended_parameter_grid
)

# Mock data
@pytest.fixture
def mock_schedule_request():
    """Return a mock schedule request."""
    return ScheduleRequest(
        classes=[],
        instructorAvailability={},
        startDate="2025-01-01",
        endDate="2025-01-07"
    )

@pytest.fixture
def mock_schedule_response():
    """Return a mock schedule response."""
    return ScheduleResponse(
        assignments={},
        metadata=ScheduleMetadata(
            score=0.85,
            duration_ms=1500,
            solutions_found=10
        )
    )

@pytest.fixture
def mock_params():
    """Return mock genetic algorithm parameters."""
    return {
        "population_size": 100,
        "elite_size": 5,
        "mutation_rate": 0.1,
        "crossover_rate": 0.8,
        "use_adaptive_control": True
    }

@pytest.fixture
def mock_experiment_result():
    """Return a mock experiment result."""
    return ExperimentResult(
        parameters={
            "population_size": 100,
            "mutation_rate": 0.1
        },
        fitness=0.85,
        duration_ms=1500,
        generations=25,
        solutions_found=10,
        convergence_gen=15,
        generation_stats=[
            {"generation": 0, "best_fitness": 0.5, "avg_fitness": 0.3, "diversity": 0.8},
            {"generation": 1, "best_fitness": 0.6, "avg_fitness": 0.4, "diversity": 0.75}
        ]
    )


class TestParameterGrid:
    """Tests for the ParameterGrid class."""
    
    def test_generate_combinations(self):
        """Test generating parameter combinations."""
        param_space = {
            "population_size": [50, 100],
            "mutation_rate": [0.1, 0.2]
        }
        
        grid = ParameterGrid(param_space)
        combinations = grid.generate_combinations()
        
        assert len(combinations) == 4
        assert {"population_size": 50, "mutation_rate": 0.1} in combinations
        assert {"population_size": 50, "mutation_rate": 0.2} in combinations
        assert {"population_size": 100, "mutation_rate": 0.1} in combinations
        assert {"population_size": 100, "mutation_rate": 0.2} in combinations
    
    def test_generate_combinations_limit(self):
        """Test limiting the number of combinations."""
        param_space = {
            "population_size": [50, 100],
            "mutation_rate": [0.1, 0.2]
        }
        
        grid = ParameterGrid(param_space)
        combinations = grid.generate_combinations(max_combinations=2)
        
        assert len(combinations) == 2


class TestStatsCollector:
    """Tests for the StatsCollector class."""
    
    def test_add_generation_stats(self):
        """Test adding generation statistics."""
        collector = StatsCollector()
        
        collector.add_generation_stats(0, 0.5, 0.3, 0.8)
        collector.add_generation_stats(1, 0.6, 0.4, 0.75, 0.12, 0.82)
        
        stats = collector.get_stats()
        
        assert len(stats) == 2
        assert stats[0] == {"generation": 0, "best_fitness": 0.5, "avg_fitness": 0.3, "diversity": 0.8}
        assert stats[1] == {
            "generation": 1, 
            "best_fitness": 0.6, 
            "avg_fitness": 0.4, 
            "diversity": 0.75,
            "mutation_rate": 0.12,
            "crossover_rate": 0.82
        }
    
    def test_get_convergence_generation(self):
        """Test detecting convergence generation."""
        collector = StatsCollector()
        
        # Add stats with improving fitness
        for i in range(10):
            collector.add_generation_stats(
                i, 0.5 + i*0.05, 0.3 + i*0.03, 0.8 - i*0.02
            )
            
        # Add stats with minimal improvement (converged)
        for i in range(10, 20):
            collector.add_generation_stats(
                i, 0.95 + i*0.0001, 0.6 + i*0.0001, 0.6
            )
            
        conv_gen = collector.get_convergence_generation(window_size=5, threshold=0.001)
        
        # Should detect convergence around generation 10-15
        assert conv_gen is not None
        assert 10 <= conv_gen <= 15
        
    def test_no_convergence(self):
        """Test when no convergence is detected."""
        collector = StatsCollector()
        
        # Add stats with continuously improving fitness
        for i in range(10):
            collector.add_generation_stats(
                i, 0.5 + i*0.05, 0.3 + i*0.03, 0.8 - i*0.02
            )
            
        conv_gen = collector.get_convergence_generation()
        
        # Should not detect convergence
        assert conv_gen is None


class TestExperimentResult:
    """Tests for the ExperimentResult class."""
    
    def test_to_dict(self, mock_experiment_result):
        """Test converting result to dictionary."""
        result_dict = mock_experiment_result.to_dict()
        
        assert result_dict["parameters"] == mock_experiment_result.parameters
        assert result_dict["fitness"] == mock_experiment_result.fitness
        assert result_dict["duration_ms"] == mock_experiment_result.duration_ms
        assert result_dict["generations"] == mock_experiment_result.generations
        assert result_dict["solutions_found"] == mock_experiment_result.solutions_found
        assert result_dict["convergence_gen"] == mock_experiment_result.convergence_gen
        assert result_dict["generation_stats"] == mock_experiment_result.generation_stats
    
    def test_from_dict(self):
        """Test creating result from dictionary."""
        result_dict = {
            "parameters": {"population_size": 100, "mutation_rate": 0.1},
            "fitness": 0.85,
            "duration_ms": 1500,
            "generations": 25,
            "solutions_found": 10,
            "convergence_gen": 15,
            "generation_stats": [
                {"generation": 0, "best_fitness": 0.5, "avg_fitness": 0.3, "diversity": 0.8}
            ]
        }
        
        result = ExperimentResult.from_dict(result_dict)
        
        assert result.parameters == result_dict["parameters"]
        assert result.fitness == result_dict["fitness"]
        assert result.duration_ms == result_dict["duration_ms"]
        assert result.generations == result_dict["generations"]
        assert result.solutions_found == result_dict["solutions_found"]
        assert result.convergence_gen == result_dict["convergence_gen"]
        assert result.generation_stats == result_dict["generation_stats"]
        
    def test_from_dict_minimal(self):
        """Test creating result from minimal dictionary."""
        result_dict = {
            "parameters": {"population_size": 100},
            "fitness": 0.85,
            "duration_ms": 1500,
            "generations": 25,
            "solutions_found": 10
        }
        
        result = ExperimentResult.from_dict(result_dict)
        
        assert result.parameters == result_dict["parameters"]
        assert result.fitness == result_dict["fitness"]
        assert result.convergence_gen is None
        assert result.generation_stats == []


@patch('app.scheduling.solvers.genetic.optimizer.GeneticOptimizer')
class TestExperimentManager:
    """Tests for the ExperimentManager class."""
    
    def test_init(self, mock_optimizer, mock_schedule_request):
        """Test initializing experiment manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExperimentManager(mock_schedule_request, results_dir=tmpdir)
            
            assert manager.request == mock_schedule_request
            assert manager.weights is None
            assert manager.results_dir == Path(tmpdir)
            assert manager.results == []
    
    def test_run_single_experiment(self, mock_optimizer, mock_schedule_request, 
                                  mock_schedule_response, mock_params):
        """Test running a single experiment."""
        # Setup mock optimizer instance
        optimizer_instance = mock_optimizer.return_value
        optimizer_instance.optimize.return_value = mock_schedule_response
        optimizer_instance.generations_run = 25
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExperimentManager(mock_schedule_request, results_dir=tmpdir)
            
            # Run experiment
            result = manager.run_single_experiment(mock_params, collect_generation_stats=False)
            
            # Verify optimizer was created with correct parameters
            mock_optimizer.assert_called_once_with(**mock_params)
            
            # Verify optimizer.optimize was called
            optimizer_instance.optimize.assert_called_once()
            
            # Check result
            assert result.parameters == mock_params
            assert result.fitness == mock_schedule_response.metadata.score
            assert result.duration_ms == mock_schedule_response.metadata.duration_ms
            assert result.generations == 25
            assert result.solutions_found == mock_schedule_response.metadata.solutions_found
    
    def test_run_experiments(self, mock_optimizer, mock_schedule_request, 
                            mock_schedule_response, mock_params):
        """Test running multiple experiments."""
        # Setup mock optimizer instance
        optimizer_instance = mock_optimizer.return_value
        optimizer_instance.optimize.return_value = mock_schedule_response
        optimizer_instance.generations_run = 25
        
        # Create parameter grid
        param_space = {
            "population_size": [50, 100],
            "mutation_rate": [0.1, 0.2]
        }
        param_grid = ParameterGrid(param_space)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExperimentManager(mock_schedule_request, results_dir=tmpdir)
            
            # Run experiments
            results = manager.run_experiments(
                param_grid, 
                time_limit_seconds=30,
                collect_generation_stats=False
            )
            
            # Check results
            assert len(results) == 4
            assert len(manager.results) == 4
            
            # Verify optimizer.optimize was called 4 times
            assert optimizer_instance.optimize.call_count == 4
            
            # Check that results file was created
            results_file = Path(tmpdir) / "results.json"
            assert results_file.exists()
    
    def test_get_best_result(self, mock_optimizer, mock_schedule_request, 
                           mock_experiment_result):
        """Test getting best result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExperimentManager(mock_schedule_request, results_dir=tmpdir)
            
            # Add results with different fitness values
            result1 = ExperimentResult(
                parameters={"population_size": 50},
                fitness=0.75,
                duration_ms=1000,
                generations=20,
                solutions_found=5
            )
            
            result2 = ExperimentResult(
                parameters={"population_size": 100},
                fitness=0.85,
                duration_ms=1500,
                generations=25,
                solutions_found=10
            )
            
            result3 = ExperimentResult(
                parameters={"population_size": 200},
                fitness=0.80,
                duration_ms=2000,
                generations=30,
                solutions_found=15
            )
            
            manager.results = [result1, result2, result3]
            
            # Get best result
            best = manager.get_best_result()
            
            # Should be result2 with highest fitness
            assert best == result2
    
    def test_save_load_results(self, mock_optimizer, mock_schedule_request, 
                              mock_experiment_result):
        """Test saving and loading results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExperimentManager(mock_schedule_request, results_dir=tmpdir)
            
            # Add a result
            manager.results = [mock_experiment_result]
            
            # Save results
            manager._save_results()
            
            # Create new manager and load results
            new_manager = ExperimentManager(mock_schedule_request, results_dir=tmpdir)
            new_manager.load_results(Path(tmpdir) / "results.json")
            
            # Check that result was loaded correctly
            assert len(new_manager.results) == 1
            
            loaded_result = new_manager.results[0]
            assert loaded_result.parameters == mock_experiment_result.parameters
            assert loaded_result.fitness == mock_experiment_result.fitness
            assert loaded_result.duration_ms == mock_experiment_result.duration_ms
            assert loaded_result.generations == mock_experiment_result.generations
            assert loaded_result.convergence_gen == mock_experiment_result.convergence_gen


def test_recommended_parameter_grid():
    """Test the recommended parameter grid."""
    grid = recommended_parameter_grid()
    
    # Check that it returns a valid grid
    assert isinstance(grid, ParameterGrid)
    
    # Check that it has the expected parameters
    combinations = grid.generate_combinations()
    assert len(combinations) > 0
    
    # Check for expected parameters in the first combination
    first_combo = combinations[0]
    assert "population_size" in first_combo
    assert "mutation_rate" in first_combo
    assert "crossover_rate" in first_combo
