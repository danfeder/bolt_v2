from collections import defaultdict
from typing import List, Dict, Any
from dataclasses import dataclass
import statistics
from datetime import timedelta

from ortools.sat.python import cp_model

from .base import BaseObjective
from ..core import SchedulerContext
from ...models import ScheduleAssignment

@dataclass
class DistributionMetrics:
    """Tracks distribution metrics for schedule analysis"""
    classes_per_week: Dict[int, int]
    classes_per_period: Dict[str, Dict[int, int]]
    teacher_periods: Dict[str, Dict[str, int]]
    week_variance: float
    period_spread: Dict[str, float]
    teacher_load_variance: Dict[str, float]
    distribution_score: float

class DistributionObjective(BaseObjective):
    """
    Objective function for optimizing schedule distribution:
    1. Even distribution across weeks
    2. Even distribution within days
    3. Balanced teacher workload
    """
    
    def __init__(self):
        super().__init__(
            name="distribution",
            weight=500  # Lower weight than required periods
        )
    
    def create_terms(self, context: SchedulerContext) -> List[cp_model.LinearExpr]:
        terms = []
        
        # Group variables by week
        by_week = defaultdict(list)
        for var in context.variables:
            week_num = (var["date"] - context.start_date).days // 7
            by_week[week_num].append(var)
        
        # Create weekly distribution terms
        total_classes = len(context.request.classes)
        total_weeks = len(by_week)
        # Scale up by 100 to handle decimals as integers
        target_per_week = (total_classes * 100) // total_weeks
        
        for week_vars in by_week.values():
            # Sum of assignments for this week (scaled up)
            week_sum = sum(100 * var["variable"] for var in week_vars)
            # Penalize deviation from target
            deviation = context.model.NewIntVar(-1000, 1000, "week_deviation")
            context.model.Add(deviation == week_sum - target_per_week)
            # Use linear penalty
            penalty = context.model.NewIntVar(-750000, 0, "week_penalty")
            # Absolute value of deviation using two constraints
            context.model.Add(penalty <= -750 * deviation)
            context.model.Add(penalty <= 750 * deviation)
            terms.append(penalty)
        
        # Group variables by date and period
        by_date = defaultdict(lambda: defaultdict(list))
        for var in context.variables:
            date = var["date"].date()
            period = var["period"]
            by_date[date][period].append(var)
        
        # Create daily distribution terms
        for date, periods in by_date.items():
            # Track assignments per period
            period_sums = []
            for period in range(1, 9):
                if period in periods:
                    period_sum = sum(
                        var["variable"] for var in periods[period]
                    )
                    period_sums.append(period_sum)
            
            # Penalize uneven distribution across periods
            if period_sums:
                for i in range(len(period_sums)):
                    for j in range(i + 1, len(period_sums)):
                        # Create deviation variable for each pair
                        deviation = context.model.NewIntVar(
                            -10, 10, 
                            f"period_diff_{date}_{i}_{j}"
                        )
                        context.model.Add(
                            deviation == period_sums[i] - period_sums[j]
                        )
                        # Penalize differences
                        penalty = context.model.NewIntVar(
                            -500, 0,
                            f"period_penalty_{date}_{i}_{j}"
                        )
                        context.model.Add(penalty <= -50 * deviation)
                        context.model.Add(penalty <= 50 * deviation)
                        terms.append(penalty)
        
        # Group variables by teacher (using class ID as proxy)
        by_teacher = defaultdict(lambda: defaultdict(list))
        for var in context.variables:
            date = var["date"].date()
            by_teacher[var["classId"]][date].append(var)
        
        # Create teacher workload distribution terms
        for teacher_vars in by_teacher.values():
            for date, day_vars in teacher_vars.items():
                # Sum of assignments for this teacher on this day
                day_sum = sum(var["variable"] for var in day_vars)
                # Penalty increases with number of classes
                penalty = context.model.NewIntVar(
                    -1000, 0,
                    f"teacher_penalty_{date}"
                )
                context.model.Add(penalty == -250 * day_sum)
                terms.append(penalty)
        
        # Store metrics for debug info
        context.debug_info["distribution"] = {
            "targetClassesPerWeek": target_per_week / 100,  # Scale back down
            "totalClasses": total_classes,
            "totalWeeks": total_weeks
        }
        
        return terms
    
    def calculate_metrics(
        self,
        assignments: List[ScheduleAssignment],
        context: SchedulerContext
    ) -> DistributionMetrics:
        """Calculate distribution metrics for assigned schedule"""
        classes_per_week = defaultdict(int)
        classes_per_period = defaultdict(lambda: defaultdict(int))
        teacher_periods = defaultdict(lambda: defaultdict(str))
        
        # Group assignments and calculate metrics
        for assignment in assignments:
            date = assignment.date  # Access as property, not dict key
            period = assignment.timeSlot.period
            class_id = assignment.classId
            
            # Parse dates consistently
            assignment_date = parser.parse(date)
            
            # Weekly distribution
            week_num = (
                assignment_date - context.start_date
            ).days // 7
            classes_per_week[week_num] += 1
            
            # Daily distribution
            classes_per_period[date][period] += 1
            teacher_periods[date][class_id] += 1
        
        # Calculate variances and spreads
        week_counts = list(classes_per_week.values())
        week_variance = (
            statistics.variance(week_counts)
            if len(week_counts) > 1
            else 0.0
        )
        
        # Calculate period spread for each day
        period_spread = {}
        for date, periods in classes_per_period.items():
            counts = [periods[p] for p in range(1, 9)]
            variance = (
                statistics.variance(counts)
                if len(counts) > 1
                else 0.0
            )
            # Convert to spread score (1 - normalized variance)
            max_variance = 4.0  # Theoretical maximum
            period_spread[date] = 1.0 - min(variance / max_variance, 1.0)
        
        # Calculate teacher load variance for each day
        teacher_load_variance = {}
        for date, loads in teacher_periods.items():
            counts = list(loads.values())
            teacher_load_variance[date] = (
                statistics.variance(counts)
                if len(counts) > 1
                else 0.0
            )
        
        # Calculate overall distribution score
        total_score = 0
        for date in classes_per_period.keys():
            # Penalize poor period spread
            spread_penalty = -200 * (1.0 - period_spread[date])
            # Penalize teacher load imbalance
            load_penalty = -150 * teacher_load_variance[date]
            total_score += spread_penalty + load_penalty
        
        # Penalize weekly variance
        total_score += -100 * week_variance
        
        return DistributionMetrics(
            classes_per_week=dict(classes_per_week),
            classes_per_period=dict(classes_per_period),
            teacher_periods=dict(teacher_periods),
            week_variance=week_variance,
            period_spread=dict(period_spread),
            teacher_load_variance=dict(teacher_load_variance),
            distribution_score=total_score
        )
