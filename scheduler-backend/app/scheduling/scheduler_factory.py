"""
Scheduler Factory Module

This module provides a high-level API for creating schedulers and executing
scheduling operations. It serves as a façade over the scheduling system,
isolating clients from the complexity of the underlying implementation.
"""

from typing import Dict, Any, Optional
import logging

from ..models import ScheduleRequest, ScheduleResponse
from .abstractions import (
    SolverFactory,
    SolverConfiguration, 
    SolverType,
    OptimizationLevel,
    SolverConfigurationBuilder,
    SolverAdapterFactory
)

logger = logging.getLogger(__name__)


class SchedulerFactory:
    """
    Factory for creating and executing schedulers
    
    This class provides a simplified interface for creating and executing
    schedulers, abstracting away the complexity of the underlying implementation.
    """
    
    def __init__(self):
        """Initialize the factory"""
        self._solver_factory = SolverFactory()
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """Register default solver strategies"""
        # For now, we're adapting the existing solvers
        # Later, we'll register actual implementations of SolverStrategy
        
        # Register OR-Tools adapter
        or_tools_adapter = SolverAdapterFactory.create_adapter(SolverType.OR_TOOLS)
        self._solver_factory.register_strategy("or_tools", type(or_tools_adapter))
        
        # Register Genetic adapter
        genetic_adapter = SolverAdapterFactory.create_adapter(SolverType.GENETIC)
        self._solver_factory.register_strategy("genetic", type(genetic_adapter))
        
        # Register Hybrid adapter
        hybrid_adapter = SolverAdapterFactory.create_adapter(SolverType.HYBRID)
        self._solver_factory.register_strategy("hybrid", type(hybrid_adapter))
    
    def create_scheduler(
        self,
        request: ScheduleRequest,
        config: Optional[Dict[str, Any]] = None
    ) -> ScheduleResponse:
        """
        Create a schedule for the given request
        
        This is the main entry point for scheduling. It selects an appropriate
        solver strategy based on the request and configuration, and executes it.
        
        Args:
            request: The scheduling request
            config: Optional configuration dictionary
            
        Returns:
            The scheduling response
        """
        # Create a configuration object
        if config is None:
            # Use default configuration
            solver_config = SolverConfiguration.create_standard()
        else:
            # Create from dictionary
            solver_config = SolverConfiguration.from_dict(config)
            
            # If config doesn't specify a solver type, use HYBRID as default
            if "solver_type" not in config:
                solver_config.solver_type = SolverType.HYBRID
        
        # Check if the solver type is valid
        try:
            # This will attempt to convert the string value to a SolverType enum
            if isinstance(solver_config.solver_type, str):
                solver_config.solver_type = SolverType[solver_config.solver_type.upper()]
        except (KeyError, ValueError):
            # If the conversion fails, it's an invalid solver type
            logger.error(f"Invalid solver type: {solver_config.solver_type}")
            raise ValueError(f"Invalid solver type: {solver_config.solver_type}")
        
        # Create a strategy for the request
        strategy = self._solver_factory.create_strategy_for_request(request, solver_config)
        if not strategy:
            logger.error(f"Failed to create strategy for request: {request.id}")
            raise ValueError("No suitable strategy found for the request")
        
        # Solve the request
        result = strategy.solve(request, solver_config.to_dict())
        
        # Convert result to response
        if result.success:
            if isinstance(result.schedule, ScheduleResponse):
                return result.schedule
            else:
                return result.to_response()
        else:
            raise RuntimeError(f"Failed to solve request: {result.error}")
    
    @staticmethod
    def create_configuration_builder() -> SolverConfigurationBuilder:
        """
        Create a configuration builder
        
        This is a convenience method for creating a configuration builder,
        which provides a fluent interface for building configurations.
        
        Returns:
            A new SolverConfigurationBuilder instance
        """
        return SolverConfigurationBuilder()
    
    @staticmethod
    def create_default_configuration() -> SolverConfiguration:
        """
        Create a default configuration
        
        Returns:
            A default SolverConfiguration instance
        """
        return SolverConfiguration.create_standard()
    
    @staticmethod
    def create_minimal_configuration() -> SolverConfiguration:
        """
        Create a minimal configuration for fast solving
        
        Returns:
            A minimal SolverConfiguration instance
        """
        return SolverConfiguration.create_minimal()
    
    @staticmethod
    def create_intensive_configuration() -> SolverConfiguration:
        """
        Create an intensive configuration for higher quality
        
        Returns:
            An intensive SolverConfiguration instance
        """
        return SolverConfiguration.create_intensive()
