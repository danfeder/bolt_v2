"""
Constraint Factory Module

This module provides a factory for creating constraints based on configuration.
It abstracts the creation and initialization of constraints, making it easier
to modify constraint behavior without changing the code that uses them.
"""

from typing import Dict, Any, List, Optional, Type, ClassVar, Protocol
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
        is_relaxable: bool = False
    ):
        self.constraint_type = constraint_type
        self.name = name
        self.description = description
        self.default_enabled = default_enabled
        self.default_weight = default_weight
        self.is_relaxable = is_relaxable


class ConstraintFactory:
    """
    Factory for creating constraint instances
    
    This class manages constraint registrations and creates configured
    constraint instances based on configuration.
    """
    
    def __init__(self):
        """Initialize the factory"""
        self._registrations: Dict[str, ConstraintInfo] = {}
    
    def register(
        self,
        constraint_type: Type[Constraint],
        name: Optional[str] = None,
        description: str = "",
        default_enabled: bool = True,
        default_weight: Optional[int] = None,
        is_relaxable: bool = False
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
        """
        if name is None:
            name = constraint_type.__name__.lower()
        
        self._registrations[name] = ConstraintInfo(
            constraint_type=constraint_type,
            name=name,
            description=description,
            default_enabled=default_enabled,
            default_weight=default_weight,
            is_relaxable=is_relaxable
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
        
        # Get the registration
        info = self._registrations[name]
        
        # Create a default configuration if none provided
        if config is None:
            config = {}
        
        # Apply defaults from the registration
        if "enabled" not in config:
            config["enabled"] = info.default_enabled
        if "weight" not in config and info.default_weight is not None:
            config["weight"] = info.default_weight
        
        # Create the constraint instance
        try:
            constraint = info.constraint_type(**config)
            logger.debug(f"Created constraint: {name} (enabled={config.get('enabled', True)})")
            return constraint
        except Exception as e:
            logger.error(f"Error creating constraint {name}: {e}")
            return None
    
    def create_constraints(
        self,
        constraint_configs: Dict[str, Dict[str, Any]]
    ) -> List[Constraint]:
        """
        Create multiple constraints from a configuration dictionary
        
        Args:
            constraint_configs: Dictionary mapping constraint names to their configurations
            
        Returns:
            A list of constraint instances
        """
        constraints = []
        
        for name, config in constraint_configs.items():
            constraint = self.create_constraint(name, config)
            if constraint:
                constraints.append(constraint)
        
        return constraints
    
    def get_available_constraints(self) -> List[str]:
        """
        Get a list of all available constraint names
        
        Returns:
            A list of constraint names
        """
        return list(self._registrations.keys())
    
    def get_constraint_info(self, name: str) -> Optional[ConstraintInfo]:
        """
        Get information about a registered constraint
        
        Args:
            name: The name of the constraint
            
        Returns:
            Information about the constraint, or None if not registered
        """
        return self._registrations.get(name)


# Global constraint factory instance
_factory = ConstraintFactory()

def get_constraint_factory() -> ConstraintFactory:
    """Get the global constraint factory"""
    return _factory


def register_default_constraints() -> None:
    """Register the default constraints with the factory"""
    # This function would usually iterate through available constraints
    # and register them with the factory, possibly based on configuration
    # For now, this is a placeholder
    pass
