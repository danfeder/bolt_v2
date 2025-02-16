from collections import defaultdict
from typing import List, Dict, Any

from ortools.sat.python import cp_model

from .base import BaseConstraint, ConstraintViolation
from ..core import SchedulerContext

class SingleAssignmentConstraint(BaseConstraint):
    """
    Ensures each class is scheduled exactly once.
    
    This is a fundamental constraint that:
    1. Requires every class to be assigned to exactly one time slot
    2. Prevents any class from being scheduled multiple times
    
    Priority is set to 0 (highest) as this is a core scheduling requirement.
    """
    
    def __init__(self, enabled: bool = True):
        super().__init__(
            name="single_assignment",
            enabled=enabled,
            priority=0,  # Highest priority as this is a fundamental constraint
            weight=None  # Use default from config
        )
    
    def apply(self, context: SchedulerContext) -> None:
        """
        Apply single assignment constraints to the CP-SAT model.
        Creates sum(vars) == 1 constraint for each class.
        """
        if not self.enabled:
            return
            
        # Group variables by class
        by_class = defaultdict(list)
        for var in context.variables:
            by_class[var["name"]].append(var["variable"])
        
        # Add constraint for each class
        for class_name, vars_list in by_class.items():
            context.model.Add(sum(vars_list) == 1)
            
        print(f"Added single assignment constraints for {len(by_class)} classes")
    
    def _validate_impl(
        self,
        assignments: List[Dict[str, Any]],
        context: SchedulerContext
    ) -> List[ConstraintViolation]:
        violations = []
        
        # Count assignments per class using property access
        assignments_per_class = defaultdict(int)
        for assignment in assignments:
            assignments_per_class[assignment['name']] += 1
        
        # Check for missing or duplicate assignments
        for class_obj in context.request.classes:
            count = assignments_per_class[class_obj.name]
            if count == 0:
                violations.append(ConstraintViolation(
                    message=f"Class {class_obj.name} is not scheduled",
                    severity="error",
                    context={"name": class_obj.name}
                ))
            elif count > 1:
                violations.append(ConstraintViolation(
                    message=f"Class {class_obj.name} is scheduled {count} times",
                    severity="error",
                    context={
                        "name": class_obj.name,
                        "assignmentCount": count
                    }
                ))
        
        return violations

class NoOverlapConstraint(BaseConstraint):
    """
    Ensures no two classes are scheduled in the same time slot.
    
    This constraint prevents scheduling conflicts by:
    1. Ensuring each time slot (date + period) has at most one class
    2. Adding constraints only when multiple classes could be scheduled in a slot
    
    Priority is set to 0 (highest) as this is a core scheduling requirement.
    """
    
    def __init__(self, enabled: bool = True):
        super().__init__(
            name="no_overlap",
            enabled=enabled,
            priority=0,  # Highest priority as this is a fundamental constraint
            weight=None  # Use default from config
        )
    
    def apply(self, context: SchedulerContext) -> None:
        """
        Apply no-overlap constraints to the CP-SAT model.
        Creates sum(vars) <= 1 constraint for each time slot that
        could have multiple classes.
        """
        if not self.enabled:
            return
            
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
    
    def _validate_impl(
        self,
        assignments: List[Dict[str, Any]],
        context: SchedulerContext
    ) -> List[ConstraintViolation]:
        violations = []
        
        # Group assignments by time slot
        by_slot = defaultdict(list)
        for assignment in assignments:
            key = (assignment['date'], assignment['timeSlot']['period'])
            by_slot[key].append(assignment)
        
        # Check for overlaps
        for (date, period), slot_assignments in by_slot.items():
            if len(slot_assignments) > 1:
                class_names = [a['name'] for a in slot_assignments]
                violations.append(ConstraintViolation(
                    message=f"Multiple classes scheduled for {date} period {period}",
                    severity="error",
                    context={
                        "date": date,
                        "period": period,
                        "names": class_names
                    }
                ))
        
        return violations
