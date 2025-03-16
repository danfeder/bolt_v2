"""
Modular Constraint Factory Module

This module provides a factory for creating constraints based on configuration.
It implements a truly modular approach without category-based organization,
treating each constraint as a fully independent module.
"""

from typing import Dict, Any, List, Optional, Type, Set, Tuple
import logging
import importlib
import inspect
from types import ModuleType

from ..core import Constraint, SchedulerContext

logger = logging.getLogger(__name__)


class ConstraintMetadata:
    """Detailed information about a constraint registration"""
    def __init__(
        self, 
        constraint_type: Type[Constraint],
        name: str,
        description: str = "",
        default_enabled: bool = True,
        default_weight: Optional[int] = None,
        is_relaxable: bool = False,
        parameter_schema: Optional[Dict[str, Any]] = None,
        deprecated: bool = False,
        replacement: Optional[str] = None
    ):
        """
        Initialize constraint metadata
        
        Args:
            constraint_type: The constraint class
            name: The name of the constraint
            description: Description of the constraint's purpose
            default_enabled: Whether the constraint is enabled by default
            default_weight: Default weight for soft constraints (None for hard constraints)
            is_relaxable: Whether the constraint supports relaxation
            parameter_schema: Optional schema describing configuration parameters
            deprecated: Whether this constraint is deprecated
            replacement: Name of constraint that should be used instead (if any)
        """
        self.constraint_type = constraint_type
        self.name = name
        self.description = description
        self.default_enabled = default_enabled
        self.default_weight = default_weight
        self.is_relaxable = is_relaxable
        self.parameter_schema = parameter_schema or {}
        self.deprecated = deprecated
        self.replacement = replacement
        
        # Dependencies
        self.incompatible_with: Set[str] = set()  # Other constraints this one can't work with
        self.requires: Set[str] = set()  # Other constraints this one depends on
    
    def add_incompatibility(self, constraint_name: str) -> None:
        """Add an incompatible constraint"""
        self.incompatible_with.add(constraint_name)
    
    def add_dependency(self, constraint_name: str) -> None:
        """Add a required dependency constraint"""
        self.requires.add(constraint_name)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "name": self.name,
            "description": self.description,
            "defaultEnabled": self.default_enabled,
            "defaultWeight": self.default_weight,
            "isRelaxable": self.is_relaxable,
            "parameterSchema": self.parameter_schema,
            "incompatibleWith": list(self.incompatible_with),
            "requires": list(self.requires),
            "deprecated": self.deprecated,
            "replacement": self.replacement
        }


