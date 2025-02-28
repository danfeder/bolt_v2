"""Tests for the dashboard visualization functionality."""
import pytest
from datetime import datetime
from app.models import ScheduleAssignment, TimeSlot
from app.visualization.dashboard import (
    create_daily_distribution_chart,
    create_period_distribution_chart,
    calculate_distribution_score,
    calculate_workload_balance,
    calculate_period_spread
)

@pytest.fixture
def sample_assignments():
    """Sample schedule assignments for testing."""
    return [
        ScheduleAssignment(
            name="Class1",
            date=datetime(2025, 3, 3).isoformat(),  # Monday
            timeSlot=TimeSlot(dayOfWeek=1, period=2)
        ),
        ScheduleAssignment(
            name="Class2",
            date=datetime(2025, 3, 3).isoformat(),  # Monday
            timeSlot=TimeSlot(dayOfWeek=1, period=4)
        ),
        ScheduleAssignment(
            name="Class3",
            date=datetime(2025, 3, 4).isoformat(),  # Tuesday
            timeSlot=TimeSlot(dayOfWeek=2, period=3)
        ),
        ScheduleAssignment(
            name="Class1",
            date=datetime(2025, 3, 5).isoformat(),  # Wednesday
            timeSlot=TimeSlot(dayOfWeek=3, period=1)
        ),
        ScheduleAssignment(
            name="Class2",
            date=datetime(2025, 3, 6).isoformat(),  # Thursday
            timeSlot=TimeSlot(dayOfWeek=4, period=5)
        ),
        ScheduleAssignment(
            name="Class3",
            date=datetime(2025, 3, 7).isoformat(),  # Friday
            timeSlot=TimeSlot(dayOfWeek=5, period=2)
        ),
    ]

def test_daily_distribution_chart(sample_assignments):
    """Test creation of daily distribution chart."""
    chart = create_daily_distribution_chart(sample_assignments)
    
    # Verify chart structure
    assert chart.title == "Classes Per Day of Week"
    assert chart.type == "bar"
    assert len(chart.series) == 1
    
    # Verify data points
    data = chart.series[0].data
    assert len(data) == 5  # One for each day of the week
    
    # Check counts match our sample data
    day_counts = {point.x: point.y for point in data}
    assert day_counts["Monday"] == 2
    assert day_counts["Tuesday"] == 1
    assert day_counts["Wednesday"] == 1
    assert day_counts["Thursday"] == 1
    assert day_counts["Friday"] == 1

def test_period_distribution_chart(sample_assignments):
    """Test creation of period distribution chart."""
    chart = create_period_distribution_chart(sample_assignments)
    
    # Verify chart structure
    assert chart.title == "Classes Per Period"
    assert chart.type == "bar"
    assert len(chart.series) == 1
    
    # Verify data points
    data = chart.series[0].data
    
    # Check counts match our sample data
    period_counts = {point.x: point.y for point in data}
    assert period_counts["Period 1"] == 1
    assert period_counts["Period 2"] == 2
    assert period_counts["Period 3"] == 1
    assert period_counts["Period 4"] == 1
    assert period_counts["Period 5"] == 1

def test_distribution_score(sample_assignments):
    """Test calculation of distribution score."""
    score = calculate_distribution_score(sample_assignments)
    
    # Score should be high for this well-distributed sample
    assert 70 <= score <= 100
    
    # Create unbalanced distribution
    unbalanced = sample_assignments.copy()
    # Add 3 more assignments on Monday
    for i in range(3):
        unbalanced.append(
            ScheduleAssignment(
                name=f"ExtraClass{i}",
                date=datetime(2025, 3, 3).isoformat(),  # Monday
                timeSlot=TimeSlot(dayOfWeek=1, period=6+i)
            )
        )
    
    unbalanced_score = calculate_distribution_score(unbalanced)
    
    # Score should be lower for unbalanced distribution
    assert unbalanced_score < score

def test_workload_balance(sample_assignments):
    """Test calculation of workload balance."""
    balance = calculate_workload_balance(sample_assignments)
    
    # Balance should be high for this well-distributed sample
    assert 70 <= balance <= 100
    
    # Create unbalanced workload
    unbalanced = sample_assignments.copy()
    # Add 3 more assignments for Class1
    for i in range(3):
        unbalanced.append(
            ScheduleAssignment(
                name="Class1",
                date=datetime(2025, 3, 3+i).isoformat(),
                timeSlot=TimeSlot(dayOfWeek=1+i, period=6)
            )
        )
    
    unbalanced_balance = calculate_workload_balance(unbalanced)
    
    # Balance should be lower for unbalanced workload
    assert unbalanced_balance < balance

def test_period_spread(sample_assignments):
    """Test calculation of period spread."""
    spread = calculate_period_spread(sample_assignments)
    
    # Spread should be high for this well-distributed sample
    assert 70 <= spread <= 100
    
    # Create unbalanced period distribution
    unbalanced = sample_assignments.copy()
    # Add 3 more assignments for period 1
    for i in range(3):
        unbalanced.append(
            ScheduleAssignment(
                name=f"ExtraClass{i}",
                date=datetime(2025, 3, 3+i).isoformat(),
                timeSlot=TimeSlot(dayOfWeek=1+i, period=1)
            )
        )
    
    unbalanced_spread = calculate_period_spread(unbalanced)
    
    # Spread should be lower for unbalanced period distribution
    assert unbalanced_spread < spread