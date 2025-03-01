"""Teacher workload scheduling constraints"""
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

from ortools.sat.python import cp_model

from .base import BaseConstraint, ConstraintViolation
from ..core import SchedulerContext


class ConsecutiveClassesConstraint(BaseConstraint):
    """
    Controls scheduling of consecutive classes for teacher workload management.
    
    This constraint:
    1. When enabled (allow_consecutive=True), permits scheduling exactly 2 classes back-to-back
    2. When disabled (allow_consecutive=False), prevents any consecutive classes
    3. Regardless of setting, always prevents 3 or more consecutive classes
    """
    
    def __init__(self, enabled: bool = True, allow_consecutive: bool = True):
        """
        Initialize the constraint.
        
        Args:
            enabled: Whether this constraint is enabled at all
            allow_consecutive: If True, allows exactly 2 consecutive classes; if False, disallows any consecutive classes
        """
        super().__init__("consecutive_classes", enabled=enabled)
        self.allow_consecutive = allow_consecutive
    
    def apply(self, context: SchedulerContext) -> None:
        """
        Apply the consecutive classes constraint to the model.
        
        Args:
            context: The scheduler context containing model and variables
        """
        if not self.enabled:
            return
        
        # Check if the request has the allowConsecutiveClasses field
        allow_consecutive = self.allow_consecutive
        if hasattr(context.request.constraints, 'allowConsecutiveClasses'):
            allow_consecutive = context.request.constraints.allowConsecutiveClasses
            
        # Group variables by date and sort by period
        by_date_period = {}
        for var in context.variables:
            date = var["date"].date()
            period = var["period"]
            
            if date not in by_date_period:
                by_date_period[date] = {}
                
            by_date_period[date][period] = var["variable"]
        
        # Add constraints for consecutive periods
        constraint_count = 0
        
        for date, period_vars in by_date_period.items():
            periods = sorted(period_vars.keys())
            
            # Handle consecutive periods
            for i in range(len(periods) - 2):  # Check sequences of 3 periods
                p1, p2, p3 = periods[i], periods[i + 1], periods[i + 2]
                
                # Ensure three consecutive periods don't all have classes
                # We need at least one period to be free
                context.model.Add(
                    period_vars[p1] + period_vars[p2] + period_vars[p3] <= 2
                )
                constraint_count += 1
                
            # If not allowing any consecutive classes, add additional constraints
            if not allow_consecutive:
                for i in range(len(periods) - 1):  # Check pairs of consecutive periods
                    p1, p2 = periods[i], periods[i + 1]
                    
                    # Ensure consecutive periods don't both have classes
                    context.model.Add(
                        period_vars[p1] + period_vars[p2] <= 1
                    )
                    constraint_count += 1
        
        mode = "allowing pairs" if allow_consecutive else "no consecutive classes"
        print(f"Added {constraint_count} consecutive classes constraints ({mode})")
    
    def validate(
        self,
        assignments: List[Dict[str, Any]],
        context: SchedulerContext
    ) -> List[ConstraintViolation]:
        """
        Validate a solution against this constraint.
        
        Args:
            assignments: The assignments to validate
            context: The scheduler context
            
        Returns:
            List of constraint violations
        """
        if not self.enabled:
            return []
            
        # Check if the request has the allowConsecutiveClasses field
        allow_consecutive = self.allow_consecutive
        if hasattr(context.request.constraints, 'allowConsecutiveClasses'):
            allow_consecutive = context.request.constraints.allowConsecutiveClasses
        
        violations = []
        
        # Organize assignments by date and period
        by_date = {}
        for assignment in assignments:
            try:
                # Parse data from assignment based on its type
                if isinstance(assignment, dict):
                    # Dictionary format
                    date_val = assignment["date"]
                    # Handle date in various formats
                    if hasattr(date_val, "date") and callable(getattr(date_val, "date")):
                        date = date_val
                    else:
                        # Parse from ISO format string
                        from datetime import datetime
                        date = datetime.fromisoformat(date_val.replace('Z', '+00:00'))
                    
                    # Get period (handle different timeSlot formats)
                    if isinstance(assignment["timeSlot"], dict):
                        period = assignment["timeSlot"]["period"]
                    else:
                        period = assignment["timeSlot"].period
                else:
                    # Object format (ScheduleAssignment)
                    from datetime import datetime
                    date = datetime.fromisoformat(assignment.date.replace('Z', '+00:00'))
                    period = assignment.timeSlot.period
                
                # Convert date to date object for consistency
                if hasattr(date, "date") and callable(getattr(date, "date")):
                    date = date.date()
                
                # Initialize date dictionary if needed
                if date not in by_date:
                    by_date[date] = {}
                    
                by_date[date][period] = assignment
            except Exception as e:
                print(f"Error processing assignment in consecutive classes constraint: {str(e)}")
                continue
        
        # Check for violations
        for date, periods in by_date.items():
            period_nums = sorted(periods.keys())
            
            # Check for 3+ consecutive periods
            for i in range(len(period_nums) - 2):
                p1, p2, p3 = period_nums[i], period_nums[i + 1], period_nums[i + 2]
                if p1 + 1 == p2 and p2 + 1 == p3:  # Truly consecutive
                    violations.append(ConstraintViolation(
                        message=f"Three consecutive classes scheduled on {date} (periods {p1}, {p2}, {p3})",
                        severity="high",
                        context={
                            "date": date,
                            "periods": [p1, p2, p3],
                            "assignments": [periods[p1], periods[p2], periods[p3]]
                        }
                    ))
            
            # Check for any consecutive periods if not allowed
            if not allow_consecutive:
                for i in range(len(period_nums) - 1):
                    p1, p2 = period_nums[i], period_nums[i + 1]
                    if p1 + 1 == p2:  # Truly consecutive
                        violations.append(ConstraintViolation(
                            message=f"Consecutive classes scheduled on {date} (periods {p1}, {p2}) when not allowed",
                            severity="medium",
                            context={
                                "date": date,
                                "periods": [p1, p2],
                                "assignments": [periods[p1], periods[p2]]
                            }
                        ))
        
        return violations


