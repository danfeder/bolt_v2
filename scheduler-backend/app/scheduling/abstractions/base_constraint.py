"""
Base Constraint Classes

This module defines the base classes for constraints in the scheduler system.
These classes implement the constraint protocols and provide common functionality.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Protocol, Set, Type
import logging

from .constraint_manager import (
    Constraint,
    ConstraintViolation,
    ConstraintSeverity,
    RelaxableConstraint
)
from .context import SchedulerContext

logger = logging.getLogger(__name__)


class BaseConstraint(ABC):
    """
    Base class for all constraints
    
    This class implements the Constraint protocol and provides common
    functionality for all constraints.
    """
    
    def __init__(self, name: str, enabled: bool = True, weight: Optional[float] = None):
        """
        Initialize the constraint
        
        Args:
            name: The constraint name
            enabled: Whether the constraint is enabled
            weight: The constraint weight (None for hard constraints)
        """
        self._name = name
        self._enabled = enabled
        self._weight = weight
    
    @property
    def name(self) -> str:
        """Get the constraint name"""
        return self._name
    
    @property
    def enabled(self) -> bool:
        """Check if the constraint is enabled"""
        return self._enabled
    
    @enabled.setter
    def enabled(self, enabled: bool) -> None:
        """Set whether the constraint is enabled"""
        self._enabled = enabled
    
    @property
    def weight(self) -> Optional[float]:
        """Get the constraint weight (None for hard constraints)"""
        return self._weight
    
    @weight.setter
    def weight(self, weight: Optional[float]) -> None:
        """Set the constraint weight"""
        self._weight = weight
    
    @property
    def is_hard_constraint(self) -> bool:
        """Check if this is a hard constraint"""
        return self._weight is None
    
    @abstractmethod
    def apply(self, context: SchedulerContext) -> None:
        """
        Apply the constraint to the scheduler context
        
        Args:
            context: The scheduler context
        """
        raise NotImplementedError("Subclasses must implement apply()")
    
    @abstractmethod
    def validate(
        self, 
        assignments: List[Dict[str, Any]], 
        context: SchedulerContext
    ) -> List[ConstraintViolation]:
        """
        Validate the constraint against assignments
        
        Args:
            assignments: The assignments to validate
            context: The scheduler context
            
        Returns:
            List of constraint violations
        """
        raise NotImplementedError("Subclasses must implement validate()")
    
    def __str__(self) -> str:
        """String representation of the constraint"""
        constraint_type = "Hard" if self.is_hard_constraint else "Soft"
        enabled_status = "Enabled" if self.enabled else "Disabled"
        weight_str = "" if self.is_hard_constraint else f", weight={self.weight}"
        return f"{constraint_type} constraint '{self.name}' ({enabled_status}{weight_str})"


class BaseRelaxableConstraint(BaseConstraint):
    """
    Base class for relaxable constraints
    
    This class implements the RelaxableConstraint protocol and provides common
    functionality for constraints that can be relaxed.
    """
    
    def __init__(
        self, 
        name: str, 
        enabled: bool = True, 
        weight: Optional[float] = None,
        max_relaxation_level: int = 3
    ):
        """
        Initialize the relaxable constraint
        
        Args:
            name: The constraint name
            enabled: Whether the constraint is enabled
            weight: The constraint weight (None for hard constraints)
            max_relaxation_level: The maximum relaxation level
        """
        super().__init__(name, enabled, weight)
        self._relaxation_level = 0
        self._max_relaxation_level = max_relaxation_level
    
    @property
    def relaxation_level(self) -> int:
        """Get the current relaxation level"""
        return self._relaxation_level
    
    @relaxation_level.setter
    def relaxation_level(self, level: int) -> None:
        """
        Set the relaxation level
        
        Args:
            level: The relaxation level
        """
        # Ensure the relaxation level is within bounds
        self._relaxation_level = max(0, min(level, self._max_relaxation_level))
    
    @property
    def max_relaxation_level(self) -> int:
        """Get the maximum possible relaxation level"""
        return self._max_relaxation_level
    
    def get_relaxed_weight(self) -> float:
        """
        Get the weight adjusted for the current relaxation level
        
        If this is a hard constraint (weight is None) and the relaxation level
        is greater than 0, it will be converted to a soft constraint with a
        weight based on the relaxation level.
        
        Returns:
            The relaxed weight
        """
        # If this is a hard constraint and the relaxation level is 0, it remains a hard constraint
        if self.is_hard_constraint and self._relaxation_level == 0:
            # For use in cost functions, hard constraints should have a very high weight
            return 1_000_000
        
        # If this is a hard constraint and the relaxation level is > 0, convert to soft
        if self.is_hard_constraint:
            # Start with a high weight and reduce it based on the relaxation level
            base_weight = 10_000
            return base_weight * (1 - self._relaxation_level / (self._max_relaxation_level + 1))
        
        # For soft constraints, reduce the weight based on the relaxation level
        if self._weight is None:
            return 0  # This should not happen, but just in case
        
        return self._weight * (1 - self._relaxation_level / (self._max_relaxation_level + 1))
    
    def __str__(self) -> str:
        """String representation of the relaxable constraint"""
        base_str = super().__str__()
        relaxation_str = f", relaxation={self._relaxation_level}/{self._max_relaxation_level}"
        return f"{base_str}{relaxation_str}"
