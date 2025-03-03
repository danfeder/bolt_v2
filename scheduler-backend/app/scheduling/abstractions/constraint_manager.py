"""
Constraint Management System

This module defines the interfaces and classes for the constraint management system.
It provides a standardized way to define, apply, and validate constraints.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Dict, Any, Optional, Protocol, Set, Type, Tuple
import logging

logger = logging.getLogger(__name__)


class ConstraintSeverity(Enum):
    """Severity levels for constraint violations"""
    INFO = auto()      # Informational only, not a violation
    WARNING = auto()   # Minor violation, solution is still acceptable
    ERROR = auto()     # Significant violation, solution quality is degraded
    CRITICAL = auto()  # Critical violation, solution is invalid


@dataclass
class ConstraintViolation:
    """
    Represents a violation of a constraint
    
    This class encapsulates information about a constraint violation,
    including the constraint that was violated, the severity, a message,
    and context information for debugging.
    """
    constraint_name: str
    message: str
    severity: ConstraintSeverity
    context: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        """String representation of the violation"""
        return f"{self.severity.name} in {self.constraint_name}: {self.message}"


class Constraint(Protocol):
    """Protocol defining the interface for constraints"""
    
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
    
    def apply(self, context: Any) -> None:
        """Apply the constraint to the context"""
        ...
    
    def validate(self, assignments: List[Dict[str, Any]], context: Any) -> List[ConstraintViolation]:
        """Validate the constraint against assignments"""
        ...


class RelaxableConstraint(Protocol):
    """Protocol for constraints that can be relaxed"""
    
    @property
    def relaxation_level(self) -> int:
        """Get the current relaxation level"""
        ...
    
    @relaxation_level.setter
    def relaxation_level(self, level: int) -> None:
        """Set the relaxation level"""
        ...
    
    @property
    def max_relaxation_level(self) -> int:
        """Get the maximum possible relaxation level"""
        ...
    
    def get_relaxed_weight(self) -> float:
        """Get the weight adjusted for the current relaxation level"""
        ...


class ConstraintFactory(ABC):
    """
    Abstract factory for creating constraints
    
    This class defines the interface for factories that create constraints.
    Concrete factories will create specific types of constraints.
    """
    
    @abstractmethod
    def create(self, name: str, **kwargs) -> Constraint:
        """
        Create a constraint
        
        Args:
            name: The name of the constraint
            **kwargs: Additional parameters for the constraint
            
        Returns:
            A new constraint instance
        """
        raise NotImplementedError("Subclasses must implement create()")


class ConstraintRegistry:
    """
    Registry for constraint factories
    
    This class maintains a registry of constraint factories and provides
    methods for registering and retrieving them.
    """
    
    def __init__(self):
        """Initialize the registry"""
        self._factories: Dict[str, ConstraintFactory] = {}
    
    def register(self, constraint_type: str, factory: ConstraintFactory) -> None:
        """
        Register a factory for a constraint type
        
        Args:
            constraint_type: The type of constraint
            factory: The factory for creating constraints of this type
        """
        self._factories[constraint_type] = factory
    
    def get_factory(self, constraint_type: str) -> Optional[ConstraintFactory]:
        """
        Get the factory for a constraint type
        
        Args:
            constraint_type: The type of constraint
            
        Returns:
            The factory for the constraint type, or None if not found
        """
        return self._factories.get(constraint_type)
    
    def create_constraint(self, constraint_type: str, name: str, **kwargs) -> Optional[Constraint]:
        """
        Create a constraint of the specified type
        
        Args:
            constraint_type: The type of constraint
            name: The name of the constraint
            **kwargs: Additional parameters for the constraint
            
        Returns:
            A new constraint instance, or None if the factory is not found
        """
        factory = self.get_factory(constraint_type)
        if factory:
            return factory.create(name, **kwargs)
        else:
            logger.warning(f"No factory found for constraint type: {constraint_type}")
            return None
    
    def get_registered_types(self) -> Set[str]:
        """
        Get the set of registered constraint types
        
        Returns:
            A set of registered constraint types
        """
        return set(self._factories.keys())


class EnhancedConstraintManager:
    """
    Enhanced constraint manager for applying and validating constraints
    
    This class manages a collection of constraints and provides methods
    for applying and validating them. It utilizes the ConstraintFactory
    for constraint creation and management.
    """
    
    def __init__(self, constraint_factory=None):
        """
        Initialize the manager
        
        Args:
            constraint_factory: Optional constraint factory to use
                If not provided, the global factory will be used
        """
        self._constraints: List[Constraint] = []
        self._registry = ConstraintRegistry()
        
        # Use the provided factory or get the global one
        from .constraint_factory import get_constraint_factory
        self._factory = constraint_factory or get_constraint_factory()
    
    @property
    def registry(self) -> ConstraintRegistry:
        """Get the constraint registry"""
        return self._registry
    
    @property
    def factory(self):
        """Get the constraint factory"""
        return self._factory
    
    def add_constraint(self, constraint: Constraint) -> None:
        """
        Add a constraint to the manager
        
        Args:
            constraint: The constraint to add
        """
        # Remove any existing constraint with the same name
        self.remove_constraint(constraint.name)
        self._constraints.append(constraint)
        logger.debug(f"Added constraint: {constraint.name}")
    
    def create_and_add_constraint(
        self, 
        name: str, 
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[Constraint]:
        """
        Create a constraint by name and add it to the manager
        
        Args:
            name: The name of the constraint to create
            config: Optional configuration for the constraint
            
        Returns:
            The created constraint, or None if creation failed
        """
        constraint = self._factory.create_constraint(name, config)
        if constraint:
            self.add_constraint(constraint)
            return constraint
        return None
    
    def create_and_add_constraints_by_category(
        self, 
        category: str, 
        config: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> List[Constraint]:
        """
        Create and add all constraints in a category
        
        Args:
            category: The category of constraints to create
            config: Optional configuration for the constraints,
                   keyed by constraint name
                
        Returns:
            The list of created constraints
        """
        constraints = []
        constraint_names = self._factory.get_constraint_names_by_category(category)
        
        for name in constraint_names:
            constraint_config = config.get(name, {}) if config else {}
            constraint = self.create_and_add_constraint(name, constraint_config)
            if constraint:
                constraints.append(constraint)
                
        return constraints
    
    def remove_constraint(self, name: str) -> None:
        """
        Remove a constraint by name
        
        Args:
            name: The name of the constraint to remove
        """
        initial_count = len(self._constraints)
        self._constraints = [c for c in self._constraints if c.name != name]
        if len(self._constraints) < initial_count:
            logger.debug(f"Removed constraint: {name}")
    
    def get_constraint(self, name: str) -> Optional[Constraint]:
        """
        Get a constraint by name
        
        Args:
            name: The name of the constraint
            
        Returns:
            The constraint, or None if not found
        """
        for constraint in self._constraints:
            if constraint.name == name:
                return constraint
        return None
    
    def get_all_constraints(self) -> List[Constraint]:
        """
        Get all constraints
        
        Returns:
            List of all constraints
        """
        return self._constraints.copy()
    
    def get_enabled_constraints(self) -> List[Constraint]:
        """
        Get all enabled constraints
        
        Returns:
            List of enabled constraints
        """
        return [c for c in self._constraints if c.enabled]
    
    def get_constraints_by_category(self, category: str) -> List[Constraint]:
        """
        Get all constraints in a category
        
        Args:
            category: The category to filter by
            
        Returns:
            List of constraints in the category
        """
        # Get all constraints that are registered in this category
        constraint_names = set(self._factory.get_constraint_names_by_category(category))
        return [c for c in self._constraints if c.name in constraint_names]
    
    def get_enabled_constraints_by_category(self, category: str) -> List[Constraint]:
        """
        Get all enabled constraints in a category
        
        Args:
            category: The category to filter by
            
        Returns:
            List of enabled constraints in the category
        """
        constraints = self.get_constraints_by_category(category)
        return [c for c in constraints if c.enabled]
    
    def validate_constraint_compatibility(self) -> List[str]:
        """
        Validate that all enabled constraints are compatible with each other
        
        Returns:
            List of error messages, empty if all constraints are compatible
        """
        enabled_constraint_names = [c.name for c in self.get_enabled_constraints()]
        return self._factory.validate_constraints_compatibility(enabled_constraint_names)
    
    def apply_all(self, context: Any) -> None:
        """
        Apply all enabled constraints to the context
        
        This method applies all enabled constraints to the context,
        in priority order (hard constraints first, then soft constraints).
        
        Args:
            context: The context to apply constraints to
        """
        # Validate constraint compatibility first
        compatibility_errors = self.validate_constraint_compatibility()
        if compatibility_errors:
            for error in compatibility_errors:
                logger.warning(f"Constraint compatibility issue: {error}")
        
        # First apply hard constraints (weight is None)
        for constraint in self.get_enabled_constraints():
            if constraint.weight is None:
                try:
                    logger.debug(f"Applying hard constraint: {constraint.name}")
                    constraint.apply(context)
                except Exception as e:
                    logger.error(f"Error applying constraint {constraint.name}: {e}")
        
        # Then apply soft constraints (weight is not None)
        for constraint in self.get_enabled_constraints():
            if constraint.weight is not None:
                try:
                    logger.debug(f"Applying soft constraint: {constraint.name} (weight={constraint.weight})")
                    constraint.apply(context)
                except Exception as e:
                    logger.error(f"Error applying constraint {constraint.name}: {e}")
    
    def validate_all(
        self, 
        assignments: List[Dict[str, Any]], 
        context: Any,
        fail_fast: bool = False
    ) -> Tuple[bool, List[ConstraintViolation]]:
        """
        Validate assignments against all enabled constraints
        
        This method validates the assignments against all enabled constraints
        and returns a list of constraint violations.
        
        Args:
            assignments: The assignments to validate
            context: The context for validation
            fail_fast: If True, stops validation at the first critical violation
            
        Returns:
            A tuple of (is_valid, violations)
        """
        all_violations: List[ConstraintViolation] = []
        is_valid = True
        
        # Validate constraint compatibility first
        compatibility_errors = self.validate_constraint_compatibility()
        for error in compatibility_errors:
            all_violations.append(
                ConstraintViolation(
                    constraint_name="constraint_compatibility",
                    message=error,
                    severity=ConstraintSeverity.WARNING
                )
            )
        
        # First validate hard constraints
        hard_constraints = [c for c in self.get_enabled_constraints() if c.weight is None]
        for constraint in hard_constraints:
            try:
                violations = constraint.validate(assignments, context)
                all_violations.extend(violations)
                
                # Check if there are any critical violations
                for violation in violations:
                    if violation.severity == ConstraintSeverity.CRITICAL:
                        is_valid = False
                        if fail_fast:
                            return is_valid, all_violations
                        
            except Exception as e:
                logger.error(f"Error validating constraint {constraint.name}: {e}")
                all_violations.append(
                    ConstraintViolation(
                        constraint_name=constraint.name,
                        message=f"Error during validation: {str(e)}",
                        severity=ConstraintSeverity.ERROR
                    )
                )
                
        # Then validate soft constraints
        soft_constraints = [c for c in self.get_enabled_constraints() if c.weight is not None]
        for constraint in soft_constraints:
            try:
                violations = constraint.validate(assignments, context)
                all_violations.extend(violations)
                        
            except Exception as e:
                logger.error(f"Error validating constraint {constraint.name}: {e}")
                all_violations.append(
                    ConstraintViolation(
                        constraint_name=constraint.name,
                        message=f"Error during validation: {str(e)}",
                        severity=ConstraintSeverity.ERROR
                    )
                )
        
        return is_valid, all_violations
    
    def validate_by_category(
        self,
        category: str,
        assignments: List[Dict[str, Any]],
        context: Any
    ) -> Tuple[bool, List[ConstraintViolation]]:
        """
        Validate assignments against all enabled constraints in a category
        
        Args:
            category: The category of constraints to validate
            assignments: The assignments to validate
            context: The context for validation
            
        Returns:
            A tuple of (is_valid, violations)
        """
        all_violations: List[ConstraintViolation] = []
        is_valid = True
        
        for constraint in self.get_enabled_constraints_by_category(category):
            try:
                violations = constraint.validate(assignments, context)
                all_violations.extend(violations)
                
                # Check if there are any critical violations
                for violation in violations:
                    if violation.severity == ConstraintSeverity.CRITICAL:
                        is_valid = False
                        
            except Exception as e:
                logger.error(f"Error validating constraint {constraint.name}: {e}")
                all_violations.append(
                    ConstraintViolation(
                        constraint_name=constraint.name,
                        message=f"Error during validation: {str(e)}",
                        severity=ConstraintSeverity.ERROR
                    )
                )
        
        return is_valid, all_violations
