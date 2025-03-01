"""Tests for the genetic algorithm adaptive controller."""
import pytest
import numpy as np
from app.scheduling.solvers.genetic.adaptation import AdaptiveController


class TestAdaptiveController:
    """Test suite for the AdaptiveController class."""

    def test_initialization(self):
        """Test that the controller initializes with correct parameters."""
        controller = AdaptiveController(
            base_mutation_rate=0.2,
            base_crossover_rate=0.7,
            diversity_threshold=0.2,
            adaptation_strength=0.3
        )
        
        assert controller.base_mutation_rate == 0.2
        assert controller.base_crossover_rate == 0.7
        assert controller.current_mutation_rate == 0.2
        assert controller.current_crossover_rate == 0.7
        assert controller.diversity_threshold == 0.2
        assert controller.adaptation_strength == 0.3
        assert len(controller.diversity_history) == 0
        assert len(controller.fitness_history) == 0
        
    def test_should_adapt(self):
        """Test that should_adapt returns correct values."""
        controller = AdaptiveController(adaptation_interval=5)
        
        # Initially should adapt
        assert controller.should_adapt(5) is True
        
        # After setting last adaptation, should only adapt at intervals
        controller.last_adaptation_generation = 0
        assert controller.should_adapt(1) is False
        assert controller.should_adapt(4) is False
        assert controller.should_adapt(5) is True
        assert controller.should_adapt(10) is True
        
    def test_update_history(self):
        """Test that history is updated correctly."""
        controller = AdaptiveController(history_window=3)
        
        # Add items and check they're stored
        controller.update_history(0.5, 0.3)
        assert controller.fitness_history == [0.5]
        assert controller.diversity_history == [0.3]
        
        # Add more items and check they're stored
        controller.update_history(0.6, 0.25)
        controller.update_history(0.7, 0.2)
        assert controller.fitness_history == [0.5, 0.6, 0.7]
        assert controller.diversity_history == [0.3, 0.25, 0.2]
        
        # Add one more and check window is maintained
        controller.update_history(0.8, 0.15)
        assert controller.fitness_history == [0.6, 0.7, 0.8]
        assert controller.diversity_history == [0.25, 0.2, 0.15]
        
    def test_diversity_trend(self):
        """Test diversity trend calculation."""
        controller = AdaptiveController()
        
        # With no history, trend should be 0
        assert controller.get_diversity_trend() == 0.0
        
        # With one item, trend should be 0
        controller.diversity_history = [0.5]
        assert controller.get_diversity_trend() == 0.0
        
        # With declining diversity, trend should be negative
        controller.diversity_history = [0.5, 0.4, 0.3, 0.2, 0.1]
        trend = controller.get_diversity_trend()
        assert trend < 0
        
        # With increasing diversity, trend should be positive
        controller.diversity_history = [0.1, 0.2, 0.3, 0.4, 0.5]
        trend = controller.get_diversity_trend()
        assert trend > 0
        
    def test_convergence_rate(self):
        """Test convergence rate calculation."""
        controller = AdaptiveController()
        
        # With no history, rate should be middle value
        assert controller.get_convergence_rate() == 0.5
        
        # With one item, rate should be middle value
        controller.fitness_history = [0.5]
        assert controller.get_convergence_rate() == 0.5
        
        # With improving fitness, rate should be positive
        controller.fitness_history = [100, 110, 120, 130, 140]
        rate = controller.get_convergence_rate()
        assert rate > 0
        
        # With stagnant fitness, rate should be near zero
        controller.fitness_history = [100, 100, 100, 100, 100]
        rate = controller.get_convergence_rate()
        assert rate == 0
        
    def test_adjust_mutation_rate(self):
        """Test mutation rate adjustment."""
        controller = AdaptiveController(
            base_mutation_rate=0.1,
            min_mutation_rate=0.05,
            max_mutation_rate=0.3,
            diversity_threshold=0.2
        )
        
        # With high diversity, rate should move toward base rate
        new_rate = controller.adjust_mutation_rate(0.3, 0.0)
        assert 0.1 <= new_rate <= 0.3
        
        # With low diversity, rate should increase
        new_rate = controller.adjust_mutation_rate(0.1, 0.0)
        assert new_rate > 0.1
        
        # With negative diversity trend, rate should increase more
        new_rate = controller.adjust_mutation_rate(0.1, -0.5)
        assert new_rate > 0.1
        
        # Rates should be clamped to limits
        controller.current_mutation_rate = 0.01
        new_rate = controller.adjust_mutation_rate(0.5, 0.0)
        assert new_rate >= 0.05
        
        controller.current_mutation_rate = 0.5
        new_rate = controller.adjust_mutation_rate(0.01, -1.0)
        assert new_rate <= 0.3
        
    def test_adapt_parameters(self):
        """Test the full parameter adaptation process."""
        controller = AdaptiveController(
            base_mutation_rate=0.1,
            base_crossover_rate=0.8,
            adaptation_interval=5
        )
        
        # Before adaptation interval, no change should occur
        controller.current_mutation_rate = 0.15
        controller.current_crossover_rate = 0.75
        controller.last_adaptation_generation = 0
        
        mut_rate, cross_rate = controller.adapt_parameters(3, 100, 50, 0.25)
        assert mut_rate == 0.15
        assert cross_rate == 0.75
        
        # At adaptation interval, parameters should change
        mut_rate, cross_rate = controller.adapt_parameters(5, 100, 50, 0.25)
        assert mut_rate != 0.15
        assert cross_rate != 0.75
        
        # After adaptation, last adaptation generation should be updated
        assert controller.last_adaptation_generation == 5