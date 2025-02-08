from typing import List, Dict, Set
from datetime import datetime
from dateutil import parser
from collections import defaultdict

from app.models import (
    ScheduleRequest,
    ScheduleResponse,
    ScheduleAssignment,
    TimeSlot
)

def assert_valid_assignments(response: ScheduleResponse, request: ScheduleRequest):
    """Verify that all assignments are valid according to the schedule request"""
    
    # Check that each class is scheduled exactly once
    class_assignments = defaultdict(int)
    for assignment in response.assignments:
        class_assignments[assignment.classId] += 1
    
    for class_obj in request.classes:
        assert class_assignments[class_obj.id] == 1, \
            f"Class {class_obj.id} has {class_assignments[class_obj.id]} assignments, expected 1"

def assert_no_overlaps(response: ScheduleResponse):
    """Verify that no two classes are scheduled at the same time"""
    
    # Group assignments by date and period
    time_slots: Dict[str, Dict[int, List[str]]] = defaultdict(lambda: defaultdict(list))
    
    for assignment in response.assignments:
        date = assignment.date.split('T')[0]  # Remove time part if present
        period = assignment.timeSlot.period
        time_slots[date][period].append(assignment.classId)
        
        # Check for overlaps
        assert len(time_slots[date][period]) == 1, \
            f"Multiple classes scheduled on {date} period {period}: {time_slots[date][period]}"

def assert_respects_conflicts(response: ScheduleResponse, request: ScheduleRequest):
    """Verify that no classes are scheduled during their conflict periods"""
    
    for assignment in response.assignments:
        # Find the corresponding class
        class_obj = next(c for c in request.classes if c.id == assignment.classId)
        weekday = parser.parse(assignment.date).weekday() + 1  # 1-5 (Mon-Fri)
        
        # Check against conflicts
        for conflict in class_obj.weeklySchedule.conflicts:
            assert not (
                conflict.dayOfWeek == weekday and 
                conflict.period == assignment.timeSlot.period
            ), f"Class {class_obj.id} scheduled during conflict period: day {weekday} period {assignment.timeSlot.period}"

def assert_respects_teacher_availability(response: ScheduleResponse, request: ScheduleRequest):
    """Verify that no classes are scheduled during teacher unavailable periods"""
    
    # Create lookup for teacher unavailability
    unavailable_slots: Dict[str, Set[TimeSlot]] = defaultdict(set)
    for availability in request.teacherAvailability:
        date = availability.date.split('T')[0]
        for slot in availability.unavailableSlots:
            unavailable_slots[date].add(slot)
    
    # Check each assignment
    for assignment in response.assignments:
        date = assignment.date.split('T')[0]
        if date in unavailable_slots:
            for unavailable in unavailable_slots[date]:
                assert not (
                    assignment.timeSlot.dayOfWeek == unavailable.dayOfWeek and
                    assignment.timeSlot.period == unavailable.period
                ), f"Class scheduled during teacher unavailable period on {date}"

def assert_respects_required_periods(response: ScheduleResponse, request: ScheduleRequest):
    """Verify that classes with required periods are scheduled in one of them"""
    
    for assignment in response.assignments:
        # Find the corresponding class
        class_obj = next(c for c in request.classes if c.id == assignment.classId)
        
        # Skip if no required periods
        if not class_obj.weeklySchedule.requiredPeriods:
            continue
            
        weekday = parser.parse(assignment.date).weekday() + 1
        period = assignment.timeSlot.period
        
        # Verify scheduled in a required period
        is_required = any(
            rp.dayOfWeek == weekday and rp.period == period
            for rp in class_obj.weeklySchedule.requiredPeriods
        )
        
        assert is_required, \
            f"Class {class_obj.id} not scheduled in a required period"

def assert_respects_class_limits(response: ScheduleResponse, request: ScheduleRequest):
    """Verify that daily and weekly class limits are respected"""
    
    # Group assignments by date
    by_date = defaultdict(list)
    by_week = defaultdict(list)
    start_date = parser.parse(request.startDate)
    
    for assignment in response.assignments:
        date = parser.parse(assignment.date)
        by_date[date.date()].append(assignment)
        
        # Calculate week number
        week_num = (date - start_date).days // 7
        by_week[week_num].append(assignment)
    
    # Check daily limits
    for date, assignments in by_date.items():
        assert len(assignments) <= request.constraints.maxClassesPerDay, \
            f"Too many classes ({len(assignments)}) scheduled on {date}"
    
    # Check weekly limits
    for week, assignments in by_week.items():
        assert request.constraints.minPeriodsPerWeek <= len(assignments) <= request.constraints.maxClassesPerWeek, \
            f"Week {week} has {len(assignments)} classes, outside limits [{request.constraints.minPeriodsPerWeek}, {request.constraints.maxClassesPerWeek}]"

def assert_respects_consecutive_classes(response: ScheduleResponse, request: ScheduleRequest):
    """Verify that consecutive class constraints are respected"""
    
    if request.constraints.consecutiveClassesRule != "hard":
        return  # Skip for soft constraints
    
    # Group assignments by date
    by_date = defaultdict(list)
    for assignment in response.assignments:
        date = parser.parse(assignment.date).date()
        by_date[date].append(assignment)
    
    # Check consecutive classes
    for date, assignments in by_date.items():
        # Sort by period
        assignments.sort(key=lambda x: x.timeSlot.period)
        
        # Check for consecutive periods
        consecutive_count = 1
        for i in range(1, len(assignments)):
            if assignments[i].timeSlot.period == assignments[i-1].timeSlot.period + 1:
                consecutive_count += 1
                assert consecutive_count <= request.constraints.maxConsecutiveClasses, \
                    f"Too many consecutive classes ({consecutive_count}) on {date}"
            else:
                consecutive_count = 1

def assert_valid_schedule(response: ScheduleResponse, request: ScheduleRequest):
    """Run all schedule validation checks"""
    assert_valid_assignments(response, request)
    assert_no_overlaps(response)
    assert_respects_conflicts(response, request)
    assert_respects_teacher_availability(response, request)
    assert_respects_required_periods(response, request)
    assert_respects_class_limits(response, request)
    assert_respects_consecutive_classes(response, request)
