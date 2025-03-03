"""
Test Scheduler Router

This module contains tests for the scheduler API router.
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List, Optional, Tuple
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends

from app.models import ScheduleRequest, ScheduleResponse, ScheduleMetadata, WeightConfig, ScheduleConstraints, TimeSlot
from app.api.v1.scheduler import router as scheduler_router, get_scheduler_service
from app.services.scheduler_service import SchedulerService


class TestSchedulerRouter:
    """Tests for the scheduler API router."""

    @pytest.fixture
    def mock_scheduler_service(self):
        """Create a mock scheduler service."""
        mock = MagicMock(spec=SchedulerService)
        
        # Set up default responses for service methods
        schedule_response = ScheduleResponse(
            assignments=[],
            metadata=ScheduleMetadata(
                duration_ms=1000,
                solutions_found=1,
                score=0.0,
                gap=0.0,
                status="SUCCESS"
            )
        )
        mock.create_stable_schedule.return_value = (schedule_response, None)
        mock.create_dev_schedule.return_value = (schedule_response, None)
        mock.create_relaxed_schedule.return_value = (schedule_response, None)
        mock.compare_solvers.return_value = ({"comparison": "data"}, None)
        mock.tune_weights.return_value = ({"tuning": "data"}, None)
        mock.update_solver_config.return_value = ({"success": True}, None)
        mock.reset_solver_config.return_value = ({"success": True}, None)
        mock.get_solver_metrics.return_value = {"metrics": "data"}
        
        return mock

    @pytest.fixture
    def test_app(self, mock_scheduler_service):
        """Create a test app with the scheduler router."""
        # Create a FastAPI app
        app = FastAPI()
        
        # Override the dependency
        def get_scheduler_service_override():
            return mock_scheduler_service
        
        # Add the router with the dependency override
        app.include_router(scheduler_router)
        app.dependency_overrides[get_scheduler_service] = get_scheduler_service_override
        
        return app

    @pytest.fixture
    def client(self, test_app):
        """Create a test client."""
        return TestClient(test_app)

    @pytest.fixture
    def request_data(self):
        """Create a valid request data fixture."""
        return {
            "classes": [],
            "instructorAvailability": [],
            "startDate": "2025-01-01",
            "endDate": "2025-01-31",
            "constraints": {
                "maxClassesPerDay": 4,
                "maxClassesPerWeek": 16,
                "minPeriodsPerWeek": 8,
                "maxConsecutiveClasses": 2,
                "consecutiveClassesRule": "soft",
                "startDate": "2025-01-01",
                "endDate": "2025-01-31"
            }
        }

    def test_create_schedule_stable(self, client, mock_scheduler_service, request_data):
        """Test the create_schedule_stable endpoint."""
        # Set up the mock service response
        schedule_response = ScheduleResponse(
            assignments=[{
                "name": "Test Class", 
                "classId": "test", 
                "date": "2025-01-01",
                "timeSlot": {
                    "dayOfWeek": 1,
                    "period": 1
                }
            }],
            metadata=ScheduleMetadata(
                duration_ms=1000,
                solutions_found=1,
                score=0.0,
                gap=0.0,
                status="SUCCESS"
            )
        )
        mock_scheduler_service.create_stable_schedule.return_value = (schedule_response, None)
        
        # Make the request
        response = client.post("/scheduler/schedule/stable", json=request_data)
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["assignments"]) == 1
        assert data["data"]["assignments"][0]["classId"] == "test"
        assert data["data"]["assignments"][0]["name"] == "Test Class"

    def test_create_schedule_stable_error(self, client, mock_scheduler_service, request_data):
        """Test the create_schedule_stable endpoint with an error."""
        # Set up the mock service to return an error
        error_details = {
            "status_code": 422,
            "detail": {
                "message": "Test error"
            }
        }
        mock_scheduler_service.create_stable_schedule.return_value = (None, error_details)
        
        # Make the request
        response = client.post("/scheduler/schedule/stable", json=request_data)
        
        # Check the response
        assert response.status_code == 422
        data = response.json()
        # The error is wrapped in the 'detail' field
        assert data["detail"]["success"] is False
        assert "error" in data["detail"]["errors"][0]["message"].lower()

    def test_create_schedule_dev(self, client, mock_scheduler_service, request_data):
        """Test the create_schedule_dev endpoint."""
        # Set up the mock service response
        schedule_response = ScheduleResponse(
            assignments=[{
                "name": "Test Class", 
                "classId": "test", 
                "date": "2025-01-01",
                "timeSlot": {
                    "dayOfWeek": 1,
                    "period": 1
                }
            }],
            metadata=ScheduleMetadata(
                duration_ms=1000,
                solutions_found=1,
                score=0.0,
                gap=0.0,
                status="SUCCESS"
            )
        )
        mock_scheduler_service.create_dev_schedule.return_value = (schedule_response, None)
        
        # Make the request
        response = client.post("/scheduler/schedule/dev", json=request_data)
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["assignments"]) == 1
        assert data["data"]["assignments"][0]["classId"] == "test"
        assert data["data"]["assignments"][0]["name"] == "Test Class"

    def test_create_schedule_dev_error(self, client, mock_scheduler_service, request_data):
        """Test the create_schedule_dev endpoint with an error."""
        # Set up the mock service to return an error
        error_details = {
            "status_code": 422,
            "detail": {
                "message": "Dev schedule error"
            }
        }
        mock_scheduler_service.create_dev_schedule.return_value = (None, error_details)
        
        # Make the request
        response = client.post("/scheduler/schedule/dev", json=request_data)
        
        # Check the response
        assert response.status_code == 422
        data = response.json()
        assert data["detail"]["success"] is False
        assert "error" in data["detail"]["errors"][0]["message"].lower()

    def test_create_schedule_relaxed(self, client, mock_scheduler_service, request_data):
        """Test the create_schedule_relaxed endpoint."""
        # Set up the mock service response
        schedule_response = ScheduleResponse(
            assignments=[{
                "name": "Test Class", 
                "classId": "test", 
                "date": "2025-01-01",
                "timeSlot": {
                    "dayOfWeek": 1,
                    "period": 1
                }
            }],
            metadata=ScheduleMetadata(
                duration_ms=1000,
                solutions_found=1,
                score=0.0,
                gap=0.0,
                status="SUCCESS"
            )
        )
        mock_scheduler_service.create_relaxed_schedule.return_value = (schedule_response, None)
        
        # Make the request
        response = client.post("/scheduler/schedule/relaxed/MINIMAL", json=request_data)
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["assignments"]) == 1
        assert data["data"]["assignments"][0]["classId"] == "test"
        assert data["data"]["assignments"][0]["name"] == "Test Class"
        
        # Check that the service was called with the correct parameters
        mock_scheduler_service.create_relaxed_schedule.assert_called_once()
        args, _ = mock_scheduler_service.create_relaxed_schedule.call_args
        assert args[0] == "MINIMAL"  # Relaxation level

    def test_create_schedule_relaxed_error(self, client, mock_scheduler_service, request_data):
        """Test the create_schedule_relaxed endpoint with an error."""
        # Set up the mock service to return an error
        error_details = {
            "status_code": 422,
            "detail": {
                "message": "Relaxed schedule error"
            }
        }
        mock_scheduler_service.create_relaxed_schedule.return_value = (None, error_details)
        
        # Make the request
        response = client.post("/scheduler/schedule/relaxed/MINIMAL", json=request_data)
        
        # Check the response
        assert response.status_code == 422
        data = response.json()
        assert data["detail"]["success"] is False
        assert "error" in data["detail"]["errors"][0]["message"].lower()

    def test_compare_solvers(self, client, mock_scheduler_service, request_data):
        """Test the compare_solvers endpoint."""
        # Set up the mock service response
        comparison_data = {
            "stable": {"assignments": []},
            "dev": {"assignments": []},
            "comparison": {"metric1": "value1", "metric2": "value2"}
        }
        mock_scheduler_service.compare_solvers.return_value = (comparison_data, None)
        
        # Make the request
        response = client.post("/scheduler/compare", json=request_data)
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "stable" in data["data"]
        assert "dev" in data["data"]
        assert "comparison" in data["data"]

    def test_compare_solvers_error(self, client, mock_scheduler_service, request_data):
        """Test the compare_solvers endpoint with an error."""
        # Set up the mock service to return an error
        error_details = {
            "status_code": 422,
            "detail": {
                "message": "Solver comparison error"
            }
        }
        mock_scheduler_service.compare_solvers.return_value = (None, error_details)
        
        # Make the request
        response = client.post("/scheduler/compare", json=request_data)
        
        # Check the response
        assert response.status_code == 422
        data = response.json()
        assert data["detail"]["success"] is False
        assert "error" in data["detail"]["errors"][0]["message"].lower()

    def test_tune_weights(self, client, mock_scheduler_service, request_data):
        """Test the tune_weights endpoint."""
        # Set up the mock service response
        tuning_data = {
            "best_weights": {"weight1": 0.5, "weight2": 1.0},
            "metrics": {"score": 0.95}
        }
        mock_scheduler_service.tune_weights.return_value = (tuning_data, None)
        
        # Make the request with iterations parameter
        response = client.post("/scheduler/tune?iterations=10", json=request_data)
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "best_weights" in data["data"]
        
        # Check that the service was called with the correct parameters
        mock_scheduler_service.tune_weights.assert_called_once()
        args, _ = mock_scheduler_service.tune_weights.call_args
        assert args[1] == 10  # Iterations

    def test_tune_weights_error(self, client, mock_scheduler_service, request_data):
        """Test the tune_weights endpoint with an error."""
        # Set up the mock service to return an error
        error_details = {
            "status_code": 422,
            "detail": {
                "message": "Weight tuning error"
            }
        }
        mock_scheduler_service.tune_weights.return_value = (None, error_details)
        
        # Make the request
        response = client.post("/scheduler/tune?iterations=10", json=request_data)
        
        # Check the response
        assert response.status_code == 422
        data = response.json()
        assert data["detail"]["success"] is False
        assert "error" in data["detail"]["errors"][0]["message"].lower()

    def test_update_solver_config(self, client, mock_scheduler_service):
        """Test the update_solver_config endpoint."""
        # Create a test request with a valid WeightConfig
        request_data = {
            "final_week_compression": 3000,
            "day_usage": 2000,
            "daily_balance": 1500,
            "preferred_periods": 1000,
            "distribution": 1000,
            "avoid_periods": -500,
            "earlier_dates": 10
        }
        
        # Set up the mock service response
        result_data = {
            "success": True,
            "message": "Configuration updated successfully"
        }
        mock_scheduler_service.update_solver_config.return_value = (result_data, None)
        
        # Make the request
        response = client.post("/scheduler/config/update", json=request_data)
        
        # Check the response - it should be 200 OK
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["success"] is True
        assert "updated" in data["data"]["message"].lower()

    def test_update_solver_config_error(self, client, mock_scheduler_service):
        """Test the update_solver_config endpoint with an error."""
        # Create a test request with a valid WeightConfig
        weight_config = {
            "final_week_compression": 1000,
            "day_usage": 500,
            "daily_balance": 800,
            "preferred_periods": 600,
            "distribution": 700,
            "avoid_periods": -300,
            "earlier_dates": 400
        }
        
        # Set up the mock service to return an error
        error_details = {
            "status_code": 422,
            "detail": {
                "message": "Configuration update error"
            }
        }
        mock_scheduler_service.update_solver_config.return_value = (None, error_details)
        
        # Make the request
        response = client.post("/scheduler/config/update", json=weight_config)
        
        # Check the response
        assert response.status_code == 422
        data = response.json()
        assert data["detail"]["success"] is False
        assert "error" in data["detail"]["errors"][0]["message"].lower()

    def test_reset_solver_config(self, client, mock_scheduler_service):
        """Test the reset_solver_config endpoint."""
        # Set up the mock service response
        result_data = {
            "success": True,
            "message": "Configuration reset to defaults"
        }
        mock_scheduler_service.reset_solver_config.return_value = (result_data, None)
        
        # Make the request
        response = client.post("/scheduler/config/reset")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["success"] is True
        assert "reset" in data["data"]["message"]

    def test_reset_solver_config_error(self, client, mock_scheduler_service):
        """Test the reset_solver_config endpoint with an error."""
        # Set up the mock service to return an error
        error_details = {
            "status_code": 500,
            "detail": {
                "message": "Configuration reset error"
            }
        }
        mock_scheduler_service.reset_solver_config.return_value = (None, error_details)
        
        # Make the request
        response = client.post("/scheduler/config/reset")
        
        # Check the response
        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["success"] is False
        assert "error" in data["detail"]["errors"][0]["message"].lower()

    def test_get_solver_metrics(self, client, mock_scheduler_service):
        """Test the get_solver_metrics endpoint."""
        # Set up the mock service response
        metrics_data = {
            "performance": {"time": 0.5, "iterations": 100},
            "quality": {"score": 0.95, "violations": 0}
        }
        mock_scheduler_service.get_solver_metrics.return_value = metrics_data
        
        # Make the request
        response = client.get("/scheduler/metrics")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "performance" in data["data"]
        assert "quality" in data["data"]

    def test_get_solver_metrics_error(self, client, mock_scheduler_service):
        """Test the get_solver_metrics endpoint with an error."""
        # Set up the mock service to raise an exception
        mock_scheduler_service.get_solver_metrics.side_effect = Exception("Failed to retrieve metrics")
        
        # Make the request
        response = client.get("/scheduler/metrics")
        
        # Check the response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Failed to retrieve metrics" in str(data["detail"])
