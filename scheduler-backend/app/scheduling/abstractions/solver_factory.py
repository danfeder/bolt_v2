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
        # This is a hook for subclasses to customize strategy configuration
        pass
    
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
        # Use the solver type from the configuration
        if config.solver_type == SolverType.OR_TOOLS:
            strategy_name = "or_tools"
        elif config.solver_type == SolverType.GENETIC:
            strategy_name = "genetic"
        elif config.solver_type == SolverType.HYBRID:
            strategy_name = "hybrid"
        else:  # META or any other
            # For META, we need to intelligently select the best strategy
            return self._select_best_strategy(request, config)
        
        # Create the strategy
        strategy = self.create_strategy(strategy_name, config)
        if not strategy:
            logger.warning(
                f"Failed to create {strategy_name} strategy, "
                f"falling back to best available strategy"
            )
            return self._select_best_strategy(request, config)
        
        # Check if the strategy can solve the request
        can_solve, reason = strategy.can_solve(request)
        if not can_solve:
            logger.warning(
                f"Strategy {strategy_name} cannot solve the request: {reason}. "
                f"Falling back to best available strategy"
            )
            return self._select_best_strategy(request, config)
        
        return strategy
    
    def _select_best_strategy(
        self,
        request: ScheduleRequest,
        config: SolverConfiguration
    ) -> Optional[SolverStrategy]:
        """
        Select the best strategy for a request
        
        This method evaluates each registered strategy and selects the best one
        based on capabilities and suitability for the request.
        
        Args:
            request: The schedule request
            config: The solver configuration
            
        Returns:
            The best solver strategy for the request, or None if no strategy can solve it
        """
        # Algorithm to select the best strategy:
        # 1. Start with all registered strategies
        # 2. Filter out strategies that cannot solve the request
        # 3. Score remaining strategies based on capabilities match
        # 4. Return the highest scoring strategy
        
        candidates = []
        for name, strategy_class in self._strategies.items():
            # Create the strategy
            strategy = self.create_strategy(name, config)
            if not strategy:
                continue
            
            # Check if the strategy can solve the request
            can_solve, reason = strategy.can_solve(request)
            if not can_solve:
                logger.debug(f"Strategy {name} cannot solve the request: {reason}")
                continue
            
            # Add to candidates
            candidates.append((strategy, self._calculate_strategy_score(strategy, request, config)))
        
        # Sort candidates by score (descending)
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Return the highest scoring strategy, or None if no candidates
        if not candidates:
            logger.error("No suitable solver strategy found for the request")
            return None
        
        selected_strategy, score = candidates[0]
        logger.info(
            f"Selected strategy {selected_strategy.name} with score {score} "
            f"from {len(candidates)} candidates"
        )
        return selected_strategy
    
    def _calculate_strategy_score(
        self,
        strategy: SolverStrategy,
        request: ScheduleRequest,
        config: SolverConfiguration
    ) -> float:
        """
        Calculate a score for a strategy based on its suitability for the request
        
        The score is based on the strategy's capabilities and how well they match
        the requirements of the request and configuration.
        
        Args:
            strategy: The strategy to score
            request: The schedule request
            config: The solver configuration
            
        Returns:
            A score between 0 and 100, where higher is better
        """
        # This is a simplified scoring algorithm
        # A real implementation would consider many factors
        
        # Start with a base score
        score = 50.0
        
        # Get the strategy's capabilities
        capabilities = strategy.get_capabilities()
        
        # Score based on optimization level
        if "intensive_optimization" in capabilities and config.optimization_level.name == "INTENSIVE":
            score += 20
        elif "standard_optimization" in capabilities and config.optimization_level.name == "STANDARD":
            score += 15
        elif "minimal_optimization" in capabilities and config.optimization_level.name == "MINIMAL":
            score += 10
        
        # Score based on request size
        num_classes = len(request.classes)
        num_instructors = len(set(a.instructorId for a in request.instructorAvailability))
        
        if num_classes > 100 or num_instructors > 20:
            # Large problem
            if "large_scale" in capabilities:
                score += 20
            else:
                score -= 20
        elif num_classes > 50 or num_instructors > 10:
            # Medium problem
            if "medium_scale" in capabilities:
                score += 15
            elif "large_scale" in capabilities:
                score += 10
            else:
                score -= 10
        else:
            # Small problem
            score += 10
        
        # Score based on specific features
        if config.enable_relaxation and "constraint_relaxation" in capabilities:
            score += 10
        if config.enable_distribution_optimization and "distribution_optimization" in capabilities:
            score += 10
        if config.enable_workload_balancing and "workload_balancing" in capabilities:
            score += 10
        
        # Cap the score between 0 and 100
        return max(0, min(100, score))
    
    def get_strategy_names(self) -> List[str]:
        """
        Get the names of all registered strategies
        
        Returns:
            List of strategy names
        """
        return list(self._strategies.keys())
