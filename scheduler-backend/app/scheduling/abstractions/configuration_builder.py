"""
Configuration Builder for Solver Configuration

This module provides a builder pattern implementation for creating and configuring
solver configuration objects. It offers a fluent API for configuring solvers with
sensible defaults and validation.
"""

from typing import Dict, Any, List, Optional, Type, Union, Set
import logging

from .solver_config import SolverConfiguration, SolverType, OptimizationLevel
from ..constraints.relaxation import RelaxationLevel

logger = logging.getLogger(__name__)


class ConfigurationBuilder:
    """
    Builder for creating solver configuration objects
    
    This class follows the builder pattern to provide a fluent API for
    creating and configuring solver configuration objects with proper
    validation and sensible defaults.
    """
    
    def __init__(self):
        """Initialize the builder with default values"""
        # Initialize with default values
        self._config = {
            'solver_type': SolverType.UNIFIED,
            'optimization_level': OptimizationLevel.BALANCED,
            'timeout_seconds': 60,
            'max_iterations': 1000,
            'enable_relaxation': True,
            'relaxation_level': RelaxationLevel.NONE,
            'weights': {},
            'options': {}
        }
    
    def with_solver_type(self, solver_type: Union[str, SolverType]) -> 'ConfigurationBuilder':
        """
        Set the solver type
        
        Args:
            solver_type: The solver type (string or enum)
            
        Returns:
            The builder for chaining
        """
        if isinstance(solver_type, str):
            try:
                solver_type = SolverType[solver_type.upper()]
            except KeyError:
                logger.warning(f"Invalid solver type: {solver_type}. Using UNIFIED instead.")
                solver_type = SolverType.UNIFIED
        
        self._config['solver_type'] = solver_type
        return self
    
    def with_optimization_level(self, level: Union[str, OptimizationLevel]) -> 'ConfigurationBuilder':
        """
        Set the optimization level
        
        Args:
            level: The optimization level (string or enum)
            
        Returns:
            The builder for chaining
        """
        if isinstance(level, str):
            try:
                level = OptimizationLevel[level.upper()]
            except KeyError:
                logger.warning(f"Invalid optimization level: {level}. Using BALANCED instead.")
                level = OptimizationLevel.BALANCED
        
        self._config['optimization_level'] = level
        return self
    
    def with_timeout(self, seconds: int) -> 'ConfigurationBuilder':
        """
        Set the solver timeout in seconds
        
        Args:
            seconds: The timeout in seconds
            
        Returns:
            The builder for chaining
        """
        if seconds <= 0:
            logger.warning(f"Invalid timeout: {seconds}. Using 60 seconds instead.")
            seconds = 60
            
        self._config['timeout_seconds'] = seconds
        return self
    
    def with_max_iterations(self, iterations: int) -> 'ConfigurationBuilder':
        """
        Set the maximum number of iterations
        
        Args:
            iterations: The maximum number of iterations
            
        Returns:
            The builder for chaining
        """
        if iterations <= 0:
            logger.warning(f"Invalid max iterations: {iterations}. Using 1000 instead.")
            iterations = 1000
            
        self._config['max_iterations'] = iterations
        return self
    
    def with_relaxation(self, enabled: bool = True, level: Union[str, RelaxationLevel] = RelaxationLevel.NONE) -> 'ConfigurationBuilder':
        """
        Configure constraint relaxation
        
        Args:
            enabled: Whether relaxation is enabled
            level: The relaxation level (string or enum)
            
        Returns:
            The builder for chaining
        """
        self._config['enable_relaxation'] = enabled
        
        if isinstance(level, str):
            try:
                level = RelaxationLevel[level.upper()]
            except KeyError:
                logger.warning(f"Invalid relaxation level: {level}. Using NONE instead.")
                level = RelaxationLevel.NONE
                
        self._config['relaxation_level'] = level
        return self
    
    def with_weight(self, name: str, value: int) -> 'ConfigurationBuilder':
        """
        Set a specific weight
        
        Args:
            name: The weight name
            value: The weight value
            
        Returns:
            The builder for chaining
        """
        if 'weights' not in self._config:
            self._config['weights'] = {}
            
        self._config['weights'][name] = value
        return self
    
    def with_weights(self, weights: Dict[str, int]) -> 'ConfigurationBuilder':
        """
        Set multiple weights at once
        
        Args:
            weights: Dictionary of weight name to value
            
        Returns:
            The builder for chaining
        """
        if not isinstance(weights, dict):
            logger.warning(f"Invalid weights: {weights}. Must be a dictionary.")
            return self
            
        if 'weights' not in self._config:
            self._config['weights'] = {}
            
        self._config['weights'].update(weights)
        return self
    
    def with_option(self, name: str, value: Any) -> 'ConfigurationBuilder':
        """
        Set a specific solver option
        
        Args:
            name: The option name
            value: The option value
            
        Returns:
            The builder for chaining
        """
        if 'options' not in self._config:
            self._config['options'] = {}
            
        self._config['options'][name] = value
        return self
        
    def with_options(self, options: Dict[str, Any]) -> 'ConfigurationBuilder':
        """
        Set multiple solver options at once
        
        Args:
            options: Dictionary of option name to value
            
        Returns:
            The builder for chaining
        """
        if not isinstance(options, dict):
            logger.warning(f"Invalid options: {options}. Must be a dictionary.")
            return self
            
        if 'options' not in self._config:
            self._config['options'] = {}
            
        self._config['options'].update(options)
        return self
    
    def build(self) -> SolverConfiguration:
        """
        Build the configuration object
        
        Returns:
            A SolverConfiguration object with the configured values
        """
        # Create a new configuration object
        config = SolverConfiguration()
        
        # Set all the configured values
        config.solver_type = self._config['solver_type']
        config.optimization_level = self._config['optimization_level']
        config.timeout_seconds = self._config['timeout_seconds']
        config.max_iterations = self._config['max_iterations']
        config.enable_relaxation = self._config['enable_relaxation']
        config.relaxation_level = self._config['relaxation_level']
        config.weights = self._config['weights'].copy()
        config.options = self._config['options'].copy()
        
        return config
    
    def build_dict(self) -> Dict[str, Any]:
        """
        Build a configuration dictionary
        
        Returns:
            A dictionary with the configured values
        """
        return self._config.copy()
    