class ModularConstraintFactory:
    """
    Factory for creating constraint instances in a truly modular way
    
    This class manages constraint registrations and creates configured
    constraint instances without requiring category grouping.
    """
    
    def __init__(self):
        """Initialize the factory"""
        self._registrations: Dict[str, ConstraintMetadata] = {}
    
    def register(
        self,
        constraint_type: Type[Constraint],
        name: Optional[str] = None,
        description: str = "",
        default_enabled: bool = True,
        default_weight: Optional[int] = None,
        is_relaxable: bool = False,
        parameter_schema: Optional[Dict[str, Any]] = None,
        deprecated: bool = False,
        replacement: Optional[str] = None
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
            parameter_schema: Optional schema describing configuration parameters
        """
        if name is None:
            name = constraint_type.__name__.lower()
            if name.endswith('constraint'):
                name = name[:-10]  # Remove 'constraint' suffix
        
        # Register the constraint metadata
        self._registrations[name] = ConstraintMetadata(
            constraint_type=constraint_type,
            name=name,
            description=description,
            default_enabled=default_enabled,
            default_weight=default_weight,
            is_relaxable=is_relaxable,
            parameter_schema=parameter_schema,
            deprecated=deprecated,
            replacement=replacement
        )
        
        logger.debug(f"Registered constraint: {name}")
    
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
            
        # Get constraint metadata
        metadata = self._registrations[name]
        
        # Create a new constraint instance
        constraint_args = {}
        
        # Set enabled if provided, otherwise use default
        if "enabled" in config:
            constraint_args["enabled"] = config["enabled"]
        else:
            constraint_args["enabled"] = metadata.default_enabled
            
        # Set weight if provided, otherwise use default
        if "weight" in config:
            constraint_args["weight"] = config["weight"]
        elif metadata.default_weight is not None:
            constraint_args["weight"] = metadata.default_weight
            
        # Pass any additional configuration parameters
        for key, value in config.items():
            if key not in ["enabled", "weight"]:
                constraint_args[key] = value
                
        # Create the constraint
        try:
            # Some constraints might not accept 'enabled' or 'weight' directly in constructor
            # Use inspect to check what parameters the constraint accepts
            from inspect import signature
            sig = signature(metadata.constraint_type.__init__)
            filtered_args = {}
            
            # Only include parameters that the constructor accepts
            for param_name, param_value in constraint_args.items():
                if param_name in sig.parameters or param_name == 'kwargs' or '**kwargs' in str(sig):
                    filtered_args[param_name] = param_value
            
            # Create the constraint with filtered arguments
            constraint = metadata.constraint_type(**filtered_args)
            
            # Set enabled/weight attributes directly if they exist but weren't in constructor
            if 'enabled' in constraint_args and hasattr(constraint, 'enabled') and 'enabled' not in filtered_args:
                constraint.enabled = constraint_args['enabled']
                
            if 'weight' in constraint_args and hasattr(constraint, 'weight') and 'weight' not in filtered_args:
                constraint.weight = constraint_args['weight']
                
            return constraint
        except Exception as e:
            logger.error(f"Error creating constraint {name}: {e}")
            return None
    
    def get_constraint_metadata(self, name: str) -> Optional[ConstraintMetadata]:
        """
        Get metadata about a registered constraint
        
        Args:
            name: The name of the constraint
            
        Returns:
            The constraint metadata, or None if the constraint is not registered
        """
        return self._registrations.get(name)
    
    def get_all_constraint_metadata(self) -> Dict[str, ConstraintMetadata]:
        """
        Get metadata about all registered constraints
        
        Returns:
            A dictionary mapping constraint names to their metadata
        """
        return self._registrations.copy()
        
    def get_constraint_names(self) -> List[str]:
        """
        Get the names of all registered constraints
        
        Returns:
            A list of constraint names
        """
        return list(self._registrations.keys())
        
    def set_incompatible_constraints(
        self, 
        constraint_name: str, 
        incompatible_constraints: List[str]
    ) -> None:
        """
        Set constraints that are incompatible with a given constraint
        
        Args:
            constraint_name: The name of the constraint
            incompatible_constraints: Names of constraints that are incompatible
        """
        if constraint_name not in self._registrations:
            logger.warning(f"Cannot set incompatible constraints for unknown constraint: {constraint_name}")
            return
            
        metadata = self._registrations[constraint_name]
        for incompatible in incompatible_constraints:
            metadata.add_incompatibility(incompatible)
            
            # Add reciprocal incompatibility if the other constraint exists
            if incompatible in self._registrations:
                self._registrations[incompatible].add_incompatibility(constraint_name)
    
    def set_required_constraints(
        self, 
        constraint_name: str, 
        required_constraints: List[str]
    ) -> None:
        """
        Set constraints that are required by a given constraint
        
        Args:
            constraint_name: The name of the constraint
            required_constraints: Names of constraints that are required
        """
        if constraint_name not in self._registrations:
            logger.warning(f"Cannot set required constraints for unknown constraint: {constraint_name}")
            return
            
        metadata = self._registrations[constraint_name]
        for required in required_constraints:
            metadata.add_dependency(required)
    
    def validate_constraint_compatibility(
        self,
        enabled_constraints: List[str]
    ) -> Tuple[bool, List[str], Dict[str, List[str]]]:
        """
        Validate that a set of enabled constraints are compatible with each other
        
        Args:
            enabled_constraints: Names of constraints to validate
            
        Returns:
            Tuple containing:
            - Whether the constraints are compatible
            - List of error messages
            - Dictionary mapping constraint names to lists of missing dependencies
        """
        errors = []
        missing_dependencies = {}
        
        # Check for incompatibilities
        for i, constraint1 in enumerate(enabled_constraints):
            if constraint1 not in self._registrations:
                errors.append(f"Unknown constraint: {constraint1}")
                continue
                
            metadata1 = self._registrations[constraint1]
            
            # Check for incompatibilities with other enabled constraints
            for constraint2 in enabled_constraints[i+1:]:
                if constraint2 in metadata1.incompatible_with:
                    errors.append(
                        f"Incompatible constraints: {constraint1} and {constraint2}"
                    )
        
        # Check for missing dependencies
        for constraint in enabled_constraints:
            if constraint not in self._registrations:
                continue
                
            metadata = self._registrations[constraint]
            
            missing = [
                req for req in metadata.requires 
                if req not in enabled_constraints
            ]
            
            if missing:
                missing_dependencies[constraint] = missing
                errors.append(
                    f"Constraint {constraint} requires {', '.join(missing)}"
                )
        
        return len(errors) == 0, errors, missing_dependencies
    
    def resolve_dependencies(
        self, 
        constraint_names: List[str]
    ) -> List[str]:
        """
        Resolve dependencies for a list of constraints
        
        This adds any missing constraints that are required by the given constraints.
        
        Args:
            constraint_names: Names of constraints to resolve dependencies for
            
        Returns:
            A complete list of constraints with dependencies added
        """
        result = set(constraint_names)
        
        # Iteratively add dependencies until fixed point
        size = 0
        while size != len(result):
            size = len(result)
            for name in list(result):
                if name not in self._registrations:
                    continue
                    
                metadata = self._registrations[name]
                result.update(metadata.requires)
        
        return list(result)


# Function to load constraint modules
def load_constraint_modules() -> Dict[str, ModuleType]:
    """
    Load all constraint modules from the constraints package
    
    Returns:
        A dictionary mapping module names to modules
    """
    import importlib
    import sys
    
    constraint_modules = {}
    
    # List of module names to import
    module_names = [
        "base", "assignment", "instructor", "limits", 
        "periods", "relaxable_limits", "teacher_workload", "examples"
    ]
    
    # Base package for absolute imports
    base_package = "app.scheduling.constraints"
    
    # Try to import each module
    for module_name in module_names:
        try:
            module = importlib.import_module(f"{base_package}.{module_name}")
            constraint_modules[module_name] = module
            logger.debug(f"Successfully imported {module_name} constraints")
        except ImportError as e:
            logger.debug(f"Could not import {module_name} constraints: {e}")
            
            # Try relative import as fallback
            try:
                from .. import constraints
                module = getattr(constraints, module_name, None)
                if module:
                    constraint_modules[module_name] = module
                    logger.debug(f"Successfully imported {module_name} constraints via relative import")
            except (ImportError, AttributeError) as e2:
                logger.debug(f"Could not import {module_name} constraints via relative import: {e2}")
    
    return constraint_modules


# Helper function to get a constraint class from a module
def get_constraint_class(modules: Dict[str, ModuleType], module_name: str, class_name: str):
    """
    Get a constraint class from a module
    
    Args:
        modules: Dictionary mapping module names to modules
        module_name: Name of the module containing the class
        class_name: Name of the class to get
        
    Returns:
        The constraint class, or None if not found
    """
    module = modules.get(module_name)
    if not module:
        logger.warning(f"Module {module_name} not loaded, cannot get {class_name}")
        return None
    
    constraint_class = getattr(module, class_name, None)
    if not constraint_class:
        logger.warning(f"Class {class_name} not found in {module_name} module")
        return None
        
    return constraint_class


# Global factory instance
_factory = ModularConstraintFactory()

def get_modular_constraint_factory() -> ModularConstraintFactory:
    """
    Get the global constraint factory
    
    Returns:
        The global ModularConstraintFactory instance
    """
    return _factory


def register_modular_constraints() -> None:
    """
    Register constraints with the modular factory
    
    This function loads and registers all available constraints as independent
    modules without category-based organization.
    """
    # Load constraint modules
    modules = load_constraint_modules()
    
    # Use the global factory directly to avoid recursion
    factory = _factory
    
    # Define constraint metadata
    constraint_metadata = {}
    
    # ASSIGNMENT CONSTRAINTS
    
    # SingleAssignmentConstraint
    single_assignment = get_constraint_class(modules, 'assignment', 'SingleAssignmentConstraint')
    if single_assignment:
        constraint_metadata["single_assignment"] = {
            "type": single_assignment,
            "description": "Ensures each class is assigned at least once",
            "default_enabled": True,
            "default_weight": None,  # Hard constraint
            "is_relaxable": False,
            "parameter_schema": {}
        }
    
    # NoOverlapConstraint
    no_overlap = get_constraint_class(modules, 'assignment', 'NoOverlapConstraint')
    if no_overlap:
        constraint_metadata["no_overlap"] = {
            "type": no_overlap,
            "description": "Prevents classes from being scheduled in the same period",
            "default_enabled": True,
            "default_weight": None,  # Hard constraint
            "is_relaxable": False,
            "parameter_schema": {}
        }
    
    # INSTRUCTOR CONSTRAINTS
    
    # InstructorAvailabilityConstraint
    instructor_availability = get_constraint_class(modules, 'instructor', 'InstructorAvailabilityConstraint')
    if instructor_availability:
        constraint_metadata["instructor_availability"] = {
            "type": instructor_availability,
            "description": "Ensures classes are only scheduled when instructor is available",
            "default_enabled": True,
            "default_weight": None,  # Hard constraint
            "is_relaxable": False,
            "parameter_schema": {}
        }
    
    # ConsecutivePeriodConstraint
    consecutive_period = get_constraint_class(modules, 'instructor', 'ConsecutivePeriodConstraint')
    if consecutive_period:
        constraint_metadata["consecutive_period"] = {
            "type": consecutive_period,
            "description": "Prevents an instructor from being scheduled for consecutive periods in a day",
            "default_enabled": True,
            "default_weight": 5000,  # Soft constraint
            "is_relaxable": True,
            "parameter_schema": {}
        }
    
    # InstructorLoadConstraint - MARKED AS DEPRECATED
    instructor_load = get_constraint_class(modules, 'instructor', 'InstructorLoadConstraint')
    if instructor_load:
        constraint_metadata["instructor_load"] = {
            "type": instructor_load,
            "description": "Ensures an instructor does not exceed maximum classes per day and per week",
            "default_enabled": False,  # Disabled by default
            "default_weight": 8000,
            "is_relaxable": True,
            "deprecated": True,
            "replacement": "daily_limit,weekly_limit",
            "parameter_schema": {
                "max_classes_per_day": {
                    "type": "integer",
                    "default": 3,
                    "description": "Maximum classes per day"
                },
                "max_classes_per_week": {
                    "type": "integer",
                    "default": 12,
                    "description": "Maximum classes per week"
                }
            }
        }
    
    # LIMIT CONSTRAINTS
    
    # DailyLimitConstraint
    daily_limit = get_constraint_class(modules, 'limits', 'DailyLimitConstraint')
    if daily_limit:
        constraint_metadata["daily_limit"] = {
            "type": daily_limit,
            "description": "Ensures the number of classes per day doesn't exceed the maximum",
            "default_enabled": True,
            "default_weight": None,  # Hard constraint
            "is_relaxable": False,
            "parameter_schema": {}
        }
    
    # WeeklyLimitConstraint
    weekly_limit = get_constraint_class(modules, 'limits', 'WeeklyLimitConstraint')
    if weekly_limit:
        constraint_metadata["weekly_limit"] = {
            "type": weekly_limit,
            "description": "Ensures the number of classes per week doesn't exceed the maximum",
            "default_enabled": True,
            "default_weight": None,  # Hard constraint
            "is_relaxable": False,
            "parameter_schema": {}
        }
    
    # MinimumPeriodsConstraint
    minimum_periods = get_constraint_class(modules, 'limits', 'MinimumPeriodsConstraint')
    if minimum_periods:
        constraint_metadata["minimum_periods"] = {
            "type": minimum_periods,
            "description": "Ensures the minimum number of classes per week is met",
            "default_enabled": True,
            "default_weight": None,  # Hard constraint
            "is_relaxable": False,
            "parameter_schema": {}
        }
    
    # PERIOD CONSTRAINTS
    
    # RequiredPeriodsConstraint
    required_periods = get_constraint_class(modules, 'periods', 'RequiredPeriodsConstraint')
    if required_periods:
        constraint_metadata["required_periods"] = {
            "type": required_periods,
            "description": "Enforces required periods as hard constraints",
            "default_enabled": True,
            "default_weight": None,  # Hard constraint
            "is_relaxable": False,
            "parameter_schema": {}
        }
    
    # ConflictPeriodsConstraint
    conflict_periods = get_constraint_class(modules, 'periods', 'ConflictPeriodsConstraint')
    if conflict_periods:
        constraint_metadata["conflict_periods"] = {
            "type": conflict_periods,
            "description": "Prevents assignments to conflicting periods",
            "default_enabled": True,
            "default_weight": None,  # Hard constraint
            "is_relaxable": False,
            "parameter_schema": {}
        }
    
    # RELAXABLE LIMITS
    
    # RelaxableDailyLimitConstraint
    relaxable_daily_limit = get_constraint_class(modules, 'relaxable_limits', 'RelaxableDailyLimitConstraint')
    if relaxable_daily_limit:
        constraint_metadata["relaxable_daily_limit"] = {
            "type": relaxable_daily_limit,
            "description": "Relaxable version of the daily limit constraint",
            "default_enabled": False,  # Disabled by default, use regular DailyLimitConstraint instead
            "default_weight": None,  # Hard constraint with relaxation
            "is_relaxable": True,
            "parameter_schema": {
                "relaxation_priority": {
                    "type": "integer",
                    "default": 2,
                    "description": "Priority for relaxation (lower values are relaxed first)"
                },
                "never_relax": {
                    "type": "boolean",
                    "default": False,
                    "description": "If true, this constraint will never be relaxed"
                }
            }
        }
    
    # RelaxableWeeklyLimitConstraint
    relaxable_weekly_limit = get_constraint_class(modules, 'relaxable_limits', 'RelaxableWeeklyLimitConstraint')
    if relaxable_weekly_limit:
        constraint_metadata["relaxable_weekly_limit"] = {
            "type": relaxable_weekly_limit,
            "description": "Relaxable version of the weekly limit constraint",
            "default_enabled": False,  # Disabled by default, use regular WeeklyLimitConstraint instead
            "default_weight": None,  # Hard constraint with relaxation
            "is_relaxable": True,
            "parameter_schema": {
                "relaxation_priority": {
                    "type": "integer",
                    "default": 3,
                    "description": "Priority for relaxation (lower values are relaxed first)"
                },
                "never_relax": {
                    "type": "boolean",
                    "default": False,
                    "description": "If true, this constraint will never be relaxed"
                }
            }
        }
    
    # TEACHER WORKLOAD
    
    # ConsecutiveClassesConstraint
    consecutive_classes = get_constraint_class(modules, 'teacher_workload', 'ConsecutiveClassesConstraint')
    if consecutive_classes:
        constraint_metadata["consecutive_classes"] = {
            "type": consecutive_classes,
            "description": "Controls scheduling of consecutive classes for teacher workload management",
            "default_enabled": True,
            "default_weight": None,  # Hard constraint
            "is_relaxable": False,
            "parameter_schema": {
                "allow_consecutive": {
                    "type": "boolean",
                    "default": True,
                    "description": "If true, allows exactly 2 consecutive classes; if false, disallows any consecutive classes"
                }
            }
        }
    
    # TeacherBreakConstraint
    teacher_break = get_constraint_class(modules, 'teacher_workload', 'TeacherBreakConstraint')
    if teacher_break:
        constraint_metadata["teacher_break"] = {
            "type": teacher_break,
            "description": "Ensures the teacher gets adequate breaks during the day",
            "default_enabled": True,
            "default_weight": 3000,  # Soft constraint
            "is_relaxable": True,
            "parameter_schema": {
                "required_breaks": {
                    "type": "array",
                    "items": {
                        "type": "integer"
                    },
                    "default": [],
                    "description": "List of periods that should be kept free for breaks"
                }
            }
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
            parameter_schema=meta["parameter_schema"]
        )
    
    # Auto-discover additional constraints
    discover_and_register_additional_constraints(factory, modules)
    
    # Set up constraint relationships (dependencies and incompatibilities)
    
    # Example: consecutive_period requires no_overlap
    factory.set_required_constraints(
        "consecutive_period",
        ["no_overlap"]
    )
    
    # Example: relaxable_daily_limit is incompatible with regular daily_limit
    factory.set_incompatible_constraints(
        "relaxable_daily_limit",
        ["daily_limit"]
    )
    
    # Example: relaxable_weekly_limit is incompatible with regular weekly_limit
    factory.set_incompatible_constraints(
        "relaxable_weekly_limit",
        ["weekly_limit"]
    )
    
    # Example: instructor_load is incompatible with daily_limit and weekly_limit
    # since it manages the same constraints
    factory.set_incompatible_constraints(
        "instructor_load",
        ["daily_limit", "weekly_limit"]
    )
    
    # Log the registered constraints
    logger.info(f"Registered {len(constraint_metadata)} constraints using modular approach")


def discover_and_register_additional_constraints(
    factory: ModularConstraintFactory,
    modules: Dict[str, ModuleType]
) -> None:
    """
    Discover and register any additional constraints using reflection
    
    Args:
        factory: The constraint factory to register with
        modules: Dictionary of loaded modules
    """
    import inspect
    
    discovered_count = 0
    registered_names = set(factory.get_constraint_names())
    
    # Look through all modules for constraint classes
    for module_name, module in modules.items():
        if not module:
            continue
        
        for item_name in dir(module):
            # Skip if not a potential constraint class
            if not item_name.endswith('Constraint'):
                continue
            
            # Get normalized name
            normalized_name = item_name.lower()
            if normalized_name.endswith('constraint'):
                normalized_name = normalized_name[:-10]  # Remove 'constraint' suffix
            
            # Skip if already registered
            if normalized_name in registered_names:
                continue
            
            # Get the class
            constraint_class = getattr(module, item_name)
            if not inspect.isclass(constraint_class):
                continue
            
            # Skip if doesn't inherit from BaseConstraint or similar
            if not hasattr(constraint_class, 'apply') or not hasattr(constraint_class, 'validate'):
                continue
            
            # Determine if relaxable
            is_relaxable = hasattr(constraint_class, 'relaxation_level') or \
                          hasattr(constraint_class, 'set_relaxation_level')
            
            # Register the constraint
            factory.register(
                constraint_type=constraint_class,
                name=normalized_name,
                description=getattr(constraint_class, '__doc__', f"Auto-discovered {item_name}"),
                default_enabled=True,
                default_weight=1000 if is_relaxable else None,  # Default weight for soft constraints
                is_relaxable=is_relaxable
            )
            
            discovered_count += 1
    
    logger.debug(f"Auto-discovered and registered {discovered_count} additional constraints")


# Initialize factory with the default constraint registrations
register_modular_constraints()

if __name__ == "__main__":
    # If run directly, initialize the constraint registry
    # This is redundant now but kept for clarity
    pass
