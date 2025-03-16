"""
Modular Constraint Manager Module

This module provides a constraint manager that works with the modular constraint factory.
It maintains a collection of constraints and applies them to scheduling operations
without relying on category-based organization.
"""

from typing import Dict, List, Any, Optional, Set, Tuple, Union
import logging

from ..core import Constraint, SchedulerContext
from .modular_constraint_factory import (
    ModularConstraintFactory, 
    get_modular_constraint_factory
)

logger = logging.getLogger(__name__)


class ModularConstraintManager:
    """
    Manager for handling constraints in a truly modular way
    
    This class manages a collection of constraints and applies them
    to scheduling operations. It provides methods for adding, removing,
    enabling, and disabling specific constraints without category-based
    organization.
    """
    
    def __init__(self, factory: Optional[ModularConstraintFactory] = None):
        """
        Initialize the constraint manager
        
        Args:
            factory: The constraint factory to use (uses global instance if None)
        """
        self.factory = factory or get_modular_constraint_factory()
        self.constraints: Dict[str, Constraint] = {}
    
    def add_constraint(
        self, 
        name: str, 
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[Constraint]:
        """
        Add a constraint by name
        
        Args:
            name: The name of the constraint to add
            config: Optional configuration for the constraint
            
        Returns:
            The added constraint, or None if it couldn't be created
        """
        # Check if the constraint is deprecated before creating it
        metadata = self.factory.get_constraint_metadata(name)
        if metadata and metadata.deprecated:
            replacement_msg = f", use '{metadata.replacement}' instead" if metadata.replacement else ""
            logger.warning(
                f"Constraint '{name}' is deprecated and may be removed in a future version{replacement_msg}"
            )
            
        constraint = self.factory.create_constraint(name, config)
        if constraint:
            self.constraints[name] = constraint
        return constraint
    
    def add_constraints(
        self, 
        names: List[str], 
        configs: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Constraint]:
        """
        Add multiple constraints by name
        
        Args:
            names: List of constraint names to add
            configs: Optional dictionary mapping constraint names to configurations
            
        Returns:
            Dictionary mapping constraint names to added constraints
        """
        added = {}
        configs = configs or {}
        
        for name in names:
            config = configs.get(name)
            constraint = self.add_constraint(name, config)
            if constraint:
                added[name] = constraint
                
        return added
    
    def add_all_constraints(
        self, 
        configs: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Constraint]:
        """
        Add all available constraints
        
        Args:
            configs: Optional dictionary mapping constraint names to configurations
            
        Returns:
            Dictionary mapping constraint names to added constraints
        """
        names = self.factory.get_constraint_names()
        return self.add_constraints(names, configs)
    
    def remove_constraint(self, name: str) -> None:
        """
        Remove a constraint by name
        
        Args:
            name: The name of the constraint to remove
        """
        if name in self.constraints:
            del self.constraints[name]
    
    def enable_constraint(self, name: str) -> None:
        """
        Enable a constraint by name
        
        Args:
            name: The name of the constraint to enable
        """
        if name in self.constraints:
            self.constraints[name].enabled = True
    
    def disable_constraint(self, name: str) -> None:
        """
        Disable a constraint by name
        
        Args:
            name: The name of the constraint to disable
        """
        if name in self.constraints:
            self.constraints[name].enabled = False
    
    def get_constraint(self, name: str) -> Optional[Constraint]:
        """
        Get a constraint by name
        
        Args:
            name: The name of the constraint to get
            
        Returns:
            The constraint, or None if it doesn't exist
        """
        return self.constraints.get(name)
    
    def get_all_constraints(self) -> Dict[str, Constraint]:
        """
        Get all constraints
        
        Returns:
            Dictionary mapping constraint names to constraints
        """
        return self.constraints.copy()
    
    def get_enabled_constraints(self) -> Dict[str, Constraint]:
        """
        Get all enabled constraints
        
        Returns:
            Dictionary mapping constraint names to enabled constraints
        """
        return {
            name: constraint 
            for name, constraint in self.constraints.items() 
            if constraint.enabled
        }
    
    def apply_constraints(self, context: SchedulerContext) -> None:
        """
        Apply all enabled constraints to the model
        
        Args:
            context: The scheduler context
        """
        for name, constraint in self.constraints.items():
            if constraint.enabled:
                try:
                    constraint.apply(context)
                except Exception as e:
                    logger.error(f"Error applying constraint {name}: {e}")
    
    def validate(
        self, 
        assignments: List[Dict[str, Any]], 
        context: SchedulerContext
    ) -> Dict[str, List[Any]]:
        """
        Validate assignments against all enabled constraints
        
        Args:
            assignments: The assignments to validate
            context: The scheduler context
            
        Returns:
            Dictionary mapping constraint names to lists of violations
        """
        violations = {}
        
        for name, constraint in self.constraints.items():
            if constraint.enabled:
                try:
                    constraint_violations = constraint.validate(assignments, context)
                    if constraint_violations:
                        violations[name] = constraint_violations
                except Exception as e:
                    logger.error(f"Error validating constraint {name}: {e}")
                    violations[name] = [{
                        "message": f"Error validating constraint: {str(e)}",
                        "severity": "error"
                    }]
                    
        return violations
    
    def validate_compatibility(self) -> Tuple[bool, List[str], Dict[str, List[str]]]:
        """
        Validate that all enabled constraints are compatible with each other
        
        Returns:
            Tuple containing:
            - Whether the constraints are compatible
            - List of error messages
            - Dictionary mapping constraint names to lists of missing dependencies
        """
        enabled_constraints = [
            name for name, constraint in self.constraints.items()
            if constraint.enabled
        ]
        
        return self.factory.validate_constraint_compatibility(enabled_constraints)
    
    def resolve_dependencies(
        self, 
        enabled_constraints: List[str]
    ) -> List[str]:
        """
        Resolve dependencies for a list of constraints
        
        This returns a complete list of constraints with all dependencies included.
        
        Args:
            enabled_constraints: List of constraint names to resolve dependencies for
            
        Returns:
            A complete list of constraint names with dependencies
        """
        return self.factory.resolve_dependencies(enabled_constraints)
    
    def get_constraint_configuration(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the current configuration of all constraints
        
        Returns:
            Dictionary mapping constraint names to their configurations
        """
        configuration = {}
        
        for name, constraint in self.constraints.items():
            # Get enabled status
            config = {"enabled": constraint.enabled}
            
            # Get weight if available
            if hasattr(constraint, "weight"):
                config["weight"] = constraint.weight
                
            # Add any other accessible attributes
            for attr_name in dir(constraint):
                # Skip special, private, and method attributes
                if attr_name.startswith('_') or attr_name in ('enabled', 'weight', 'apply', 'validate'):
                    continue
                    
                # Get the attribute if it's a simple data value
                attr = getattr(constraint, attr_name)
                if not callable(attr) and not isinstance(attr, (dict, list, set, tuple)):
                    config[attr_name] = attr
                    
            configuration[name] = config
            
        return configuration
    
    def configure_constraints(
        self, 
        configuration: Dict[str, Dict[str, Any]]
    ) -> None:
        """
        Configure constraints from a configuration dictionary
        
        Args:
            configuration: Dictionary mapping constraint names to configurations
        """
        for name, config in configuration.items():
            if name in self.constraints:
                # Configure an existing constraint
                constraint = self.constraints[name]
                
                # Set enabled status
                if "enabled" in config:
                    constraint.enabled = config["enabled"]
                    
                # Set weight if available
                if "weight" in config and hasattr(constraint, "weight"):
                    constraint.weight = config["weight"]
                    
                # Set other attributes
                for attr_name, value in config.items():
                    if attr_name not in ('enabled', 'weight'):
                        if hasattr(constraint, attr_name):
                            setattr(constraint, attr_name, value)
            else:
                # Create a new constraint
                self.add_constraint(name, config)
