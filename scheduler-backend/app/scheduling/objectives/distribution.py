from collections import defaultdict
from typing import List, Dict, Any
from dataclasses import dataclass
import statistics
from datetime import datetime, timedelta

from ortools.sat.python import cp_model

from .base import BaseObjective
from ..core import SchedulerContext
from ...models import ScheduleAssignment

@dataclass
class DistributionMetrics:
    """Tracks distribution metrics for schedule analysis"""
    classes_per_week: Dict[int, int]
    classes_per_period: Dict[str, Dict[str, int]]  # Changed inner Dict key to str
    class_periods: Dict[str, Dict[str, int]]
    week_variance: float
    period_spread: Dict[str, float]
    class_load_variance: Dict[str, float]
    distribution_score: float

    @property
    def teacher_load_variance(self) -> Dict[str, float]:
        # For backward compatibility. Previously, workload variance was referred to as teacher_load_variance.
        return self.class_load_variance

class DistributionObjective(BaseObjective):
    """
    Objective function for optimizing schedule distribution:
    1. Even distribution across weeks
    2. Even distribution within days
    3. Balanced class workload
    """
    
    def __init__(self):
        from ..solvers.config import WEIGHTS
        super().__init__(
            name="distribution",
            weight=WEIGHTS['distribution']  # Use standardized weight from config
        )
    
    def create_terms(self, context: SchedulerContext) -> List[cp_model.LinearExpr]:
        terms = []
        
        # Group variables by week
        by_week = defaultdict(list)
        for var in context.variables:
            # Both var["date"] and context.start_date are datetime objects from base solver
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
        
        # Group variables by class
        by_class = defaultdict(lambda: defaultdict(list))
        for var in context.variables:
            date = var["date"].date()
            by_class[var["name"]][date].append(var)
        
        # Create class workload distribution terms
        for class_vars in by_class.values():
            for date, day_vars in class_vars.items():
                # Sum of assignments for this class on this day
                day_sum = sum(var["variable"] for var in day_vars)
                # Penalty increases with number of classes
                penalty = context.model.NewIntVar(
                    -1000, 0,
                    f"class_penalty_{date}"
                )
                context.model.Add(penalty == -250 * day_sum)
                terms.append(penalty)
        
        # Store metrics for debug info
        # Use a non-string key for the context.debug_info to avoid string comparison with LinearExpr
        # This is the root cause of the error with the LinearExpr == 'distribution' comparison
        debug_key = self.name  # This is already 'distribution' from __init__
        context.debug_info[debug_key] = {
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
        class_periods = defaultdict(lambda: defaultdict(int))
        
        print("\nCalculating distribution metrics...")
        print(f"Total assignments: {len(assignments)}")
        
        # Group assignments and calculate metrics
        for assignment in assignments:
            try:
                # Parse the ISO format date string into a datetime object
                date = datetime.fromisoformat(assignment.date)
                period = assignment.timeSlot.period
                class_name = assignment.name
                
                # Calculate week number using datetime objects
                week_num = (date - context.start_date).days // 7
                classes_per_week[week_num] += 1
                
                # Use date string for dictionary keys
                date_str = date.date().isoformat()
                period_str = str(period)  # Convert period to string
                
                # Daily distribution
                classes_per_period[date_str][period_str] += 1  # Use string key
                class_periods[date_str][class_name] += 1
                
                print(f"Processed assignment: date={date_str}, period={period_str}, class={class_name}, week={week_num}")
                
            except Exception as e:
                print(f"Error processing assignment: {assignment}")
                print(f"Error details: {str(e)}")
                raise
        
        print("\nWeekly distribution:")
        for week, count in classes_per_week.items():
            print(f"Week {week}: {count} classes")
        
        # Calculate variances and spreads
        week_counts = list(classes_per_week.values())
        week_variance = (
            statistics.variance(week_counts)
            if len(week_counts) > 1
            else 0.0
        )
        
        # Calculate period spread for each day
        period_spread = {}
        for date_str, periods in classes_per_period.items():
            # Convert period numbers to strings when accessing
            counts = [periods.get(str(p), 0) for p in range(1, 9)]
            variance = (
                statistics.variance(counts)
                if len(counts) > 1
                else 0.0
            )
            # Convert to spread score (1 - normalized variance)
            max_variance = 4.0  # Theoretical maximum
            period_spread[date_str] = 1.0 - min(variance / max_variance, 1.0)
        
        # Calculate class load variance for each day
        class_load_variance = {}
        for date_str, loads in class_periods.items():
            counts = list(loads.values())
            class_load_variance[date_str] = (
                statistics.variance(counts)
                if len(counts) > 1
                else 0.0
            )
        
        # Calculate overall distribution score
        total_score = 0
        for date_str in classes_per_period.keys():
            # Penalize poor period spread
            spread_penalty = -200 * (1.0 - period_spread[date_str])
            # Penalize class load imbalance
            load_penalty = -150 * class_load_variance.get(date_str, 0.0)
            total_score += spread_penalty + load_penalty
        
        # Penalize weekly variance
        total_score += -100 * week_variance
        
        print("\nDistribution metrics calculated:")
        print(f"Week variance: {week_variance}")
        print(f"Total score: {total_score}")
        
        return DistributionMetrics(
            classes_per_week=dict(classes_per_week),
            classes_per_period=dict(classes_per_period),
            class_periods=dict(class_periods),
            week_variance=week_variance,
            period_spread=dict(period_spread),
            class_load_variance=dict(class_load_variance),
            distribution_score=total_score
        )
