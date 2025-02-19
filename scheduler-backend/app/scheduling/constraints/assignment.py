"""Assignment-related scheduling constraints"""
from collections import defaultdict
from typing import List, Dict, Any
from ..core import SchedulerContext  
from .base import BaseConstraint, ConstraintViolation

class BaseAssignmentConstraint(BaseConstraint):
    """Base class for assignment constraints"""
    pass

class SingleAssignmentConstraint(BaseAssignmentConstraint):
    """Ensures each class is assigned at least once"""
    
    def __init__(self, enabled: bool = True):
        super().__init__("single_assignment", enabled=enabled)
    
    def apply(self, context: SchedulerContext) -> None:
        if not self.enabled:
            return
            
        # Group variables by class
        class_vars = defaultdict(list)
        for var in context.variables:
            class_vars[var["name"]].append(var["variable"])
            
        # Add constraint for each class to be scheduled at least once
        for class_name, vars_list in class_vars.items():
            context.model.Add(sum(vars_list) >= 1)
            
    def validate(
        self,
        assignments: List[Dict[str, Any]],
        context: SchedulerContext
    ) -> List[ConstraintViolation]:
        violations = []
        
        # Count assignments per class
        class_counts = defaultdict(int)
        for assignment in assignments:
            class_counts[assignment["name"]] += 1
            
        # Check that each class has at least one assignment
        for class_obj in context.request.classes:
            if class_counts[class_obj.name] == 0:
                violations.append(ConstraintViolation(
                    message=f"Class {class_obj.name} has no assignments",
                    severity="error",
                    context={"className": class_obj.name}
                ))
                
        return violations

class NoOverlapConstraint(BaseAssignmentConstraint):
    """Prevents classes from being scheduled in the same period"""
    
    def __init__(self, enabled: bool = True):
        super().__init__("no_overlap", enabled=enabled)
    
    def apply(self, context: SchedulerContext) -> None:
        if not self.enabled:
            return
            
        # Group variables by timeslot
        by_time = defaultdict(list)
        for var in context.variables:
            key = (var["date"].date(), var["period"])
            by_time[key].append(var["variable"])
            
        # Add constraint to prevent overlap in each timeslot
        for vars_list in by_time.values():
            context.model.Add(sum(vars_list) <= 1)
            
    def validate(
        self,
        assignments: List[Dict[str, Any]],
        context: SchedulerContext
    ) -> List[ConstraintViolation]:
        violations = []
        
        # Group assignments by timeslot
        by_time = defaultdict(list)
        for assignment in assignments:
            key = (assignment["date"].date(), assignment["timeSlot"]["period"])
            by_time[key].append(assignment["name"])
            
        # Check for overlaps
        for (date, period), classes in by_time.items():
            if len(classes) > 1:
                violations.append(ConstraintViolation(
                    message=(
                        f"Multiple classes scheduled on {date} period {period}: "
                        f"{', '.join(classes)}"
                    ),
                    severity="error",
                    context={
                        "date": str(date),
                        "period": period,
                        "classes": classes
                    }
                ))
                
        return violations
