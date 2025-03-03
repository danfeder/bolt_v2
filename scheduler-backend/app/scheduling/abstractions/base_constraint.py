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
        self._category = "general"
        self._description = self.__doc__ or f"Constraint: {name}"
    
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
    
    @property
    def category(self) -> str:
        """Get the constraint category"""
        return self._category
    
    @category.setter
    def category(self, category: str) -> None:
        """Set the constraint category"""
        self._category = category
    
    @property
    def description(self) -> str:
        """Get the constraint description"""
        return self._description
    
    @description.setter
    def description(self, description: str) -> None:
        """Set the constraint description"""
        self._description = description
    
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
    
    def create_violation(
        self,
        message: str,
        severity: ConstraintSeverity = ConstraintSeverity.ERROR,
        context: Optional[Dict[str, Any]] = None
    ) -> ConstraintViolation:
        """
        Create a constraint violation
        
        This is a convenience method for creating standardized constraint
        violations with the appropriate constraint name.
        
        Args:
            message: The violation message
            severity: The violation severity
            context: Additional context information for the violation
            
        Returns:
            A new constraint violation
        """
        return ConstraintViolation(
            constraint_name=self.name,
            message=message,
            severity=severity,
            context=context or {}
        )
    
    def create_info_violation(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ConstraintViolation:
        """Create an informational (non-violation) message"""
        return self.create_violation(
            message=message,
            severity=ConstraintSeverity.INFO,
            context=context
        )
    
    def create_warning_violation(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ConstraintViolation:
        """Create a warning violation (minor issue)"""
        return self.create_violation(
            message=message,
            severity=ConstraintSeverity.WARNING,
            context=context
        )
    
    def create_error_violation(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ConstraintViolation:
        """Create an error violation (significant issue)"""
        return self.create_violation(
            message=message,
            severity=ConstraintSeverity.ERROR,
            context=context
        )
    
    def create_critical_violation(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ConstraintViolation:
        """Create a critical violation (solution is invalid)"""
        return self.create_violation(
            message=message,
            severity=ConstraintSeverity.CRITICAL,
            context=context
        )
    
    def format_violation_context(
        self,
        assignment: Dict[str, Any],
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format an assignment and additional context into a standardized
        constraint violation context dictionary
        
        Args:
            assignment: The assignment related to the violation
            additional_context: Additional context information
            
        Returns:
            A context dictionary for a constraint violation
        """
        context = {
            "assignment": {
                "name": assignment.get("name", ""),
                "period": assignment.get("period", ""),
                "date": assignment.get("date", ""),
                "instructor": assignment.get("instructor", ""),
            }
        }
        
        if additional_context:
            context.update(additional_context)
            
        return context
    
    def __str__(self) -> str:
        """String representation of the constraint"""
        weight_str = "Hard" if self.is_hard_constraint else f"Soft (weight={self.weight})"
        enabled_str = "Enabled" if self.enabled else "Disabled"
        return f"{self.name} ({weight_str}, {enabled_str}, Category: {self.category})"


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
        self._relaxation_level = max(0, min(level, self._max_relaxation_level))
    
    @property
    def max_relaxation_level(self) -> int:
        """Get the maximum possible relaxation level"""
        return self._max_relaxation_level
    
    def get_relaxed_weight(self) -> Optional[float]:
        """
        Get the weight adjusted for the current relaxation level
        
        If this is a hard constraint (weight is None) and the relaxation level
        is greater than 0, it will be converted to a soft constraint with a
        weight based on the relaxation level.
        
        Returns:
            The relaxed weight
        """
        if self.relaxation_level == 0:
            return self.weight
            
        # If this is a hard constraint and relaxation level > 0,
        # convert it to a soft constraint with a high weight
        if self.is_hard_constraint:
            # Start with a high weight and reduce it as relaxation level increases
            return 10000 / (1 + self.relaxation_level)
            
        # For soft constraints, reduce the weight as relaxation level increases
        return self.weight / (1 + self.relaxation_level)
    
    def create_relaxable_violation(
        self,
        message: str,
        severity: ConstraintSeverity,
        context: Optional[Dict[str, Any]] = None,
        relaxation_info: Optional[Dict[str, Any]] = None
    ) -> ConstraintViolation:
        """
        Create a constraint violation with relaxation information
        
        Args:
            message: The violation message
            severity: The violation severity
            context: Additional context information
            relaxation_info: Information about the relaxation
            
        Returns:
            A constraint violation with relaxation information
        """
        context_with_relaxation = context.copy() if context else {}
        
        # Add relaxation information to the context
        if relaxation_info:
            context_with_relaxation["relaxation"] = relaxation_info
        else:
            context_with_relaxation["relaxation"] = {
                "current_level": self.relaxation_level,
                "max_level": self.max_relaxation_level,
                "original_weight": self.weight,
                "relaxed_weight": self.get_relaxed_weight()
            }
            
        return self.create_violation(
            message=message,
            severity=severity,
            context=context_with_relaxation
        )
    
    def __str__(self) -> str:
        """String representation of the relaxable constraint"""
        base_str = super().__str__()
        relaxation_str = f"Relaxation: {self.relaxation_level}/{self.max_relaxation_level}"
        return f"{base_str}, {relaxation_str}"
