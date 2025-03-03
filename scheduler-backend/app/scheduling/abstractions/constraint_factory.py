"""
Constraint Factory Module

This module provides a factory for creating constraints based on configuration.
It abstracts the creation and initialization of constraints, making it easier
to modify constraint behavior without changing the code that uses them.
"""

from typing import Dict, Any, List, Optional, Type, ClassVar, Protocol, Set
import logging

from ..core import Constraint, SchedulerContext
from ..constraints.base import BaseConstraint

logger = logging.getLogger(__name__)


class ConstraintInfo:
    """Information about a constraint registration"""
    def __init__(
        self, 
        constraint_type: Type[Constraint],
        name: str,
        description: str = "",
        default_enabled: bool = True,
        default_weight: Optional[int] = None,
        is_relaxable: bool = False,
        category: str = "general"
    ):
        self.constraint_type = constraint_type
        self.name = name
        self.description = description
        self.default_enabled = default_enabled
        self.default_weight = default_weight
        self.is_relaxable = is_relaxable
        self.category = category
        
        # Set that contains the names of other constraints that are incompatible with this one
        self.incompatible_with: Set[str] = set()
        
        # Set that contains the names of other constraints that are required by this one
        self.requires: Set[str] = set()


class ConstraintFactory:
    """
    Factory for creating constraint instances
    
    This class manages constraint registrations and creates configured
    constraint instances based on configuration.
    """
    
    def __init__(self):
        """Initialize the factory"""
        self._registrations: Dict[str, ConstraintInfo] = {}
        # Map of category to constraint names for efficient retrieval
        self._categories: Dict[str, Set[str]] = {}
    
    def register(
        self,
        constraint_type: Type[Constraint],
        name: Optional[str] = None,
        description: str = "",
        default_enabled: bool = True,
        default_weight: Optional[int] = None,
        is_relaxable: bool = False,
        category: str = "general"
    ) -> None:
        """
        Register a constraint type
        
        Args:
            constraint_type: The constraint type to register
            name: The name to register the constraint with (defaults to constraint class name)
            description: A description of the constraint
            default_enabled: Whether the constraint is enabled by default
            default_weight: The default weight for the constraint (None for hard constraints)
            is_relaxable: Whether the constraint can be relaxed
            category: The category of the constraint for organization
        """
        if name is None:
            name = constraint_type.__name__.lower()
        
        # Register the constraint info
        self._registrations[name] = ConstraintInfo(
            constraint_type=constraint_type,
            name=name,
            description=description,
            default_enabled=default_enabled,
            default_weight=default_weight,
            is_relaxable=is_relaxable,
            category=category
        )
        
        # Add to category map
        if category not in self._categories:
            self._categories[category] = set()
        self._categories[category].add(name)
        
        logger.debug(f"Registered constraint: {name} in category {category}")
    
    def create_constraint(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[Constraint]:
        """
        Create a constraint by name
        
        Args:
            name: The name of the constraint to create
            config: Optional configuration for the constraint
            
        Returns:
            A new constraint instance, or None if the constraint is not registered
        """
        if name not in self._registrations:
            logger.warning(f"Unknown constraint: {name}")
            return None
        
        # Create configuration dict with default values if not provided
        if config is None:
            config = {}
            
        # Get constraint info
        info = self._registrations[name]
        
        # Create a new constraint instance
        constraint_args = {}
        
        # Set enabled if provided, otherwise use default
        if "enabled" in config:
            constraint_args["enabled"] = config["enabled"]
        else:
            constraint_args["enabled"] = info.default_enabled
            
        # Set weight if provided, otherwise use default
        if "weight" in config:
            constraint_args["weight"] = config["weight"]
        elif info.default_weight is not None:
            constraint_args["weight"] = info.default_weight
            
        # Pass any additional configuration parameters
        for key, value in config.items():
            if key not in ["enabled", "weight"]:
                constraint_args[key] = value
                
        # Create the constraint
        try:
            constraint = info.constraint_type(name=name, **constraint_args)
            return constraint
        except Exception as e:
            logger.error(f"Error creating constraint {name}: {e}")
            return None
    
    def get_constraint_info(self, name: str) -> Optional[ConstraintInfo]:
        """
        Get information about a registered constraint
        
        Args:
            name: The name of the constraint
            
        Returns:
            The constraint info, or None if the constraint is not registered
        """
        return self._registrations.get(name)
    
    def get_all_constraint_info(self) -> Dict[str, ConstraintInfo]:
        """
        Get information about all registered constraints
        
        Returns:
            A dictionary mapping constraint names to their info
        """
        return self._registrations.copy()
        
    def get_constraint_names(self) -> List[str]:
        """
        Get the names of all registered constraints
        
        Returns:
            A list of constraint names
        """
        return list(self._registrations.keys())
        
    def get_constraint_names_by_category(self, category: str) -> List[str]:
        """
        Get the names of constraints in a category
        
        Args:
            category: The category to get constraints for
            
        Returns:
            A list of constraint names in the category
        """
        return list(self._categories.get(category, set()))
        
    def get_all_categories(self) -> List[str]:
        """
        Get all constraint categories
        
        Returns:
            A list of category names
        """
        return list(self._categories.keys())
    
    def set_incompatible_constraints(self, constraint_name: str, incompatible_with: List[str]) -> None:
        """
        Set constraints that are incompatible with a constraint
        
        Args:
            constraint_name: The name of the constraint
            incompatible_with: List of constraint names that are incompatible
        """
        if constraint_name not in self._registrations:
            logger.warning(f"Cannot set incompatibilities for unknown constraint: {constraint_name}")
            return
            
        self._registrations[constraint_name].incompatible_with = set(incompatible_with)
        
    def set_required_constraints(self, constraint_name: str, requires: List[str]) -> None:
        """
        Set constraints that are required by a constraint
        
        Args:
            constraint_name: The name of the constraint
            requires: List of constraint names that are required
        """
        if constraint_name not in self._registrations:
            logger.warning(f"Cannot set requirements for unknown constraint: {constraint_name}")
            return
            
        self._registrations[constraint_name].requires = set(requires)
    
    def validate_constraints_compatibility(self, constraint_names: List[str]) -> List[str]:
        """
        Validate that a set of constraints are compatible with each other
        
        Args:
            constraint_names: List of constraint names to validate
            
        Returns:
            List of error messages, empty if all constraints are compatible
        """
        errors = []
        enabled_constraints = set(constraint_names)
        
        # Check for incompatible constraints
        for name in constraint_names:
            if name not in self._registrations:
                errors.append(f"Unknown constraint: {name}")
                continue
                
            info = self._registrations[name]
            
            # Check for incompatible constraints
            for incompatible in info.incompatible_with:
                if incompatible in enabled_constraints:
                    errors.append(
                        f"Constraint '{name}' is incompatible with '{incompatible}'"
                    )
            
            # Check for required constraints
            for required in info.requires:
                if required not in enabled_constraints:
                    errors.append(
                        f"Constraint '{name}' requires '{required}' which is not enabled"
                    )
        
        return errors


# Global constraint factory instance
_factory = ConstraintFactory()

def get_constraint_factory() -> ConstraintFactory:
    """Get the global constraint factory"""
    return _factory


def register_default_constraints() -> None:
    """
    Register the default constraints with the factory
    
    This function automatically registers all available constraints with
    the constraint factory. It discovers constraints by importing modules
    from the constraints package and finding classes that implement
    the Constraint protocol.
    """
    import importlib
    import inspect
    import os
    import pkgutil
    from types import ModuleType
    
    from ..constraints import base
    from ..constraints import assignment
    from ..constraints import instructor
    from ..constraints import limits
    from ..constraints import periods
    from ..constraints import relaxable_limits
    from ..constraints import teacher_workload
    
    factory = get_constraint_factory()
    
    # Define constraint metadata for better organization and documentation
    constraint_metadata = {
        # Assignment constraints
        "single_assignment": {
            "type": assignment.SingleAssignmentConstraint,
            "description": "Ensures each class is assigned at least once",
            "default_enabled": True,
            "default_weight": None,  # Hard constraint
            "is_relaxable": False,
            "category": "assignment"
        },
        "no_overlap": {
            "type": assignment.NoOverlapConstraint,
            "description": "Prevents classes from being scheduled in the same period",
            "default_enabled": True,
            "default_weight": None,  # Hard constraint
            "is_relaxable": False,
            "category": "assignment"
        },
        
        # Instructor constraints
        "instructor_availability": {
            "type": instructor.InstructorAvailabilityConstraint,
            "description": "Ensures classes are only scheduled when instructor is available",
            "default_enabled": True,
            "default_weight": None,  # Hard constraint
            "is_relaxable": False,
            "category": "instructor"
        },
        "consecutive_period": {
            "type": instructor.ConsecutivePeriodConstraint,
            "description": "Prevents an instructor from being scheduled for consecutive periods in a day",
            "default_enabled": True,
            "default_weight": 5000,  # Soft constraint
            "is_relaxable": True,
            "category": "instructor"
        },
        "instructor_load": {
            "type": instructor.InstructorLoadConstraint,
            "description": "Ensures an instructor does not exceed maximum classes per day and per week",
            "default_enabled": True,
            "default_weight": 8000,  # High weight soft constraint
            "is_relaxable": True,
            "category": "instructor"
        },
        
        # Add more constraints as needed...
    }
    
    # Register each constraint with the factory
    for name, meta in constraint_metadata.items():
        factory.register(
            constraint_type=meta["type"],
            name=name,
            description=meta["description"],
            default_enabled=meta["default_enabled"],
            default_weight=meta["default_weight"],
            is_relaxable=meta["is_relaxable"],
            category=meta["category"]
        )
        
    # Log the registered constraints
    logger.info(f"Registered {len(constraint_metadata)} default constraints")
    
    # Set up constraint compatibility relationships
    # These are examples and should be adjusted based on actual constraint logic
    
    # Example 1: Some constraint pairs might be incompatible
    # For example, you can't have multiple load balancing strategies at once
    factory.set_incompatible_constraints(
        "instructor_load",
        ["teacher_workload"]  # These two constraints might have conflicting logic
    )
    
    # Example 2: Some constraints might require others to be effective
    # For example, a constraint that optimizes consecutive classes needs the no-overlap constraint
    factory.set_required_constraints(
        "consecutive_period",
        ["no_overlap"]  # Consecutive periods assumes no overlap
    )
    
    # Add more compatibility relationships as needed
    # This allows the system to validate that the enabled constraints are compatible
    
    # Also try to discover and register any constraints not explicitly listed above
    discover_and_register_additional_constraints(factory)


def discover_and_register_additional_constraints(factory: ConstraintFactory) -> None:
    """
    Discover and register any additional constraints that are not explicitly listed
    
    This function uses introspection to find constraint classes in the constraints
    package that haven't been explicitly registered.
    
    Args:
        factory: The constraint factory to register constraints with
    """
    import importlib
    import inspect
    import pkgutil
    from types import ModuleType
    
    from .. import constraints
    from ..core import Constraint
    
    # Keep track of already registered constraints to avoid duplicates
    registered_types = {info.constraint_type for info in factory._registrations.values()}
    
    # Discover constraint modules
    constraint_modules = []
    for _, module_name, _ in pkgutil.iter_modules(constraints.__path__):
        try:
            module = importlib.import_module(f"..constraints.{module_name}", package=__name__)
            constraint_modules.append(module)
        except ImportError as e:
            logger.warning(f"Failed to import constraint module {module_name}: {e}")
    
    # Find constraint classes in the modules
    registered_count = 0
    for module in constraint_modules:
        for name, obj in inspect.getmembers(module):
            # Skip if not a class or already registered
            if not inspect.isclass(obj) or obj in registered_types:
                continue
                
            # Skip if it doesn't inherit from BaseConstraint
            if not hasattr(obj, "__bases__") or not any(
                base.__name__ == "BaseConstraint" for base in inspect.getmro(obj)
            ):
                continue
                
            # Skip abstract classes
            if inspect.isabstract(obj):
                continue
                
            # Register the constraint
            constraint_name = name.lower()
            if constraint_name.endswith("constraint"):
                constraint_name = constraint_name[:-10]  # Remove "constraint" suffix
                
            factory.register(
                constraint_type=obj,
                name=constraint_name,
                description=obj.__doc__ or f"Constraint: {name}",
                default_enabled=True,
                default_weight=None if "hard" in name.lower() else 1000,
                is_relaxable="relaxable" in name.lower(),
                category="general"
            )
            registered_count += 1
            
    if registered_count > 0:
        logger.info(f"Auto-discovered and registered {registered_count} additional constraints")
