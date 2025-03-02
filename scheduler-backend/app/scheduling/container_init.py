"""
Container Initialization Module

This module initializes the dependency injection container with all the services
and dependencies needed by the application. It serves as a centralized place
for configuring the dependency injection container.
"""

import logging
from typing import Dict, Any, Optional

from .dependencies import get_container, DependencyContainer
from .core import ConstraintManager, SolverConfig
from .abstractions.solver_factory import SolverFactory
from .abstractions.solver_strategy import SolverStrategy
from .abstractions.constraint_factory import ConstraintFactory, get_constraint_factory

logger = logging.getLogger(__name__)


def initialize_container(
    config: Optional[Dict[str, Any]] = None
) -> DependencyContainer:
    """
    Initialize the dependency injection container
    
    This function registers all the services and dependencies needed
    by the application, configuring them according to the provided config.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        The initialized dependency container
    """
    container = get_container()
    
    # Register core services
    container.register(ConstraintManager, singleton=True)
    container.register(SolverConfig, singleton=True)
    container.register(SolverFactory, singleton=True)
    container.register(ConstraintFactory, get_constraint_factory().__class__, singleton=True)
    
    # Create and register a constraint manager instance
    constraint_manager = ConstraintManager()
    container.register_instance(ConstraintManager, constraint_manager)
    
    # Create and register a solver factory instance
    solver_factory = SolverFactory()
    container.register_instance(SolverFactory, solver_factory)
    
    # Create and register a constraint factory instance
    constraint_factory = get_constraint_factory()
    container.register_instance(ConstraintFactory, constraint_factory)
    
    logger.info("Dependency injection container initialized")
    return container


def register_strategies(container: Optional[DependencyContainer] = None) -> None:
    """
    Register solver strategies with the factory
    
    This function registers the available solver strategies with the SolverFactory,
    making them available for use by the application.
    
    Args:
        container: Optional container instance, if not provided the global container is used
    """
    if container is None:
        container = get_container()
    
    # Get the strategy factory
    try:
        factory = container.resolve(SolverFactory)
    except KeyError:
        logger.error("SolverFactory not registered with the container")
        return
    
    # Import the necessary strategies
    from .abstractions.solver_adapter import UnifiedSolverAdapter
    
    # Register the strategies
    factory.register_strategy("unified", UnifiedSolverAdapter)
    factory.register_strategy("or_tools", UnifiedSolverAdapter)
    factory.register_strategy("genetic", UnifiedSolverAdapter)
    factory.register_strategy("hybrid", UnifiedSolverAdapter)
    
    logger.info(f"Registered {len(factory.get_strategy_names())} solver strategies")


def register_constraints(container: Optional[DependencyContainer] = None) -> None:
    """
    Register constraints with the factory
    
    This function registers the available constraints with the ConstraintFactory,
    making them available for use by the application.
    
    Args:
        container: Optional container instance, if not provided the global container is used
    """
    if container is None:
        container = get_container()
    
    # Get the constraint factory
    try:
        factory = container.resolve(ConstraintFactory)
    except KeyError:
        logger.error("ConstraintFactory not registered with the container")
        return
    
    # Import the necessary constraints
    from .constraints.availability import AvailabilityConstraint
    from .constraints.single_assignment import SingleAssignmentConstraint
    from .constraints.instructor_load import InstructorLoadConstraint
    
    # Register the constraints
    factory.register(AvailabilityConstraint, name="availability", default_enabled=True, is_relaxable=True)
    factory.register(SingleAssignmentConstraint, name="single_assignment", default_enabled=True, is_relaxable=False)
    factory.register(InstructorLoadConstraint, name="instructor_load", default_enabled=True, is_relaxable=True)
    
    logger.info(f"Registered {len(factory.get_available_constraints())} constraints")
