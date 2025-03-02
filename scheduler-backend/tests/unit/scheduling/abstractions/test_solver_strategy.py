"""
Tests for the solver strategy module

This module contains tests for the SolverStrategy and related classes
in the abstractions package.
"""

import pytest
from typing import Dict, Any, List, Optional, Set, Type, Union
from datetime import datetime, timedelta

from app.models import ScheduleRequest, ScheduleResponse, ScheduleAssignment, ScheduleMetadata, ScheduleConstraints, TimeSlot
from app.scheduling.abstractions.solver_strategy import (
    SolverStrategy,
    SolverResult
)
from app.scheduling.abstractions.concrete_strategies import (
    ORToolsStrategy,
    GeneticAlgorithmStrategy,
    HybridStrategy
)
from app.scheduling.abstractions.solver_factory import SolverFactory
from app.scheduling.abstractions.solver_config import SolverConfiguration, SolverType


class TestSolverResult:
    """Tests for the SolverResult class"""
    
    def test_initialization(self):
        """Test initialization of SolverResult"""
        # Success result
        result = SolverResult(
            success=True,
            schedule="test_schedule",
            metadata={"runtime_ms": 100, "score": 85}
        )
        
        assert result.success == True
        assert result.schedule == "test_schedule"
        assert result.error is None
        assert result.metadata == {"runtime_ms": 100, "score": 85}
        assert result.assignments == []
        
        # Failure result
        result = SolverResult(
            success=False,
            error="Test error"
        )
        
        assert result.success == False
        assert result.schedule is None
        assert result.error == "Test error"
        assert result.metadata == {}
        assert result.assignments == []
    
    def test_to_response(self):
        """Test conversion to ScheduleResponse"""
        result = SolverResult(
            success=True,
            metadata={
                "runtime_ms": 150,
                "solutions_found": 3,
                "score": 90,
                "gap": 0.05,
                "solver_name": "test_solver"
            },
            assignments=[
                {
                    "name": "Class1",
                    "classId": "class1",
                    "date": "2025-01-01",
                    "timeSlot": TimeSlot(dayOfWeek=1, period=2)
                }
            ]
        )
        
        response = result.to_response()
        
        assert isinstance(response, ScheduleResponse)
        assert len(response.assignments) == 1
        assert response.metadata.duration_ms == 150
        assert response.metadata.solutions_found == 3
        assert response.metadata.score == 90
        assert response.metadata.gap == 0.05
        assert response.metadata.solver == "test_solver"


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


