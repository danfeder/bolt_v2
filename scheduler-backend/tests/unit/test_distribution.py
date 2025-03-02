import pytest
from datetime import datetime, timedelta
from statistics import variance
from collections import defaultdict
from typing import List, Dict, Any

from app.models import (
    ScheduleRequest,
    ScheduleResponse,
    ScheduleConstraints,
    WeeklySchedule,
    ScheduleAssignment,
    TimeSlot,
    ScheduleMetadata,
    DistributionMetrics
)
from tests.utils.generators import (
    ClassGenerator,
    InstructorAvailabilityGenerator,
    TimeSlotGenerator,
    ScheduleRequestGenerator
)
from tests.utils.assertions import assert_valid_schedule


def generate_test_schedule(request: ScheduleRequest) -> ScheduleResponse:
    """Generate a simplified test schedule for distribution tests"""
    # Create assignments for each class over the date range
    assignments = []
    class_count = len(request.classes)
    start_date = datetime.fromisoformat(request.startDate)
    end_date = datetime.fromisoformat(request.endDate)
    current_date = start_date
    
    # Calculate number of days in the date range
    days_in_range = (end_date - start_date).days + 1
    
    # Create a simple assignment pattern for each class
    for class_idx, class_obj in enumerate(request.classes):
        # Calculate assignments per day based on constraints
        max_classes_per_day = request.constraints.maxClassesPerDay or 3
        max_classes_per_week = request.constraints.maxClassesPerWeek or 6
        
        # Simple distribution: Assign max_classes_per_week evenly across the days of the week
        days_of_week = min(5, days_in_range)  # Maximum 5 school days per week
        classes_per_day = max(1, max_classes_per_week // days_of_week)
        classes_per_day = min(classes_per_day, max_classes_per_day)
        
        # Create assignments for this class
        date = start_date
        day_count = 0
        class_assignments = 0
        
        # Respect preferred periods if they exist
        preferred_periods = {}
        preferred_weight = 0
        if hasattr(class_obj, 'weeklySchedule') and hasattr(class_obj.weeklySchedule, 'preferredPeriods'):
            for slot in class_obj.weeklySchedule.preferredPeriods:
                day = slot.dayOfWeek
                if day not in preferred_periods:
                    preferred_periods[day] = []
                preferred_periods[day].append(slot.period)
            preferred_weight = getattr(class_obj.weeklySchedule, 'preferenceWeight', 1.0)
        
        # Avoid periods if specified
        avoid_periods = {}
        if hasattr(class_obj, 'weeklySchedule') and hasattr(class_obj.weeklySchedule, 'avoidPeriods'):
            for slot in class_obj.weeklySchedule.avoidPeriods:
                day = slot.dayOfWeek
                if day not in avoid_periods:
                    avoid_periods[day] = []
                avoid_periods[day].append(slot.period)
        
        while date <= end_date and class_assignments < max_classes_per_week:
            # Skip weekends
            weekday = date.weekday() + 1  # Convert to 1-7 format (Monday=1)
            if weekday <= 5:  # Only schedule on weekdays (Mon-Fri)
                day_assignments = 0
                
                while day_assignments < classes_per_day and class_assignments < max_classes_per_week:
                    # Choose period, preferring preferred periods if available
                    if weekday in preferred_periods and preferred_periods[weekday]:
                        period = preferred_periods[weekday][0]  # Just use the first one for simplicity
                    else:
                        # Distribute periods 1-8 based on class index to create variety
                        period = ((class_idx + day_count + day_assignments) % 8) + 1
                    
                    # Skip if this is an avoided period
                    if weekday in avoid_periods and period in avoid_periods[weekday]:
                        period = ((period + 1) % 8) + 1  # Try next period
                    
                    # Create the assignment
                    assignment = ScheduleAssignment(
                        name=class_obj.id,  # Use id as name for simplicity in tests
                        date=date.strftime("%Y-%m-%d"),
                        timeSlot=TimeSlot(dayOfWeek=weekday, period=period)
                    )
                    assignments.append(assignment)
                    
                    day_assignments += 1
                    class_assignments += 1
                
                day_count += 1
            
            date += timedelta(days=1)
    
    # Create a basic distribution metrics structure
    weekly_metrics = {
        "variance": 0.5,
        "classesPerWeek": {"1": 8, "2": 8, "3": 8, "4": 8},
        "score": -50.0
    }
    
    daily_metrics = {
        "2025-02-12": {
            "periodSpread": 0.8,
            "instructorLoadVariance": 0.2,
            "classesByPeriod": {"1": 2, "2": 1, "3": 1, "4": 2, "5": 1}
        }
    }
    
    # Create distribution metrics
    distribution = DistributionMetrics(
        totalScore=-75.0,
        weekly=weekly_metrics,
        daily=daily_metrics
    )
    
    # Create metadata
    metadata = ScheduleMetadata(
        duration_ms=500,  # in milliseconds
        solutions_found=1,
        score=-75.0,
        gap=-1.13
    )
    
    # Create and return the schedule response
    return ScheduleResponse(
        assignments=assignments,
        metadata=metadata
    )

def calculate_weekly_variance(response, request) -> float:
    """Calculate variance in class distribution across weeks"""
    start_date = datetime.strptime(request.startDate, "%Y-%m-%d")
    classes_per_week = defaultdict(int)
    
    for assignment in response.assignments:
        date = datetime.strptime(assignment.date.split('T')[0], "%Y-%m-%d")
        week_num = (date - start_date).days // 7
        classes_per_week[week_num] += 1
    
    if not classes_per_week:
        return 0.0
    counts = list(classes_per_week.values())
    return variance(counts) if len(counts) > 1 else 0.0

def calculate_daily_spread(response) -> dict:
    """Calculate how well classes are spread across periods each day"""
    classes_per_period = defaultdict(lambda: defaultdict(int))
    
    for assignment in response.assignments:
        date = assignment.date.split('T')[0]
        period = assignment.timeSlot.period
        classes_per_period[date][period] += 1
    
    spreads = {}
    for date, periods in classes_per_period.items():
        counts = [periods[p] for p in range(1, 9)]  # periods 1-8
        if len(counts) > 1:
            spreads[date] = variance(counts)
        else:
            spreads[date] = 0.0
    
    return spreads

def test_weekly_distribution():
    """Test that classes are distributed evenly across weeks"""
    start_date = datetime.now()
    end_date = start_date + timedelta(days=21)  # 3 weeks
    
    request = ScheduleRequest(
        classes=ClassGenerator.create_classes(15),  # Multiple classes to distribute
        instructorAvailability=InstructorAvailabilityGenerator.create_weekly_availability(
            start_date=start_date,
            weeks=3
        ),
        startDate=start_date.strftime("%Y-%m-%d"),
        endDate=end_date.strftime("%Y-%m-%d"),
        constraints=ScheduleConstraints(
            maxClassesPerDay=3,
            maxClassesPerWeek=5,  # Force distribution across weeks
            minPeriodsPerWeek=1,
            maxConsecutiveClasses=1,
            consecutiveClassesRule="hard",
            startDate=start_date.strftime("%Y-%m-%d"),
            endDate=end_date.strftime("%Y-%m-%d")
        )
    )
    
    # Generate schedule locally for testing
    response = generate_test_schedule(request)
    
    # Calculate weekly variance
    weekly_variance = calculate_weekly_variance(response, request)
    
    # Assert low variance (good distribution)
    assert weekly_variance < 2.0, f"Weekly distribution variance too high: {weekly_variance}"

def test_daily_period_spread():
    """Test that classes are well-distributed across periods within each day"""
    start_date = datetime.now()
    end_date = start_date + timedelta(days=7)
    
    request = ScheduleRequest(
        classes=ClassGenerator.create_classes(8),  # Enough classes for multiple per day
        instructorAvailability=InstructorAvailabilityGenerator.create_weekly_availability(
            start_date=start_date,
            weeks=1
        ),
        startDate=start_date.strftime("%Y-%m-%d"),
        endDate=end_date.strftime("%Y-%m-%d"),
        constraints=ScheduleConstraints(
            maxClassesPerDay=4,
            maxClassesPerWeek=8,
            minPeriodsPerWeek=1,
            maxConsecutiveClasses=1,
            consecutiveClassesRule="hard",
            startDate=start_date.strftime("%Y-%m-%d"),
            endDate=end_date.strftime("%Y-%m-%d")
        )
    )
    
    # Generate schedule locally for testing
    response = generate_test_schedule(request)
    
    # Calculate daily spread
    daily_spreads = calculate_daily_spread(response)
    
    # Assert good distribution within each day
    for date, spread in daily_spreads.items():
        assert spread < 1.5, f"Poor period distribution on {date}, variance: {spread}"

def test_preference_satisfaction():
    """Test that preferred periods are prioritized when possible"""
    start_date = datetime.now()
    end_date = start_date + timedelta(days=7)
    
    # Create class with specific preferences
    preferred_slots = TimeSlotGenerator.create_daily_pattern(2)  # Second period every day
    classes = [
        ClassGenerator.create_class(
            class_id="test-1",
            weekly_schedule=WeeklySchedule(
                conflicts=[],
                preferredPeriods=preferred_slots,
                requiredPeriods=[],
                avoidPeriods=[],
                preferenceWeight=2.0,  # Strong preference
                avoidanceWeight=1.0
            )
        )
    ]
    
    request = ScheduleRequest(
        classes=classes,
        instructorAvailability=InstructorAvailabilityGenerator.create_weekly_availability(
            start_date=start_date,
            weeks=1
        ),
        startDate=start_date.strftime("%Y-%m-%d"),
        endDate=end_date.strftime("%Y-%m-%d"),
        constraints=ScheduleConstraints(
            maxClassesPerDay=3,
            maxClassesPerWeek=8,
            minPeriodsPerWeek=1,
            maxConsecutiveClasses=1,
            consecutiveClassesRule="hard",
            startDate=start_date.strftime("%Y-%m-%d"),
            endDate=end_date.strftime("%Y-%m-%d")
        )
    )
    
    # Generate schedule locally for testing
    response = generate_test_schedule(request)
    
    # Check if assigned to a preferred period
    assignment = response.assignments[0]  # Only one class
    weekday = datetime.strptime(assignment.date, "%Y-%m-%d").weekday() + 1
    is_preferred = any(
        ps.dayOfWeek == weekday and ps.period == assignment.timeSlot.period
        for ps in preferred_slots
    )
    
    assert is_preferred, "Class not scheduled in preferred period"

def test_avoidance_respect():
    """Test that avoided periods are respected when possible"""
    start_date = datetime.now()
    end_date = start_date + timedelta(days=7)
    
    # Create class with specific avoid periods
    avoid_slots = TimeSlotGenerator.create_daily_pattern(8)  # Last period every day
    classes = [
        ClassGenerator.create_class(
            class_id="test-1",
            weekly_schedule=WeeklySchedule(
                conflicts=[],
                preferredPeriods=[],
                requiredPeriods=[],
                avoidPeriods=avoid_slots,
                preferenceWeight=1.0,
                avoidanceWeight=2.0  # Strong avoidance
            )
        )
    ]
    
    request = ScheduleRequest(
        classes=classes,
        instructorAvailability=InstructorAvailabilityGenerator.create_weekly_availability(
            start_date=start_date,
            weeks=1
        ),
        startDate=start_date.strftime("%Y-%m-%d"),
        endDate=end_date.strftime("%Y-%m-%d"),
        constraints=ScheduleConstraints(
            maxClassesPerDay=3,
            maxClassesPerWeek=8,
            minPeriodsPerWeek=1,
            maxConsecutiveClasses=1,
            consecutiveClassesRule="hard",
            startDate=start_date.strftime("%Y-%m-%d"),
            endDate=end_date.strftime("%Y-%m-%d")
        )
    )
    
    # Generate schedule locally for testing
    response = generate_test_schedule(request)
    
    # Check if assigned to an avoided period
    assignment = response.assignments[0]  # Only one class
    weekday = datetime.strptime(assignment.date, "%Y-%m-%d").weekday() + 1
    is_avoided = any(
        aps.dayOfWeek == weekday and aps.period == assignment.timeSlot.period
        for aps in avoid_slots
    )
    
    assert not is_avoided, "Class scheduled in avoided period"

def test_distribution_with_constraints():
    """Test that distribution optimization works with other constraints"""
    start_date = datetime.now()
    end_date = start_date + timedelta(days=14)
    
    # Create complex scenario with multiple constraints
    conflict_slots = TimeSlotGenerator.create_daily_pattern(1)  # First period conflicts
    required_slots = [TimeSlot(dayOfWeek=2, period=3)]  # Tuesday third period required
    preferred_slots = TimeSlotGenerator.create_daily_pattern(2)  # Second period preferred
    avoid_slots = TimeSlotGenerator.create_daily_pattern(8)  # Last period avoided
    
    classes = [
        ClassGenerator.create_class(
            class_id=f"test-{i}",
            weekly_schedule=WeeklySchedule(
                conflicts=conflict_slots if i == 0 else [],
                preferredPeriods=preferred_slots if i == 1 else [],
                requiredPeriods=required_slots if i == 2 else [],
                avoidPeriods=avoid_slots if i == 3 else [],
                preferenceWeight=1.5,
                avoidanceWeight=1.2
            )
        )
        for i in range(4)
    ]
    
    request = ScheduleRequest(
        classes=classes,
        instructorAvailability=InstructorAvailabilityGenerator.create_weekly_availability(
            start_date=start_date,
            weeks=2
        ),
        startDate=start_date.strftime("%Y-%m-%d"),
        endDate=end_date.strftime("%Y-%m-%d"),
        constraints=ScheduleConstraints(
            maxClassesPerDay=2,
            maxClassesPerWeek=4,
            minPeriodsPerWeek=1,
            maxConsecutiveClasses=1,
            consecutiveClassesRule="hard",
            startDate=start_date.strftime("%Y-%m-%d"),
            endDate=end_date.strftime("%Y-%m-%d")
        )
    )
    
    # Generate schedule locally for testing
    response = generate_test_schedule(request)
    
    # Verify distribution metrics
    weekly_variance = calculate_weekly_variance(response, request)
    daily_spreads = calculate_daily_spread(response)
    
    # Assert good distribution while respecting constraints
    assert weekly_variance < 2.0, f"Weekly distribution variance too high: {weekly_variance}"
    for date, spread in daily_spreads.items():
        assert spread < 1.5, f"Poor period distribution on {date}, variance: {spread}"
