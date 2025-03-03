"""
Solver Factory Module

This module defines the factory for creating solver strategies.
It provides a centralized way to create and configure solver strategies.
"""

from typing import Dict, Any, List, Optional, Set, Type, Union
import logging

from ...models import ScheduleRequest
from .solver_strategy import SolverStrategy
from .solver_config import SolverConfiguration, SolverType
from .configuration_builder import ConfigurationBuilder, configure

logger = logging.getLogger(__name__)


class SolverFactory:
    """
    Factory for creating solver strategies
    
    This class provides methods for creating and configuring solver strategies
    based on the request and configuration.
    """
    
    def __init__(self):
        """Initialize the factory"""
        self._strategies: Dict[str, Type[SolverStrategy]] = {}
    
    def register_strategy(self, name: str, strategy_class: Type[SolverStrategy]) -> None:
        """
        Register a solver strategy
        
        Args:
            name: The strategy name
            strategy_class: The strategy class
        """
        self._strategies[name] = strategy_class
        logger.info(f"Registered solver strategy: {name}")
    
    def create_strategy(
        self,
        name: str,
        config: Optional[SolverConfiguration] = None
    ) -> Optional[SolverStrategy]:
        """
        Create a solver strategy by name
        
        Args:
            name: The strategy name
            config: Optional configuration for the strategy
            
        Returns:
            A new solver strategy instance, or None if not found
        """
        if name not in self._strategies:
            logger.warning(f"Unknown solver strategy: {name}")
            return None
        
        strategy_class = self._strategies[name]
        try:
            strategy = strategy_class(name)
            
            # Configure the strategy with the provided configuration
            if config:
                self._configure_strategy(strategy, config)
                
            return strategy
        except Exception as e:
            logger.error(f"Error creating solver strategy {name}: {e}")
            return None
    
    def _configure_strategy(self, strategy: SolverStrategy, config: SolverConfiguration) -> None:
        """
        Configure a strategy with the provided configuration
        
        Args:
            strategy: The strategy to configure
            config: The configuration
        """
        # Convert the configuration to a dictionary for the strategy
        config_dict = {
            'solver_type': config.solver_type.name if hasattr(config.solver_type, 'name') else config.solver_type,
            'optimization_level': config.optimization_level.name if hasattr(config.optimization_level, 'name') else config.optimization_level,
            'timeout_seconds': config.timeout_seconds,
            'max_iterations': config.max_iterations,
            'enable_relaxation': config.enable_relaxation,
            'relaxation_level': config.relaxation_level.name if hasattr(config.relaxation_level, 'name') else config.relaxation_level,
            'weights': config.weights,
            'options': config.options
        }
        
        # Configure the strategy with the dictionary
        strategy.configure(config_dict)
    
    def create_strategy_with_builder(
        self,
        name: str,
        builder_fn=None
    ) -> Optional[SolverStrategy]:
        """
        Create a solver strategy using a builder function
        
        Args:
            name: The strategy name
            builder_fn: Optional function that takes a ConfigurationBuilder and returns it configured
            
        Returns:
            A new solver strategy instance, or None if not found
        """
        if name not in self._strategies:
            logger.warning(f"Unknown solver strategy: {name}")
            return None
        
        # Create a new builder with default configuration
        builder = configure()
        
        # Apply the builder function if provided
        if builder_fn:
            builder = builder_fn(builder)
        
        # Build the configuration
        config = builder.build()
        
        # Create the strategy
        return self.create_strategy(name, config)
    
    def create_strategy_for_request(
        self,
        request: ScheduleRequest,
        config: SolverConfiguration
    ) -> Optional[SolverStrategy]:
        """
        Create the best solver strategy for a request
        
        This method selects the best strategy for the request and configuration,
        by evaluating each registered strategy's capability to solve the request.
        
        Args:
            request: The schedule request
            config: The solver configuration
            
        Returns:
            The best solver strategy for the request, or None if no strategy can solve it
        """
        # Determine the strategy name from the configuration
        strategy_name = None
        
        if hasattr(config, 'solver_type') and config.solver_type:
            strategy_type = config.solver_type
            if hasattr(strategy_type, 'name'):
                strategy_name = strategy_type.name.lower()
            else:
                strategy_name = str(strategy_type).lower()
        
        # If no strategy specified in configuration, evaluate available strategies
        if not strategy_name or strategy_name not in self._strategies:
            logger.info(f"No specific strategy requested, evaluating available strategies")
            
            # Find strategies that can solve the request
            capable_strategies = []
            for name, strategy_class in self._strategies.items():
                try:
                    # Create a temporary instance to check if it can solve the request
                    temp_strategy = strategy_class(name)
                    can_solve, reason = temp_strategy.can_solve(request)
                    
                    if can_solve:
                        capable_strategies.append((name, strategy_class))
                    else:
                        logger.debug(f"Strategy {name} cannot solve the request: {reason}")
                except Exception as e:
                    logger.warning(f"Error evaluating strategy {name}: {e}")
            
            # If no capable strategies found, return None
            if not capable_strategies:
                logger.warning(f"No strategy found that can solve the request")
                return None
            
            # Select the first capable strategy (could be improved with scoring)
            strategy_name, strategy_class = capable_strategies[0]
            logger.info(f"Selected strategy {strategy_name} for the request")
        
        # Create the strategy with the given configuration
        return self.create_strategy(strategy_name, config)
    
    def get_strategy_names(self) -> List[str]:
        """
        Get the names of all registered strategies
        
        Returns:
            A list of strategy names
        """
        return list(self._strategies.keys())
    
    def get_strategy_capabilities(self, name: str) -> Set[str]:
        """
        Get the capabilities of a strategy
        
        Args:
            name: The strategy name
            
        Returns:
            A set of capability strings, or an empty set if not found
        """
        if name not in self._strategies:
            logger.warning(f"Unknown solver strategy: {name}")
            return set()
        
        strategy_class = self._strategies[name]
        try:
            strategy = strategy_class(name)
            return strategy.get_capabilities()
        except Exception as e:
            logger.error(f"Error getting capabilities for {name}: {e}")
            return set()
