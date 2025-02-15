from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from ortools.sat.python import cp_model

from ..core import ConstraintManager, Constraint, SchedulerContext, config

@dataclass
class ConstraintViolation:
    """Represents a constraint violation for validation"""
    message: str
    severity: str  # 'error' or 'warning'
    context: Dict[str, Any]

class BaseConstraint(ABC):
    """
    Abstract base class for implementing constraints.
    All constraints must inherit from this class and implement apply().
    """
    def __init__(
        self,
        name: str,
        enabled: bool = True,
        priority: int = 1,
        weight: Optional[int] = None
    ):
        self._name = name
        self._enabled = enabled
        self._priority = priority
        self._weight = weight or config.WEIGHTS.get(name, 1000)
        
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    @property
    def priority(self) -> int:
        return self._priority
        
    @property
    def weight(self) -> int:
        return self._weight
    
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable this constraint"""
        self._enabled = enabled
        
    def set_weight(self, weight: int) -> None:
        """Update the weight of this constraint"""
        self._weight = weight
        
    @abstractmethod
    def apply(self, context: SchedulerContext) -> None:
        """
        Apply this constraint to the CP-SAT model.
        This method must be implemented by all constraint classes.
        """
        pass
    
    def validate(
        self,
        assignments: List[Dict[str, Any]],
        context: SchedulerContext
    ) -> List[ConstraintViolation]:
        """
        Validate that assignments satisfy this constraint.
        Returns list of violations found.
        """
        if not self.enabled:
            return []
        return self._validate_impl(assignments, context)
    
    def _validate_impl(
        self,
        assignments: List[Dict[str, Any]],
        context: SchedulerContext
    ) -> List[ConstraintViolation]:
        """
        Implementation method for validation.
        Override this in constraint subclasses.
        """
        return []
