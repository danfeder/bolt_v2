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
        RequiredPeriodsObjective(),  # weight=1000
    ]

# Priority weights for different types of constraints/objectives
WEIGHTS = {
    'required_periods': 10000,    # Highest priority - required periods must be satisfied
    'early_scheduling': 5000,     # High priority - schedule earlier when possible
    'preferred_periods': 1000,    # Medium priority - try to use preferred periods
    'avoid_periods': -500,        # Penalty for using avoided periods
    'distribution': 500,          # Balance the schedule distribution
    'earlier_dates': 10,         # Slight preference for earlier dates
}
