from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Any

from ortools.sat.python import cp_model

from .base import BaseConstraint, ConstraintViolation
from ..core import SchedulerContext

class DailyLimitConstraint(BaseConstraint):
    """Ensures the number of classes per day doesn't exceed the maximum"""
    
    def __init__(self):
        super().__init__("daily_limit")
    
    def apply(self, context: SchedulerContext) -> None:
        # Group variables by date
        by_date = defaultdict(list)
        for var in context.variables:
            # var["date"] is already a datetime object from base solver
            date = var["date"].date()
            by_date[date].append(var["variable"])
        
        # Add constraint for each date
        limit_count = 0
        for date, vars_list in by_date.items():
            print(f"Adding daily limit constraint for {date}: {len(vars_list)} variables")
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
        
        # Count assignments per day
        by_date = defaultdict(int)
        for assignment in assignments:
            date = assignment["date"].date()
            by_date[date] += 1
        
        # Check for violations
        for date, count in by_date.items():
            if count > context.request.constraints.maxClassesPerDay:
                violations.append(ConstraintViolation(
                    message=(
                        f"Too many classes scheduled on {date}: "
                        f"got {count}, maximum is {context.request.constraints.maxClassesPerDay}"
                    ),
                    severity="error",
                    context={
                        "date": str(date),
                        "count": count,
                        "maximum": context.request.constraints.maxClassesPerDay
                    }
                ))
        
        return violations

class WeeklyLimitConstraint(BaseConstraint):
    """Ensures the number of classes per week doesn't exceed the maximum"""
    
    def __init__(self):
        super().__init__("weekly_limit")
    
    def apply(self, context: SchedulerContext) -> None:
        # Group variables by week
        by_week = defaultdict(list)
        for var in context.variables:
            # Both var["date"] and context.start_date are datetime objects
            week_num = (var["date"] - context.start_date).days // 7
            by_week[week_num].append(var["variable"])
            
        # Add constraint for each week
        limit_count = 0
        for week_num, vars_list in by_week.items():
            print(f"Adding weekly limit constraint for week {week_num}: {len(vars_list)} variables")
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
        
        # Count assignments per week
        by_week = defaultdict(int)
        for assignment in assignments:
            date = assignment["date"]
            week_num = (date - context.start_date).days // 7
            by_week[week_num] += 1
        
        # Check for violations
        for week_num, count in by_week.items():
            if count > context.request.constraints.maxClassesPerWeek:
                violations.append(ConstraintViolation(
                    message=(
                        f"Too many classes scheduled in week {week_num + 1}: "
                        f"got {count}, maximum is {context.request.constraints.maxClassesPerWeek}"
                    ),
                    severity="error",
                    context={
                        "weekNumber": week_num + 1,
                        "count": count,
                        "maximum": context.request.constraints.maxClassesPerWeek
                    }
                ))
        
        return violations

