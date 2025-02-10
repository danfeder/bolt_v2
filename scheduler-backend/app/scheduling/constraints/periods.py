from collections import defaultdict
from typing import List, Dict, Any, Set, Tuple
from dateutil import parser
from dateutil.tz import UTC

from ortools.sat.python import cp_model

from .base import BaseConstraint, ConstraintViolation
from ..core import SchedulerContext

class RequiredPeriodsConstraint(BaseConstraint):
    """Ensures classes with required periods are scheduled in one of them"""
    
    def __init__(self):
        super().__init__("required_periods")
        
    def apply(self, context: SchedulerContext) -> None:
        required_count = 0
        
        # First identify classes that share required periods
        required_period_map = defaultdict(list)
        for class_obj in context.request.classes:
            if not class_obj.weeklySchedule.requiredPeriods:
                continue
            for rp in class_obj.weeklySchedule.requiredPeriods:
                key = (rp.dayOfWeek, rp.period)
                required_period_map[key].append(class_obj.id)
                
        # Log conflicts for debugging
        for (day, period), class_ids in required_period_map.items():
            if len(class_ids) > 1:
                print(
                    f"Warning: Multiple classes require day {day} period {period}: "
                    f"{class_ids}"
                )
        
        # Add constraints for each class with required periods
        for class_obj in context.request.classes:
            if not class_obj.weeklySchedule.requiredPeriods:
                continue
                
            # Get variables for this class that match required periods
            class_vars = []
            for var in context.variables:
                if var["classId"] == class_obj.id:
                    weekday = var["date"].weekday() + 1
                    period = var["period"]
                    
                    # Check if this slot matches a required period
                    is_required = any(
                        rp.dayOfWeek == weekday and rp.period == period
                        for rp in class_obj.weeklySchedule.requiredPeriods
                    )
                    
                    if is_required:
                        class_vars.append(var["variable"])
            
            if not class_vars:
                raise Exception(
                    f"No valid time slots found for required periods of class {class_obj.id}. "
                    f"Required periods: {[(rp.dayOfWeek, rp.period) for rp in class_obj.weeklySchedule.requiredPeriods]}"
                )
            
            # Class must be scheduled in one of its required periods
            context.model.Add(sum(class_vars) == 1)
            required_count += 1
        
        print(f"Added required period constraints for {required_count} classes")
    
    def validate(
        self,
        assignments: List[Dict[str, Any]],
        context: SchedulerContext
    ) -> List[ConstraintViolation]:
        violations = []
        
        # Check each class with required periods
        for class_obj in context.request.classes:
            if not class_obj.weeklySchedule.requiredPeriods:
                continue
                
            # Find this class's assignment
            assignment = next(
                (a for a in assignments if a["classId"] == class_obj.id),
                None
            )
            
            if not assignment:
                violations.append(ConstraintViolation(
                    message=f"Class {class_obj.id} with required periods is not scheduled",
                    severity="error",
                    context={"classId": class_obj.id}
                ))
                continue
                
            # Check if assigned time matches a required period
            weekday = parser.parse(assignment["date"]).weekday() + 1
            period = assignment["timeSlot"]["period"]
            
            is_required = any(
                rp.dayOfWeek == weekday and rp.period == period
                for rp in class_obj.weeklySchedule.requiredPeriods
            )
            
            if not is_required:
                violations.append(ConstraintViolation(
                    message=(
                        f"Class {class_obj.id} not scheduled in a required period. "
                        f"Assigned: day {weekday} period {period}"
                    ),
                    severity="error",
                    context={
                        "classId": class_obj.id,
                        "assignedDay": weekday,
                        "assignedPeriod": period,
                        "requiredPeriods": [
                            {"day": rp.dayOfWeek, "period": rp.period}
                            for rp in class_obj.weeklySchedule.requiredPeriods
                        ]
                    }
                ))
        
        return violations

class ConflictPeriodsConstraint(BaseConstraint):
    """Ensures classes are not scheduled during their conflict periods"""
    
    def __init__(self):
        super().__init__("conflict_periods")
        
    def apply(self, context: SchedulerContext) -> None:
        conflict_count = 0
        
        # Add constraints for each class with conflicts
        for class_obj in context.request.classes:
            if not class_obj.weeklySchedule.conflicts:
                continue
                
            # Get variables for this class
            for var in context.variables:
                if var["classId"] == class_obj.id:
                    weekday = var["date"].weekday() + 1
                    period = var["period"]
                    
                    # Check if this slot conflicts
                    is_conflict = any(
                        conflict.dayOfWeek == weekday and conflict.period == period
                        for conflict in class_obj.weeklySchedule.conflicts
                    )
                    
                    if is_conflict:
                        context.model.Add(var["variable"] == 0)
                        conflict_count += 1
        
        print(f"Added {conflict_count} conflict period constraints")
    
    def validate(
        self,
        assignments: List[Dict[str, Any]],
        context: SchedulerContext
    ) -> List[ConstraintViolation]:
        violations = []
        
        # Check each class with conflicts
        for class_obj in context.request.classes:
            if not class_obj.weeklySchedule.conflicts:
                continue
                
            # Find this class's assignment
            assignment = next(
                (a for a in assignments if a["classId"] == class_obj.id),
                None
            )
            
            if not assignment:
                continue  # Missing assignment will be caught by SingleAssignmentConstraint
                
            # Check if assigned time conflicts
            weekday = parser.parse(assignment["date"]).weekday() + 1
            period = assignment["timeSlot"]["period"]
            
            conflicts = [
                conflict for conflict in class_obj.weeklySchedule.conflicts
                if conflict.dayOfWeek == weekday and conflict.period == period
            ]
            
            if conflicts:
                violations.append(ConstraintViolation(
                    message=(
                        f"Class {class_obj.id} scheduled during conflict period "
                        f"day {weekday} period {period}"
                    ),
                    severity="error",
                    context={
                        "classId": class_obj.id,
                        "assignedDay": weekday,
                        "assignedPeriod": period,
                        "conflicts": [
                            {"day": c.dayOfWeek, "period": c.period}
                            for c in conflicts
                        ]
                    }
                ))
        
        return violations
