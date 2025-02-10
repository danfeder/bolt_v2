from collections import defaultdict
from typing import List, Dict, Any

from ortools.sat.python import cp_model

from .base import BaseConstraint, ConstraintViolation
from ..core import SchedulerContext

class SingleAssignmentConstraint(BaseConstraint):
    """Ensures each class is scheduled exactly once"""
    
    def __init__(self):
        super().__init__("single_assignment")
    
    def apply(self, context: SchedulerContext) -> None:
        # Group variables by class
        by_class = defaultdict(list)
        for var in context.variables:
            by_class[var["classId"]].append(var["variable"])
        
        # Add constraint for each class
        for class_id, vars_list in by_class.items():
            context.model.Add(sum(vars_list) == 1)
            
        print(f"Added single assignment constraints for {len(by_class)} classes")
    
    def validate(
        self,
        assignments: List[Dict[str, Any]],
        context: SchedulerContext
    ) -> List[ConstraintViolation]:
        violations = []
        
        # Count assignments per class using property access
        assignments_per_class = defaultdict(int)
        for assignment in assignments:
            assignments_per_class[assignment.classId] += 1
        
        # Check for missing or duplicate assignments
        for class_obj in context.request.classes:
            count = assignments_per_class[class_obj.id]
            if count == 0:
                violations.append(ConstraintViolation(
                    message=f"Class {class_obj.id} is not scheduled",
                    severity="error",
                    context={"classId": class_obj.id}
                ))
            elif count > 1:
                violations.append(ConstraintViolation(
                    message=f"Class {class_obj.id} is scheduled {count} times",
                    severity="error",
                    context={
                        "classId": class_obj.id,
                        "assignmentCount": count
                    }
                ))
        
        return violations

class NoOverlapConstraint(BaseConstraint):
    """Ensures no two classes are scheduled in the same period"""
    
    def __init__(self):
        super().__init__("no_overlap")
    
    def apply(self, context: SchedulerContext) -> None:
        # Group variables by date and period
        by_slot = defaultdict(list)
        for var in context.variables:
            key = (var["date"].date(), var["period"])
            by_slot[key].append(var["variable"])
        
        # Add constraint for each time slot
        overlap_constraints = 0
        for key, vars_list in by_slot.items():
            if len(vars_list) > 1:  # Only need constraint if multiple classes could be scheduled
                context.model.Add(sum(vars_list) <= 1)
                overlap_constraints += 1
                
        print(f"Added {overlap_constraints} no-overlap constraints")
    
    def validate(
        self,
        assignments: List[Dict[str, Any]],
        context: SchedulerContext
    ) -> List[ConstraintViolation]:
        violations = []
        
        # Group assignments by time slot
        by_slot = defaultdict(list)
        for assignment in assignments:
            key = (assignment.date, assignment.timeSlot.period)
            by_slot[key].append(assignment)
        
        # Check for overlaps
        for (date, period), slot_assignments in by_slot.items():
            if len(slot_assignments) > 1:
                class_ids = [a.classId for a in slot_assignments]
                violations.append(ConstraintViolation(
                    message=f"Multiple classes scheduled for {date} period {period}",
                    severity="error",
                    context={
                        "date": date,
                        "period": period,
                        "classIds": class_ids
                    }
                ))
        
        return violations