class MinimumPeriodsConstraint(BaseConstraint):
    """Ensures the minimum number of classes per week is met"""
    
    def __init__(self):
        super().__init__("minimum_periods")
    
    def apply(self, context: SchedulerContext) -> None:
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
        sorted_weeks = sorted(by_week.keys())
        first_week = sorted_weeks[0] if sorted_weeks else 0
        last_week = sorted_weeks[-1] if sorted_weeks else 0
        
        # Calculate total remaining classes to schedule
        total_classes = len(context.request.classes)
        
        for week_num, vars_list in by_week.items():
            weekdays = weekdays_by_week[week_num]
            
            if week_num == first_week:
                # Pro-rate minimum for first week based on available weekdays
                min_periods = (context.request.constraints.minPeriodsPerWeek * weekdays) // 5
                print(f"Adding pro-rated minimum periods constraint for first week {week_num}:")
                print(f"- {len(vars_list)} variables")
                print(f"- {weekdays} weekdays")
                print(f"- Minimum periods: {min_periods}")
                context.model.Add(sum(vars_list) >= min_periods)
                limit_count += 1
                
            elif week_num == last_week:
                # For last week, encourage scheduling early in the week
                # Sort days in ascending order
                sorted_days = sorted(by_day[week_num].keys())
                cumulative_vars = []
                
                # Add variables day by day
                for day in sorted_days:
                    day_vars = [v["variable"] for v in by_day[week_num][day]]
                    cumulative_vars.extend(day_vars)
                    
                    # Try to schedule any remaining classes in these slots
                    remaining = total_classes - sum(len(by_day[w][d]) for w in sorted_weeks 
                                                 for d in by_day[w].keys() if w < week_num or 
                                                 (w == week_num and d < day))
                    if remaining > 0:
                        print(f"Encouraging scheduling {remaining} remaining classes on {day}")
                        # Add soft constraint with high weight to encourage early scheduling
                        early_var = context.model.NewIntVar(0, remaining, f"early_scheduling_{day}")
                        context.model.Add(early_var <= sum(day_vars))
                        
                        # Store early scheduling variables in context
                        if "early_scheduling_vars" not in context.debug_info:
                            context.debug_info["early_scheduling_vars"] = []
                        context.debug_info["early_scheduling_vars"].append(early_var)
                
            else:
                # Normal week - use full minimum
                print(f"Adding minimum periods constraint for week {week_num}:")
                print(f"- {len(vars_list)} variables")
                print(f"- {weekdays} weekdays")
                print(f"- Minimum periods: {context.request.constraints.minPeriodsPerWeek}")
                context.model.Add(sum(vars_list) >= context.request.constraints.minPeriodsPerWeek)
                limit_count += 1
            
        print(f"Added minimum periods constraints for {limit_count} weeks")
    
    def validate(
        self,
        assignments: List[Dict[str, Any]],
        context: SchedulerContext
    ) -> List[ConstraintViolation]:
        violations = []
        
        # Count assignments per week and also track weekdays per week
        by_week = defaultdict(int)
        weekdays_by_week = defaultdict(set)  # Use set to count unique weekdays
        
        for assignment in assignments:
            date = assignment["date"]
            week_num = (date - context.start_date).days // 7
            by_week[week_num] += 1
            
            # Only track weekdays (Mon-Fri)
            if date.weekday() < 5:
                weekdays_by_week[week_num].add(date.date())
        
        # Determine first and last weeks
        sorted_weeks = sorted(by_week.keys())
        first_week = sorted_weeks[0] if sorted_weeks else 0
        last_week = sorted_weeks[-1] if sorted_weeks else 0
        
        # Check for violations (excluding first and last weeks)
        for week_num, count in by_week.items():
            # Skip first and last weeks as they have special handling
            if week_num in (first_week, last_week):
                continue
                
            # Check regular weeks against full minimum
            if count < context.request.constraints.minPeriodsPerWeek:
                violations.append(ConstraintViolation(
                    message=(
                        f"Too few classes scheduled in week {week_num + 1}: "
                        f"got {count}, minimum is {context.request.constraints.minPeriodsPerWeek}"
                    ),
                    severity="error",
                    context={
                        "weekNumber": week_num + 1,
                        "count": count,
                        "minimum": context.request.constraints.minPeriodsPerWeek
                    }
                ))
            
            # For first week, check pro-rated minimum if it's not a full week
            if week_num == first_week and len(weekdays_by_week[week_num]) < 5:
                available_days = len(weekdays_by_week[week_num])
                pro_rated_min = (context.request.constraints.minPeriodsPerWeek * available_days) // 5
                
                if count < pro_rated_min:
                    violations.append(ConstraintViolation(
                        message=(
                            f"Too few classes scheduled in first week (pro-rated): "
                            f"got {count}, minimum is {pro_rated_min} "
                            f"({available_days} available days)"
                        ),
                        severity="error",
                        context={
                            "weekNumber": week_num + 1,
                            "count": count,
                            "minimum": pro_rated_min,
                            "availableDays": available_days
                        }
                    ))
        
        return violations
