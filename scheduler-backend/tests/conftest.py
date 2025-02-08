import pytest
from datetime import datetime, timedelta
from typing import List
from app.models import (
    ScheduleRequest,
    Class,
    TimeSlot,
    WeeklySchedule,
    TeacherAvailability,
    ScheduleConstraints
)

@pytest.fixture
def base_time_slots() -> List[TimeSlot]:
    """Basic time slots for testing"""
    return [
        TimeSlot(dayOfWeek=1, period=1),  # Monday first period
        TimeSlot(dayOfWeek=2, period=2),  # Tuesday second period
        TimeSlot(dayOfWeek=3, period=3),  # Wednesday third period
        TimeSlot(dayOfWeek=4, period=4),  # Thursday fourth period
        TimeSlot(dayOfWeek=5, period=5),  # Friday fifth period
    ]

@pytest.fixture
def base_weekly_schedule(base_time_slots) -> WeeklySchedule:
    """Basic weekly schedule for testing"""
    return WeeklySchedule(
        conflicts=[base_time_slots[0]],  # Monday first period conflict
        preferredPeriods=[base_time_slots[1]],  # Tuesday second period preferred
        requiredPeriods=[base_time_slots[2]],  # Wednesday third period required
        avoidPeriods=[base_time_slots[4]],  # Friday fifth period avoid
        preferenceWeight=1.5,
        avoidanceWeight=1.2
    )

@pytest.fixture
def base_class(base_weekly_schedule) -> Class:
    """Basic class for testing"""
    return Class(
        id="test-101",
        name="Test Class 101",
        grade="1",
        weeklySchedule=base_weekly_schedule
    )

@pytest.fixture
def base_teacher_availability(base_time_slots) -> TeacherAvailability:
    """Basic teacher availability for testing"""
    return TeacherAvailability(
        date=datetime.now().strftime("%Y-%m-%d"),
        unavailableSlots=[base_time_slots[0]],  # Monday first period unavailable
        preferredSlots=[base_time_slots[1]],    # Tuesday second period preferred
        avoidSlots=[base_time_slots[4]]         # Friday fifth period avoid
    )

@pytest.fixture
def base_schedule_constraints() -> ScheduleConstraints:
    """Basic schedule constraints for testing"""
    return ScheduleConstraints(
        maxClassesPerDay=3,
        maxClassesPerWeek=8,
        minPeriodsPerWeek=1,
        maxConsecutiveClasses=1,
        consecutiveClassesRule="hard"
    )

@pytest.fixture
def date_range():
    """Get a standard date range for testing (2 weeks)"""
    start_date = datetime.now()
    end_date = start_date + timedelta(days=14)
    return {
        "start": start_date.strftime("%Y-%m-%d"),
        "end": end_date.strftime("%Y-%m-%d")
    }

@pytest.fixture
def base_schedule_request(
    base_class,
    base_teacher_availability,
    base_schedule_constraints,
    date_range
) -> ScheduleRequest:
    """Basic schedule request for testing"""
    return ScheduleRequest(
        classes=[base_class],
        teacherAvailability=[base_teacher_availability],
        startDate=date_range["start"],
        endDate=date_range["end"],
        constraints=base_schedule_constraints
    )
