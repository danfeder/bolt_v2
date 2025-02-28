"""Component configuration for solvers"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
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

@dataclass
class MetaOptimizationConfig:
    """Configuration for meta-optimization weight tuning"""
    POPULATION_SIZE: int = 20
    GENERATIONS: int = 10
    MUTATION_RATE: float = 0.2
    CROSSOVER_RATE: float = 0.7
    EVAL_TIME_LIMIT: int = 60  # Seconds for each inner optimization run
    PARALLEL_EVALUATION: bool = True
    
    @classmethod
    def from_env(cls) -> 'MetaOptimizationConfig':
        """Create config from environment variables"""
        return cls(
            POPULATION_SIZE=int(os.getenv('META_POPULATION_SIZE', '20')),
            GENERATIONS=int(os.getenv('META_GENERATIONS', '10')),
            MUTATION_RATE=float(os.getenv('META_MUTATION_RATE', '0.2')),
            CROSSOVER_RATE=float(os.getenv('META_CROSSOVER_RATE', '0.7')),
            EVAL_TIME_LIMIT=int(os.getenv('META_EVAL_TIME_LIMIT', '60')),
            PARALLEL_EVALUATION=bool(int(os.getenv('META_PARALLEL_EVALUATION', '1')))
        )

# Detect if we're in a test environment
IS_TEST_ENV = 'PYTEST_CURRENT_TEST' in os.environ

# Feature flags
ENABLE_METRICS = bool(int(os.getenv('ENABLE_METRICS', '1')))
ENABLE_SOLUTION_COMPARISON = bool(int(os.getenv('ENABLE_SOLUTION_COMPARISON', '1')))
ENABLE_EXPERIMENTAL_DISTRIBUTION = bool(int(os.getenv('ENABLE_EXPERIMENTAL_DISTRIBUTION', '0')))
# Disable genetic optimization in test environment by default
ENABLE_GENETIC_OPTIMIZATION = bool(int(os.getenv('ENABLE_GENETIC_OPTIMIZATION', '0' if IS_TEST_ENV else '1')))
ENABLE_CONSECUTIVE_CLASSES = bool(int(os.getenv('ENABLE_CONSECUTIVE_CLASSES', '1')))
ENABLE_TEACHER_BREAKS = bool(int(os.getenv('ENABLE_TEACHER_BREAKS', '0')))
ENABLE_WEIGHT_TUNING = bool(int(os.getenv('ENABLE_WEIGHT_TUNING', '0')))
# Disable grade grouping in test environment by default 
ENABLE_GRADE_GROUPING = bool(int(os.getenv('ENABLE_GRADE_GROUPING', '0')))
ENABLE_CONSTRAINT_RELAXATION = bool(int(os.getenv('ENABLE_CONSTRAINT_RELAXATION', '1')))

# Load configurations
GENETIC_CONFIG = GeneticConfig.from_env()
META_CONFIG = MetaOptimizationConfig.from_env()

# Time limits
SOLVER_TIME_LIMIT_SECONDS = int(os.getenv('SOLVER_TIME_LIMIT', '300'))

# Objective weights
WEIGHTS = {
    'required_periods': 10000,
    'day_usage': 2000,
    'final_week_compression': 3000,
    'daily_balance': 1500,
    'distribution': 1000,
    'grade_grouping': 1200,  # Higher weight than distribution but lower than daily_balance
    'avoid_periods': -500,
    'earlier_dates': 10,
}

# Default weights for resetting
DEFAULT_WEIGHTS = WEIGHTS.copy()

def update_weights(new_weights: Dict[str, int]) -> None:
    """Update objective weights with new values"""
    global WEIGHTS
    
    # Validate weight names
    for key in new_weights:
        if key not in WEIGHTS:
            raise ValueError(f"Unknown weight key: {key}")
            
    # Update only provided weights
    for key, value in new_weights.items():
        WEIGHTS[key] = value
        
def reset_weights() -> None:
    """Reset weights to default values"""
    global WEIGHTS
    WEIGHTS = DEFAULT_WEIGHTS.copy()

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
from ..constraints.relaxable_limits import (
    RelaxableDailyLimitConstraint,
    RelaxableWeeklyLimitConstraint
)
from ..constraints.relaxation import (
    RelaxationController,
    RelaxationLevel,
    RelaxableConstraint
)

# Objectives
from ..objectives.required import RequiredPeriodsObjective
from ..objectives.distribution import DistributionObjective
from ..objectives.day_usage import DayUsageObjective
from ..objectives.final_week import FinalWeekCompressionObjective
from ..objectives.daily_balance import DailyBalanceObjective
from ..objectives.grade_grouping import GradeGroupingObjective

def get_base_constraints() -> List[Constraint]:
    """Get the common constraints used by all solvers"""
    constraints = [
        SingleAssignmentConstraint(),  # Critical constraints 
        NoOverlapConstraint(),
        InstructorAvailabilityConstraint(),
        RequiredPeriodsConstraint(),
        ConflictPeriodsConstraint(),
    ]
    
    # Use relaxable constraints if enabled, otherwise use standard constraints
    if ENABLE_CONSTRAINT_RELAXATION:
        constraints.extend([
            RelaxableDailyLimitConstraint(
                enabled=True
            ),
            RelaxableWeeklyLimitConstraint(
                enabled=True
            ),
        ])
    else:
        # Standard constraints
        constraints.extend([
            DailyLimitConstraint(),
            WeeklyLimitConstraint(),
        ])
    
    constraints.append(MinimumPeriodsConstraint())
    
    # Add teacher workload constraints if enabled
    if ENABLE_CONSECUTIVE_CLASSES:
        constraints.append(ConsecutiveClassesConstraint(
            enabled=True
        ))
    
    if ENABLE_TEACHER_BREAKS:
        constraints.append(TeacherBreakConstraint(
            enabled=True
        ))
        
    return constraints

def get_base_objectives() -> List[Objective]:
    """Get the common objectives used by all solvers"""
    objectives = [
        RequiredPeriodsObjective(),     # weight=10000
        DayUsageObjective(),            # weight=2000
        FinalWeekCompressionObjective(),  # weight=3000
        DailyBalanceObjective(),        # weight=1500
        DistributionObjective(),        # weight=1000
    ]
    
    # Only add grade grouping if enabled
    if ENABLE_GRADE_GROUPING:
        objectives.append(GradeGroupingObjective())  # weight=1200
    
    return objectives
