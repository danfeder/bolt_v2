"""
Solver Strategy Pattern Implementation

This module defines the interfaces and base classes for the Strategy pattern
used by the scheduler's solvers. Each strategy encapsulates a specific
algorithm for solving the scheduling problem.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Protocol, TypeVar, Generic, Set, Tuple

from ...models import ScheduleRequest, ScheduleResponse, ScheduleAssignment, ScheduleMetadata
from ..core import SchedulerContext

T = TypeVar('T')


class SolverResult(Generic[T]):
    """Result of a solver execution with metadata"""
    
    def __init__(
        self, 
        success: bool,
        schedule: Optional[T] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        assignments: Optional[List[ScheduleAssignment]] = None
    ):
        self.success = success
        self.schedule = schedule
        self.error = error
        self.metadata = metadata or {}
        self.assignments = assignments or []
    
    def to_response(self) -> ScheduleResponse:
        """Convert the result to a ScheduleResponse"""
        return ScheduleResponse(
            assignments=self.assignments,
            metadata=ScheduleMetadata(
                duration_ms=self.metadata.get('runtime_ms', 0),
                solutions_found=self.metadata.get('solutions_found', 0),
                score=self.metadata.get('score', 0),
                gap=self.metadata.get('gap', 0),
                distribution=self.metadata.get('distribution', None),
                solver=self.metadata.get('solver_name', 'unknown')
            )
        )


class SolverConstraint(Protocol):
    """Protocol for solver constraints"""
    
    @property
    def name(self) -> str:
        """Get the constraint name"""
        ...
    
    @property
    def enabled(self) -> bool:
        """Check if the constraint is enabled"""
        ...
    
    @property
    def weight(self) -> Optional[float]:
        """Get the constraint weight (None for hard constraints)"""
        ...
    
    def apply(self, context: SchedulerContext) -> None:
        """Apply the constraint to the scheduler context"""
        ...


class SolverObjective(Protocol):
    """Protocol for solver objectives"""
    
    @property
    def name(self) -> str:
        """Get the objective name"""
        ...
    
    @property
    def weight(self) -> float:
        """Get the objective weight"""
        ...
    
    def apply(self, context: SchedulerContext) -> None:
        """Apply the objective to the scheduler context"""
        ...


class SolverStrategy(ABC):
    """
    Abstract base class for solver strategies
    
    This class defines the interface for all solver strategies.
    Each strategy implements a specific algorithm for solving the scheduling problem.
    """
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize the strategy
        
        Args:
            name: The name of the strategy
            description: A description of the strategy
        """
        self._name = name
        self._description = description
        self._constraints: List[SolverConstraint] = []
        self._objectives: List[SolverObjective] = []
    
    @property
    def name(self) -> str:
        """Get the strategy name"""
        return self._name
    
    @property
    def description(self) -> str:
        """Get the strategy description"""
        return self._description
    
    @property
    def constraints(self) -> List[SolverConstraint]:
        """Get the constraints used by this strategy"""
        return self._constraints
    
    @property
    def objectives(self) -> List[SolverObjective]:
        """Get the objectives used by this strategy"""
        return self._objectives
    
    def add_constraint(self, constraint: SolverConstraint) -> None:
        """
        Add a constraint to the strategy
        
        Args:
            constraint: The constraint to add
        """
        self._constraints.append(constraint)
    
    def add_objective(self, objective: SolverObjective) -> None:
        """
        Add an objective to the strategy
        
        Args:
            objective: The objective to add
        """
        self._objectives.append(objective)
    
    @abstractmethod
    def solve(self, request: ScheduleRequest, config: Dict[str, Any]) -> SolverResult:
        """
        Solve the scheduling problem
        
        Args:
            request: The scheduling request
            config: Configuration for the solver
            
        Returns:
            The result of the solving process
        """
        raise NotImplementedError("Subclasses must implement solve()")
    
    @abstractmethod
    def can_solve(self, request: ScheduleRequest) -> Tuple[bool, Optional[str]]:
        """
        Check if this strategy can solve the given request
        
        Args:
            request: The scheduling request
            
        Returns:
            A tuple of (can_solve, reason) where reason is None if can_solve is True,
            otherwise it contains a string explaining why the strategy cannot solve the request
        """
        raise NotImplementedError("Subclasses must implement can_solve()")
    
    @abstractmethod
    def get_capabilities(self) -> Set[str]:
        """
        Get the capabilities of this strategy
        
        Returns:
            A set of capability strings
        """
        raise NotImplementedError("Subclasses must implement get_capabilities()")
