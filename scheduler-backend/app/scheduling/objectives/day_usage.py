"""Objective to encourage using all available days in each week"""
from collections import defaultdict
from typing import List, Dict, Any
from datetime import datetime, timedelta

from ortools.sat.python import cp_model

from .base import BaseObjective
from ..core import SchedulerContext
from ...models import ScheduleAssignment

class DayUsageObjective(BaseObjective):
    """Encourages spreading classes across all available days in a week"""
    
    def __init__(self):
        from ..solvers.config import WEIGHTS
        super().__init__(
            name="day_usage",
            weight=WEIGHTS['day_usage']
        )
    
    def create_terms(self, context: SchedulerContext) -> List[cp_model.LinearExpr]:
        terms = []
        
        # Group variables by week and day
        by_week = defaultdict(lambda: defaultdict(list))
        for var in context.variables:
            week_num = (var["date"] - context.start_date).days // 7
            day_num = var["date"].weekday()  # Monday = 0, Sunday = 6
            by_week[week_num][day_num].append(var)
        
        # For each week (except final week), encourage using all weekdays
        total_weeks = max(by_week.keys()) + 1
        for week_num in range(total_weeks - 1):  # Skip final week
            week_vars = by_week[week_num]
            
            # For each weekday (Monday-Friday)
            for day_num in range(5):  # 0-4 represents Monday-Friday
                if day_num in week_vars:
                    # Create binary variable indicating if day is used
                    day_used = context.model.NewBoolVar(f"day_used_w{week_num}_d{day_num}")
                    
                    # Sum of assignments for this day
                    day_sum = sum(var["variable"] for var in week_vars[day_num])
                    
                    # Link day_used to whether any classes are scheduled
                    context.model.Add(day_sum > 0).OnlyEnforceIf(day_used)
                    context.model.Add(day_sum == 0).OnlyEnforceIf(day_used.Not())
                    
                    # Add penalty for unused days
                    penalty = context.model.NewIntVar(-1000, 0, f"day_penalty_w{week_num}_d{day_num}")
                    context.model.Add(penalty == day_used.Not() * -1000)
                    terms.append(penalty)
        
        return terms
