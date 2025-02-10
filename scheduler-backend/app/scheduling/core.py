from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Protocol
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
