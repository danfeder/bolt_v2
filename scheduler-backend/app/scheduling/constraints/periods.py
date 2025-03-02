"""Constraints related to period assignments"""
from typing import List, Dict, Any
from datetime import datetime
from ..core import SchedulerContext
from .base import BaseConstraint, ConstraintViolation
from ...models import (
    ScheduleAssignment,
    WeeklySchedule,
    RequiredPeriod,
    ConflictPeriod,
    TimeSlot
)

class RequiredPeriodsConstraint(BaseConstraint):
    """Enforce required periods as hard constraints"""
    
    def __init__(self, enabled: bool = True):
        super().__init__("required_periods", enabled=enabled)
    
    def apply(self, context: SchedulerContext) -> None:
        """Add hard constraints for required periods"""
        if not self.enabled:
            return
            
        print(f"Applying {self.name} constraint")
            
        for class_obj in context.request.classes:
            # Look for variables matching this class
            class_vars = [
                var for var in context.variables 
                if var["name"] == class_obj.name
            ]

            # Handle required periods if present
            if hasattr(class_obj, "weeklySchedule") and class_obj.weeklySchedule.requiredPeriods:
                print(f"Found {len(class_obj.weeklySchedule.requiredPeriods)} required periods for {class_obj.name}")
                for required in class_obj.weeklySchedule.requiredPeriods:
                    if hasattr(required, "dayOfWeek"):
                        # Handle TimeSlot-based required periods with dayOfWeek
                        print(f"Required period: day={required.dayOfWeek}, period={required.period}")
                        # Find variables for this weekday and period
                        matching_vars = [
                            var for var in class_vars
                            if (var["date"].weekday() + 1 == required.dayOfWeek  # Convert 0-6 to 1-7
                                and var["period"] == required.period)
                        ]
                    elif hasattr(required, "date"):
                        # Handle RequiredPeriod-based periods with date
                        req_date = datetime.fromisoformat(required.date) if isinstance(required.date, str) else required.date
                        print(f"Required period: date={req_date}, period={required.period}")
                        # Find variables for this date and period
                        matching_vars = [
                            var for var in class_vars
                            if (var["date"].date() == req_date.date() if hasattr(req_date, "date") else var["date"].date() == req_date
                                and var["period"] == required.period)
                        ]
                    
                    if self.enabled:
                        # Force assignment to required period
                        for var_dict in matching_vars:
                            print(f"Forcing assignment for {class_obj.name} on {var_dict['date']} period {var_dict['period']}")
                            context.model.Add(var_dict["variable"] == 1)
                    else:
                        # Force non-assignment to required period
                        for var_dict in matching_vars:
                            print(f"Preventing assignment for {class_obj.name} on {var_dict['date']} period {var_dict['period']}")
                            context.model.Add(var_dict["variable"] == 0)

    def validate(self, assignments: List[Dict[str, Any]], context: SchedulerContext) -> List[ConstraintViolation]:
        """Validate that all required periods are satisfied"""
        violations = []
        print(f"Validating {self.name} constraint")

        for class_obj in context.request.classes:
            if not hasattr(class_obj, "weeklySchedule") or not class_obj.weeklySchedule.requiredPeriods:
                continue
                
            print(f"Checking {len(class_obj.weeklySchedule.requiredPeriods)} required periods for {class_obj.name}")

            # Get assignments for this class
            class_assignments = []
            for a in assignments:
                if isinstance(a, dict) and a.get("name") == class_obj.name:
                    class_assignments.append(a)
                elif hasattr(a, "classId") and a.classId == class_obj.name:
                    class_assignments.append(a)
            
            print(f"Found {len(class_assignments)} assignments")

            # Check each required period
            for required in class_obj.weeklySchedule.requiredPeriods:
                matching = []
                
                # Handle RequiredPeriod objects with date attribute
                if hasattr(required, "date"):
                    required_date = datetime.fromisoformat(required.date) if isinstance(required.date, str) else required.date
                    required_period = required.period
                    
                    for a in class_assignments:
                        if isinstance(a, dict):
                            # Handle dict format
                            date_str = a["date"]
                            if isinstance(date_str, datetime):
                                assignment_date = date_str
                            else:
                                assignment_date = datetime.fromisoformat(date_str)
                            
                            period = a["timeSlot"].period if hasattr(a["timeSlot"], "period") else a["timeSlot"]["period"]
                        else:
                            # Handle object format
                            assignment_date = datetime.fromisoformat(a.date)
                            period = a.timeSlot.period
                        
                        if (assignment_date.date() == required_date.date() if hasattr(required_date, "date") else 
                            assignment_date.date() == required_date) and period == required_period:
                            matching.append(a)
                
                # Handle TimeSlot objects with dayOfWeek attribute
                elif hasattr(required, "dayOfWeek"):
                    required_day = required.dayOfWeek
                    required_period = required.period
                    
                    for a in class_assignments:
                        if isinstance(a, dict):
                            # Handle dict format
                            date_str = a["date"]
                            if isinstance(date_str, datetime):
                                weekday = date_str.weekday() + 1
                            else:
                                weekday = datetime.fromisoformat(date_str).weekday() + 1
                            
                            period = a["timeSlot"].period if hasattr(a["timeSlot"], "period") else a["timeSlot"]["period"]
                        else:
                            # Handle object format
                            weekday = datetime.fromisoformat(a.date).weekday() + 1
                            period = a.timeSlot.period
                        
                        if weekday == required_day and period == required_period:
                            matching.append(a)

                if not matching:
                    if hasattr(required, "dayOfWeek"):
                        msg = (f"Class {class_obj.name} is missing required assignment "
                              f"on day {required.dayOfWeek} period {required.period}")
                    else:  # RequiredPeriod with date
                        msg = (f"Class {class_obj.name} is missing required assignment "
                              f"on date {required.date} period {required.period}")
                    print(f"Violation: {msg}")
                    context_dict = {
                        "name": class_obj.name,
                        "period": required.period
                    }
                    
                    # Add the appropriate date/day information based on the required period type
                    if hasattr(required, "dayOfWeek"):
                        context_dict["dayOfWeek"] = required.dayOfWeek
                    else:  # RequiredPeriod with date
                        context_dict["date"] = required.date
                    
                    violations.append(ConstraintViolation(
                        message=msg,
                        severity="error",
                        context=context_dict
                    ))

        print(f"Found {len(violations)} violations")
        return violations

