"""Runtime constraint relaxation system for intelligent constraint handling."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Type, Set
import logging

from ..core import SchedulerContext
from .base import BaseConstraint, ConstraintViolation

logger = logging.getLogger(__name__)

class RelaxationLevel(Enum):
    """Levels of constraint relaxation from none to maximum."""
    NONE = 0        # No relaxation allowed
    MINIMAL = 1     # Minimal relaxation allowed
    MODERATE = 2    # Moderate relaxation allowed
    SIGNIFICANT = 3 # Significant relaxation allowed
    MAXIMUM = 4     # Maximum relaxation allowed

@dataclass
class RelaxationResult:
    """Result of a relaxation operation."""
    constraint_name: str
    original_level: RelaxationLevel
    applied_level: RelaxationLevel
    success: bool
    message: str
    relaxation_params: Dict[str, Any] = field(default_factory=dict)

class RelaxableConstraint(BaseConstraint):
    """
    Base class for constraints that support runtime relaxation.
    
    This extends BaseConstraint with relaxation capabilities.
    """
    
    def __init__(
        self, 
        name: str, 
        enabled: bool = True, 
        priority: int = 1, 
        weight: Optional[float] = None,
        can_relax: bool = True,
        relaxation_priority: int = 1,
        never_relax: bool = False
    ):
        """
        Initialize a relaxable constraint.
        
        Args:
            name: Unique name for this constraint
            enabled: Whether this constraint is enabled
            priority: Priority level (lower is higher priority)
            weight: Weight for soft constraints (None for hard constraints)
            can_relax: Whether this constraint can be relaxed at runtime
            relaxation_priority: Priority for relaxation (higher = relax later)
            never_relax: Flag to prevent relaxation regardless of other settings
        """
        super().__init__(name, enabled, priority, weight)
        self.can_relax = can_relax
        self.relaxation_priority = relaxation_priority
        self.never_relax = never_relax
        self.current_relaxation_level = RelaxationLevel.NONE
        self.relaxation_params: Dict[str, Any] = {}
        
    def relax(self, level: RelaxationLevel, context: Optional[SchedulerContext] = None) -> RelaxationResult:
        """
        Attempt to relax this constraint to the specified level.
        
        Args:
            level: The relaxation level to apply
            context: Optional scheduler context for reference
            
        Returns:
            RelaxationResult with details about the relaxation
        """
        if self.never_relax:
            return RelaxationResult(
                constraint_name=self.name,
                original_level=self.current_relaxation_level,
                applied_level=self.current_relaxation_level,
                success=False,
                message=f"Constraint {self.name} is marked as never_relax",
                relaxation_params=self.relaxation_params.copy()
            )
            
        if not self.can_relax:
            return RelaxationResult(
                constraint_name=self.name,
                original_level=self.current_relaxation_level,
                applied_level=self.current_relaxation_level,
                success=False,
                message=f"Constraint {self.name} does not support relaxation",
                relaxation_params=self.relaxation_params.copy()
            )
            
        # Store original level for reporting
        original_level = self.current_relaxation_level
        
        # Only allow increasing relaxation
        if level.value < self.current_relaxation_level.value:
            return RelaxationResult(
                constraint_name=self.name,
                original_level=original_level,
                applied_level=self.current_relaxation_level,
                success=False,
                message=f"Cannot decrease relaxation level from {self.current_relaxation_level} to {level}",
                relaxation_params=self.relaxation_params.copy()
            )
            
        # Apply relaxation logic (subclasses should override this)
        success, message, params = self._apply_relaxation(level, context)
        
        if success:
            self.current_relaxation_level = level
            self.relaxation_params.update(params)
            
        return RelaxationResult(
            constraint_name=self.name,
            original_level=original_level,
            applied_level=self.current_relaxation_level,
            success=success,
            message=message,
            relaxation_params=self.relaxation_params.copy()
        )
        
    def _apply_relaxation(
        self, 
        level: RelaxationLevel, 
        context: Optional[SchedulerContext]
    ) -> tuple[bool, str, Dict[str, Any]]:
        """
        Apply relaxation logic specific to this constraint.
        
        Args:
            level: The relaxation level to apply
            context: Optional scheduler context for reference
            
        Returns:
            Tuple of (success, message, params)
        """
        # Default implementation (subclasses should override this)
        return False, "Relaxation not implemented for this constraint", {}
        
    def get_description(self) -> Dict[str, Any]:
        """Get a description of this constraint's current state."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "priority": self.priority,
            "weight": self.weight,
            "can_relax": self.can_relax,
            "relaxation_priority": self.relaxation_priority,
            "never_relax": self.never_relax,
            "current_relaxation_level": self.current_relaxation_level.name,
            "relaxation_params": self.relaxation_params.copy()
        }
        
