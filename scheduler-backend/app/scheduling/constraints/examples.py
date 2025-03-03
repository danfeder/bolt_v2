"""
Example constraints that demonstrate the enhanced validation features

This module contains example constraints that show how to use the enhanced
validation features of the constraint system.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, time

from ..abstractions.base_constraint import BaseConstraint, BaseRelaxableConstraint
from ..abstractions.constraint_manager import ConstraintViolation, ConstraintSeverity
from ..core import SchedulerContext


class DayOfWeekConstraint(BaseConstraint):
    """
    Example constraint that enforces a day of week requirement
    
    This constraint demonstrates how to use the enhanced validation
    features to provide better error messages and context.
    """
    
    def __init__(
        self, 
        name: str = "day_of_week", 
        enabled: bool = True,
        allowed_days: Optional[List[int]] = None  # 0=Monday, 6=Sunday
    ):
        """
        Initialize the constraint
        
        Args:
            name: The constraint name
            enabled: Whether the constraint is enabled
            allowed_days: List of allowed days of week (0=Monday, 6=Sunday)
                If None, all days are allowed
        """
        super().__init__(name, enabled)
        self.allowed_days = allowed_days or [0, 1, 2, 3, 4]  # Weekdays by default
        self.category = "schedule"
        self.description = "Restricts assignments to specific days of the week"
    
    def apply(self, context: SchedulerContext) -> None:
        """
        Apply the constraint to the scheduler context
        
        Args:
            context: The scheduler context
        """
        if not self.enabled:
            return
            
        # Add constraints to the model to prevent assignments on disallowed days
        for var in context.variables:
            date = var["date"]
            day_of_week = date.weekday()  # 0=Monday, 6=Sunday
            
            if day_of_week not in self.allowed_days:
                # Add a constraint to prevent this assignment
                context.model.Add(var["variable"] == 0)
    
    def validate(
        self, 
        assignments: List[Dict[str, Any]], 
        context: SchedulerContext
    ) -> List[ConstraintViolation]:
        """
        Validate the constraint against assignments
        
        Args:
            assignments: The assignments to validate
            context: The scheduler context
            
        Returns:
            List of constraint violations
        """
        if not self.enabled:
            return []
            
        violations = []
        
        for assignment in assignments:
            # Get the date from the assignment
            date = assignment.get("date")
            if not date:
                # If no date is provided, we can't validate
                continue
                
            # Ensure date is a datetime object
            if isinstance(date, str):
                try:
                    date = datetime.fromisoformat(date)
                except ValueError:
                    # If we can't parse the date, skip this assignment
                    continue
            
            # Get the day of week
            day_of_week = date.weekday()  # 0=Monday, 6=Sunday
            
            # Check if this day is allowed
            if day_of_week not in self.allowed_days:
                # Create a context with information about the violation
                context_dict = self.format_violation_context(
                    assignment,
                    {
                        "day_of_week": day_of_week,
                        "allowed_days": self.allowed_days,
                        "date": date.isoformat()
                    }
                )
                
                # Create a critical violation (this is a hard constraint)
                violations.append(
                    self.create_critical_violation(
                        message=f"Assignment on {date.strftime('%A')} is not allowed",
                        context=context_dict
                    )
                )
                
        return violations


class TimeWindowConstraint(BaseRelaxableConstraint):
    """
    Example constraint that enforces a time window requirement
    
    This constraint demonstrates how to use the enhanced relaxable
    constraint features.
    """
    
    def __init__(
        self, 
        name: str = "time_window", 
        enabled: bool = True,
        weight: float = 5000,
        start_time: time = time(8, 0),  # 8:00 AM
        end_time: time = time(17, 0),   # 5:00 PM
        max_relaxation_level: int = 3
    ):
        """
        Initialize the constraint
        
        Args:
            name: The constraint name
            enabled: Whether the constraint is enabled
            weight: The constraint weight (soft constraint)
            start_time: The earliest allowed time
            end_time: The latest allowed time
            max_relaxation_level: The maximum relaxation level
        """
        super().__init__(name, enabled, weight, max_relaxation_level)
        self.start_time = start_time
        self.end_time = end_time
        self.category = "schedule"
        self.description = "Restricts assignments to a specific time window"
    
    def apply(self, context: SchedulerContext) -> None:
        """
        Apply the constraint to the scheduler context
        
        Args:
            context: The scheduler context
        """
        if not self.enabled:
            return
            
        # Get the relaxed weight for this constraint
        relaxed_weight = self.get_relaxed_weight()
        
        # If relaxed completely (weight is None or very low), skip
        if relaxed_weight is None or relaxed_weight < 1:
            return
            
        # Apply as soft constraint with the relaxed weight
        for var in context.variables:
            # Get the time from the variable
            period_time = self._get_period_time(var["period"], context)
            
            if period_time:
                # Check if the time is outside the allowed window
                if period_time < self.start_time or period_time > self.end_time:
                    # If completely relaxed, don't add any penalty
                    if self.relaxation_level >= self.max_relaxation_level:
                        continue
                        
                    # Add a cost for violating the time window
                    # The cost is reduced based on the relaxation level
                    cost = int(relaxed_weight)
                    context.model.Add(var["variable"] == 0).OnlyEnforceIf(var["variable"])
                    context.model.AddWeightedSumInRange([var["variable"]], [cost], 0, 0)
    
    def validate(
        self, 
        assignments: List[Dict[str, Any]], 
        context: SchedulerContext
    ) -> List[ConstraintViolation]:
        """
        Validate the constraint against assignments
        
        Args:
            assignments: The assignments to validate
            context: The scheduler context
            
        Returns:
            List of constraint violations
        """
        if not self.enabled:
            return []
            
        violations = []
        
        for assignment in assignments:
            # Get the period from the assignment
            period = assignment.get("period")
            if period is None:
                # If no period is provided, we can't validate
                continue
                
            # Get the time for this period
            period_time = self._get_period_time(period, context)
            if not period_time:
                # If we can't determine the time, skip this assignment
                continue
            
            # Check if the time is outside the allowed window
            if period_time < self.start_time or period_time > self.end_time:
                # Determine the severity based on the relaxation level
                if self.relaxation_level >= self.max_relaxation_level:
                    severity = ConstraintSeverity.INFO  # Just informational if fully relaxed
                elif self.relaxation_level > 0:
                    severity = ConstraintSeverity.WARNING  # Warning if partially relaxed
                else:
                    severity = ConstraintSeverity.ERROR  # Error if not relaxed
                
                # Format the time for display
                period_time_str = period_time.strftime("%I:%M %p")
                start_time_str = self.start_time.strftime("%I:%M %p")
                end_time_str = self.end_time.strftime("%I:%M %p")
                
                # Create a violation with relaxation information
                violations.append(
                    self.create_relaxable_violation(
                        message=f"Assignment at {period_time_str} is outside allowed window "
                                f"({start_time_str} - {end_time_str})",
                        severity=severity,
                        context=self.format_violation_context(
                            assignment,
                            {
                                "period_time": period_time_str,
                                "allowed_window": {
                                    "start": start_time_str,
                                    "end": end_time_str
                                }
                            }
                        )
                    )
                )
                
        return violations
    
    def _get_period_time(self, period: int, context: SchedulerContext) -> Optional[time]:
        """
        Convert a period number to a time
        
        Args:
            period: The period number
            context: The scheduler context
            
        Returns:
            The time for this period, or None if not available
        """
        # This is a simplified example. In a real implementation,
        # we would look up the period time from the context or configuration.
        # Here we'll just use a simple mapping assuming periods are 1-hour
        # blocks starting at 8:00 AM.
        if not isinstance(period, int) or period < 0 or period > 12:
            return None
            
        # Period 0 = 8:00 AM, Period 1 = 9:00 AM, etc.
        hour = 8 + period
        if hour > 23:
            hour -= 24
            
        return time(hour, 0)
