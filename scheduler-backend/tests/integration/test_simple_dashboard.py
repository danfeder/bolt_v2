"""Simple test for debugging dashboard issues."""
import pytest
from fastapi.testclient import TestClient
import traceback

from app.main import app
from app.models import ScheduleRequest, ScheduleConstraints, Class, WeeklySchedule
from app.visualization.routes import schedule_history

client = TestClient(app)

def create_simple_request():
    """Create a very simple request with minimal constraints."""
    class1 = Class(
        id="Test Class 1",
        name="Test Class 1",
        grade="Test",
        gradeGroup=0,
        equipmentNeeds=[],
        weeklySchedule=WeeklySchedule(
            conflicts=[],
            preferredPeriods=[],
            requiredPeriods=[],
            avoidPeriods=[],
            preferenceWeight=1.5,
            avoidanceWeight=1.2
        )
    )
    
    constraints = ScheduleConstraints(
        maxClassesPerDay=3,
        maxClassesPerWeek=12,
        minPeriodsPerWeek=5,
        maxConsecutiveClasses=2,
        consecutiveClassesRule="soft",
        startDate="2025-03-03",
        endDate="2025-03-10",
        allowConsecutiveClasses=True,
        requiredBreakPeriods=[]
    )
    
    request = ScheduleRequest(
        classes=[class1],
        instructorAvailability=[],
        startDate="2025-03-03",
        endDate="2025-03-10",
        constraints=constraints
    )
    
    return request

def test_simple_analyze():
    """Test analyzing a very simple schedule."""
    try:
        # Create a simple request
        request = create_simple_request()
        print(f"\nCreated simple request with {len(request.classes)} classes")
        print(f"Date range: {request.startDate} to {request.endDate}")
        
        # Analyze the schedule
        print("Analyzing schedule...")
        response = client.post(
            "/dashboard/analyze",
            json=request.model_dump(),
            params={"solver_type": "stable"}
        )
        
        print(f"Response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Analysis failed: {response.text}")
            # Try to parse the JSON error response
            try:
                error_data = response.json()
                print(f"Error detail: {error_data.get('detail')}")
            except Exception as parse_err:
                print(f"Could not parse error response: {str(parse_err)}")
        else:
            data = response.json()
            print(f"Analysis succeeded, schedule ID: {data.get('schedule_id')}")
            print(f"Quality metrics: {data.get('quality_metrics')}")
            
        assert response.status_code == 200
        
    except Exception as e:
        print(f"Error during test: {str(e)}")
        print(traceback.format_exc())
        raise
