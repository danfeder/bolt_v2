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
            avail_date = avail.date
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
        
        # If there's no instructor availability, return immediately
        if not context.request.instructorAvailability:
            return violations
            
        # Build lookup of unavailable periods
        unavailable_slots: Dict[str, Set[int]] = defaultdict(set)
        for avail in context.request.instructorAvailability:
            avail_date = avail.date
            if avail_date.tzinfo is None:
                try:
                    from datetime import timezone
                    avail_date = avail_date.replace(tzinfo=timezone.utc)
                except (ImportError, AttributeError):
                    # Fallback if timezone import fails
                    pass
            date_str = avail_date.date().isoformat()
            unavailable_slots[date_str].update(avail.periods)
        
        # Check each assignment
        for assignment in assignments:
            try:
                # Parse data from assignment based on its type
                if isinstance(assignment, dict):
                    # Dictionary format
                    class_name = assignment["name"]
                    date_val = assignment["date"]
                    # Handle date in various formats
                    if hasattr(date_val, "date"):
                        date_str = date_val.date().isoformat()
                    else:
                        # Parse ISO format string
                        from datetime import datetime
                        date_str = datetime.fromisoformat(date_val.replace('Z', '+00:00')).date().isoformat()
                    
                    # Get period (handling both dict and object)
                    if isinstance(assignment["timeSlot"], dict):
                        period = assignment["timeSlot"]["period"]
                    else:
                        period = assignment["timeSlot"].period
                else:
                    # Object format (ScheduleAssignment)
                    class_name = assignment.name if hasattr(assignment, "name") else assignment.classId
                    from datetime import datetime
                    date_str = datetime.fromisoformat(assignment.date.replace('Z', '+00:00')).date().isoformat()
                    period = assignment.timeSlot.period
                
                # Check if this assignment violates instructor availability
                if date_str in unavailable_slots and period in unavailable_slots[date_str]:
                    violations.append(ConstraintViolation(
                        message=(
                            f"Class {class_name} scheduled during "
                            f"unavailable period {period} on {date_str}"
                        ),
                        severity="error",
                        context={
                            "name": class_name,
                            "date": date_str,
                            "period": period
                        }
                    ))
            except Exception as e:
                print(f"Error validating instructor availability: {str(e)}")
                continue
                
        return violations

class ConsecutivePeriodConstraint(BaseConstraint):
    """Prevents an instructor from being scheduled for consecutive periods in a day."""
    
    def __init__(self):
        super().__init__("consecutive_period")
        
    def apply(self, context: SchedulerContext) -> None:
        from collections import defaultdict
        instructor_daily = defaultdict(list)
        # Group variables by instructor and day, with their period and variable indicator.
        for var in context.variables:
            instructor = var.get("instructor")
            if instructor:
                day = var["date"].date()
                instructor_daily[(instructor, day)].append((var["period"], var["variable"]))
        # For each group, sort by period and add consecutive constraints.
        for key, period_vars in instructor_daily.items():
            period_vars.sort(key=lambda x: x[0])
            for i in range(len(period_vars) - 1):
                context.model.Add(period_vars[i][1] + period_vars[i+1][1] <= 1)
        print("Added consecutive period constraints for instructors")
        
    def validate(self, assignments: List[Dict[str, Any]], context: SchedulerContext) -> List[ConstraintViolation]:
        violations = []
        instructor_daily = defaultdict(list)
        
        # Group assignments by instructor and day
        for assignment in assignments:
            instructor = assignment.get("instructor")
            if instructor:
                day = assignment["date"].date()
                instructor_daily[(instructor, day)].append(assignment["timeSlot"]["period"])
        
        # Check for consecutive periods
        for (instructor, day), periods in instructor_daily.items():
            periods.sort()
            for i in range(len(periods) - 1):
                if periods[i] + 1 == periods[i + 1]:
                    violations.append(ConstraintViolation(
                        message=(
                            f"Instructor {instructor} has consecutive classes in "
                            f"periods {periods[i]} and {periods[i + 1]} on {day}"
                        ),
                        severity="error",
                        context={
                            "instructor": instructor,
                            "date": str(day),
                            "period1": periods[i],
                            "period2": periods[i + 1]
                        }
                    ))
        return violations

class InstructorLoadConstraint(BaseConstraint):
    """Ensures an instructor does not exceed maximum classes per day and per week."""
    
    def __init__(self, max_classes_per_day: int = 3, max_classes_per_week: int = 12):
        super().__init__("instructor_load")
        self.max_classes_per_day = max_classes_per_day
        self.max_classes_per_week = max_classes_per_week

    def apply(self, context: SchedulerContext) -> None:
        from collections import defaultdict
        instructor_daily = defaultdict(list)
        instructor_weekly = defaultdict(list)
        # Group variables by instructor and day, and instructor and week (using ISO week number)
        for var in context.variables:
            instructor = var.get("instructor")
            if instructor:
                day = var["date"].date()
                instructor_daily[(instructor, day)].append(var["variable"])
                week = var["date"].isocalendar()[1]
                instructor_weekly[(instructor, week)].append(var["variable"])
        # Add constraints for daily limits
        for (instructor, day), variables in instructor_daily.items():
            context.model.Add(sum(variables) <= self.max_classes_per_day)
        # Add constraints for weekly limits
        for (instructor, week), variables in instructor_weekly.items():
            context.model.Add(sum(variables) <= self.max_classes_per_week)
        print("Added instructor load constraints")
    
    def validate(self, assignments: List[Dict[str, Any]], context: SchedulerContext) -> List[ConstraintViolation]:
        violations = []
        # Group assignments by instructor and day/week to check limits
        instructor_daily = defaultdict(int)
        instructor_weekly = defaultdict(int)
        
        for assignment in assignments:
            date = assignment["date"]
            instructor = assignment.get("instructor")
            if instructor:
                instructor_daily[(instructor, date.date())] += 1
                week = date.isocalendar()[1]
                instructor_weekly[(instructor, week)] += 1
        
        # Check daily limits
        for (instructor, day), count in instructor_daily.items():
            if count > self.max_classes_per_day:
                violations.append(ConstraintViolation(
                    message=(
                        f"Instructor {instructor} has {count} classes on {day}, "
                        f"exceeding limit of {self.max_classes_per_day}"
                    ),
                    severity="error",
                    context={
                        "instructor": instructor,
                        "date": str(day),
                        "count": count,
                        "limit": self.max_classes_per_day
                    }
                ))
        
        # Check weekly limits
        for (instructor, week), count in instructor_weekly.items():
            if count > self.max_classes_per_week:
                violations.append(ConstraintViolation(
                    message=(
                        f"Instructor {instructor} has {count} classes in week {week}, "
                        f"exceeding limit of {self.max_classes_per_week}"
                    ),
                    severity="error",
                    context={
                        "instructor": instructor,
                        "week": week,
                        "count": count,
                        "limit": self.max_classes_per_week
                    }
                ))
        
        return violations
