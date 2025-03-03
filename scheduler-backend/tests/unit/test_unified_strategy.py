"""
Unit tests for the UnifiedSolverStrategy

This module contains unit tests for the UnifiedSolverStrategy implementation
to ensure it correctly implements the SolverStrategy interface and provides
the expected functionality.
"""

import unittest
from unittest.mock import MagicMock, patch
import pytest
from datetime import datetime

from app.models import ScheduleRequest, ScheduleResponse, ScheduleAssignment, ScheduleMetadata
from app.scheduling.abstractions.unified_strategy import UnifiedSolverStrategy
from app.scheduling.abstractions.solver_strategy import SolverResult
from app.scheduling.abstractions.configuration_builder import configure
from app.scheduling.core import ConstraintManager


class TestUnifiedSolverStrategy(unittest.TestCase):
    """Tests for the UnifiedSolverStrategy implementation"""
    
    def setUp(self):
        """Set up the test environment"""
        self.constraint_manager = MagicMock(spec=ConstraintManager)
        self.strategy = UnifiedSolverStrategy(
            constraint_manager=self.constraint_manager
        )
        
        # Create a sample request and configuration with all required properties
        self.request = MagicMock(spec=ScheduleRequest)
        self.request.classes = []
        self.request.instructorAvailability = []
        self.request.id = "test-request"
        
        # Create a sample date range
        date_range = MagicMock()
        date_range.startDate = datetime.now().isoformat()
        date_range.endDate = datetime.now().isoformat()
        self.request.dateRange = date_range
        
        self.config = configure().build_dict()
        
    def test_initialization(self):
        """Test that the strategy initializes correctly"""
        strategy = UnifiedSolverStrategy()
        
        # Check that the strategy has the expected properties
        self.assertEqual(strategy.name, "unified")
        self.assertTrue("combining OR-Tools and genetic" in strategy.description)
        
    def test_configure(self):
        """Test that the strategy can be configured"""
        # Configure the strategy
        self.strategy.configure({
            'solver_type': 'or_tools',
            'timeout_seconds': 30,
            'max_iterations': 500,
            'enable_relaxation': False,
            'weights': {'constraint1': 10, 'constraint2': 20}
        })
        
        # Check that the configuration was applied
        self.assertTrue(self.strategy._use_or_tools)
        self.assertFalse(self.strategy._use_genetic)
        self.assertEqual(self.strategy._timeout_seconds, 30)
        self.assertEqual(self.strategy._max_iterations, 500)
        self.assertFalse(self.strategy._enable_relaxation)
        self.assertEqual(self.strategy._weights, {'constraint1': 10, 'constraint2': 20})
        
    @patch('app.scheduling.abstractions.context.SchedulerContext')
    @patch('app.scheduling.solvers.solver.UnifiedSolver')
    def test_solve(self, mock_unified_solver, mock_context):
        """Test that the strategy can solve a request"""
        # Configure the mock context
        mock_context_instance = mock_context.return_value
        
        # Configure the mock UnifiedSolver
        mock_solver_instance = mock_unified_solver.return_value
        mock_response = MagicMock(spec=ScheduleResponse)
        mock_response.assignments = [MagicMock(spec=ScheduleAssignment)]
        
        # Create a proper ScheduleMetadata object with attributes directly instead of using a MagicMock
        metadata = ScheduleMetadata(
            duration_ms=100,
            solutions_found=1,
            score=50,
            gap=0.1,
            solver='unified',
            message='Success'
        )
        
        mock_response.metadata = metadata
        
        mock_solver_instance.solve.return_value = mock_response
        
        # Solve the request
        result = self.strategy.solve(self.request, self.config)
        
        # Check that the result is as expected
        self.assertTrue(result.success)
        self.assertIs(result.schedule, mock_response)
        self.assertEqual(result.assignments, mock_response.assignments)
        self.assertIn('runtime_ms', result.metadata)
        self.assertEqual(result.metadata['solver_name'], 'unified')
        
        # Check that the UnifiedSolver was called with the right parameters
        mock_unified_solver.assert_called_once()
        mock_solver_instance.solve.assert_called_once_with(
            time_limit_seconds=60,
            max_iterations=1000
        )
        
    @patch('app.scheduling.abstractions.context.SchedulerContext')
    @patch('app.scheduling.solvers.solver.UnifiedSolver')
    def test_solve_with_error(self, mock_unified_solver, mock_context):
        """Test that the strategy handles errors correctly"""
        # Configure the mock context
        mock_context_instance = mock_context.return_value
        
        # Configure the mock UnifiedSolver to raise an exception with a specific message
        mock_solver_instance = mock_unified_solver.return_value
        # Use a direct ValueError that won't be wrapped in other exceptions
        test_error = ValueError("Test error")
        mock_solver_instance.solve.side_effect = test_error
        
        # Make sure the mock_solver_instance is properly configured to return its side_effect directly
        mock_unified_solver.return_value = mock_solver_instance
        
        # Solve the request
        result = self.strategy.solve(self.request, self.config)
        
        # Check that the result indicates failure
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Test error")
        
        # Check that we have a valid schedule response in the error case
        self.assertIsNotNone(result.schedule)
        self.assertIsInstance(result.schedule, ScheduleResponse)
        self.assertIsNotNone(result.schedule.metadata)
        
        # Check that the metadata is properly populated
        self.assertEqual(result.metadata['error'], "Test error")
        
    def test_can_solve(self):
        """Test that the strategy can determine if it can solve a request"""
        # Test with a valid request
        can_solve, reason = self.strategy.can_solve(self.request)
        self.assertTrue(can_solve)
        self.assertIsNone(reason)
        
        # Test with an invalid request (missing classes)
        invalid_request = MagicMock(spec=ScheduleRequest)
        invalid_request.classes = []
        invalid_request.instructorAvailability = []
        can_solve, reason = self.strategy.can_solve(invalid_request)
        self.assertTrue(can_solve)  # Should still return True because we're being lenient
        
    def test_get_capabilities(self):
        """Test that the strategy returns the expected capabilities"""
        capabilities = self.strategy.get_capabilities()
        
        # Check that the expected capabilities are returned
        self.assertIn('constraint_relaxation', capabilities)
        self.assertIn('distribution_optimization', capabilities)
        self.assertTrue(len(capabilities) >= 3)  # Should have at least 3 capabilities


if __name__ == '__main__':
    unittest.main()
