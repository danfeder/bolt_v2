import pytest
import csv
from datetime import datetime, timedelta
from pathlib import Path
from app.scheduling.solvers.solver import UnifiedSolver
from typing import List, Dict, Set
from app.models import (
    ScheduleRequest,
    ScheduleConstraints,
    TimeSlot,
    WeeklySchedule
)
from tests.utils.generators import (
    ClassGenerator,
    InstructorAvailabilityGenerator,
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
    
    solver = UnifiedSolver()
    response = solver.create_schedule(request)
    assert_valid_schedule(response, request)
    
    # Verify metadata
    assert response.metadata.solver == "cp-sat-unified"
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
        instructorAvailability=InstructorAvailabilityGenerator.create_weekly_availability(
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
            consecutiveClassesRule="hard",
            startDate=start_date.strftime("%Y-%m-%d"),
            endDate=end_date.strftime("%Y-%m-%d")
        )
    )
    
    solver = UnifiedSolver()
    response = solver.create_schedule(request)
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
        instructorAvailability=InstructorAvailabilityGenerator.create_weekly_availability(
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
            consecutiveClassesRule="hard",
            startDate=start_date.strftime("%Y-%m-%d"),
            endDate=end_date.strftime("%Y-%m-%d")
        )
    )
    
    solver = UnifiedSolver()
    response = solver.create_schedule(request)
    assert_valid_schedule(response, request)

