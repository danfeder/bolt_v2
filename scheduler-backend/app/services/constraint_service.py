"""
Constraint Service Module

This module provides a service for managing constraints in the scheduling system.
It wraps the modular constraint manager to provide higher-level operations
suitable for API usage.
"""

from typing import Dict, List, Any, Optional, Tuple, Union
import logging

from ..scheduling.abstractions.modular_constraint_factory import (
    get_modular_constraint_factory,
    ModularConstraintFactory
)
from ..scheduling.abstractions.modular_constraint_manager import (
    ModularConstraintManager
)
from ..core.result import Result, success, error, warning
from ..scheduling.core import Constraint

logger = logging.getLogger(__name__)


class ConstraintService:
    """
    Service for managing constraints in the scheduling system
    
    This service provides operations for listing, configuring, and validating
    constraints in the modular constraint system.
    """
    
    def __init__(self):
        """Initialize the constraint service"""
        self._factory = get_modular_constraint_factory()
        self._manager = ModularConstraintManager(self._factory)
        
        # Initialize with default constraints
        self._setup_default_constraints()
    
    def _setup_default_constraints(self) -> None:
        """Set up default constraints for the constraint manager"""
        # Add essential constraints that should always be enabled
        essential_constraints = [
            "single_assignment",
            "no_overlap",
            "instructor_availability",
            "daily_limit",
            "weekly_limit"
        ]
        
        # Add optional constraints that are enabled by default but can be disabled
        optional_constraints = [
            "consecutive_period",
            "required_periods",
            "conflict_periods"
        ]
        
        # Add all essential constraints
        for constraint_name in essential_constraints:
            self._manager.add_constraint(constraint_name)
        
        # Add all optional constraints
        for constraint_name in optional_constraints:
            self._manager.add_constraint(constraint_name)
    
    def get_all_constraints(self) -> Result[Dict[str, Any]]:
        """
        Get information about all available constraints
        
        Returns:
            Result with dictionary containing constraint information
        """
        try:
            # Get all constraint metadata
            constraint_metadata = {}
            for name in self._factory.get_constraint_names():
                metadata = self._factory.get_constraint_metadata(name)
                if metadata:
                    constraint_metadata[name] = metadata.to_dict()
            
            # Get current configuration for all constraints
            constraint_config = self._manager.get_constraint_configuration()
            
            # Combine metadata and configuration
            result = {
                "constraints": constraint_metadata,
                "configuration": constraint_config
            }
            
            return success(result)
        except Exception as e:
            logger.error(f"Error getting constraints: {e}")
            return error(str(e))
    
    def get_active_constraints(self) -> Result[Dict[str, Any]]:
        """
        Get information about currently active constraints
        
        Returns:
            Result with dictionary containing active constraint information
        """
        try:
            # Get enabled constraints with their configuration
            enabled_constraints = self._manager.get_enabled_constraints()
            
            # Convert to dictionary format
            result = {
                name: {
                    "enabled": constraint.enabled,
                    "config": self._get_constraint_config(constraint)
                }
                for name, constraint in enabled_constraints.items()
            }
            
            return success(result)
        except Exception as e:
            logger.error(f"Error getting active constraints: {e}")
            return error(str(e))
    
    def _get_constraint_config(self, constraint: Constraint) -> Dict[str, Any]:
        """
        Extract configuration from a constraint
        
        Args:
            constraint: The constraint to extract configuration from
            
        Returns:
            Dictionary with configuration values
        """
        config = {}
        
        # Extract weight if available
        if hasattr(constraint, "weight"):
            config["weight"] = constraint.weight
        
        # Extract relaxation level if available
        if hasattr(constraint, "relaxation_level"):
            config["relaxation_level"] = constraint.relaxation_level
        
        # Extract other public attributes
        for attr_name in dir(constraint):
            # Skip special, private, and method attributes
            if attr_name.startswith('_') or attr_name in ('enabled', 'weight', 'apply', 'validate', 'relaxation_level'):
                continue
                
            # Get the attribute if it's a simple data value
            attr = getattr(constraint, attr_name)
            if not callable(attr) and not isinstance(attr, (dict, list, set, tuple)):
                config[attr_name] = attr
        
        return config
    
    def get_constraint(self, constraint_name: str) -> Result[Dict[str, Any]]:
        """
        Get information about a specific constraint
        
        Args:
            constraint_name: The name of the constraint
            
        Returns:
            Result with constraint information
        """
        try:
            # Get constraint metadata
            metadata = self._factory.get_constraint_metadata(constraint_name)
            if not metadata:
                return error(f"Unknown constraint: {constraint_name}")
            
            # Get constraint instance if it exists
            constraint = self._manager.get_constraint(constraint_name)
            
            # Prepare result
            result = {
                "metadata": metadata.to_dict(),
                "instance": None
            }
            
            # Add instance information if available
            if constraint:
                result["instance"] = {
                    "enabled": constraint.enabled,
                    "config": self._get_constraint_config(constraint)
                }
            
            return success(result)
        except Exception as e:
            logger.error(f"Error getting constraint {constraint_name}: {e}")
            return error(str(e))
    
    def validate_constraints(self, constraint_names: List[str]) -> Result[Dict[str, Any]]:
        """
        Validate a set of constraints for compatibility
        
        Args:
            constraint_names: List of constraint names to validate
            
        Returns:
            Result with validation information
        """
        try:
            # First check if all constraints exist
            unknown_constraints = [
                name for name in constraint_names 
                if not self._factory.get_constraint_metadata(name)
            ]
            
            if unknown_constraints:
                return error(
                    f"Unknown constraints: {', '.join(unknown_constraints)}"
                )
            
            # Validate compatibility
            is_valid, errors, missing_dependencies = self._factory.validate_constraint_compatibility(
                constraint_names
            )
            
            # Prepare result
            result = {
                "valid": is_valid,
                "errors": errors,
                "missing_dependencies": missing_dependencies
            }
            
            # Calculate resolved set (with dependencies)
            resolved_constraints = self._factory.resolve_dependencies(constraint_names)
            added_dependencies = [c for c in resolved_constraints if c not in constraint_names]
            
            result["resolved_constraints"] = resolved_constraints
            result["added_dependencies"] = added_dependencies
            
            return success(result)
        except Exception as e:
            logger.error(f"Error validating constraints: {e}")
            return error(str(e))
    
    def update_constraint_configuration(
        self, 
        config: Dict[str, Dict[str, Any]]
    ) -> Result[Dict[str, Any]]:
        """
        Update the configuration for multiple constraints
        
        Args:
            config: Dictionary mapping constraint names to configurations
            
        Returns:
            Result with updated configuration information
        """
        try:
            # First validate that all constraints exist
            unknown_constraints = [
                name for name in config.keys() 
                if not self._factory.get_constraint_metadata(name)
            ]
            
            if unknown_constraints:
                return error(
                    f"Unknown constraints: {', '.join(unknown_constraints)}"
                )
            
            # Extract enabled constraints
            enabled_constraints = [
                name for name, cfg in config.items()
                if cfg.get("enabled", True)
            ]
            
            # Validate compatibility of enabled constraints
            is_valid, errors, missing_dependencies = self._factory.validate_constraint_compatibility(
                enabled_constraints
            )
            
            if not is_valid:
                return error(
                    "Invalid constraint configuration",
                    details={
                        "errors": errors,
                        "missing_dependencies": missing_dependencies
                    }
                )
            
            # Update configuration
            self._manager.configure_constraints(config)
            
            # Get updated configuration
            updated_config = self._manager.get_constraint_configuration()
            
            return success({
                "configuration": updated_config
            })
        except Exception as e:
            logger.error(f"Error updating constraint configuration: {e}")
            return error(str(e))
    
    def enable_constraint(
        self, 
        constraint_name: str, 
        config: Optional[Dict[str, Any]] = None
    ) -> Result[Dict[str, Any]]:
        """
        Enable a specific constraint
        
        Args:
            constraint_name: The name of the constraint to enable
            config: Optional configuration for the constraint
            
        Returns:
            Result with updated constraint information
        """
        try:
            # Check if constraint exists
            metadata = self._factory.get_constraint_metadata(constraint_name)
            if not metadata:
                return error(f"Unknown constraint: {constraint_name}")
            
            # Check if constraint is deprecated and provide a warning
            result_data = {}
            if metadata.deprecated:
                replacement_msg = f", use '{metadata.replacement}' instead" if metadata.replacement else ""
                warning_msg = f"Constraint '{constraint_name}' is deprecated and may be removed in a future version{replacement_msg}"
                logger.warning(warning_msg)
                result_data["warning"] = warning_msg
            
            # Get constraint or create it if it doesn't exist
            constraint = self._manager.get_constraint(constraint_name)
            if not constraint:
                constraint = self._manager.add_constraint(constraint_name, config)
                if not constraint:
                    return error(f"Failed to create constraint: {constraint_name}")
            else:
                # Update existing constraint configuration
                if config:
                    self._manager.configure_constraints({
                        constraint_name: config
                    })
            
            # Enable the constraint
            self._manager.enable_constraint(constraint_name)
            
            # Check compatibility with other enabled constraints
            enabled_constraints = [
                name for name, c in self._manager.get_enabled_constraints().items()
            ]
            
            is_valid, errors, missing_dependencies = self._factory.validate_constraint_compatibility(
                enabled_constraints
            )
            
            if not is_valid:
                # Disable the constraint if it's not compatible
                self._manager.disable_constraint(constraint_name)
                
                return error(
                    f"Enabling {constraint_name} would create compatibility issues",
                    details={
                        "errors": errors,
                        "missing_dependencies": missing_dependencies
                    }
                )
            
            # Get updated constraint
            constraint = self._manager.get_constraint(constraint_name)
            
            # Prepare result data
            result_data.update({
                "name": constraint_name,
                "enabled": constraint.enabled,
                "config": self._get_constraint_config(constraint)
            })
            
            # Return success with data and any warnings
            if "warning" in result_data:
                warning_message = result_data.pop("warning")  # Extract warning message
                return warning(
                    result_data,  # Pass data as first argument
                    message=warning_message  # Pass message as keyword argument
                )
            else:
                return success(result_data)
        except Exception as e:
            logger.error(f"Error enabling constraint {constraint_name}: {e}")
            return error(str(e))
    
    def disable_constraint(
        self, 
        constraint_name: str
    ) -> Result[Dict[str, Any]]:
        """
        Disable a specific constraint
        
        Args:
            constraint_name: The name of the constraint to disable
            
        Returns:
            Result with updated constraint information
        """
        try:
            # Check if constraint exists
            constraint = self._manager.get_constraint(constraint_name)
            if not constraint:
                return error(f"Constraint not found: {constraint_name}")
            
            # Check if any other constraints depend on this one
            dependent_constraints = []
            for name, c in self._manager.get_enabled_constraints().items():
                if name == constraint_name:
                    continue
                    
                metadata = self._factory.get_constraint_metadata(name)
                if metadata and constraint_name in metadata.requires:
                    dependent_constraints.append(name)
            
            if dependent_constraints:
                return error(
                    f"Cannot disable {constraint_name}: other constraints depend on it",
                    details={
                        "dependent_constraints": dependent_constraints
                    }
                )
            
            # Disable the constraint
            self._manager.disable_constraint(constraint_name)
            
            # After disabling, the constraint might not be available via get_constraint
            # since that method might only return enabled constraints
            # Return a success result with known information instead
            
            return success({
                "name": constraint_name,
                "enabled": False,  # We just disabled it
                "config": {}      # Empty config for disabled constraint
            })
        except Exception as e:
            logger.error(f"Error disabling constraint {constraint_name}: {e}")
            return error(str(e))
    
    def reset_constraints(self) -> Result[Dict[str, Any]]:
        """
        Reset all constraints to their default configuration
        
        Returns:
            Result with updated configuration information
        """
        try:
            # Clear existing constraints
            for name in list(self._manager.get_all_constraints().keys()):
                self._manager.remove_constraint(name)
            
            # Set up default constraints
            self._setup_default_constraints()
            
            # Get updated configuration
            updated_config = self._manager.get_constraint_configuration()
            
            return success({
                "configuration": updated_config
            })
        except Exception as e:
            logger.error(f"Error resetting constraints: {e}")
            return error(str(e))
    
    def get_constraint_manager(self) -> ModularConstraintManager:
        """
        Get the constraint manager instance
        
        This is useful for other services that need to use the constraint manager,
        such as the scheduler service.
        
        Returns:
            The ModularConstraintManager instance
        """
        return self._manager