class TeacherBreakConstraint(BaseConstraint):
    """
    Ensures the teacher gets adequate breaks during the day.
    
    This is a companion to the ConsecutiveClassesConstraint that can enforce
    additional break requirements such as ensuring lunch periods or specific
    break patterns.
    """
    
    def __init__(self, enabled: bool = True, required_breaks: List[int] = None):
        """
        Initialize the constraint.
        
        Args:
            enabled: Whether this constraint is enabled
            required_breaks: List of periods that should be breaks (e.g., [4] for lunch period)
        """
        super().__init__("teacher_breaks", enabled=enabled)
        self.required_breaks = required_breaks or []
    
    def apply(self, context: SchedulerContext) -> None:
        """
        Apply the teacher break constraint to the model.
        
        Args:
            context: The scheduler context containing model and variables
        """
        if not self.enabled:
            return
        
        # Get required break periods from request if available
        required_breaks = self.required_breaks
        if hasattr(context.request.constraints, 'requiredBreakPeriods'):
            required_breaks = context.request.constraints.requiredBreakPeriods
            
        if not required_breaks:
            return
            
        # Group variables by date and required break periods
        by_date = defaultdict(list)
        for var in context.variables:
            date = var["date"].date()
            period = var["period"]
            
            if period in required_breaks:
                by_date[date].append(var["variable"])
        
        # Add constraint to ensure required break periods are free
        constraint_count = 0
        for date, vars_list in by_date.items():
            for break_var in vars_list:
                context.model.Add(break_var == 0)  # Period must be free
                constraint_count += 1
        
        print(f"Added {constraint_count} teacher break constraints for required periods {required_breaks}")
    
    def validate(
        self,
        assignments: List[Dict[str, Any]],
        context: SchedulerContext
    ) -> List[ConstraintViolation]:
        """
        Validate a solution against this constraint.
        
        Args:
            assignments: The assignments to validate
            context: The scheduler context
            
        Returns:
            List of constraint violations
        """
        if not self.enabled:
            return []
        
        # Get required break periods from request if available
        required_breaks = self.required_breaks
        if hasattr(context.request.constraints, 'requiredBreakPeriods'):
            required_breaks = context.request.constraints.requiredBreakPeriods
            
        if not required_breaks:
            return []
            
        violations = []
        
        # Check for classes scheduled during required break periods
        by_date_period = {}
        for assignment in assignments:
            try:
                # Parse data from assignment based on its type
                if isinstance(assignment, dict):
                    # Dictionary format
                    date_val = assignment["date"]
                    # Handle date in various formats
                    if hasattr(date_val, "date") and callable(getattr(date_val, "date")):
                        date = date_val
                    else:
                        # Parse from ISO format string
                        from datetime import datetime
                        date = datetime.fromisoformat(date_val.replace('Z', '+00:00'))
                    
                    # Get period (handle different timeSlot formats)
                    if isinstance(assignment["timeSlot"], dict):
                        period = assignment["timeSlot"]["period"]
                    else:
                        period = assignment["timeSlot"].period
                else:
                    # Object format (ScheduleAssignment)
                    from datetime import datetime
                    date = datetime.fromisoformat(assignment.date.replace('Z', '+00:00'))
                    period = assignment.timeSlot.period
                
                # Convert date to date object for consistency
                if hasattr(date, "date") and callable(getattr(date, "date")):
                    date = date.date()
                
                # Initialize date dictionary if needed
                if date not in by_date_period:
                    by_date_period[date] = {}
                    
                by_date_period[date][period] = assignment
            except Exception as e:
                print(f"Error processing assignment in teacher break constraint: {str(e)}")
                continue
        
        # Check for violations
        for date, periods in by_date_period.items():
            for break_period in required_breaks:
                if break_period in periods:
                    violations.append(ConstraintViolation(
                        message=f"Class scheduled during required break period {break_period} on {date}",
                        severity="high",
                        context={
                            "date": date,
                            "period": break_period,
                            "assignment": periods[break_period]
                        }
                    ))
        
        return violations