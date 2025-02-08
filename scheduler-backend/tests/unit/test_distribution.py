import pytest
from datetime import datetime, timedelta
from statistics import variance
from collections import defaultdict
from app.scheduler import create_schedule_dev
from app.models import (
    ScheduleRequest,
    ScheduleConstraints,
    TimeSlot,
    WeeklySchedule
)
from tests.utils.generators import (
    ClassGenerator,
    TeacherAvailabilityGenerator,
    TimeSlotGenerator,
    ScheduleRequestGenerator
)
from tests.utils.assertions import assert_valid_schedule

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
        classes=ClassGenerator.create_multiple_classes(15),  # Multiple classes to distribute
        teacherAvailability=TeacherAvailabilityGenerator.create_weekly_availability(
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
            consecutiveClassesRule="hard"
        )
    )
    
    # Generate schedule
    response = create_schedule_dev(request)
    
    # Calculate weekly variance
    weekly_variance = calculate_weekly_variance(response, request)
    
    # Assert low variance (good distribution)
    assert weekly_variance < 2.0, f"Weekly distribution variance too high: {weekly_variance}"

def test_daily_period_spread():
    """Test that classes are well-distributed across periods within each day"""
    start_date = datetime.now()
    end_date = start_date + timedelta(days=7)
    
    request = ScheduleRequest(
        classes=ClassGenerator.create_multiple_classes(8),  # Enough classes for multiple per day
        teacherAvailability=TeacherAvailabilityGenerator.create_weekly_availability(
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
            consecutiveClassesRule="hard"
        )
    )
    
    # Generate schedule
    response = create_schedule_dev(request)
    
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
        teacherAvailability=TeacherAvailabilityGenerator.create_weekly_availability(
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
            consecutiveClassesRule="hard"
        )
    )
    
    # Generate schedule
    response = create_schedule_dev(request)
    
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
        teacherAvailability=TeacherAvailabilityGenerator.create_weekly_availability(
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
            consecutiveClassesRule="hard"
        )
    )
    
    # Generate schedule
    response = create_schedule_dev(request)
    
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
        teacherAvailability=TeacherAvailabilityGenerator.create_weekly_availability(
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
            consecutiveClassesRule="hard"
        )
    )
    
    # Generate schedule
    response = create_schedule_dev(request)
    
    # Verify distribution metrics
    weekly_variance = calculate_weekly_variance(response, request)
    daily_spreads = calculate_daily_spread(response)
    
    # Assert good distribution while respecting constraints
    assert weekly_variance < 2.0, f"Weekly distribution variance too high: {weekly_variance}"
    for date, spread in daily_spreads.items():
        assert spread < 1.5, f"Poor period distribution on {date}, variance: {spread}"
