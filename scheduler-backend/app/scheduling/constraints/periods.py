"""Constraints related to period assignments"""
from typing import List
from ..core import Constraint, SchedulerContext
from ...models import ScheduleAssignment
from ...utils.date_utils import to_utc_isoformat

class RequiredPeriodsConstraint(Constraint):
    """Enforce required periods as hard constraints"""
    
    def __init__(self):
        super().__init__("Required Periods")
    
    def apply(self, context: SchedulerContext) -> None:
        """Add hard constraints for required periods"""
        for class_obj in context.request.classes:
            # Look for variables matching this class
            class_vars = [
                var for var in context.variables 
                if var["name"] == class_obj.name
            ]

            # Handle required periods if present
            if class_obj.required_periods:
                for required in class_obj.required_periods:
                    # Find matching variable for this required period
                    matching_vars = [
                        var for var in class_vars
                        if (to_utc_isoformat(var["date"]) == required.date
                            and var["period"] == required.period)
                    ]
                    
                    if matching_vars:
                        # Force assignment to this period
                        context.model.Add(matching_vars[0]["variable"] == 1)
                        
                        # Prevent assignment to any other periods on this day
                        same_day_vars = [
                            var for var in class_vars
                        if (to_utc_isoformat(var["date"]) == required.date
                            and var["period"] != required.period)
                        ]
                        for var in same_day_vars:
                            context.model.Add(var["variable"] == 0)

    def validate(self, assignments: List[ScheduleAssignment], context: SchedulerContext) -> List[str]:
        """Validate that all required periods are satisfied"""
        violations = []

        for class_obj in context.request.classes:
            if not class_obj.required_periods:
                continue

            # Get assignments for this class
            class_assignments = [
                a for a in assignments if a.name == class_obj.name
            ]

            # Check each required period
            for required in class_obj.required_periods:
                matching = [
                    a for a in class_assignments
                    if (a.date == required.date
                        and a.timeSlot.period == required.period)
                ]

                if not matching:
                    violations.append(
                        f"Class {class_obj.name} is missing required assignment "
                        f"on {required.date} period {required.period}"
                    )

        return violations

class ConflictPeriodsConstraint(Constraint):
    """Prevent assignments to conflicting periods"""

    def __init__(self):
        super().__init__("Conflict Periods")

    def apply(self, context: SchedulerContext) -> None:
        """Add constraints to prevent assignment to conflicting periods"""
        for class_obj in context.request.classes:
            if not class_obj.conflicts:
                continue

            # Get all variables for this class
            class_vars = [
                var for var in context.variables 
                if var["name"] == class_obj.name
            ]

            # Prevent assignment to any conflicting periods
            for var in class_vars:
                weekday = var["date"].weekday() + 1  # Convert to 1-5 for Monday-Friday
                conflicts = [
                    c for c in class_obj.conflicts
                    if c.dayOfWeek == weekday and c.period == var["period"]
                ]
                if conflicts:
                    context.model.Add(var["variable"] == 0)

    def validate(self, assignments: List[ScheduleAssignment], context: SchedulerContext) -> List[str]:
        """Validate that no assignments violate conflicts"""
        violations = []

        for class_obj in context.request.classes:
            if not class_obj.conflicts:
                continue

            # Check each assignment against conflicts
            class_assignments = [
                a for a in assignments if a.name == class_obj.name
            ]

            for assignment in class_assignments:
                conflicts = [
                    c for c in class_obj.conflicts
                    if (c.dayOfWeek == assignment.timeSlot.dayOfWeek
                        and c.period == assignment.timeSlot.period)
                ]

                if conflicts:
                    violations.append(
                        f"Class {class_obj.name} is assigned to conflicting period "
                        f"on day {assignment.timeSlot.dayOfWeek} "
                        f"period {assignment.timeSlot.period}"
                    )

        return violations