# Convenience function to create a builder
def configure() -> ConfigurationBuilder:
    """
    Create a new configuration builder
    
    Returns:
        A new ConfigurationBuilder instance
    """
    return ConfigurationBuilder()


# Common configuration presets
def create_fast_config() -> SolverConfiguration:
    """
    Create a configuration preset optimized for speed
    
    Returns:
        A SolverConfiguration optimized for speed
    """
    return (ConfigurationBuilder()
            .with_solver_type(SolverType.OR_TOOLS)
            .with_optimization_level(OptimizationLevel.SPEED)
            .with_timeout(30)
            .with_max_iterations(500)
            .with_relaxation(True, RelaxationLevel.MEDIUM)
            .build())


def create_quality_config() -> SolverConfiguration:
    """
    Create a configuration preset optimized for solution quality
    
    Returns:
        A SolverConfiguration optimized for quality
    """
    return (ConfigurationBuilder()
            .with_solver_type(SolverType.HYBRID)
            .with_optimization_level(OptimizationLevel.QUALITY)
            .with_timeout(120)
            .with_max_iterations(2000)
            .with_relaxation(True, RelaxationLevel.LOW)
            .build())


def create_balanced_config() -> SolverConfiguration:
    """
    Create a balanced configuration preset
    
    Returns:
        A balanced SolverConfiguration
    """
    return (ConfigurationBuilder()
            .with_solver_type(SolverType.UNIFIED)
            .with_optimization_level(OptimizationLevel.BALANCED)
            .with_timeout(60)
            .with_max_iterations(1000)
            .with_relaxation(True, RelaxationLevel.MINIMAL)
            .build())
