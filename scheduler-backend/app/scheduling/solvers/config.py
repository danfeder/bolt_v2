"""Component configuration for solvers"""
from dataclasses import dataclass
from typing import List
import os

from ..core import Constraint, Objective

@dataclass
class GeneticConfig:
    """Configuration for genetic algorithm solver"""
    POPULATION_SIZE: int = 100
    ELITE_SIZE: int = 2
    MUTATION_RATE: float = 0.1
    CROSSOVER_RATE: float = 0.8
    MAX_GENERATIONS: int = 100
    CONVERGENCE_THRESHOLD: float = 0.01
    USE_ADAPTIVE_CONTROL: bool = True
    ADAPTATION_INTERVAL: int = 5
    DIVERSITY_THRESHOLD: float = 0.15
    ADAPTATION_STRENGTH: float = 0.5
    
    @classmethod
    def from_env(cls) -> 'GeneticConfig':
        """Create config from environment variables"""
        return cls(
            POPULATION_SIZE=int(os.getenv('GA_POPULATION_SIZE', '100')),
            ELITE_SIZE=int(os.getenv('GA_ELITE_SIZE', '2')),
            MUTATION_RATE=float(os.getenv('GA_MUTATION_RATE', '0.1')),
            CROSSOVER_RATE=float(os.getenv('GA_CROSSOVER_RATE', '0.8')),
            MAX_GENERATIONS=int(os.getenv('GA_MAX_GENERATIONS', '100')),
            CONVERGENCE_THRESHOLD=float(os.getenv('GA_CONVERGENCE_THRESHOLD', '0.01')),
            USE_ADAPTIVE_CONTROL=bool(int(os.getenv('GA_USE_ADAPTIVE_CONTROL', '1'))),
            ADAPTATION_INTERVAL=int(os.getenv('GA_ADAPTATION_INTERVAL', '5')),
            DIVERSITY_THRESHOLD=float(os.getenv('GA_DIVERSITY_THRESHOLD', '0.15')),
            ADAPTATION_STRENGTH=float(os.getenv('GA_ADAPTATION_STRENGTH', '0.5'))
        )

# Feature flags
ENABLE_METRICS = bool(int(os.getenv('ENABLE_METRICS', '1')))
ENABLE_SOLUTION_COMPARISON = bool(int(os.getenv('ENABLE_SOLUTION_COMPARISON', '1')))
ENABLE_EXPERIMENTAL_DISTRIBUTION = bool(int(os.getenv('ENABLE_EXPERIMENTAL_DISTRIBUTION', '0')))
ENABLE_GENETIC_OPTIMIZATION = bool(int(os.getenv('ENABLE_GENETIC_OPTIMIZATION', '0')))

# Load genetic algorithm config
GENETIC_CONFIG = GeneticConfig.from_env()

# Time limits
SOLVER_TIME_LIMIT_SECONDS = int(os.getenv('SOLVER_TIME_LIMIT', '300'))

# Objective weights
WEIGHTS = {
    'required_periods': 10000,
    'day_usage': 2000,
    'final_week_compression': 3000,
    'daily_balance': 1500,
    'distribution': 1000,
}

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
