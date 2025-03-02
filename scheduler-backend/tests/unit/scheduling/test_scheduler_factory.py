"""
Tests for the scheduler factory module

This module contains tests for the SchedulerFactory class.
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any
from datetime import datetime, timedelta

from app.models import ScheduleRequest, ScheduleResponse, ScheduleAssignment, ScheduleMetadata, ScheduleConstraints, Class, InstructorAvailability
from app.scheduling.scheduler_factory import SchedulerFactory
from app.scheduling.abstractions import (
    SolverFactory,
    SolverConfiguration,
    SolverType,
    SolverStrategy,
    SolverResult,
    SolverConfigurationBuilder
)


@pytest.fixture
def minimal_schedule_request():
    """Create a minimal ScheduleRequest for testing"""
    start_date = datetime.now()
    end_date = start_date + timedelta(days=30)
    
    # Create constraints object with required fields based on the actual model
    constraints = ScheduleConstraints(
        maxClassesPerDay=4,
        maxClassesPerWeek=16,
        minPeriodsPerWeek=8,
        maxConsecutiveClasses=2,
        consecutiveClassesRule="soft",
        startDate=start_date.strftime("%Y-%m-%d"),
        endDate=end_date.strftime("%Y-%m-%d"),
        allowConsecutiveClasses=True,
        requiredBreakPeriods=[4]  # Example lunch period
    )
    
    # Create a minimal class - using proper Class model instead of dict
    test_class = Class(
        id="test-class-1",
        name="Test Class 1",
        grade="3",
        gradeGroup=4
    )
    
    # Create minimal instructor availability - using proper InstructorAvailability model
    test_availability = InstructorAvailability(
        date=datetime.now(),
        periods=[1, 2, 3]
    )
    
    # Create a minimal request
    return ScheduleRequest(
        id="test-request",
        name="Test Request",
        constraints=constraints,
        startDate=start_date.strftime("%Y-%m-%d"),
        endDate=end_date.strftime("%Y-%m-%d"),
        classes=[test_class],
        instructorAvailability=[test_availability]
    )


class TestSchedulerFactory:
    """Tests for the SchedulerFactory class"""
    
    def test_initialization(self):
        """Test initialization of SchedulerFactory"""
        with patch("app.scheduling.scheduler_factory.SolverFactory") as mock_solver_factory:
            # Create a mock instance
            mock_solver_factory_instance = MagicMock()
            mock_solver_factory.return_value = mock_solver_factory_instance
            
            # Create the factory
            factory = SchedulerFactory()
            
            # Verify the solver factory was created
            mock_solver_factory.assert_called_once()
            
            # Verify default strategies were registered
            assert mock_solver_factory_instance.register_strategy.call_count == 3
    
    def test_create_scheduler(self, minimal_schedule_request):
        """Test create_scheduler method with a valid configuration"""
        # Mock the solver factory and strategy to avoid actual execution
        with patch("app.scheduling.scheduler_factory.SolverFactory") as mock_solver_factory:
            # Create mock instances
            mock_solver_factory_instance = MagicMock()
            mock_strategy = MagicMock()
            mock_solver_factory_instance.create_strategy_for_request.return_value = mock_strategy
            mock_solver_factory.return_value = mock_solver_factory_instance
            
            # Create a mock response
            mock_response = ScheduleResponse(
                metadata=ScheduleMetadata(
                    duration_ms=100,
                    solutions_found=1,
                    score=100,
                    gap=0.0,
                    solver="test_solver",
                    status="SUCCESS"
                ),
                assignments=[]
            )
            
            # Set up the mock strategy to return the response
            mock_strategy.solve.return_value = SolverResult(
                success=True,
                schedule=mock_response,
                metadata={},
                assignments=[]
            )
            
            # Create the factory
            factory = SchedulerFactory()
            
            # Use the fixture
            request = minimal_schedule_request
            config = {
                "solver_type": "OR_TOOLS",
                "timeout_seconds": 60,
                "max_iterations": 1000
            }
            
            # Test the scheduler creation
            scheduler = factory.create_scheduler(request, config)
            
            # Verify the result
            assert scheduler is not None
            assert isinstance(scheduler, ScheduleResponse)
            assert scheduler.metadata.solver == "test_solver"
            
            # Verify the strategy was created and called with the correct arguments
            mock_solver_factory_instance.create_strategy_for_request.assert_called_once()
            mock_strategy.solve.assert_called_once()
    
    def test_create_scheduler_error(self, minimal_schedule_request):
        """Test that creating a scheduler with an invalid solver type raises an error"""
        # Mock the SolverFactory to properly test the error handling
        with patch("app.scheduling.scheduler_factory.SolverFactory") as mock_solver_factory:
            # Create a mock instance
            mock_solver_factory_instance = MagicMock()
            mock_solver_factory.return_value = mock_solver_factory_instance
            
            # Set up the mock to raise an appropriate error
            mock_solver_factory_instance.create_strategy_for_request.side_effect = ValueError("Invalid solver type: INVALID_SOLVER")
            
            # Create the factory
            factory = SchedulerFactory()
            
            # Use the fixture
            request = minimal_schedule_request
            config = {
                "solver_type": "INVALID_SOLVER"
            }
            
            # Test that creating a scheduler with an invalid solver type raises an error
            with pytest.raises(ValueError) as excinfo:
                factory.create_scheduler(request, config)
            
            # Check that the error message contains 'Invalid solver type'
            assert "Invalid solver type" in str(excinfo.value)
    
    def test_create_configuration_builder(self):
        """Test create_configuration_builder method"""
        builder = SchedulerFactory.create_configuration_builder()
        assert isinstance(builder, SolverConfigurationBuilder)
    
    def test_create_default_configuration(self):
        """Test create_default_configuration method"""
        config = SchedulerFactory.create_default_configuration()
        assert isinstance(config, SolverConfiguration)
        assert config.solver_type == SolverType.HYBRID
        assert config.timeout_seconds == 60
    
    def test_create_minimal_configuration(self):
        """Test create_minimal_configuration method"""
        config = SchedulerFactory.create_minimal_configuration()
        assert isinstance(config, SolverConfiguration)
        assert config.solver_type == SolverType.OR_TOOLS
        assert config.timeout_seconds == 10
        assert config.enable_distribution_optimization == False
        assert config.enable_workload_balancing == False
    
    def test_create_intensive_configuration(self):
        """Test create_intensive_configuration method"""
        config = SchedulerFactory.create_intensive_configuration()
        assert isinstance(config, SolverConfiguration)
        assert config.solver_type == SolverType.HYBRID
        assert config.timeout_seconds == 300
        assert config.max_iterations == 50000
        assert config.population_size == 200
