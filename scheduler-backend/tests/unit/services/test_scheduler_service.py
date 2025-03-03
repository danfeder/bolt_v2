"""
Test Scheduler Service

This module contains tests for the scheduler service.
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List, Optional, Tuple

from app.models import ScheduleRequest, ScheduleResponse, ScheduleMetadata, ScheduleConstraints
from app.services.scheduler_service import SchedulerService
from app.scheduling.solvers.solver import UnifiedSolver


class TestSchedulerService:
    """Tests for the SchedulerService class."""

    @pytest.fixture
    def schedule_request(self):
        """Create a valid schedule request fixture."""
        return ScheduleRequest(
            classes=[],
            instructorAvailability=[],
            startDate="2025-01-01",
            endDate="2025-01-31",
            constraints=ScheduleConstraints(
                maxClassesPerDay=4,
                maxClassesPerWeek=16,
                minPeriodsPerWeek=8,
                maxConsecutiveClasses=2,
                consecutiveClassesRule="soft",
                startDate="2025-01-01",
                endDate="2025-01-31"
            )
        )

    @pytest.fixture
    def mock_solver(self):
        """Create a mock solver."""
        mock = MagicMock(spec=UnifiedSolver)
        # Set up a valid response
        mock.solve.return_value = ScheduleResponse(
            assignments=[],
            metadata=ScheduleMetadata(
                duration_ms=1000,
                solutions_found=1,
                score=0.0,
                gap=0.0,
                status="SUCCESS"
            )
        )
        return mock

    @pytest.fixture
    def scheduler_service(self, mock_solver):
        """Create a scheduler service with mock solvers."""
        return SchedulerService(
            unified_solver=mock_solver,
            stable_solver=mock_solver,
            dev_solver=mock_solver
        )

    def test_init(self):
        """Test initialization of the scheduler service."""
        # Test default initialization
        service = SchedulerService()
        assert hasattr(service, "_unified_solver")
        assert hasattr(service, "_stable_solver")
        assert hasattr(service, "_dev_solver")
        
        # Test initialization with dependencies
        mock_solver = MagicMock(spec=UnifiedSolver)
        service = SchedulerService(unified_solver=mock_solver)
        assert service._unified_solver is mock_solver

    def test_create_stable_schedule_success(self, scheduler_service, mock_solver, schedule_request):
        """Test creating a stable schedule successfully."""
        # Set up the mock to return a successful response
        mock_solver.solve.return_value = ScheduleResponse(
            assignments=[],
            metadata=ScheduleMetadata(
                duration_ms=1000,
                solutions_found=1,
                score=0.0,
                gap=0.0,
                status="SUCCESS"
            )
        )
        
        # Call the service method
        response, error = scheduler_service.create_stable_schedule(schedule_request)
        
        # Check that the solver was called
        mock_solver.solve.assert_called_once_with(schedule_request)
        
        # Check the response
        assert response.metadata.status == "SUCCESS"
        assert error is None

    def test_create_stable_schedule_timeout(self, scheduler_service, mock_solver, schedule_request):
        """Test handling a timeout when creating a stable schedule."""
        # Set up the mock to return a timeout response
        mock_solver.solve.return_value = ScheduleResponse(
            assignments=[],
            metadata=ScheduleMetadata(
                duration_ms=5000,
                solutions_found=0,
                score=0.0,
                gap=0.0,
                status="TIMEOUT"
            )
        )
        
        # Call the service method
        response, error = scheduler_service.create_stable_schedule(schedule_request)
        
        # Check the error response
        assert response.metadata.status == "TIMEOUT"
        assert error is not None
        assert error["status_code"] == 408
        assert "timed out" in error["detail"]["message"]

    def test_create_stable_schedule_no_solution(self, scheduler_service, mock_solver, schedule_request):
        """Test handling no solution when creating a stable schedule."""
        # Set up the mock to return an empty response
        mock_solver.solve.return_value = ScheduleResponse(
            assignments=[],
            metadata=ScheduleMetadata(
                duration_ms=3000,
                solutions_found=0,
                score=0.0,
                gap=0.0,
                status="INFEASIBLE"
            )
        )
        
        # Call the service method
        response, error = scheduler_service.create_stable_schedule(schedule_request)
        
        # Check the error response
        assert response.metadata.status == "INFEASIBLE"
        assert error is not None
        assert error["status_code"] == 422
        assert "No feasible schedule" in error["detail"]["message"]

    def test_create_stable_schedule_error(self, scheduler_service, mock_solver, schedule_request):
        """Test handling an error when creating a stable schedule."""
        # Set up the mock to return an error response
        mock_solver.solve.return_value = ScheduleResponse(
            assignments=[],
            metadata=ScheduleMetadata(
                duration_ms=500,
                solutions_found=0,
                score=0.0,
                gap=0.0,
                status="ERROR", 
                error="Test error"
            )
        )
        
        # Call the service method
        response, error = scheduler_service.create_stable_schedule(schedule_request)
        
        # Check the error response
        assert response.metadata.status == "ERROR"
        assert error is not None
        assert error["status_code"] == 500
        assert "error" in error["detail"]["message"].lower()
        assert error["detail"]["additional_info"]["error"] == "Test error"

    def test_create_stable_schedule_exception(self, scheduler_service, mock_solver, schedule_request):
        """Test handling an exception when creating a stable schedule."""
        # Set up the mock to raise an exception
        mock_solver.solve.side_effect = Exception("Test exception")
        
        # Call the service method
        response, error = scheduler_service.create_stable_schedule(schedule_request)
        
        # Check the error response
        assert response.assignments == []
        assert response.metadata.status == "ERROR"
        assert error is not None
        assert error["status_code"] == 500
        assert "Test exception" in error["detail"]["message"]

    def test_create_dev_schedule(self, scheduler_service, mock_solver, schedule_request):
        """Test creating a development schedule."""
        # Set up the mock to return a successful response
        mock_solver.solve.return_value = ScheduleResponse(
            assignments=[],
            metadata=ScheduleMetadata(
                duration_ms=1000,
                solutions_found=1,
                score=0.0,
                gap=0.0,
                status="SUCCESS"
            )
        )
        
        # Call the service method
        response, error = scheduler_service.create_dev_schedule(schedule_request)
        
        # Check that the solver was called
        mock_solver.solve.assert_called_with(schedule_request)
        
        # Check the response
        assert response.metadata.status == "SUCCESS"
        assert error is None

    def test_compare_solvers(self, scheduler_service, mock_solver, schedule_request):
        """Test comparing solvers."""
        # Set up the mock to return a successful response
        stable_response = ScheduleResponse(
            assignments=[],
            metadata=ScheduleMetadata(
                duration_ms=1000,
                solutions_found=1,
                score=0.0,
                gap=0.0,
                status="SUCCESS"
            )
        )
        dev_response = ScheduleResponse(
            assignments=[],
            metadata=ScheduleMetadata(
                duration_ms=800,
                solutions_found=1,
                score=0.0,
                gap=0.0,
                status="SUCCESS"
            )
        )
        
        # Set up the solver mocks
        scheduler_service._stable_solver.solve.return_value = stable_response
        scheduler_service._dev_solver.solve.return_value = dev_response
        scheduler_service._dev_solver._compare_solutions.return_value = {"comparison": "data"}
        
        # Call the service method
        result, error = scheduler_service.compare_solvers(schedule_request)
        
        # Check that both solvers were called
        scheduler_service._stable_solver.solve.assert_called_with(schedule_request)
        scheduler_service._dev_solver.solve.assert_called_with(schedule_request)
        
        # Check that the comparison was performed
        scheduler_service._dev_solver._compare_solutions.assert_called_once()
        
        # Check the response
        assert "stable" in result
        assert "dev" in result
        assert "comparison" in result
        assert result["comparison"] == {"comparison": "data"}
        assert error is None

    @patch("app.services.scheduler_service.ENABLE_WEIGHT_TUNING", True)
    def test_tune_weights_enabled(self, scheduler_service, mock_solver, schedule_request):
        """Test tuning weights when enabled."""
        # Set up the mock to return a successful tuning result
        mock_solver.tune_weights.return_value = {"weights": {"key": "value"}}
        
        # Call the service method
        result, error = scheduler_service.tune_weights(schedule_request, 5)
        
        # Check that the tuning was performed
        mock_solver.tune_weights.assert_called_once()
        
        # Check the response
        assert "best_weights" in result
        assert result["best_weights"] == {"weights": {"key": "value"}}
        assert error is None

    @patch("app.services.scheduler_service.ENABLE_WEIGHT_TUNING", False)
    def test_tune_weights_disabled(self, scheduler_service, mock_solver, schedule_request):
        """Test tuning weights when disabled."""
        # Call the service method
        result, error = scheduler_service.tune_weights(schedule_request, 5)
        
        # Check that the tuning was not performed
        mock_solver.tune_weights.assert_not_called()
        
        # Check the error response
        assert result == {}
        assert error is not None
        assert error["status_code"] == 403
        assert "disabled" in error["detail"]["message"]

    def test_update_solver_config(self, scheduler_service, mock_solver):
        """Test updating the solver configuration."""
        # Create a mock weight config
        weight_config = MagicMock()
        weight_config.weights = {"key": "value"}
        
        # Call the service method
        result, error = scheduler_service.update_solver_config(weight_config)
        
        # Check that the weights were updated
        mock_solver.update_weights.assert_called_once_with(weight_config.weights)
        
        # Check the response
        assert result["success"] is True
        assert "updated successfully" in result["message"]
        assert error is None

    def test_reset_solver_config(self, scheduler_service, mock_solver):
        """Test resetting the solver configuration."""
        # Call the service method
        result, error = scheduler_service.reset_solver_config()
        
        # Check the response
        assert result["success"] is True
        assert "reset" in result["message"]
        assert error is None

    @patch("app.services.scheduler_service.ENABLE_CONSTRAINT_RELAXATION", True)
    def test_create_relaxed_schedule_enabled(self, scheduler_service, mock_solver, schedule_request):
        """Test creating a relaxed schedule when enabled."""
        # Set up the mock to return a successful response
        mock_solver.solve.return_value = ScheduleResponse(
            assignments=[{"date": "2025-01-01"}],
            metadata=ScheduleMetadata(
                duration_ms=1000,
                solutions_found=1,
                score=0.0,
                gap=0.0,
                status="SUCCESS"
            )
        )
        
        # Call the service method
        with patch("app.services.scheduler_service.UnifiedSolver") as mock_solver_class:
            # Set up the mock solver class to return our mock solver
            mock_solver_class.return_value = mock_solver
            
            # Call the service method
            response, error = scheduler_service.create_relaxed_schedule("MINIMAL", schedule_request)
        
        # Check the response
        assert len(response.assignments) == 1
        assert error is None

    @patch("app.services.scheduler_service.ENABLE_CONSTRAINT_RELAXATION", False)
    def test_create_relaxed_schedule_disabled(self, scheduler_service, mock_solver, schedule_request):
        """Test creating a relaxed schedule when disabled."""
        # Call the service method
        response, error = scheduler_service.create_relaxed_schedule("MINIMAL", schedule_request)
        
        # Check the error response
        assert response.assignments == []
        assert error is not None
        assert error["status_code"] == 403
        assert "disabled" in error["detail"]["message"]

    def test_create_relaxed_schedule_invalid_level(self, scheduler_service, mock_solver, schedule_request):
        """Test creating a relaxed schedule with an invalid relaxation level."""
        # Call the service method with an invalid level
        with patch("app.services.scheduler_service.ENABLE_CONSTRAINT_RELAXATION", True):
            response, error = scheduler_service.create_relaxed_schedule("INVALID", schedule_request)
        
        # Check the error response
        assert response.assignments == []
        assert error is not None
        assert error["status_code"] == 400
        assert "Invalid relaxation level" in error["detail"]["message"]

    def test_get_solver_metrics(self, scheduler_service, mock_solver):
        """Test getting solver metrics."""
        # Reset mock to avoid any previous calls
        mock_solver.get_metrics.reset_mock()
        
        # Set up the mock to return metrics
        mock_solver.get_metrics.return_value = {"metric1": "value1", "metric2": "value2"}
        
        # Call the service method
        metrics = scheduler_service.get_solver_metrics()
        
        # Check that the metrics were retrieved exactly once
        mock_solver.get_metrics.assert_called_once()
        
        # Check the response
        assert metrics == {"metric1": "value1", "metric2": "value2"}
