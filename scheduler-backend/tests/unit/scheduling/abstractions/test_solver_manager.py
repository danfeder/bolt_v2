"""
Tests for the solver manager module

This module contains tests for the SolverManager class
in the abstractions package.
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List, Optional, Set, Type, Union
from datetime import datetime, timedelta

from app.models import (
    ScheduleRequest,
    ScheduleResponse,
    ScheduleMetadata,
    ScheduleAssignment,
    ScheduleConstraints,
    TimeSlot
)
from app.scheduling.abstractions.solver_manager import SolverManager
from app.scheduling.abstractions.solver_config import (
    SolverConfiguration,
    SolverType,
    OptimizationLevel,
    SolverConfigurationBuilder
)
from app.scheduling.abstractions.solver_strategy import SolverStrategy, SolverResult
from app.scheduling.abstractions.concrete_strategies import (
    ORToolsStrategy,
    GeneticAlgorithmStrategy,
    HybridStrategy
)
from app.scheduling.abstractions.solver_factory import SolverFactory


# Example minimal ScheduleRequest for testing
@pytest.fixture
def minimal_schedule_request():
    """Create a minimal ScheduleRequest for testing"""
    start_date = datetime.now()
    end_date = start_date + timedelta(days=30)
    
    # Create constraints object
    constraints = ScheduleConstraints(
        maxClassesPerDay=4,
        maxClassesPerWeek=16,
        minPeriodsPerWeek=8,
        maxConsecutiveClasses=2,
        consecutiveClassesRule="soft",
        startDate=start_date.isoformat(),
        endDate=end_date.isoformat(),
        allowConsecutiveClasses=True,
        requiredBreakPeriods=[4]
    )
    
    return ScheduleRequest(
        classes=[],
        instructorAvailability=[],
        preferences={},
        startDate=start_date.isoformat(),
        endDate=end_date.isoformat(),
        constraints=constraints
    )


class TestSolverManager:
    """Tests for the SolverManager class"""
    
    def test_initialization(self):
        """Test initialization of SolverManager"""
        manager = SolverManager()
        
        # Default strategies should be registered
        strategy_names = manager.get_available_strategies()
        assert len(strategy_names) == 3
        assert "or_tools" in strategy_names
        assert "genetic" in strategy_names
        assert "hybrid" in strategy_names
    
    def test_register_strategy(self):
        """Test registering a custom strategy"""
        manager = SolverManager()
        
        # Create a mock strategy class
        mock_strategy_class = MagicMock()
        
        # Register the strategy
        manager.register_strategy("custom", mock_strategy_class)
        
        # Check that it was registered
        assert "custom" in manager.get_available_strategies()
    
    def test_solve_success(self, minimal_schedule_request):
        """Test solving a request with success"""
        # Create a mock factory
        mock_factory = MagicMock(spec=SolverFactory)
        
        # Create a mock strategy
        mock_strategy = MagicMock(spec=SolverStrategy)
        mock_strategy.name = "mock_strategy"
        
        # Configure the mock factory to return the mock strategy
        mock_factory.create_strategy_for_request.return_value = mock_strategy
        
        # Configure the mock strategy to return a success result
        mock_result = SolverResult(
            success=True,
            metadata={
                "runtime_ms": 100, 
                "solutions_found": 1, 
                "score": 95,
                "gap": 0.1  # Adding required gap field
            },
            assignments=[{
                "name": "Class1",
                "classId": "class1",
                "date": "2025-01-01",
                "timeSlot": TimeSlot(dayOfWeek=1, period=2)
            }]
        )
        mock_strategy.solve.return_value = mock_result
        
        # Create a manager with the mock factory
        manager = SolverManager()
        manager._factory = mock_factory
        
        # Solve the request
        config = SolverConfiguration()
        response = manager.solve(minimal_schedule_request, config)
        
        # Check that the factory was called with the right arguments
        mock_factory.create_strategy_for_request.assert_called_once_with(minimal_schedule_request, config)
        
        # Check that the strategy was called with the right arguments
        mock_strategy.solve.assert_called_once()
        args, kwargs = mock_strategy.solve.call_args
        assert args[0] == minimal_schedule_request
        assert isinstance(args[1], dict)
        
        # Check the response
        assert isinstance(response, ScheduleResponse)
        assert response.metadata.solutions_found == 1
        assert response.metadata.score == 95
        assert len(response.assignments) == 1
    
    def test_solve_no_strategy(self, minimal_schedule_request):
        """Test solving a request when no strategy is available"""
        # Create a mock factory
        mock_factory = MagicMock(spec=SolverFactory)
        
        # Configure the mock factory to return None
        mock_factory.create_strategy_for_request.return_value = None
        
        # Create a manager with the mock factory
        manager = SolverManager()
        manager._factory = mock_factory
        
        # Solve the request
        response = manager.solve(minimal_schedule_request)
        
        # Check the response
        assert isinstance(response, ScheduleResponse)
        assert response.metadata.solutions_found == 0
        assert response.metadata.error is not None
        assert "No suitable solver strategy found" in response.metadata.error
        assert len(response.assignments) == 0
    
    def test_solve_with_dict_config(self, minimal_schedule_request):
        """Test solving with a dictionary configuration"""
        # Create a mock factory
        mock_factory = MagicMock(spec=SolverFactory)
        
        # Create a mock strategy
        mock_strategy = MagicMock(spec=SolverStrategy)
        mock_strategy.name = "mock_strategy"
        
        # Configure the mock factory to return the mock strategy
        mock_factory.create_strategy_for_request.return_value = mock_strategy
        
        # Configure the mock strategy to return a success result
        mock_result = SolverResult(
            success=True,
            metadata={
                "runtime_ms": 100,
                "solutions_found": 1,
                "score": 95,
                "gap": 0.05  # Adding required gap field
            }
        )
        mock_strategy.solve.return_value = mock_result
        
        # Create a manager with the mock factory
        manager = SolverManager()
        manager._factory = mock_factory
        
        # Solve the request with a dict config
        config_dict = {"solver_type": "OR_TOOLS", "timeout_seconds": 30}
        response = manager.solve(minimal_schedule_request, config_dict)
        
        # Check that the factory was called with a SolverConfiguration
        mock_factory.create_strategy_for_request.assert_called_once()
        args, kwargs = mock_factory.create_strategy_for_request.call_args
        assert isinstance(args[1], SolverConfiguration)
        assert args[1].solver_type == SolverType.OR_TOOLS
        assert args[1].timeout_seconds == 30
    
    def test_solve_with_error(self, minimal_schedule_request):
        """Test solving when an error occurs"""
        # Create a mock factory
        mock_factory = MagicMock(spec=SolverFactory)
        
        # Create a mock strategy
        mock_strategy = MagicMock(spec=SolverStrategy)
        mock_strategy.name = "mock_strategy"
        
        # Configure the mock factory to return the mock strategy
        mock_factory.create_strategy_for_request.return_value = mock_strategy
        
        # Configure the mock strategy to raise an exception
        mock_strategy.solve.side_effect = Exception("Test error")
        
        # Create a manager with the mock factory
        manager = SolverManager()
        manager._factory = mock_factory
        
        # Solve the request
        response = manager.solve(minimal_schedule_request)
        
        # Check the response
        assert isinstance(response, ScheduleResponse)
        assert response.metadata.solutions_found == 0
        assert response.metadata.error is not None
        assert "Test error" in response.metadata.error
        assert len(response.assignments) == 0
    
    def test_factory_methods(self):
        """Test factory methods for creating manager and configurations"""
        # Create default manager
        manager = SolverManager.create_default()
        assert isinstance(manager, SolverManager)
        
        # Create configurations
        standard_config = SolverManager.create_standard_configuration()
        assert isinstance(standard_config, SolverConfiguration)
        assert standard_config.optimization_level == OptimizationLevel.STANDARD
        
        intensive_config = SolverManager.create_intensive_configuration()
        assert isinstance(intensive_config, SolverConfiguration)
        assert intensive_config.optimization_level == OptimizationLevel.INTENSIVE
        
        minimal_config = SolverManager.create_minimal_configuration()
        assert isinstance(minimal_config, SolverConfiguration)
        assert minimal_config.optimization_level == OptimizationLevel.MINIMAL
        
        # Create builder
        builder = SolverManager.create_custom_configuration()
        assert isinstance(builder, SolverConfigurationBuilder)