def test_schedule_from_json_corrected(setup_logging, performance_logger, timer, csv_data, integration_constraints):
    """Test schedule generation using the Schedule_From_Json_Corrected.csv dataset"""
    logger = setup_logging
    logger.info("Starting integration test with Schedule_From_Json_Corrected.csv dataset")
    
    start_date = datetime.now()
    logger.debug(f"Test start time: {start_date}")
    end_date = start_date + timedelta(days=7)
    
    # Verify the CSV data is loaded correctly
    assert len(csv_data) > 0, "CSV data should not be empty"
    logger.info(f"Loaded {len(csv_data)} classes from CSV")
    
    # Convert CSV data into classes with appropriate weekly schedules
    classes = []
    day_map = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5}
    
    for class_data in csv_data:
        # Create sets of periods for each class
        preferred_periods = []
        conflicts = []
        
        # Convert the period data into TimeSlots for each day
        for day_name in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
            # Parse conflict periods from CSV
            conflict_periods = [int(p.strip()) for p in class_data[day_name].split() if p.strip()]
            day_num = day_map[day_name]
            
            # Each period listed in CSV is a conflict period
            for period in conflict_periods:
                conflicts.append(TimeSlot(dayOfWeek=day_num, period=period))
        
        classes.append(ClassGenerator.create_class(
            class_id=class_data['Class'],  # Use Class field directly
            weekly_schedule=WeeklySchedule(
                conflicts=conflicts,
                preferredPeriods=preferred_periods,
                requiredPeriods=[],  # No strict requirements from CSV
                avoidPeriods=[],     # No explicit avoid periods
                preferenceWeight=1.0,
                avoidanceWeight=1.0
            )
        ))
    
    # Create schedule request with realistic constraints
    request = ScheduleRequest(
        classes=classes,
        instructorAvailability=InstructorAvailabilityGenerator.create_weekly_availability(
            start_date=start_date,
            weeks=1
        ),
        startDate=start_date.strftime("%Y-%m-%d"),
        endDate=end_date.strftime("%Y-%m-%d"),
        constraints=ScheduleConstraints(
            maxClassesPerDay=4,    # Adjusted based on real data patterns
            maxClassesPerWeek=15,  # Reasonable limit for a week
            minPeriodsPerWeek=1,
            maxConsecutiveClasses=2,
            consecutiveClassesRule="soft",  # Allow some flexibility
            startDate=start_date.strftime("%Y-%m-%d"),
            endDate=end_date.strftime("%Y-%m-%d")
        )
    )
    
    # Generate schedule and verify
    with timer as t:
        solver = UnifiedSolver()
        response = solver.create_schedule(request)
        assert_valid_schedule(response, request)
    
    performance_logger.info(f"Schedule generation completed in {t.duration:.2f} seconds")
    
    # Additional validations specific to this dataset
    logger.info("Validating schedule assignments and constraints")
    assignments = response.assignments
    assigned_slots: Dict[str, Set[tuple]] = {}  # class_id -> set of (day, period)
    validation_stats = {
        "total_assignments": len(assignments),
        "classes_scheduled": set(),
        "periods_per_class": {},
        "assignments_per_day": {},
    }
    
    for assignment in assignments:
        class_id = assignment.classId
        if class_id not in assigned_slots:
            assigned_slots[class_id] = set()
        
        slot = (assignment.timeSlot.dayOfWeek, assignment.timeSlot.period)
        assigned_slots[class_id].add(slot)
        
        # Verify assignment matches CSV preferences
        class_data = next(c for c in csv_data if c['Class'] == class_id)
        day_name = next(name for name, num in day_map.items() if num == assignment.timeSlot.dayOfWeek)
        # Convert CSV periods to integers for comparison
        conflict_periods = [int(p.strip()) for p in class_data[day_name].split() if p.strip()]
        assert assignment.timeSlot.period not in conflict_periods, \
            f"Class {class_id} assigned to conflicting slot on {day_name} (period {assignment.timeSlot.period})"
        
        # Track statistics
        validation_stats["classes_scheduled"].add(class_id)
        validation_stats["periods_per_class"][class_id] = validation_stats["periods_per_class"].get(class_id, 0) + 1
        day_key = f"Day {assignment.timeSlot.dayOfWeek}"
        validation_stats["assignments_per_day"][day_key] = validation_stats["assignments_per_day"].get(day_key, 0) + 1
    
    # Verify scheduling coverage
    for class_id, slots in assigned_slots.items():
        assert len(slots) >= request.constraints.minPeriodsPerWeek, \
            f"Class {class_id} scheduled for fewer than minimum periods"
        
        # Check daily limit
        daily_counts = {}
        for day, _ in slots:
            daily_counts[day] = daily_counts.get(day, 0) + 1
            assert daily_counts[day] <= request.constraints.maxClassesPerDay, \
                f"Class {class_id} exceeds max classes per day"
    
    # Log validation statistics
    logger.info("Schedule Validation Statistics:")
    logger.info(f"Total assignments: {validation_stats['total_assignments']}")
    logger.info(f"Unique classes scheduled: {len(validation_stats['classes_scheduled'])}")
    logger.info("\nAssignments per day:")
    for day, count in sorted(validation_stats["assignments_per_day"].items()):
        logger.info(f"  {day}: {count} assignments")
    logger.info("\nPeriods per class:")
    for class_id, count in sorted(validation_stats["periods_per_class"].items()):
        logger.info(f"  {class_id}: {count} periods")

    # Verify optimization metrics and log performance
    assert response.metadata.solver == "cp-sat-unified"
    assert response.metadata.duration > 0
    assert response.metadata.score > 0
    
    performance_logger.info(f"Solver performance metrics:")
    performance_logger.info(f"  Duration: {response.metadata.duration:.2f} seconds")
    performance_logger.info(f"  Score: {response.metadata.score}")
    performance_logger.info(f"  Total test execution time: {t.duration:.2f} seconds")

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
        instructorAvailability=InstructorAvailabilityGenerator.create_weekly_availability(
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
            consecutiveClassesRule="hard",
            startDate=start_date.strftime("%Y-%m-%d"),
            endDate=end_date.strftime("%Y-%m-%d")
        )
    )
    
    # Should raise an exception due to impossible constraints
    with pytest.raises(Exception) as exc_info:
        solver = UnifiedSolver()
        solver.create_schedule(request)
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
        instructorAvailability=InstructorAvailabilityGenerator.create_weekly_availability(
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
            consecutiveClassesRule="hard",
            startDate=start_date.strftime("%Y-%m-%d"),
            endDate=end_date.strftime("%Y-%m-%d")
        )
    )
    
    solver = UnifiedSolver()
    response = solver.create_schedule(request)
    assert_valid_schedule(response, request)
    
    # Verify that prio-1 got its required period
    prio1_assignment = next(a for a in response.assignments if a.classId == "prio-1")
    assert prio1_assignment.timeSlot.dayOfWeek == 2
    assert prio1_assignment.timeSlot.period == 3
