"""
Solver Manager Module

This module defines the SolverManager class, which provides a high-level
interface for solving scheduling problems using the strategy pattern.
"""

from typing import Dict, Any, List, Optional, Union
import logging
import time

from ...models import (
    ScheduleRequest,
    ScheduleResponse,
    ScheduleAssignment,
    ScheduleMetadata
)
from .solver_strategy import SolverStrategy, SolverResult
from .solver_config import (
    SolverConfiguration,
    SolverType,
    OptimizationLevel,
    SolverConfigurationBuilder
)
from .solver_factory import SolverFactory
from .concrete_strategies import ORToolsStrategy, GeneticAlgorithmStrategy, HybridStrategy

logger = logging.getLogger(__name__)


class SolverManager:
    """
    High-level manager for solving scheduling problems
    
    This class provides a simple interface for solving scheduling problems
    using the strategy pattern. It manages the creation and configuration
    of solver strategies based on the request and configuration.
    """
    
    def __init__(self):
        """Initialize the manager"""
        self._factory = SolverFactory()
        self._register_default_strategies()
    
    def _register_default_strategies(self) -> None:
        """Register default solver strategies"""
        self._factory.register_strategy("or_tools", ORToolsStrategy)
        self._factory.register_strategy("genetic", GeneticAlgorithmStrategy)
        self._factory.register_strategy("hybrid", HybridStrategy)
    
    def solve(
        self,
        request: ScheduleRequest,
        config: Optional[Union[Dict[str, Any], SolverConfiguration]] = None
    ) -> ScheduleResponse:
        """
        Solve a scheduling problem
        
        This method selects an appropriate solver strategy based on the
        request and configuration, then uses it to solve the problem.
        
        Args:
            request: The scheduling request
            config: Configuration for the solver (optional)
            
        Returns:
            The schedule response
        """
        # Convert config to SolverConfiguration if it's a dict
        if isinstance(config, dict):
            config = SolverConfiguration.from_dict(config)
        elif config is None:
            config = SolverConfiguration()
        
        logger.info(
            f"Solving schedule request with {len(request.classes)} classes and "
            f"{len(request.instructorAvailability)} instructor availability records"
        )
        
        # Record start time
        start_time = time.time()
        
        try:
            # Create a strategy for the request
            strategy = self._factory.create_strategy_for_request(request, config)
            if not strategy:
                logger.error("No suitable solver strategy found")
                return ScheduleResponse(
                    assignments=[],
                    metadata=ScheduleMetadata(
                        duration_ms=int((time.time() - start_time) * 1000),
                        solutions_found=0,
                        score=0,
                        gap=0.0,  # Adding the gap field
                        error="No suitable solver strategy found"
                    )
                )
            
            logger.info(f"Selected solver strategy: {strategy.name}")
            
            # Solve the problem
            result = strategy.solve(request, config.to_dict())
            
            # Calculate total duration
            total_duration_ms = int((time.time() - start_time) * 1000)
            
            # Update duration in metadata
            if result.metadata:
                result.metadata["runtime_ms"] = total_duration_ms
            
            # Convert result to response
            response = result.to_response()
            
            logger.info(
                f"Solved schedule request in {total_duration_ms}ms "
                f"with {len(response.assignments)} assignments"
            )
            
            return response
        except Exception as e:
            logger.error(f"Error solving schedule request: {e}")
            
            # Calculate total duration
            total_duration_ms = int((time.time() - start_time) * 1000)
            
            return ScheduleResponse(
                assignments=[],
                metadata=ScheduleMetadata(
                    duration_ms=total_duration_ms,
                    solutions_found=0,
                    score=0,
                    gap=0.0,  # Adding the gap field
                    error=f"Error solving schedule request: {str(e)}"
                )
            )
    
    def register_strategy(self, name: str, strategy_class: type) -> None:
        """
        Register a custom solver strategy
        
        Args:
            name: The strategy name
            strategy_class: The strategy class
        """
        self._factory.register_strategy(name, strategy_class)
    
    def get_available_strategies(self) -> List[str]:
        """
        Get the names of all available solver strategies
        
        Returns:
            List of strategy names
        """
        return self._factory.get_strategy_names()
    
    @classmethod
    def create_default(cls) -> 'SolverManager':
        """
        Create a solver manager with default strategies
        
        Returns:
            A new SolverManager instance with default strategies
        """
        return cls()
    
    @classmethod
    def create_standard_configuration(cls) -> SolverConfiguration:
        """
        Create a standard solver configuration
        
        Returns:
            A standard SolverConfiguration instance
        """
        return SolverConfiguration.create_standard()
    
    @classmethod
    def create_intensive_configuration(cls) -> SolverConfiguration:
        """
        Create an intensive solver configuration for higher quality
        
        Returns:
            An intensive SolverConfiguration instance
        """
        return SolverConfiguration.create_intensive()
    
    @classmethod
    def create_minimal_configuration(cls) -> SolverConfiguration:
        """
        Create a minimal solver configuration for fast solving
        
        Returns:
            A minimal SolverConfiguration instance
        """
        return SolverConfiguration.create_minimal()
    
    @classmethod
    def create_custom_configuration(cls) -> SolverConfigurationBuilder:
        """
        Create a custom solver configuration using the builder pattern
        
        Returns:
            A SolverConfigurationBuilder instance
        """
        return SolverConfigurationBuilder()
