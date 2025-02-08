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
    TimeSlotGenerator
)
from tests.utils.assertions import (
    assert_valid_assignments,
    assert_no_overlaps,
    assert_respects_conflicts,
    assert_respects_teacher_availability,
    assert_respects_required_periods,
    assert_respects_class_limits,
    assert_respects_consecutive_classes,
    assert_valid_schedule
)

def test_single_assignment():
    """Test that each class is scheduled exactly once"""
    # Create a simple schedule request with multiple classes
    start_date = datetime.now()
    end_date = start_date + timedelta(days=14)
    
    request = ScheduleRequest(
        classes=ClassGenerator.create_multiple_classes(3),
        teacherAvailability=TeacherAvailabilityGenerator.create_weekly_availability(
            start_date=start_date,
            weeks=2
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
    
    # Verify each class is scheduled exactly once
    assert_valid_assignments(response, request)

def test_no_overlaps():
    """Test that no two classes are scheduled at the same time"""
    # Create classes with overlapping preferences to test conflict resolution
    start_date = datetime.now()
    end_date = start_date + timedelta(days=7)
    
    # Create two classes that prefer the same periods
    preferred_slots = TimeSlotGenerator.create_daily_pattern(2)  # Second period every day
    classes = [
        ClassGenerator.create_class(
            class_id="test-1",
            weekly_schedule=WeeklySchedule(
                conflicts=[],
                preferredPeriods=preferred_slots,
                requiredPeriods=[],
                avoidPeriods=[],
                preferenceWeight=1.5,
                avoidanceWeight=1.0
            )
        ),
        ClassGenerator.create_class(
            class_id="test-2",
            weekly_schedule=WeeklySchedule(
                conflicts=[],
                preferredPeriods=preferred_slots,
                requiredPeriods=[],
                avoidPeriods=[],
                preferenceWeight=1.5,
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
    
    # Verify no overlaps
    assert_no_overlaps(response)

def test_respects_conflicts():
    """Test that classes are not scheduled during their conflict periods"""
    start_date = datetime.now()
    end_date = start_date + timedelta(days=7)
    
    # Create class with specific conflicts
    conflict_slots = TimeSlotGenerator.create_daily_pattern(1)  # First period every day
    classes = [
        ClassGenerator.create_class(
            class_id="test-1",
            weekly_schedule=WeeklySchedule(
                conflicts=conflict_slots,
                preferredPeriods=[],
                requiredPeriods=[],
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
            maxClassesPerDay=3,
            maxClassesPerWeek=8,
            minPeriodsPerWeek=1,
            maxConsecutiveClasses=1,
            consecutiveClassesRule="hard"
        )
    )
    
    # Generate schedule
    response = create_schedule_dev(request)
    
    # Verify conflicts are respected
    assert_respects_conflicts(response, request)

def test_respects_teacher_availability():
    """Test that classes are not scheduled during teacher unavailable periods"""
    start_date = datetime.now()
    end_date = start_date + timedelta(days=7)
    
    # Create specific teacher unavailability pattern
    unavailable_slots = TimeSlotGenerator.create_daily_pattern(4)  # Fourth period every day
    
    request = ScheduleRequest(
        classes=ClassGenerator.create_multiple_classes(2),
        teacherAvailability=TeacherAvailabilityGenerator.create_weekly_availability(
            start_date=start_date,
            weeks=1,
            unavailable_pattern=unavailable_slots
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
    
    # Verify teacher availability is respected
    assert_respects_teacher_availability(response, request)

def test_respects_required_periods():
    """Test that classes are scheduled in their required periods"""
    start_date = datetime.now()
    end_date = start_date + timedelta(days=7)
    
    # Create class with specific required periods
    required_slots = [TimeSlot(dayOfWeek=2, period=3)]  # Tuesday third period
    classes = [
        ClassGenerator.create_class(
            class_id="test-1",
            weekly_schedule=WeeklySchedule(
                conflicts=[],
                preferredPeriods=[],
                requiredPeriods=required_slots,
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
            maxClassesPerDay=3,
            maxClassesPerWeek=8,
            minPeriodsPerWeek=1,
            maxConsecutiveClasses=1,
            consecutiveClassesRule="hard"
        )
    )
    
    # Generate schedule
    response = create_schedule_dev(request)
    
    # Verify required periods are respected
    assert_respects_required_periods(response, request)

def test_respects_class_limits():
    """Test that daily and weekly class limits are respected"""
    start_date = datetime.now()
    end_date = start_date + timedelta(days=14)
    
    request = ScheduleRequest(
        classes=ClassGenerator.create_multiple_classes(10),  # Create many classes
        teacherAvailability=TeacherAvailabilityGenerator.create_weekly_availability(
            start_date=start_date,
            weeks=2
        ),
        startDate=start_date.strftime("%Y-%m-%d"),
        endDate=end_date.strftime("%Y-%m-%d"),
        constraints=ScheduleConstraints(
            maxClassesPerDay=2,    # Strict daily limit
            maxClassesPerWeek=5,   # Strict weekly limit
            minPeriodsPerWeek=1,
            maxConsecutiveClasses=1,
            consecutiveClassesRule="hard"
        )
    )
    
    # Generate schedule
    response = create_schedule_dev(request)
    
    # Verify class limits are respected
    assert_respects_class_limits(response, request)

def test_respects_consecutive_classes():
    """Test that consecutive class constraints are respected"""
    start_date = datetime.now()
    end_date = start_date + timedelta(days=7)
    
    request = ScheduleRequest(
        classes=ClassGenerator.create_multiple_classes(5),
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
            maxConsecutiveClasses=1,  # No consecutive classes allowed
            consecutiveClassesRule="hard"
        )
    )
    
    # Generate schedule
    response = create_schedule_dev(request)
    
    # Verify consecutive class constraints are respected
    assert_respects_consecutive_classes(response, request)

def test_all_constraints():
    """Test that all constraints are respected simultaneously"""
    start_date = datetime.now()
    end_date = start_date + timedelta(days=14)
    
    # Create complex test scenario
    conflict_slots = TimeSlotGenerator.create_daily_pattern(1)  # First period conflicts
    required_slots = [TimeSlot(dayOfWeek=2, period=3)]  # Tuesday third period required
    unavailable_slots = TimeSlotGenerator.create_daily_pattern(4)  # Fourth period unavailable
    
    classes = [
        ClassGenerator.create_class(
            class_id="test-1",
            weekly_schedule=WeeklySchedule(
                conflicts=conflict_slots,
                preferredPeriods=[],
                requiredPeriods=required_slots,
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
                requiredPeriods=[],
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
    
    # Generate schedule
    response = create_schedule_dev(request)
    
    # Verify all constraints
    assert_valid_schedule(response, request)
