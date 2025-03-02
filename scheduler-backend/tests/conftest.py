import pytest
import logging
import csv
import os
import json
import random
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator, Callable
import time
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from app.main import app

from app.models import (
    ScheduleRequest,
    Class,
    TimeSlot,
    WeeklySchedule,
    InstructorAvailability,
    ScheduleConstraints
)

# ======= Test Client Fixtures =======

@pytest.fixture
def client() -> TestClient:
    """Return a TestClient instance for API testing"""
    return TestClient(app)

# ======= Basic Model Fixtures =======

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
        periods=5,
        days=5,
        timeSlots=base_time_slots
    )

@pytest.fixture
def base_class(base_weekly_schedule) -> Class:
    """Basic class for testing"""
    return Class(
        id="test-class-1",
        name="Test Class",
        capacity=20,
        grade=9,
        schedule=base_weekly_schedule
    )

@pytest.fixture
def base_instructor_availability(base_time_slots) -> InstructorAvailability:
    """Basic instructor availability for testing"""
    return InstructorAvailability(
        instructorId="test-instructor-1",
        name="Test Instructor",
        availableTimeSlots=base_time_slots,
        maxClassesPerDay=3,
        maxConsecutiveClasses=2,
        requireBreakAfter=3
    )

@pytest.fixture
def base_schedule_constraints() -> ScheduleConstraints:
    """Basic schedule constraints for testing"""
    return ScheduleConstraints(
        allowSplitSessions=True,
        balanceClassSizes=True,
        preventConcurrentClasses=True,
        maxCoachingLoad=3,
        ensureCompleteRotation=True,
        respectAvailability=True
    )

@pytest.fixture
def date_range():
    """Get a standard date range for testing (2 weeks)"""
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=14)  # 2 weeks
    return {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat()
    }

@pytest.fixture
def base_schedule_request(
    base_class,
    base_instructor_availability,
    base_schedule_constraints,
    date_range
):
    """Basic schedule request for testing"""
    return ScheduleRequest(
        classes=[base_class],
        instructors=[base_instructor_availability],
        constraints=base_schedule_constraints,
        startDate=date_range["startDate"],
        endDate=date_range["endDate"],
        rotationEnabled=True,
        optimizationLevel="standard",
        balanceStudentLoad=True,
        allowPartialSchedules=False
    )

# ======= Test Data Fixtures =======

@pytest.fixture
def csv_data():
    """Load Schedule_From_Json_Corrected.csv data"""
    data_path = Path(__file__).parent / "fixtures" / "Schedule_From_Json_Corrected.csv"
    
    if not data_path.exists():
        pytest.skip(f"Test data file not found: {data_path}")
    
    with open(data_path, newline='') as f:
        reader = csv.DictReader(f)
        return [row for row in reader]

@pytest.fixture
def integration_constraints():
    """Schedule constraints specifically for integration testing"""
    return ScheduleConstraints(
        allowSplitSessions=False,
        balanceClassSizes=True,
        preventConcurrentClasses=True,
        maxCoachingLoad=2,
        ensureCompleteRotation=True,
        respectAvailability=True,
        enforceBreaks=True,
        maximumConsecutiveClasses=2,
        restrictGradeMixing=True,
        allowSubstitutions=False
    )

# ======= Utility Fixtures =======

@pytest.fixture
def setup_logging():
    """Configure logging for tests"""
    logger = logging.getLogger("test")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    # Create logs directory if it doesn't exist
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    return logger

@pytest.fixture
def performance_logger(setup_logging):
    """Logger specifically for performance metrics"""
    logger = logging.getLogger("performance")
    logger.setLevel(logging.INFO)
    return logger

@pytest.fixture
def timer():
    """Timer utility for performance measurements"""
    @contextmanager
    def _timer(description: str, logger=None):
        start = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start
            message = f"{description}: {elapsed:.4f} seconds"
            if logger:
                logger.info(message)
            else:
                print(message)
    
    return _timer

# ======= Mock Fixtures =======

@pytest.fixture
def mock_solver():
    """Create a mock solver for testing"""
    mock = MagicMock()
    mock.solve.return_value = {
        "success": True,
        "schedule": {},
        "metrics": {
            "runtime": 0.5,
            "iterations": 100,
            "score": 0.95
        }
    }
    return mock

@pytest.fixture
def mock_constraint_factory():
    """Create a mock constraint factory for testing"""
    mock = MagicMock()
    mock_constraint = MagicMock()
    mock_constraint.validate.return_value = (True, [])
    mock_constraint.apply.return_value = True
    
    mock.create.return_value = mock_constraint
    return mock

@pytest.fixture
def temp_file():
    """Create a temporary file for testing"""
    fd, path = tempfile.mkstemp()
    yield path
    os.close(fd)
    os.unlink(path)

# ======= Test Configuration =======

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "api: mark test as API test")
    config.addinivalue_line("markers", "performance: mark test for performance measurement")

def pytest_addoption(parser):
    """Add custom command line options to pytest"""
    parser.addoption(
        "--run-slow", action="store_true", default=False, help="run slow tests"
    )
    parser.addoption(
        "--run-performance", action="store_true", default=False, help="run performance tests"
    )

def pytest_collection_modifyitems(config, items):
    """Skip slow tests unless --run-slow is specified"""
    skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
    skip_performance = pytest.mark.skip(reason="need --run-performance option to run")
    
    for item in items:
        if "slow" in item.keywords and not config.getoption("--run-slow"):
            item.add_marker(skip_slow)
        if "performance" in item.keywords and not config.getoption("--run-performance"):
            item.add_marker(skip_performance)
