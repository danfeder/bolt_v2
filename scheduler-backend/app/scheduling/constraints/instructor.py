from collections import defaultdict
from typing import List, Dict, Any, Set, Tuple
from datetime import datetime
from dateutil.tz import UTC

from ortools.sat.python import cp_model

from .base import BaseConstraint, ConstraintViolation
from ..core import SchedulerContext

class InstructorAvailabilityConstraint(BaseConstraint):
    """Ensures classes are only scheduled when instructor is available"""
    
    def __init__(self):
        super().__init__("instructor_availability")
        
    def apply(self, context: SchedulerContext) -> None:
        # Build lookup of unavailable periods
        unavailable_slots: Dict[str, Set[int]] = defaultdict(set)
        for avail in context.request.instructorAvailability:
            avail_date = datetime.fromisoformat(avail.date)
            if avail_date.tzinfo is None:
                avail_date = avail_date.replace(tzinfo=UTC)
                
            date_str = avail_date.date().isoformat()
            unavailable_slots[date_str].update(avail.periods)
        
        # Add constraints for each variable that would be during an unavailable period
        unavailable_count = 0
        for var in context.variables:
            date_str = var["date"].date().isoformat()
            if date_str in unavailable_slots and var["period"] in unavailable_slots[date_str]:
                context.model.Add(var["variable"] == 0)
                unavailable_count += 1
        
        print(f"Added {unavailable_count} instructor availability constraints")
    
    def validate(
        self,
        assignments: List[Dict[str, Any]],
        context: SchedulerContext
    ) -> List[ConstraintViolation]:
        violations = []
        
        # Build lookup of unavailable periods
        unavailable_slots: Dict[str, Set[int]] = defaultdict(set)
        for avail in context.request.instructorAvailability:
            avail_date = datetime.fromisoformat(avail.date)
            if avail_date.tzinfo is None:
                avail_date = avail_date.replace(tzinfo=UTC)
                
            date_str = avail_date.date().isoformat()
            unavailable_slots[date_str].update(avail.periods)
        
        # Check each assignment
        for assignment in assignments:
            date = datetime.fromisoformat(assignment.date).date().isoformat()
            period = assignment.timeSlot.period
            
            if date in unavailable_slots and period in unavailable_slots[date]:
                violations.append(ConstraintViolation(
                    message=(
                        f"Class {assignment.name} scheduled during "
                        f"unavailable period {period} on {date}"
                    ),
                    severity="error",
                    context={
                        "name": assignment.name,
                        "date": date,
                        "period": period
                    }
                ))
        
        return violations