class ConflictPeriodsConstraint(BaseConstraint):
    """Prevent assignments to conflicting periods"""

    def __init__(self, enabled: bool = True):
        super().__init__("conflict_periods", enabled=enabled)

    def apply(self, context: SchedulerContext) -> None:
        """Add constraints to prevent assignment to conflicting periods"""
        if not self.enabled:
            return
            
        print(f"Applying {self.name} constraint")

        for class_obj in context.request.classes:
            if not hasattr(class_obj, "weeklySchedule") or not class_obj.weeklySchedule.conflicts:
                continue

            # Get all variables for this class
            class_vars = [
                var for var in context.variables 
                if var["name"] == class_obj.name
            ]

            print(f"Found {len(class_obj.weeklySchedule.conflicts)} conflicts for {class_obj.name}")
            # Prevent assignment to any conflicting periods
            for var in class_vars:
                weekday = var["date"].weekday() + 1  # Convert to 1-5 for Monday-Friday
                for conflict in class_obj.weeklySchedule.conflicts:
                    if conflict.dayOfWeek == weekday and conflict.period == var["period"]:
                        if self.enabled:
                            print(f"Preventing {class_obj.name} on day {weekday} period {var['period']}")
                            context.model.Add(var["variable"] == 0)
                        else:
                            print(f"Forcing conflict for {class_obj.name} on day {weekday} period {var['period']}")
                            context.model.Add(var["variable"] == 1)

    def validate(self, assignments: List[Dict[str, Any]], context: SchedulerContext) -> List[ConstraintViolation]:
        """Validate that no assignments violate conflicts"""
        violations = []
        print(f"Validating {self.name} constraint")

        for class_obj in context.request.classes:
            if not hasattr(class_obj, "weeklySchedule") or not class_obj.weeklySchedule.conflicts:
                continue

            print(f"Checking {len(class_obj.weeklySchedule.conflicts)} conflicts for {class_obj.name}")

            # Check each assignment against conflicts
            for assignment in assignments:
                # Handle different assignment formats (dict or object)
                class_name = assignment.get("name") if isinstance(assignment, dict) else assignment.classId
                
                if class_name == class_obj.name:
                    # Extract date and period based on assignment format
                    if isinstance(assignment, dict):
                        if isinstance(assignment["date"], datetime):
                            weekday = assignment["date"].weekday() + 1
                        else:
                            weekday = datetime.fromisoformat(assignment["date"]).weekday() + 1
                        period = assignment["timeSlot"]["period"] if isinstance(assignment["timeSlot"], dict) else assignment["timeSlot"].period
                    else:
                        weekday = datetime.fromisoformat(assignment.date).weekday() + 1
                        period = assignment.timeSlot.period
                    
                    # Check if this period is in conflicts
                    for conflict in class_obj.weeklySchedule.conflicts:
                        if conflict.dayOfWeek == weekday and conflict.period == period:
                            msg = (
                                f"Class {class_obj.name} is assigned to conflicting period "
                                f"on day {weekday} period {period}"
                            )
                            print(f"Violation: {msg}")
                            violations.append(ConstraintViolation(
                                message=msg,
                                severity="error",
                                context={
                                    "name": class_obj.name,
                                    "day": weekday,
                                    "period": period
                                }
                            ))

        print(f"Found {len(violations)} violations")
        return violations
