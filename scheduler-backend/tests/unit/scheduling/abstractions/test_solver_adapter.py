"""
Tests for the solver adapter module

This module contains tests for the SolverAdapter classes in the abstractions package.
"""

import pytest
from unittest.mock import patch, MagicMock
from typing import Dict, Any
from datetime import datetime, timedelta

from app.models import ScheduleRequest, ScheduleResponse, ScheduleAssignment, ScheduleMetadata, ScheduleConstraints, Class, InstructorAvailability
from app.scheduling.abstractions.solver_adapter import UnifiedSolverAdapter, SolverAdapterFactory
from app.scheduling.abstractions.solver_config import SolverType, SolverConfiguration


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
    
    # Create a minimal request with empty lists for classes and instructorAvailability
    # We'll populate these in the test cases as needed
    return ScheduleRequest(
        id="test-request",
        name="Test Request",
        constraints=constraints,
        startDate=start_date.strftime("%Y-%m-%d"),
        endDate=end_date.strftime("%Y-%m-%d"),
        classes=[],  
        instructorAvailability=[]
    )


class TestUnifiedSolverAdapter:
    """Tests for the UnifiedSolverAdapter class"""
    
    def test_initialization(self):
        """Test initialization of UnifiedSolverAdapter"""
        adapter = UnifiedSolverAdapter()
        
        assert adapter.name == "unified_solver_adapter"
        assert adapter.description == "Adapter for UnifiedSolver"
        assert len(adapter.constraints) == 0
        assert len(adapter.objectives) == 0
    
    @patch("app.scheduling.abstractions.solver_adapter.UnifiedSolver")
    def test_solve(self, mock_unified_solver, minimal_schedule_request):
        """Test solve method with mocked UnifiedSolver"""
        # Create a mock UnifiedSolver instance
        mock_solver_instance = MagicMock()
        mock_unified_solver.return_value = mock_solver_instance
        
        # Mock the solve method to return a response
        mock_response = ScheduleResponse(
            assignments=[],
            metadata=ScheduleMetadata(
                duration_ms=100,
                solutions_found=1,
                score=95,
                gap=0.05,
                solver="test_solver"
            )
        )
        mock_solver_instance.solve.return_value = mock_response
        
        # Create the adapter
        adapter = UnifiedSolverAdapter()
        
        # Use the test request from the fixture
        request = minimal_schedule_request
        config: Dict[str, Any] = {
            "solver_type": "OR_TOOLS",
            "timeout_seconds": 60,
            "max_iterations": 1000
        }
        
        # Call solve
        result = adapter.solve(request, config)
        
        # Verify the result
        assert result.success == True
        assert result.schedule == mock_response
        assert result.error is None
        assert result.metadata["runtime_ms"] == 100
        assert result.metadata["solutions_found"] == 1
        assert result.metadata["score"] == 95
        assert result.metadata["gap"] == 0.05
        assert result.metadata["solver_name"] == "test_solver"
        
        # Verify the UnifiedSolver was created and called correctly
        mock_unified_solver.assert_called_once()
        mock_solver_instance.solve.assert_called_once_with(
            time_limit_seconds=60,
            max_iterations=1000
        )
    
    def test_can_solve(self, minimal_schedule_request):
        """Test can_solve method"""
        adapter = UnifiedSolverAdapter()
        
        # Test with valid request
        request = minimal_schedule_request
        # Add valid class and instructor availability
        test_class = Class(
            id="test-class-1",
            name="Test Class 1",
            grade="3",
            gradeGroup=4
        )
        
        test_availability = InstructorAvailability(
            date=datetime.now(),
            periods=[1, 2, 3]
        )
        
        request.classes = [test_class]
        request.instructorAvailability = [test_availability]
        
        can_solve, reason = adapter.can_solve(request)
        assert can_solve == True
        assert reason is None
        
        # Test with invalid request (no classes)
        request.classes = []
        can_solve, reason = adapter.can_solve(request)
        assert can_solve == False
        assert "no classes" in reason.lower()
        
        # Test with invalid request (no instructor availability)
        request.classes = [test_class]
        request.instructorAvailability = []
        can_solve, reason = adapter.can_solve(request)
        assert can_solve == False
        assert "no instructor availability" in reason.lower()
    
    def test_get_capabilities(self):
        """Test get_capabilities method"""
        adapter = UnifiedSolverAdapter()
        
        # Test with default configuration
        capabilities = adapter.get_capabilities()
        assert "constraint_relaxation" in capabilities
        assert "distribution_optimization" in capabilities
        assert "standard_optimization" in capabilities
        assert "medium_scale" in capabilities
        
        # Test with OR_TOOLS configuration
        adapter._config = SolverConfiguration(solver_type=SolverType.OR_TOOLS)
        capabilities = adapter.get_capabilities()
        assert "exact_solution" in capabilities
        
        # Test with GENETIC configuration
        adapter._config = SolverConfiguration(solver_type=SolverType.GENETIC)
        capabilities = adapter.get_capabilities()
        assert "approximate_solution" in capabilities
        assert "large_scale" in capabilities


class TestSolverAdapterFactory:
    """Tests for the SolverAdapterFactory class"""
    
    def test_create_adapter(self):
        """Test create_adapter method"""
        # Test with OR_TOOLS
        adapter = SolverAdapterFactory.create_adapter(SolverType.OR_TOOLS)
        assert isinstance(adapter, UnifiedSolverAdapter)
        assert adapter.name == "or_tools_adapter"
        
        # Test with GENETIC
        adapter = SolverAdapterFactory.create_adapter(SolverType.GENETIC)
        assert isinstance(adapter, UnifiedSolverAdapter)
        assert adapter.name == "genetic_adapter"
        
        # Test with HYBRID
        adapter = SolverAdapterFactory.create_adapter(SolverType.HYBRID)
        assert isinstance(adapter, UnifiedSolverAdapter)
        assert adapter.name == "hybrid_adapter"
