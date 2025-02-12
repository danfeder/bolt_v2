"""Common solver configurations and constants"""
from typing import List

# Constraints
from ..constraints.assignment import SingleAssignmentConstraint, NoOverlapConstraint
from ..constraints.teacher import TeacherAvailabilityConstraint
from ..constraints.periods import RequiredPeriodsConstraint, ConflictPeriodsConstraint
from ..constraints.limits import (
    DailyLimitConstraint, 
    WeeklyLimitConstraint, 
    MinimumPeriodsConstraint
)

# Objectives
from ..objectives.required import RequiredPeriodsObjective
from ..objectives.distribution import DistributionObjective
from ..objectives.day_usage import DayUsageObjective
from ..objectives.final_week import FinalWeekCompressionObjective
from ..objectives.daily_balance import DailyBalanceObjective

# Base Types
from ..core import Constraint, Objective

def get_base_constraints() -> List[Constraint]:
    """Get the common constraints used by all solvers"""
    return [
        SingleAssignmentConstraint(),
        NoOverlapConstraint(),
        TeacherAvailabilityConstraint(),
        RequiredPeriodsConstraint(),
        ConflictPeriodsConstraint(),
        DailyLimitConstraint(),
        WeeklyLimitConstraint(),
        MinimumPeriodsConstraint(),
    ]

def get_base_objectives() -> List[Objective]:
    """Get the common objectives used by all solvers"""
    return [
        RequiredPeriodsObjective(),     # weight=10000
        DayUsageObjective(),            # weight=2000
        FinalWeekCompressionObjective(),  # weight=3000
        DailyBalanceObjective(),        # weight=1500
        DistributionObjective(),        # weight=1000
    ]

from typing import Dict

# Required periods are handled as hard constraints and are not configurable
REQUIRED_PERIODS_ENABLED = True

# Default priority weights for different types of constraints/objectives
DEFAULT_WEIGHTS = {
    'final_week_compression': 3000,   # High priority for final week optimization
    'day_usage': 2000,               # Encourage using all available days
    'daily_balance': 1500,           # Balance number of classes per day
    'preferred_periods': 1000,        # Medium priority - try to use preferred periods
    'distribution': 1000,             # Balance the period distribution
    'avoid_periods': -500,            # Penalty for using avoided periods
    'earlier_dates': 10,             # Slight preference for earlier dates
}

# Example of how to use required periods in constraints:
# 
# class RequiredPeriodsConstraint(Constraint):
#     def apply(self, context: SchedulerContext) -> None:
#         """Add hard constraint for required periods"""
#         if not REQUIRED_PERIODS_ENABLED:
#             return
#
#         for class_obj in context.request.classes:
#             for required in class_obj.required_periods:
#                 # Force assignment to required period
#                 context.model.Add(context.get_variable(class_obj.id, required.date, required.period) == 1)

# Current weights that can be modified at runtime
WEIGHTS = DEFAULT_WEIGHTS.copy()

def update_weights(new_weights: Dict[str, int]) -> None:
    """Update solver weights at runtime"""
    global WEIGHTS
    WEIGHTS.update(new_weights)

def reset_weights() -> None:
    """Reset weights to default values"""
    global WEIGHTS
    WEIGHTS = DEFAULT_WEIGHTS.copy()
