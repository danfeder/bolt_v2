"""Relaxable limit constraints that can be adjusted at runtime."""
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple
import logging

from ortools.sat.python import cp_model

from ..core import SchedulerContext
from .base import ConstraintViolation
from .relaxation import RelaxableConstraint, RelaxationLevel

logger = logging.getLogger(__name__)

class RelaxableDailyLimitConstraint(RelaxableConstraint):
    """
    Relaxable version of the daily limit constraint.
    
    This constraint can be progressively relaxed to allow more classes per day.
    """
    
    def __init__(
        self, 
        enabled: bool = True,
        relaxation_priority: int = 2,
        never_relax: bool = False
    ):
        """Initialize a relaxable daily limit constraint."""
        super().__init__(
            name="relaxable_daily_limit",
            enabled=enabled,
            priority=1,
            weight=None,  # Hard constraint
            can_relax=True,
            relaxation_priority=relaxation_priority,
            never_relax=never_relax
        )
        # Extra classes allowed by relaxation level
        self.extra_classes_by_level = {
            RelaxationLevel.NONE: 0,
            RelaxationLevel.MINIMAL: 1,
            RelaxationLevel.MODERATE: 2,
            RelaxationLevel.SIGNIFICANT: 3,
            RelaxationLevel.MAXIMUM: 4
        }
        # Default relaxation parameters
        self.relaxation_params = {"extra_classes_allowed": 0}
        
    def apply(self, context: SchedulerContext) -> None:
        """Apply the constraint to the model, respecting current relaxation level."""
        if not self.enabled:
            return
        
        # Determine max classes per day with relaxation
        original_max = context.request.constraints.maxClassesPerDay
        extra_classes = self.relaxation_params.get("extra_classes_allowed", 0)
        effective_max = original_max + extra_classes
        
        # Group variables by date
        by_date = defaultdict(list)
        for var in context.variables:
            date = var["date"].date()
            by_date[date].append(var["variable"])
        
        # Add constraint for each date
        limit_count = 0
        for date, vars_list in by_date.items():
            context.model.Add(sum(vars_list) <= effective_max)
            limit_count += 1
            
        logger.info(
            f"Added relaxable daily limit constraints for {limit_count} days "
            f"(max: {original_max} + {extra_classes} = {effective_max})"
        )
        
    def _apply_relaxation(
        self, 
        level: RelaxationLevel, 
        context: Optional[SchedulerContext]
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Apply relaxation to this constraint."""
        # Get extra classes allowed at this level
        extra_classes = self.extra_classes_by_level.get(level, 0)
        
        # Check if this would be a meaningful change
        current_extra = self.relaxation_params.get("extra_classes_allowed", 0)
        if extra_classes <= current_extra:
            return (
                False,
                f"No additional relaxation applied, already allowing {current_extra} extra classes",
                {}
            )
            
        # Apply relaxation
        return (
            True,
            f"Increased daily class limit by {extra_classes} classes",
            {"extra_classes_allowed": extra_classes}
        )
        
    def validate(
        self,
        assignments: List[Dict[str, Any]],
        context: SchedulerContext
    ) -> List[ConstraintViolation]:
        """Validate the constraint, respecting current relaxation level."""
        violations = []
        
        # Determine effective maximum
        original_max = context.request.constraints.maxClassesPerDay
        extra_classes = self.relaxation_params.get("extra_classes_allowed", 0)
        effective_max = original_max + extra_classes
        
        # Count assignments per day
        by_date = defaultdict(int)
        for assignment in assignments:
            date = assignment["date"].date() if hasattr(assignment["date"], "date") else assignment["date"]
            by_date[date] += 1
        
        # Check for violations
        for date, count in by_date.items():
            if count > effective_max:
                violations.append(ConstraintViolation(
                    message=(
                        f"Too many classes scheduled on {date}: "
                        f"got {count}, relaxed maximum is {effective_max} "
                        f"(original: {original_max}, extra: {extra_classes})"
                    ),
                    severity="error",
                    context={
                        "date": str(date),
                        "count": count,
                        "original_maximum": original_max,
                        "extra_allowed": extra_classes,
                        "effective_maximum": effective_max,
                        "relaxation_level": self.current_relaxation_level.name
                    }
                ))
        
        return violations


class RelaxableWeeklyLimitConstraint(RelaxableConstraint):
    """
    Relaxable version of the weekly limit constraint.
    
    This constraint can be progressively relaxed to allow more classes per week.
    """
    
    def __init__(
        self, 
        enabled: bool = True,
        relaxation_priority: int = 3,
        never_relax: bool = False
    ):
        """Initialize a relaxable weekly limit constraint."""
        super().__init__(
            name="relaxable_weekly_limit",
            enabled=enabled,
            priority=1,
            weight=None,  # Hard constraint
            can_relax=True,
            relaxation_priority=relaxation_priority,
            never_relax=never_relax
        )
        # Extra classes allowed by relaxation level
        self.extra_classes_by_level = {
            RelaxationLevel.NONE: 0,
            RelaxationLevel.MINIMAL: 2,
            RelaxationLevel.MODERATE: 4,
            RelaxationLevel.SIGNIFICANT: 6,
            RelaxationLevel.MAXIMUM: 8
        }
        # Default relaxation parameters
        self.relaxation_params = {"extra_classes_allowed": 0}
        
    def apply(self, context: SchedulerContext) -> None:
        """Apply the constraint to the model, respecting current relaxation level."""
        if not self.enabled:
            return
        
        # Determine max classes per week with relaxation
        original_max = context.request.constraints.maxClassesPerWeek
        extra_classes = self.relaxation_params.get("extra_classes_allowed", 0)
        effective_max = original_max + extra_classes
        
        # Group variables by week
        by_week = defaultdict(list)
        for var in context.variables:
            week_num = (var["date"] - context.start_date).days // 7
            by_week[week_num].append(var["variable"])
        
        # Add constraint for each week
        limit_count = 0
        for week_num, vars_list in by_week.items():
            context.model.Add(sum(vars_list) <= effective_max)
            limit_count += 1
            
        logger.info(
            f"Added relaxable weekly limit constraints for {limit_count} weeks "
            f"(max: {original_max} + {extra_classes} = {effective_max})"
        )
        
    def _apply_relaxation(
        self, 
        level: RelaxationLevel, 
        context: Optional[SchedulerContext]
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Apply relaxation to this constraint."""
        # Get extra classes allowed at this level
        extra_classes = self.extra_classes_by_level.get(level, 0)
        
        # Check if this would be a meaningful change
        current_extra = self.relaxation_params.get("extra_classes_allowed", 0)
        if extra_classes <= current_extra:
            return (
                False,
                f"No additional relaxation applied, already allowing {current_extra} extra classes",
                {}
            )
            
        # Apply relaxation
        return (
            True,
            f"Increased weekly class limit by {extra_classes} classes",
            {"extra_classes_allowed": extra_classes}
        )
        
    def validate(
        self,
        assignments: List[Dict[str, Any]],
        context: SchedulerContext
    ) -> List[ConstraintViolation]:
        """Validate the constraint, respecting current relaxation level."""
        violations = []
        
        # Determine effective maximum
        original_max = context.request.constraints.maxClassesPerWeek
        extra_classes = self.relaxation_params.get("extra_classes_allowed", 0)
        effective_max = original_max + extra_classes
        
        # Count assignments per week
        by_week = defaultdict(int)
        for assignment in assignments:
            date = assignment["date"]
            week_num = (date - context.start_date).days // 7
            by_week[week_num] += 1
        
        # Check for violations
        for week_num, count in by_week.items():
            if count > effective_max:
                violations.append(ConstraintViolation(
                    message=(
                        f"Too many classes scheduled in week {week_num + 1}: "
                        f"got {count}, relaxed maximum is {effective_max} "
                        f"(original: {original_max}, extra: {extra_classes})"
                    ),
                    severity="error",
                    context={
                        "weekNumber": week_num + 1,
                        "count": count,
                        "original_maximum": original_max,
                        "extra_allowed": extra_classes,
                        "effective_maximum": effective_max,
                        "relaxation_level": self.current_relaxation_level.name
                    }
                ))
        
        return violations