class RelaxationController:
    """
    Controls the relaxation process for a set of constraints.
    
    This class manages which constraints to relax, in what order,
    and to what level, based on priority and other factors.
    """
    
    def __init__(self):
        """Initialize the relaxation controller."""
        self.relaxable_constraints: Dict[str, RelaxableConstraint] = {}
        self.relaxation_results: List[RelaxationResult] = []
        self.never_relax_constraints: Set[str] = set()
        
    def register_constraint(self, constraint: RelaxableConstraint) -> None:
        """
        Register a constraint with the relaxation controller.
        
        Args:
            constraint: The constraint to register
        """
        self.relaxable_constraints[constraint.name] = constraint
        
        if constraint.never_relax:
            self.never_relax_constraints.add(constraint.name)
            
    def relax_constraints(
        self, 
        target_level: RelaxationLevel, 
        context: Optional[SchedulerContext] = None,
        constraint_names: Optional[List[str]] = None
    ) -> List[RelaxationResult]:
        """
        Relax constraints to the target level.
        
        Args:
            target_level: The relaxation level to apply
            context: Optional scheduler context for reference
            constraint_names: Optional list of constraint names to relax
                            (if None, relax all eligible constraints)
            
        Returns:
            List of RelaxationResult objects
        """
        results: List[RelaxationResult] = []
        
        # Get constraints to relax
        constraints_to_relax = []
        if constraint_names:
            # Specific constraints requested
            for name in constraint_names:
                if name in self.relaxable_constraints:
                    constraints_to_relax.append(self.relaxable_constraints[name])
                else:
                    logger.warning(f"Constraint {name} not found for relaxation")
        else:
            # All eligible constraints
            constraints_to_relax = [
                c for c in self.relaxable_constraints.values()
                if c.can_relax and not c.never_relax and c.enabled
            ]
            
        # Sort by relaxation priority (higher relaxation_priority = relax later)
        constraints_to_relax.sort(key=lambda c: c.relaxation_priority)
        
        # Apply relaxation in order
        for constraint in constraints_to_relax:
            result = constraint.relax(target_level, context)
            results.append(result)
            logger.info(
                f"Relaxed constraint {constraint.name} from {result.original_level} to "
                f"{result.applied_level}: {result.success} - {result.message}"
            )
            
        # Store results
        self.relaxation_results.extend(results)
        
        return results
        
    def get_relaxation_status(self) -> Dict[str, Any]:
        """Get the current relaxation status of all constraints."""
        status = {
            "constraints": {
                name: constraint.get_description()
                for name, constraint in self.relaxable_constraints.items()
            },
            "never_relax_constraints": list(self.never_relax_constraints),
            "relaxation_history": [
                {
                    "constraint": result.constraint_name,
                    "original_level": result.original_level.name,
                    "applied_level": result.applied_level.name,
                    "success": result.success,
                    "message": result.message,
                    "params": result.relaxation_params
                }
                for result in self.relaxation_results
            ]
        }
        return status
        
    def reset_relaxation(self) -> None:
        """Reset all constraints to no relaxation."""
        for constraint in self.relaxable_constraints.values():
            constraint.current_relaxation_level = RelaxationLevel.NONE
            constraint.relaxation_params = {}
            
        self.relaxation_results.clear()