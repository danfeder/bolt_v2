"""Integration tests for dashboard API routes."""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.main import app
from app.models import ScheduleRequest, ScheduleConstraints
from app.visualization.routes import schedule_history
from tests.utils.generators import (
    ClassGenerator,
    ScheduleRequestGenerator
)

client = TestClient(app)

@pytest.fixture
def test_schedule_request():
    """Create a simple schedule request for testing."""
    return ScheduleRequestGenerator.create_request(
        num_classes=3,
        num_weeks=1
    )

def test_analyze_schedule(test_schedule_request):
    """Test analyzing a schedule and generating dashboard data."""
    response = client.post(
        "/dashboard/analyze",
        json=test_schedule_request.model_dump(),
        params={"solver_type": "stable"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify structure
    assert "schedule_id" in data
    assert "timestamp" in data
    assert "quality_metrics" in data
    assert "daily_distribution" in data
    assert "period_distribution" in data
    assert "grade_distribution" in data
    assert "constraint_satisfaction" in data
    assert "grade_period_heatmap" in data
    
    # Verify quality metrics
    quality_metrics = data["quality_metrics"]
    assert "distribution_score" in quality_metrics
    assert "preference_satisfaction" in quality_metrics
    assert "workload_balance" in quality_metrics
    assert "period_spread" in quality_metrics
    assert "overall_score" in quality_metrics
    
    # Verify chart data
    daily_distribution = data["daily_distribution"]
    assert daily_distribution["title"] == "Classes Per Day of Week"
    assert daily_distribution["type"] == "bar"
    assert len(daily_distribution["series"]) > 0
    
    # Check that the schedule was stored in history
    schedule_id = data["schedule_id"]
    assert schedule_id in schedule_history

def test_get_schedule_history():
    """Test retrieving schedule history."""
    # First analyze a schedule to have something in history
    request = ScheduleRequestGenerator.create_request(
        num_classes=2,
        num_weeks=1
    )
    client.post(
        "/dashboard/analyze",
        json=request.model_dump(),
        params={"solver_type": "stable"}
    )
    
    # Get history
    response = client.get("/dashboard/history")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify structure
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Verify entry structure
    entry = data[0]
    assert "schedule_id" in entry
    assert "timestamp" in entry
    assert "quality_metrics" in entry
    assert "assignment_count" in entry
    assert "class_count" in entry

def test_get_chart_data():
    """Test retrieving chart data for a specific schedule."""
    # First analyze a schedule to have something in history
    request = ScheduleRequestGenerator.create_request(
        num_classes=2,
        num_weeks=1
    )
    analyze_response = client.post(
        "/dashboard/analyze",
        json=request.model_dump(),
        params={"solver_type": "stable"}
    )
    schedule_id = analyze_response.json()["schedule_id"]
    
    # Get daily chart data
    response = client.get(f"/dashboard/chart/daily/{schedule_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify structure
    assert "series" in data
    assert "title" in data
    assert "type" in data
    assert data["title"] == "Classes Per Day of Week"
    
    # Get period chart data
    response = client.get(f"/dashboard/chart/period/{schedule_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify structure
    assert "series" in data
    assert "title" in data
    assert "type" in data
    assert data["title"] == "Classes Per Period"
    
    # Test invalid chart type
    response = client.get(f"/dashboard/chart/invalid/{schedule_id}")
    assert response.status_code == 400

def test_get_schedule_metrics():
    """Test retrieving metrics for a specific schedule."""
    # First analyze a schedule to have something in history
    request = ScheduleRequestGenerator.create_request(
        num_classes=2,
        num_weeks=1
    )
    analyze_response = client.post(
        "/dashboard/analyze",
        json=request.model_dump(),
        params={"solver_type": "stable"}
    )
    schedule_id = analyze_response.json()["schedule_id"]
    
    # Get metrics
    response = client.get(f"/dashboard/metrics/{schedule_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify structure
    assert "distribution_score" in data
    assert "preference_satisfaction" in data
    assert "workload_balance" in data
    assert "period_spread" in data
    assert "overall_score" in data
    
    # Test invalid schedule ID
    response = client.get("/dashboard/metrics/invalid-id")
    assert response.status_code == 404

def test_compare_schedules():
    """Test comparing two schedules."""
    # Create and analyze two schedules
    request1 = ScheduleRequestGenerator.create_request(
        num_classes=2,
        num_weeks=1
    )
    analyze_response1 = client.post(
        "/dashboard/analyze",
        json=request1.model_dump(),
        params={"solver_type": "stable"}
    )
    schedule_id1 = analyze_response1.json()["schedule_id"]
    
    # Create a slightly different request
    request2 = ScheduleRequestGenerator.create_request(
        num_classes=3,  # Different number of classes
        num_weeks=1
    )
    analyze_response2 = client.post(
        "/dashboard/analyze",
        json=request2.model_dump(),
        params={"solver_type": "dev"}  # Use different solver
    )
    schedule_id2 = analyze_response2.json()["schedule_id"]
    
    # Compare schedules
    response = client.post(
        "/dashboard/compare",
        params={
            "baseline_id": schedule_id1,
            "comparison_id": schedule_id2
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify structure
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Verify entry structure
    metric = data[0]
    assert "metric_name" in metric
    assert "baseline_value" in metric
    assert "comparison_value" in metric
    assert "difference" in metric
    assert "percentage_change" in metric
    assert "improvement" in metric
    
    # Test invalid schedule IDs
    response = client.post(
        "/dashboard/compare",
        params={
            "baseline_id": "invalid-id",
            "comparison_id": schedule_id2
        }
    )
    assert response.status_code == 404