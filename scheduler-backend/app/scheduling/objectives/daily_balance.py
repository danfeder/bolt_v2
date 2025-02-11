"""Objective to encourage similar number of classes across used days"""
from collections import defaultdict
from typing import List, Dict, Any
from datetime import datetime, timedelta

from ortools.sat.python import cp_model

from .base import BaseObjective
from ..core import SchedulerContext
from ...models import ScheduleAssignment

class DailyBalanceObjective(BaseObjective):
    """Encourages similar number of classes on each used day"""
    
    def __init__(self):
        from ..solvers.config import WEIGHTS
        super().__init__(
            name="daily_balance",
            weight=WEIGHTS['daily_balance']
        )
    
    def create_terms(self, context: SchedulerContext) -> List[cp_model.LinearExpr]:
        terms = []
        
        # Group variables by week and day
        by_week = defaultdict(lambda: defaultdict(list))
        for var in context.variables:
            week_num = (var["date"] - context.start_date).days // 7
            day_num = var["date"].weekday()  # Monday = 0, Sunday = 6
            by_week[week_num][day_num].append(var)
        
        # Process each week (except final week)
        total_weeks = max(by_week.keys()) + 1
        for week_num in range(total_weeks - 1):  # Skip final week
            week_vars = by_week[week_num]
            
            # Create day usage indicators and class counts
            day_used = {}
            day_count = {}
            
            # For each weekday (Monday-Friday)
            for day_num in range(5):  # 0-4 represents Monday-Friday
                if day_num in week_vars:
                    # Binary variable indicating if day is used
                    day_used[day_num] = context.model.NewBoolVar(
                        f"balance_day_used_w{week_num}_d{day_num}"
                    )
                    
                    # Sum of assignments for this day
                    day_sum = sum(var["variable"] for var in week_vars[day_num])
                    day_count[day_num] = day_sum
                    
                    # Link day_used to whether any classes are scheduled
                    context.model.Add(day_sum > 0).OnlyEnforceIf(day_used[day_num])
                    context.model.Add(day_sum == 0).OnlyEnforceIf(day_used[day_num].Not())
            
            # Compare each pair of used days
            for day_i in range(5):
                if day_i not in week_vars:
                    continue
                    
                for day_j in range(day_i + 1, 5):
                    if day_j not in week_vars:
                        continue
                        
                    # Create deviation variable for this pair
                    deviation = context.model.NewIntVar(
                        -10, 10,
                        f"daily_balance_dev_w{week_num}_d{day_i}_{day_j}"
                    )
                    
                    # Calculate difference in class count
                    context.model.Add(
                        deviation == day_count[day_i] - day_count[day_j]
                    )
                    
                    # Penalize differences between used days
                    penalty = context.model.NewIntVar(
                        -1000, 0,
                        f"daily_balance_penalty_w{week_num}_d{day_i}_{day_j}"
                    )
                    
                    # Only apply penalty if both days are used
                    context.model.Add(
                        penalty == -100 * deviation
                    ).OnlyEnforceIf([day_used[day_i], day_used[day_j]])
                    context.model.Add(
                        penalty == -100 * -deviation
                    ).OnlyEnforceIf([day_used[day_i], day_used[day_j]])
                    context.model.Add(
                        penalty == 0
                    ).OnlyEnforceIf([day_used[day_i].Not()])
                    context.model.Add(
                        penalty == 0
                    ).OnlyEnforceIf([day_used[day_j].Not()])
                    
                    terms.append(penalty)
        
        return terms
