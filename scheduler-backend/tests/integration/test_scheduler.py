import pytest
from datetime import datetime, timedelta
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

def test_basic_schedule_generation():
    """Test basic end-to-end schedule generation"""
    request = ScheduleRequestGenerator.create_request(
        num_classes=5,
        num_weeks=1
    )
    
    response = create_schedule_dev(request)
    assert_valid_schedule(response, request)
    
    # Verify metadata
    assert response.metadata.solver == "cp-sat-dev"
    assert response.metadata.duration > 0
    assert response.metadata.score > 0

def test_complex_constraints():
    """Test schedule generation with complex interacting constraints"""
    start_date = datetime.now()
    end_date = start_date + timedelta(days=14)
    
    # Create classes with various constraints
    classes = []
    
    # Class 1: Required periods and conflicts
    classes.append(ClassGenerator.create_class(
        class_id="complex-1",
        weekly_schedule=WeeklySchedule(
            conflicts=TimeSlotGenerator.create_daily_pattern(1),  # No first periods
            preferredPeriods=[],
            requiredPeriods=[TimeSlot(dayOfWeek=2, period=3)],  # Tuesday third period
            avoidPeriods=[],
            preferenceWeight=1.0,
            avoidanceWeight=1.0
        )
    ))
    
    # Class 2: Strong period preferences
    classes.append(ClassGenerator.create_class(
        class_id="complex-2",
        weekly_schedule=WeeklySchedule(
            conflicts=[],
            preferredPeriods=TimeSlotGenerator.create_daily_pattern(2),  # Prefer second periods
            requiredPeriods=[],
            avoidPeriods=[],
            preferenceWeight=2.0,  # Strong preference
            avoidanceWeight=1.0
        )
    ))
    
    # Class 3: Multiple avoid periods
    classes.append(ClassGenerator.create_class(
        class_id="complex-3",
        weekly_schedule=WeeklySchedule(
            conflicts=[],
            preferredPeriods=[],
            requiredPeriods=[],
            avoidPeriods=TimeSlotGenerator.create_daily_pattern(8),  # Avoid last periods
            preferenceWeight=1.0,
            avoidanceWeight=1.5  # Strong avoidance
        )
    ))
    
    # Create teacher availability with complex patterns
    unavailable_slots = (
        TimeSlotGenerator.create_daily_pattern(4) +  # Fourth period
        TimeSlotGenerator.create_daily_pattern(5)    # Fifth period (lunch)
    )
    
    request = ScheduleRequest(
        classes=classes,
        teacherAvailability=TeacherAvailabilityGenerator.create_weekly_availability(
            start_date=start_date,
            weeks=2,
            unavailable_pattern=unavailable_slots
        ),
        startDate=start_date.strftime("%Y-%m-%d"),
        endDate=end_date.strftime("%Y-%m-%d"),
        constraints=ScheduleConstraints(
            maxClassesPerDay=2,
            maxClassesPerWeek=5,
            minPeriodsPerWeek=1,
            maxConsecutiveClasses=1,
            consecutiveClassesRule="hard"
        )
    )
    
    response = create_schedule_dev(request)
    assert_valid_schedule(response, request)

