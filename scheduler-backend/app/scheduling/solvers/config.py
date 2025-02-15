"""Common solver configurations and constants"""
from dataclasses import dataclass, field
import os
from typing import Dict, List

# Constraints
from ..constraints.assignment import SingleAssignmentConstraint, NoOverlapConstraint
from ..constraints.instructor import InstructorAvailabilityConstraint
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

@dataclass
class SolverConfig:
    """Configuration for the unified solver"""
    
    # Feature flags
    ENABLE_METRICS: bool = field(default=False)
    ENABLE_SOLUTION_COMPARISON: bool = field(default=False)
    ENABLE_EXPERIMENTAL_DISTRIBUTION: bool = field(default=False)
    
    # Optimization parameters
    TIME_LIMIT_SECONDS: int = field(default=300)  # 5 minutes default
    OPTIMIZATION_TOLERANCE: float = field(default=0.01)
    
    # Weights for different optimization objectives
    WEIGHTS: Dict[str, int] = field(default_factory=lambda: {
        'final_week_compression': 3000,   # High priority for final week optimization
        'day_usage': 2000,               # Encourage using all available days
        'daily_balance': 1500,           # Balance number of classes per day
        'preferred_periods': 1000,        # Medium priority - try to use preferred periods
        'distribution': 1000,             # Balance the period distribution
        'avoid_periods': -500,            # Penalty for using avoided periods
        'earlier_dates': 10,             # Slight preference for earlier dates
    })

    @classmethod
    def from_env(cls) -> 'SolverConfig':
        """Create configuration from environment variables"""
        return cls(
            ENABLE_METRICS=os.getenv('ENABLE_METRICS', '0') == '1',
            ENABLE_SOLUTION_COMPARISON=os.getenv('ENABLE_SOLUTION_COMPARISON', '0') == '1',
            ENABLE_EXPERIMENTAL_DISTRIBUTION=os.getenv('ENABLE_EXPERIMENTAL_DISTRIBUTION', '0') == '1',
            TIME_LIMIT_SECONDS=int(os.getenv('SOLVER_TIME_LIMIT', '300')),
            OPTIMIZATION_TOLERANCE=float(os.getenv('OPTIMIZATION_TOLERANCE', '0.01')),
        )

def get_base_constraints() -> List[Constraint]:
    """Get the common constraints used by all solvers"""
    return [
        SingleAssignmentConstraint(),
        NoOverlapConstraint(),
        InstructorAvailabilityConstraint(),
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

# Global instance
config = SolverConfig()

def update_weights(new_weights: Dict[str, int]) -> None:
    """Update solver weights at runtime"""
    config.WEIGHTS.update(new_weights)

def reset_weights() -> None:
    """Reset weights to default values"""
    config.WEIGHTS = SolverConfig().WEIGHTS.copy()
