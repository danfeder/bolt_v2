from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Protocol, Optional
from ortools.sat.python import cp_model

from ..models import (
    ScheduleRequest,
    ScheduleResponse,
    ScheduleAssignment,
    ScheduleMetadata
)

class SchedulerContext:
    """Context object for sharing state between scheduler components"""
    def __init__(
        self,
        model: cp_model.CpModel,
        solver: cp_model.CpSolver,
        request: ScheduleRequest,
        start_date: datetime,
        end_date: datetime
    ):
        self.model = model
        self.solver = solver
        self.request = request
        self.start_date = start_date
        self.end_date = end_date
        self.variables: List[Dict[str, Any]] = []
        self.debug_info: Dict[str, Any] = {}
        
        # Index classes by name for quick lookup
        self.classes_by_name = {
            c.name: c for c in request.classes
        }
        
        # Index instructor availability by date
        self.instructor_unavailable = {}
        for avail in request.teacherAvailability:
            date_str = avail.date  # date is already a string in YYYY-MM-DD format
            if date_str not in self.instructor_unavailable:
                self.instructor_unavailable[date_str] = set()
            periods = [slot.period for slot in avail.unavailableSlots]
            self.instructor_unavailable[date_str].update(periods)

class Constraint(Protocol):
    """Protocol defining the interface for scheduler constraints"""
    @property
    def name(self) -> str:
        """Get the constraint's name for logging"""
        ...
    
    def apply(self, context: SchedulerContext) -> None:
        """Apply this constraint to the scheduling model"""
        ...

class Objective(Protocol):
    """Protocol defining the interface for scheduler objectives"""
    @property
    def name(self) -> str:
        """Get the objective's name for logging"""
        ...
    
    @property
    def weight(self) -> int:
        """Get the objective's weight for the solver"""
        ...
    
    def create_terms(self, context: SchedulerContext) -> List[cp_model.LinearExpr]:
        """Create objective terms for the solver"""
        ...

class SchedulerBase(ABC):
    """Base class for scheduler implementations"""
    def __init__(self):
        self.constraints: List[Constraint] = []
        self.objectives: List[Objective] = []
        
    def add_constraint(self, constraint: Constraint) -> None:
        """Add a constraint to the scheduler"""
        self.constraints.append(constraint)
        
    def add_objective(self, objective: Objective) -> None:
        """Add an objective to the scheduler"""
        self.objectives.append(objective)
    
    @abstractmethod
    def create_schedule(self, request: ScheduleRequest) -> ScheduleResponse:
        """Create a schedule satisfying all constraints and optimizing objectives"""
        pass

@dataclass
class SchedulerMetrics:
    """Metrics for scheduler performance and results"""
    duration_ms: int
    score: int
    distribution_score: float
    solver_status: str
    solutions_found: int
    optimization_gap: float

# Default constraint weights
DEFAULT_WEIGHTS = {
    "single_assignment": 10000,
    "no_overlap": 10000,
    "required_periods": 8000,
    "instructor_availability": 7000,
    "conflict_periods": 6000,
    "consecutive_classes": 5000,
    "class_limits": 4000,
    "avoid_periods": -2000,
    "preferred_periods": 1000
}

class SolverConfig:
    """Configuration for solver behavior and weights"""
    def __init__(self):
        self.WEIGHTS = DEFAULT_WEIGHTS.copy()
        self.ENABLE_METRICS = True
        self.ENABLE_SOLUTION_COMPARISON = True
        self.ENABLE_EXPERIMENTAL_DISTRIBUTION = False

# Global config instance
config = SolverConfig()

def get_config() -> SolverConfig:
    """Get the global solver configuration"""
    return config

class SolverCallback(cp_model.CpSolverSolutionCallback):
    """Base callback class for logging solver progress"""
    def __init__(self):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._solutions = 0
        self._start_time = datetime.now()
        self._last_log_time = datetime.now()
        self._last_log_count = 0
        
    def on_solution_callback(self):
        """Called when solver finds a new solution"""
        self._solutions += 1
        current_time = datetime.now()
        
        # Log every 3 seconds
        if (current_time - self._last_log_time).total_seconds() >= 3.0:
            elapsed = (current_time - self._start_time).total_seconds()
            solutions_since_last = self._solutions - self._last_log_count
            rate = solutions_since_last / (current_time - self._last_log_time).total_seconds()
            
            print(f"\nSearch status at {elapsed:.1f}s:")
            print(f"- Solutions found: {self._solutions} ({rate:.1f} solutions/sec)")
            print(f"- Best objective: {self.BestObjectiveBound()}")
            print(f"- Current bound: {self.ObjectiveValue()}")
            if self.ObjectiveValue() != 0:
                gap = ((self.ObjectiveValue() - self.BestObjectiveBound()) 
                      / abs(self.ObjectiveValue()))
                print(f"- Gap: {gap:.2%}")
            
            self._last_log_time = current_time
            self._last_log_count = self._solutions

class ConstraintManager:
    """
    Manages and applies a collection of constraints in a consistent order.
    """
    def __init__(self):
        self._constraints: List[Constraint] = []
        
    def add_constraint(self, constraint: Constraint) -> None:
        """Add a constraint to be managed"""
        self._constraints.append(constraint)
        # Sort by priority after adding
        self._constraints.sort(key=lambda c: getattr(c, 'priority', 1))
        
    def get_enabled_constraints(self) -> List[Constraint]:
        """Get all currently enabled constraints"""
        return [c for c in self._constraints if getattr(c, 'enabled', True)]
        
    def apply_all(self, context: SchedulerContext) -> None:
        """Apply all enabled constraints in priority order"""
        for constraint in self.get_enabled_constraints():
            constraint.apply(context)
            
    def validate_all(
        self,
        assignments: List[Dict[str, Any]],
        context: SchedulerContext
    ) -> List[Any]:  # Returns List[ConstraintViolation] but avoiding circular import
        """Validate assignments against all enabled constraints"""
        violations = []
        for constraint in self.get_enabled_constraints():
            if hasattr(constraint, 'validate'):
                violations.extend(constraint.validate(assignments, context))
        return violations
