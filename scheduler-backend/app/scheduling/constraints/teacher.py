from collections import defaultdict
from typing import List, Dict, Any, Set, Tuple
from datetime import datetime
from dateutil.tz import UTC

from ortools.sat.python import cp_model

from .base import BaseConstraint, ConstraintViolation
from ..core import SchedulerContext

class TeacherAvailabilityConstraint(BaseConstraint):
    """Ensures classes are only scheduled when teachers are available"""
    
    def __init__(self):
        super().__init__("teacher_availability")
        
    def apply(self, context: SchedulerContext) -> None:
        # Build lookup of unavailable periods
        unavailable_slots: Set[Tuple[str, int]] = set()
        for teacher_avail in context.request.teacherAvailability:
            avail_date = datetime.fromisoformat(teacher_avail.date)
            if avail_date.tzinfo is None:
                avail_date = avail_date.replace(tzinfo=UTC)
                
            for slot in teacher_avail.unavailableSlots:
                key = (avail_date.date().isoformat(), slot.period)
                unavailable_slots.add(key)
        
        # Add constraints for each variable that would be during an unavailable period
        unavailable_count = 0
        for var in context.variables:
            key = (var["date"].date().isoformat(), var["period"])
            if key in unavailable_slots:
                context.model.Add(var["variable"] == 0)
                unavailable_count += 1
        
        print(f"Added {unavailable_count} teacher availability constraints")
    
    def validate(
        self,
        assignments: List[Dict[str, Any]],
        context: SchedulerContext
    ) -> List[ConstraintViolation]:
        violations = []
        
        # Build lookup of unavailable periods
        unavailable_slots: Set[Tuple[str, int]] = set()
        for teacher_avail in context.request.teacherAvailability:
            avail_date = datetime.fromisoformat(teacher_avail.date)
            if avail_date.tzinfo is None:
                avail_date = avail_date.replace(tzinfo=UTC)
                
            for slot in teacher_avail.unavailableSlots:
                key = (avail_date.date().isoformat(), slot.period)
                unavailable_slots.add(key)
        
        # Check each assignment
        for assignment in assignments:
            date = datetime.fromisoformat(assignment.date).date().isoformat()
            period = assignment.timeSlot.period
            key = (date, period)
            
            if key in unavailable_slots:
                violations.append(ConstraintViolation(
                    message=(
                        f"Class {assignment.classId} scheduled during "
                        f"unavailable period {period} on {date}"
                    ),
                    severity="error",
                    context={
                        "classId": assignment.classId,
                        "date": date,
                        "period": period
                    }
                ))
        
        return violations
