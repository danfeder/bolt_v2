"""Base classes for scheduling constraints"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class ConstraintViolation:
    """Represents a violation of a scheduling constraint"""
    
    message: str
    severity: str
    context: Dict[str, Any]


class BaseConstraint:
    """
    Base class for scheduling constraints.
    
    All constraints should inherit from this and implement apply() and validate().
    """
    
    def __init__(self, name: str, enabled: bool = True, priority: int = 1, weight: Optional[float] = None):
        """
        Initialize a constraint.
        
        Args:
            name: Unique name for this constraint
            enabled: Whether this constraint is enabled
            priority: Priority level (lower is higher priority)
            weight: Weight for soft constraints (None for hard constraints)
        """
        self.name = name
        self.enabled = enabled  # Changed from property to instance variable
        self.priority = priority
        self.weight = weight
        
    def apply(self, context: 'SchedulerContext') -> None:  # type: ignore # noqa: F821
        """
        Apply this constraint to the model.
        
        Args:
            context: The scheduler context containing model and variables
        """
        raise NotImplementedError("Subclasses must implement apply()")
        
    def validate(
        self,
        assignments: List[Dict[str, Any]],
        context: 'SchedulerContext'  # type: ignore # noqa: F821
    ) -> List[ConstraintViolation]:
        """
        Validate a solution against this constraint.
        
        Args:
            assignments: The assignments to validate
            context: The scheduler context
            
        Returns:
            List of constraint violations
        """
        raise NotImplementedError("Subclasses must implement validate()")