def test_edge_cases():
    """Test schedule generation with edge cases"""
    start_date = datetime.now()
    end_date = start_date + timedelta(days=7)
    
    # Edge case 1: Class with many conflicts
    many_conflicts = []
    for day in range(1, 6):  # Monday-Friday
        many_conflicts.extend([
            TimeSlot(dayOfWeek=day, period=p)
            for p in [1, 2, 3, 6, 7, 8]  # Only periods 4-5 available
        ])
    
    # Edge case 2: Class with many required periods
    many_required = [
        TimeSlot(dayOfWeek=1, period=2),  # Monday second
        TimeSlot(dayOfWeek=2, period=3),  # Tuesday third
        TimeSlot(dayOfWeek=3, period=4),  # Wednesday fourth
    ]
    
    classes = [
        # Class with minimal availability
        ClassGenerator.create_class(
            class_id="edge-1",
            weekly_schedule=WeeklySchedule(
                conflicts=many_conflicts,
                preferredPeriods=[],
                requiredPeriods=[],
                avoidPeriods=[],
                preferenceWeight=1.0,
                avoidanceWeight=1.0
            )
        ),
        # Class with multiple required periods
        ClassGenerator.create_class(
            class_id="edge-2",
            weekly_schedule=WeeklySchedule(
                conflicts=[],
                preferredPeriods=[],
                requiredPeriods=many_required,
                avoidPeriods=[],
                preferenceWeight=1.0,
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
            maxClassesPerDay=2,
            maxClassesPerWeek=5,
            minPeriodsPerWeek=1,
            maxConsecutiveClasses=1,
            consecutiveClassesRule="hard"
        )
    )
    
    response = create_schedule_dev(request)
    assert_valid_schedule(response, request)

def test_error_handling():
    """Test scheduler error handling with invalid inputs"""
    start_date = datetime.now()
    end_date = start_date + timedelta(days=7)
    
    # Test case 1: Overlapping required periods
    overlapping_required = [
        TimeSlot(dayOfWeek=2, period=3),  # Tuesday third period
        TimeSlot(dayOfWeek=2, period=3)   # Same period
    ]
    
    classes = [
        ClassGenerator.create_class(
            class_id="test-1",
            weekly_schedule=WeeklySchedule(
                conflicts=[],
                preferredPeriods=[],
                requiredPeriods=overlapping_required,
                avoidPeriods=[],
                preferenceWeight=1.0,
                avoidanceWeight=1.0
            )
        ),
        ClassGenerator.create_class(
            class_id="test-2",
            weekly_schedule=WeeklySchedule(
                conflicts=[],
                preferredPeriods=[],
                requiredPeriods=overlapping_required,
                avoidPeriods=[],
                preferenceWeight=1.0,
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
            maxClassesPerDay=2,
            maxClassesPerWeek=5,
            minPeriodsPerWeek=1,
            maxConsecutiveClasses=1,
            consecutiveClassesRule="hard"
        )
    )
    
    # Should raise an exception due to impossible constraints
    with pytest.raises(Exception) as exc_info:
        create_schedule_dev(request)
    assert "No solution found" in str(exc_info.value)

def test_optimization_priorities():
    """Test that optimization priorities are respected"""
    start_date = datetime.now()
    end_date = start_date + timedelta(days=7)
    
    # Create classes with competing preferences
    classes = [
        # Class with required period (highest priority)
        ClassGenerator.create_class(
            class_id="prio-1",
            weekly_schedule=WeeklySchedule(
                conflicts=[],
                preferredPeriods=[],
                requiredPeriods=[TimeSlot(dayOfWeek=2, period=3)],
                avoidPeriods=[],
                preferenceWeight=1.0,
                avoidanceWeight=1.0
            )
        ),
        # Class with strong preference (medium priority)
        ClassGenerator.create_class(
            class_id="prio-2",
            weekly_schedule=WeeklySchedule(
                conflicts=[],
                preferredPeriods=[TimeSlot(dayOfWeek=2, period=3)],  # Same as required above
                requiredPeriods=[],
                avoidPeriods=[],
                preferenceWeight=2.0,
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
            maxClassesPerDay=2,
            maxClassesPerWeek=5,
            minPeriodsPerWeek=1,
            maxConsecutiveClasses=1,
            consecutiveClassesRule="hard"
        )
    )
    
    response = create_schedule_dev(request)
    assert_valid_schedule(response, request)
    
    # Verify that prio-1 got its required period
    prio1_assignment = next(a for a in response.assignments if a.classId == "prio-1")
    assert prio1_assignment.timeSlot.dayOfWeek == 2
    assert prio1_assignment.timeSlot.period == 3
