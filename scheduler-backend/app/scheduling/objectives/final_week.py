"""Objective to compress remaining classes into early days of final week"""
from collections import defaultdict
from typing import List, Dict, Any
from datetime import datetime, timedelta

from ortools.sat.python import cp_model

from .base import BaseObjective
from ..core import SchedulerContext
from ...models import ScheduleAssignment

class FinalWeekCompressionObjective(BaseObjective):
    """Encourages scheduling final week classes as early as possible"""
    
    def __init__(self):
        from ..solvers.config import WEIGHTS
        super().__init__(
            name="final_week_compression",
            weight=WEIGHTS['final_week_compression']
        )
    
    def create_terms(self, context: SchedulerContext) -> List[cp_model.LinearExpr]:
        terms = []
        
        # Group variables by week and day
        by_week = defaultdict(lambda: defaultdict(list))
        for var in context.variables:
            week_num = (var["date"] - context.start_date).days // 7
            day_num = var["date"].weekday()  # Monday = 0, Sunday = 6
            by_week[week_num][day_num].append(var)
        
        # Only focus on the final week
        final_week = max(by_week.keys())
        if final_week in by_week:
            final_week_vars = by_week[final_week]
            
            # For each weekday (Monday-Friday)
            for day_num in range(5):  # 0-4 represents Monday-Friday
                if day_num in final_week_vars:
                    day_vars = final_week_vars[day_num]
                    
                    # Create weighted penalty based on day number
                    # Earlier days get less penalty
                    for var in day_vars:
                        # Scale penalty by day number (0 for Monday, increasing for later days)
                        day_penalty = context.model.NewIntVar(
                            -1000, 0, 
                            f"final_week_day_penalty_d{day_num}_c{var['name']}"
                        )
                        # Penalty increases for later days
                        context.model.Add(
                            day_penalty == var["variable"] * -200 * (day_num + 1)
                        )
                        terms.append(day_penalty)
                        
                    # Additional penalty for gaps between used days
                    if day_num > 0 and day_num - 1 in final_week_vars:
                        # Variables for previous and current day usage
                        prev_day_used = context.model.NewBoolVar(
                            f"final_week_prev_day_used_{day_num}"
                        )
                        curr_day_used = context.model.NewBoolVar(
                            f"final_week_curr_day_used_{day_num}"
                        )
                        
                        # Link usage variables to assignments
                        prev_sum = sum(
                            var["variable"] 
                            for var in final_week_vars[day_num - 1]
                        )
                        curr_sum = sum(
                            var["variable"] 
                            for var in final_week_vars[day_num]
                        )
                        
                        context.model.Add(prev_sum > 0).OnlyEnforceIf(prev_day_used)
                        context.model.Add(prev_sum == 0).OnlyEnforceIf(prev_day_used.Not())
                        context.model.Add(curr_sum > 0).OnlyEnforceIf(curr_day_used)
                        context.model.Add(curr_sum == 0).OnlyEnforceIf(curr_day_used.Not())
                        
                        # Penalize gaps (prev day unused but current day used)
                        gap_penalty = context.model.NewIntVar(
                            -1000, 0,
                            f"final_week_gap_penalty_{day_num}"
                        )
                        # Penalty if we skip a day but use a later one
                        context.model.Add(
                            gap_penalty == -500
                        ).OnlyEnforceIf([prev_day_used.Not(), curr_day_used])
                        context.model.Add(
                            gap_penalty == 0
                        ).OnlyEnforceIf([prev_day_used.Not(), curr_day_used.Not()])
                        context.model.Add(
                            gap_penalty == 0
                        ).OnlyEnforceIf([prev_day_used])
                        
                        terms.append(gap_penalty)
        
        return terms
