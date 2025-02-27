import pytest
import logging
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
import time
from app.models import (
    ScheduleRequest,
    Class,
    TimeSlot,
    WeeklySchedule,
    InstructorAvailability,
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
def base_instructor_availability(base_time_slots) -> InstructorAvailability:
    """Basic instructor availability for testing"""
    now = datetime.now()
    return InstructorAvailability(
        date=now,
        periods=[1, 2],  # First two periods unavailable
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
        consecutiveClassesRule="hard",
        startDate=datetime.now().strftime("%Y-%m-%d"),
        endDate=(datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
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
    base_instructor_availability,
    base_schedule_constraints,
    date_range
) -> ScheduleRequest:
    """Basic schedule request for testing"""
    return ScheduleRequest(
        classes=[base_class],
        instructorAvailability=[base_instructor_availability],
        startDate=date_range["start"],
        endDate=date_range["end"],
        constraints=base_schedule_constraints
    )

@pytest.fixture(scope="session")
def setup_logging():
    """Configure logging for tests"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('test_execution.log')
        ]
    )
    return logging.getLogger('scheduler_tests')

@pytest.fixture(scope="session")
def performance_logger(setup_logging):
    """Logger specifically for performance metrics"""
    logger = logging.getLogger('performance_metrics')
    logger.setLevel(logging.INFO)
    return logger

@pytest.fixture
def timer():
    """Timer utility for performance measurements"""
    class Timer:
        def __enter__(self):
            self.start = time.perf_counter()
            return self

        def __exit__(self, *args):
            self.end = time.perf_counter()
            self.duration = self.end - self.start

    return Timer()

@pytest.fixture(scope="session")
def csv_data():
    """Load Schedule_From_Json_Corrected.csv data"""
    csv_path = Path(__file__).parent.parent / 'data' / 'Schedule_From_Json_Corrected.csv'
    classes = []
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        classes = [row for row in reader]
    
    return classes

@pytest.fixture
def integration_constraints() -> ScheduleConstraints:
    """Schedule constraints specifically for integration testing"""
    start_date = datetime.now()
    end_date = start_date + timedelta(days=7)
    return ScheduleConstraints(
        maxClassesPerDay=4,
        maxClassesPerWeek=15,
        minPeriodsPerWeek=1,
        maxConsecutiveClasses=2,
        consecutiveClassesRule="soft",
        startDate=start_date.strftime("%Y-%m-%d"),
        endDate=end_date.strftime("%Y-%m-%d")
    )
