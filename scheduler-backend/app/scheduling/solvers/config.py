"""Component configuration for solvers"""
from dataclasses import dataclass, field
from typing import List, Optional
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
    PARALLEL_FITNESS: bool = True
    CROSSOVER_METHODS: List[str] = field(default_factory=lambda: ["single_point", "two_point", "uniform", "order"])
    
    @classmethod
    def from_env(cls) -> 'GeneticConfig':
        """Create config from environment variables"""
        # Parse crossover methods if provided
        crossover_methods_str = os.getenv('GA_CROSSOVER_METHODS', '')
        crossover_methods = (
            crossover_methods_str.split(',') 
            if crossover_methods_str else 
            ["single_point", "two_point", "uniform", "order"]
        )
        
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
            ADAPTATION_STRENGTH=float(os.getenv('GA_ADAPTATION_STRENGTH', '0.5')),
            PARALLEL_FITNESS=bool(int(os.getenv('GA_PARALLEL_FITNESS', '1'))),
            CROSSOVER_METHODS=crossover_methods
        )

# Feature flags
ENABLE_METRICS = bool(int(os.getenv('ENABLE_METRICS', '1')))
ENABLE_SOLUTION_COMPARISON = bool(int(os.getenv('ENABLE_SOLUTION_COMPARISON', '1')))
ENABLE_EXPERIMENTAL_DISTRIBUTION = bool(int(os.getenv('ENABLE_EXPERIMENTAL_DISTRIBUTION', '0')))
ENABLE_GENETIC_OPTIMIZATION = bool(int(os.getenv('ENABLE_GENETIC_OPTIMIZATION', '0')))
ENABLE_CONSECUTIVE_CLASSES = bool(int(os.getenv('ENABLE_CONSECUTIVE_CLASSES', '1')))
ENABLE_TEACHER_BREAKS = bool(int(os.getenv('ENABLE_TEACHER_BREAKS', '0')))

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
from ..constraints.teacher_workload import (
    ConsecutiveClassesConstraint,
    TeacherBreakConstraint
)

# Objectives
from ..objectives.required import RequiredPeriodsObjective
from ..objectives.distribution import DistributionObjective
from ..objectives.day_usage import DayUsageObjective
from ..objectives.final_week import FinalWeekCompressionObjective
from ..objectives.daily_balance import DailyBalanceObjective

def get_base_constraints() -> List[Constraint]:
    """Get the common constraints used by all solvers"""
    constraints = [
        SingleAssignmentConstraint(),
        NoOverlapConstraint(),
        InstructorAvailabilityConstraint(),
        RequiredPeriodsConstraint(),
        ConflictPeriodsConstraint(),
        DailyLimitConstraint(),
        WeeklyLimitConstraint(),
        MinimumPeriodsConstraint(),
    ]
    
    # Add teacher workload constraints if enabled
    if ENABLE_CONSECUTIVE_CLASSES:
        constraints.append(ConsecutiveClassesConstraint(
            enabled=True,
            allow_consecutive=True  # Allow pairs of consecutive classes
        ))
    
    if ENABLE_TEACHER_BREAKS:
        constraints.append(TeacherBreakConstraint(
            enabled=True,
            # Will be populated from request.constraints.requiredBreakPeriods during apply()
            required_breaks=[]
        ))
        
    return constraints

def get_base_objectives() -> List[Objective]:
    """Get the common objectives used by all solvers"""
    return [
        RequiredPeriodsObjective(),     # weight=10000
        DayUsageObjective(),            # weight=2000
        FinalWeekCompressionObjective(),  # weight=3000
        DailyBalanceObjective(),        # weight=1500
        DistributionObjective(),        # weight=1000
    ]
