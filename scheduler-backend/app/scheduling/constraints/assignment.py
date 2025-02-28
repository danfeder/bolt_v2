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
            # Handle both dictionary and object formats
            if isinstance(assignment, dict):
                class_name = assignment["name"]
            else:
                # Handle ScheduleAssignment object
                class_name = assignment.name if hasattr(assignment, "name") else assignment.classId
            
            class_counts[class_name] += 1
            
        # Check that each class has at least one assignment
        for class_obj in context.request.classes:
            class_name = class_obj.name if hasattr(class_obj, "name") else class_obj.id
            if class_counts[class_name] == 0:
                violations.append(ConstraintViolation(
                    message=f"Class {class_name} has no assignments",
                    severity="error",
                    context={"className": class_name}
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
            # Handle both dictionary and object formats
            if isinstance(assignment, dict):
                # Dictionary format
                date_val = assignment["date"]
                # Convert to datetime.date if it's already a datetime
                if hasattr(date_val, "date"):
                    date_val = date_val.date()
                elif isinstance(date_val, str):
                    # Try to parse from ISO format
                    from datetime import datetime
                    date_val = datetime.fromisoformat(date_val.replace('Z', '+00:00')).date()
                
                # Get period from timeslot (handle both dict and object)
                if isinstance(assignment["timeSlot"], dict):
                    period = assignment["timeSlot"]["period"]
                else:
                    period = assignment["timeSlot"].period
                
                class_name = assignment["name"]
            else:
                # Object format (ScheduleAssignment)
                from datetime import datetime
                date_val = datetime.fromisoformat(assignment.date.replace('Z', '+00:00')).date()
                period = assignment.timeSlot.period
                class_name = assignment.name if hasattr(assignment, "name") else assignment.classId
            
            key = (date_val, period)
            by_time[key].append(class_name)
            
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
