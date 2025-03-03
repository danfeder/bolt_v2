"""
Integration tests for the solver system

This module contains integration tests for the complete solver system,
including the factory, strategies, and configuration builder.
"""

import unittest
from unittest.mock import MagicMock, patch
import pytest

from app.models import ScheduleRequest, ScheduleResponse, ScheduleAssignment
from app.scheduling.abstractions.solver_factory import SolverFactory
from app.scheduling.abstractions.unified_strategy import UnifiedSolverStrategy
from app.scheduling.abstractions.concrete_strategies import ORToolsStrategy, GeneticAlgorithmStrategy, HybridStrategy
from app.scheduling.abstractions.configuration_builder import configure
from app.scheduling.abstractions.solver_config import SolverType, OptimizationLevel
from app.scheduling.container_init import initialize_container, register_strategies


class TestSolverIntegration(unittest.TestCase):
    """Integration tests for the solver system"""
    
    def setUp(self):
        """Set up the test environment"""
        # Initialize the dependency container
        self.container = initialize_container()
        
        # Register the strategies
        register_strategies(self.container)
        
        # Get the solver factory
        self.factory = self.container.resolve(SolverFactory)
        
        # Create a sample request
        self.request = MagicMock(spec=ScheduleRequest)
        self.request.classes = [MagicMock() for _ in range(5)]
        self.request.instructorAvailability = [MagicMock() for _ in range(3)]
        
    def test_factory_registration(self):
        """Test that strategies are registered with the factory"""
        # Check that all strategies are registered
        strategy_names = self.factory.get_strategy_names()
        self.assertIn("unified", strategy_names)
        self.assertIn("or_tools", strategy_names)
        self.assertIn("genetic", strategy_names)
        self.assertIn("hybrid", strategy_names)
        
    def test_create_strategy_with_builder(self):
        """Test creating a strategy with the builder"""
        # Configure a strategy using the builder
        strategy = self.factory.create_strategy_with_builder(
            "unified",
            lambda b: b.with_solver_type(SolverType.UNIFIED)
                       .with_optimization_level(OptimizationLevel.QUALITY)
                       .with_timeout(90)
                       .with_max_iterations(1500)
                       .with_relaxation(True, "LOW")
                       .with_weight("constraint1", 10)
        )
        
        # Check that the strategy was created
        self.assertIsNotNone(strategy)
        self.assertIsInstance(strategy, UnifiedSolverStrategy)
        
        # Check that the configuration was applied
        self.assertEqual(strategy._timeout_seconds, 90)
        self.assertEqual(strategy._max_iterations, 1500)
        self.assertTrue(strategy._enable_relaxation)
        self.assertEqual(strategy._weights, {"constraint1": 10})
        
    @patch('app.scheduling.abstractions.unified_strategy.UnifiedSolverStrategy.solve')
    def test_strategy_selection(self, mock_solve):
        """Test selecting the best strategy for a request"""
        # Configure the mock to return a successful result
        mock_result = MagicMock()
        mock_result.success = True
        mock_solve.return_value = mock_result
        
        # Create a configuration
        config = configure().with_solver_type(SolverType.UNIFIED).build()
        
        # Create a strategy for the request
        strategy = self.factory.create_strategy_for_request(self.request, config)
        
        # Check that the correct strategy was selected
        self.assertIsNotNone(strategy)
        self.assertIsInstance(strategy, UnifiedSolverStrategy)
        
    @patch('app.scheduling.abstractions.unified_strategy.UnifiedSolverStrategy.solve')
    def test_full_solving_flow(self, mock_solve):
        """Test the complete solving flow"""
        # Configure the mock to return a successful result
        mock_result = MagicMock()
        mock_result.success = True
        mock_solve.return_value = mock_result
        
        # Create a configuration with the builder
        config = configure().with_solver_type("UNIFIED").with_timeout(120).build()
        
        # Create a strategy for the request
        strategy = self.factory.create_strategy_for_request(self.request, config)
        
        # Solve the request
        result = strategy.solve(self.request, config.__dict__)
        
        # Check that the result is successful
        self.assertTrue(result.success)
        
        # Check that the mock was called with the correct arguments
        mock_solve.assert_called_once_with(self.request, config.__dict__)
        
    def test_get_strategy_capabilities(self):
        """Test getting strategy capabilities"""
        # Get capabilities for a known strategy
        capabilities = self.factory.get_strategy_capabilities("unified")
        
        # Check that the capabilities include expected values
        self.assertIn("scheduling", capabilities)
        self.assertIn("exact_solutions", capabilities)
        self.assertIn("hard_constraints", capabilities)
        
        # Test with an unknown strategy
        unknown_capabilities = self.factory.get_strategy_capabilities("unknown")
        self.assertEqual(unknown_capabilities, set())


if __name__ == '__main__':
    unittest.main()