class TestConcreteStrategies:
    """Tests for the concrete solver strategy implementations"""
    
    def test_or_tools_strategy(self, minimal_schedule_request):
        """Test the OR-Tools strategy"""
        strategy = ORToolsStrategy()
        
        # Check properties
        assert strategy.name == "or_tools"
        assert "Google OR-Tools" in strategy.description
        assert len(strategy.constraints) == 0
        assert len(strategy.objectives) == 0
        
        # Check capabilities
        capabilities = strategy.get_capabilities()
        assert isinstance(capabilities, set)
        assert "constraint_programming" in capabilities
        assert "distribution_optimization" in capabilities
        
        # Test can_solve
        can_solve, reason = strategy.can_solve(minimal_schedule_request)
        assert can_solve == True
        assert reason is None
        
        # Test solve (basic check that it returns a result)
        result = strategy.solve(minimal_schedule_request, {"timeout_seconds": 10})
        assert isinstance(result, SolverResult)
        assert result.success == True
        assert "runtime_ms" in result.metadata
    
    def test_genetic_algorithm_strategy(self, minimal_schedule_request):
        """Test the genetic algorithm strategy"""
        strategy = GeneticAlgorithmStrategy()
        
        # Check properties
        assert strategy.name == "genetic"
        assert "Genetic algorithm" in strategy.description
        assert len(strategy.constraints) == 0
        assert len(strategy.objectives) == 0
        
        # Check capabilities
        capabilities = strategy.get_capabilities()
        assert isinstance(capabilities, set)
        assert "large_scale" in capabilities
        assert "parallel_execution" in capabilities
        
        # Test can_solve
        can_solve, reason = strategy.can_solve(minimal_schedule_request)
        assert can_solve == True
        assert reason is None
        
        # Test solve (basic check that it returns a result)
        result = strategy.solve(minimal_schedule_request, {
            "population_size": 50,
            "max_iterations": 100
        })
        assert isinstance(result, SolverResult)
        assert result.success == True
        assert "runtime_ms" in result.metadata
        assert "generations" in result.metadata
    
    def test_hybrid_strategy(self, minimal_schedule_request):
        """Test the hybrid strategy"""
        strategy = HybridStrategy()
        
        # Check properties
        assert strategy.name == "hybrid"
        assert "Hybrid solver" in strategy.description
        assert len(strategy.constraints) == 0
        assert len(strategy.objectives) == 0
        
        # Check capabilities
        capabilities = strategy.get_capabilities()
        assert isinstance(capabilities, set)
        # Should include capabilities from both OR-Tools and genetic algorithm
        assert "constraint_programming" in capabilities
        assert "large_scale" in capabilities
        
        # Test can_solve
        can_solve, reason = strategy.can_solve(minimal_schedule_request)
        assert can_solve == True
        assert reason is None
        
        # Test solve (basic check that it returns a result)
        result = strategy.solve(minimal_schedule_request, {"timeout_seconds": 20})
        assert isinstance(result, SolverResult)
        assert result.success == True
        assert "runtime_ms" in result.metadata


class TestSolverFactory:
    """Tests for the SolverFactory class"""
    
    def test_initialization(self):
        """Test initialization of SolverFactory"""
        factory = SolverFactory()
        assert len(factory.get_strategy_names()) == 0
    
    def test_register_strategy(self):
        """Test registering a strategy"""
        factory = SolverFactory()
        
        # Register a strategy
        factory.register_strategy("or_tools", ORToolsStrategy)
        assert "or_tools" in factory.get_strategy_names()
        
        # Register another strategy
        factory.register_strategy("genetic", GeneticAlgorithmStrategy)
        assert len(factory.get_strategy_names()) == 2
        assert "genetic" in factory.get_strategy_names()
    
    def test_create_strategy(self):
        """Test creating a strategy"""
        factory = SolverFactory()
        factory.register_strategy("or_tools", ORToolsStrategy)
        
        # Create a strategy
        strategy = factory.create_strategy("or_tools")
        assert isinstance(strategy, ORToolsStrategy)
        assert strategy.name == "or_tools"
        
        # Create a strategy with configuration
        config = SolverConfiguration(timeout_seconds=30)
        strategy = factory.create_strategy("or_tools", config)
        assert isinstance(strategy, ORToolsStrategy)
        
        # Try to create an unknown strategy
        strategy = factory.create_strategy("unknown")
        assert strategy is None
    
    def test_create_strategy_for_request(self, minimal_schedule_request):
        """Test creating a strategy for a request"""
        factory = SolverFactory()
        factory.register_strategy("or_tools", ORToolsStrategy)
        factory.register_strategy("genetic", GeneticAlgorithmStrategy)
        factory.register_strategy("hybrid", HybridStrategy)
        
        # Create a strategy based on solver type
        config = SolverConfiguration(solver_type=SolverType.OR_TOOLS)
        strategy = factory.create_strategy_for_request(minimal_schedule_request, config)
        assert isinstance(strategy, ORToolsStrategy)
        
        # Create a strategy based on solver type
        config = SolverConfiguration(solver_type=SolverType.GENETIC)
        strategy = factory.create_strategy_for_request(minimal_schedule_request, config)
        assert isinstance(strategy, GeneticAlgorithmStrategy)
        
        # Create a strategy based on solver type
        config = SolverConfiguration(solver_type=SolverType.HYBRID)
        strategy = factory.create_strategy_for_request(minimal_schedule_request, config)
        assert isinstance(strategy, HybridStrategy)
