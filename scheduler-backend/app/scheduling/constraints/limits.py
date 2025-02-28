"""Limit-related scheduling constraints"""
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Any

from ortools.sat.python import cp_model

from .base import BaseConstraint, ConstraintViolation
from ..core import SchedulerContext

class DailyLimitConstraint(BaseConstraint):
    """Ensures the number of classes per day doesn't exceed the maximum"""
    
    def __init__(self, enabled: bool = True):
        super().__init__("daily_limit", enabled=enabled)
    
    def apply(self, context: SchedulerContext) -> None:
        if not self.enabled:
            return
            
        # Group variables by date
        by_date = defaultdict(list)
        for var in context.variables:
            # var["date"] is already a datetime object from base solver
            date = var["date"].date()
            by_date[date].append(var["variable"])
        
        # Add constraint for each date
        limit_count = 0
        for date, vars_list in by_date.items():
            context.model.Add(
                sum(vars_list) <= context.request.constraints.maxClassesPerDay
            )
            limit_count += 1
            
        print(f"Added daily limit constraints for {limit_count} days")
    
    def validate(
        self,
        assignments: List[Dict[str, Any]],
        context: SchedulerContext
    ) -> List[ConstraintViolation]:
        violations = []
        max_per_day = context.request.constraints.maxClassesPerDay
        
        # Count assignments per day
        by_date = defaultdict(int)
        for assignment in assignments:
            date = assignment["date"].date()
            by_date[date] += 1
        
        # Check for violations
        for date, count in by_date.items():
            if count > max_per_day:
                violations.append(ConstraintViolation(
                    message=(
                        f"Too many classes scheduled on {date}: "
                        f"got {count}, maximum is {max_per_day}"
                    ),
                    severity="error",
                    context={
                        "date": str(date),
                        "count": count,
                        "maximum": max_per_day
                    }
                ))
        
        return violations

class WeeklyLimitConstraint(BaseConstraint):
    """Ensures the number of classes per week doesn't exceed the maximum"""
    
    def __init__(self, enabled: bool = True):
        super().__init__("weekly_limit", enabled=enabled)
    
    def apply(self, context: SchedulerContext) -> None:
        if not self.enabled:
            return
            
        # Group variables by week
        by_week = defaultdict(list)
        for var in context.variables:
            # Both var["date"] and context.start_date are datetime objects
            week_num = (var["date"] - context.start_date).days // 7
            by_week[week_num].append(var["variable"])
            
        # Add constraint for each week
        limit_count = 0
        for week_num, vars_list in by_week.items():
            context.model.Add(
                sum(vars_list) <= context.request.constraints.maxClassesPerWeek
            )
            limit_count += 1
            
        print(f"Added weekly limit constraints for {limit_count} weeks")
    
    def validate(
        self,
        assignments: List[Dict[str, Any]],
        context: SchedulerContext
    ) -> List[ConstraintViolation]:
        violations = []
        max_per_week = context.request.constraints.maxClassesPerWeek
        
        # Count assignments per week
        by_week = defaultdict(int)
        for assignment in assignments:
            date = assignment["date"]
            week_num = (date - context.start_date).days // 7
            by_week[week_num] += 1
        
        # Check for violations
        for week_num, count in by_week.items():
            if count > max_per_week:
                violations.append(ConstraintViolation(
                    message=(
                        f"Too many classes scheduled in week {week_num + 1}: "
                        f"got {count}, maximum is {max_per_week}"
                    ),
                    severity="error",
                    context={
                        "weekNumber": week_num + 1,
                        "count": count,
                        "maximum": max_per_week
                    }
                ))
        
        return violations

class MinimumPeriodsConstraint(BaseConstraint):
    """Ensures the minimum number of classes per week is met"""
    
    def __init__(self, enabled: bool = True):
        super().__init__("minimum_periods", enabled=enabled)
        
    def apply(self, context: SchedulerContext) -> None:
        if not self.enabled:
            return
            
        # Group variables by week and count weekdays per week
        by_week = defaultdict(list)
        by_day = defaultdict(lambda: defaultdict(list))  # week -> day -> vars
        weekdays_by_week = defaultdict(int)
        seen_dates = set()  # Track unique dates to avoid double-counting
        
        for var in context.variables:
            week_num = (var["date"] - context.start_date).days // 7
            date = var["date"].date()
            
            # Count weekdays (only once per date)
            if date not in seen_dates and var["date"].weekday() < 5:
                weekdays_by_week[week_num] += 1
                seen_dates.add(date)
            
            by_week[week_num].append(var["variable"])
            by_day[week_num][date].append(var)
            
        # Add constraint for each week
        limit_count = 0
        for week_num, vars_list in by_week.items():
            weekdays = weekdays_by_week[week_num]
            # Use ceiling division and enforce a minimum threshold
            base_min = context.request.constraints.minPeriodsPerWeek
            prorated = (base_min * weekdays + 4) // 5  # Add 4 to round up
            # If base minimum is 5 or more, ensure at least 2 periods even with one day
            min_threshold = 2 if base_min >= 5 else 1
            min_periods = max(min_threshold, prorated)
            print(f"Adding pro-rated minimum periods constraint for week {week_num}:")
            print(f"- {len(vars_list)} variables")
            print(f"- {weekdays} weekdays")
            print(f"- Minimum periods: {min_periods}")
            if self.enabled:
                context.model.Add(sum(vars_list) >= min_periods)
            limit_count += 1
            
        print(f"Added minimum periods constraints for {limit_count} weeks")
    
    def validate(
        self,
        assignments: List[Dict[str, Any]],
        context: SchedulerContext
    ) -> List[ConstraintViolation]:
        violations = []
        min_periods = context.request.constraints.minPeriodsPerWeek
        
        # Count assignments per week and available weekdays
        by_week = defaultdict(int)
        weekdays_by_week = defaultdict(set)  # Use set to count unique weekdays
        
        for assignment in assignments:
            try:
                # Parse date from assignment based on its type
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
                else:
                    # Object format (ScheduleAssignment)
                    from datetime import datetime
                    date = datetime.fromisoformat(assignment.date.replace('Z', '+00:00'))
                
                # Calculate week number
                start_date = context.start_date
                week_num = (date.date() - start_date.date()).days // 7
                by_week[week_num] += 1
                
                # Only track weekdays (Mon-Fri)
                if date.weekday() < 5:
                    weekdays_by_week[week_num].add(date.date())
            except Exception as e:
                print(f"Error processing date in minimum periods constraint: {str(e)}")
                continue

        print("Validating minimum periods across weeks:")                
        # Check for violations in each week
        for week_num, count in by_week.items():
            weekdays = len(weekdays_by_week[week_num])
            base_min = min_periods
            prorated = (base_min * weekdays + 4) // 5 if weekdays > 0 else base_min  # Add 4 to round up
            min_threshold = 2 if base_min >= 5 else 1
            prorated_min = max(min_threshold, prorated)
            
            print(f"Week {week_num + 1}:")
            print(f"- Required minimum: {prorated_min}")
            print(f"- Actual count: {count}")
            print(f"- Weekdays available: {weekdays}")
            
            if count < prorated_min:
                violations.append(ConstraintViolation(
                    message=(
                        f"Too few classes scheduled in week {week_num + 1}: "
                        f"got {count}, minimum is {prorated_min} "
                        f"({weekdays} available days)"
                    ),
                    severity="error",
                    context={
                        "weekNumber": week_num + 1,
                        "count": count,
                        "minimum": prorated_min,
                        "availableDays": weekdays
                    }
                ))
        
        return violations
