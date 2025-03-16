"""
Container Initialization Module

This module initializes the dependency injection container with all the services
and dependencies needed by the application. It serves as a centralized place
for configuring the dependency injection container.
"""

import logging
import traceback
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
    logger.info("Initializing dependency container")
    container = get_container()
    
    # Register core services with better error handling
    try:
        # Register core services
        container.register(ConstraintManager, singleton=True)
        container.register(SolverConfig, singleton=True)
        container.register(SolverFactory, singleton=True)
        
        # Register the constraint factory
        factory_instance = get_constraint_factory()
        container.register(ConstraintFactory, factory_instance.__class__, singleton=True)
        container.register_instance(ConstraintFactory, factory_instance)
        
        # Create and register a constraint manager instance
        constraint_manager = ConstraintManager()
        container.register_instance(ConstraintManager, constraint_manager)
        
        # Create and register a solver factory instance
        solver_factory = SolverFactory()
        container.register_instance(SolverFactory, solver_factory)
        
        logger.info("Core services registered successfully")
    except Exception as e:
        logger.error(f"Error registering core services: {e}")
        logger.debug(traceback.format_exc())
        raise ValueError(f"Failed to initialize container: {e}")
    
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
    from .abstractions.unified_strategy import UnifiedSolverStrategy
    from .abstractions.concrete_strategies import ORToolsStrategy, GeneticAlgorithmStrategy, HybridStrategy
    
    # Register the strategies using the direct implementations instead of adapters
    factory.register_strategy("unified", UnifiedSolverStrategy)
    factory.register_strategy("or_tools", ORToolsStrategy)
    factory.register_strategy("genetic", GeneticAlgorithmStrategy)
    factory.register_strategy("hybrid", HybridStrategy)
    
    # Register the adapter for backward compatibility
    factory.register_strategy("unified_adapter", UnifiedSolverAdapter)
    
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
    
    # Register constraints with modular constraint system
    try:
        # Check if factory has the required methods for modular constraint system
        required_attrs = ['register', 'create_constraint']
        has_required_attrs = all(hasattr(factory, attr) for attr in required_attrs)
        
        if has_required_attrs:
            # Try to import and use the constraint factory features
            try:
                # Check if the register_default_constraints function is available
                try:
                    from .abstractions.constraint_factory import register_default_constraints
                    
                    # Register default constraints without categories
                    register_default_constraints()
                    logger.info("Successfully registered default constraints using auto-registration")
                except Exception as reg_error:
                    logger.warning(f"Error in default constraint registration: {reg_error}")
                    logger.info("Will attempt manual constraint registration")
                    
                    # Check for constraint compatibility validation feature
                    if hasattr(factory, 'validate_constraint_compatibility'):
                        try:
                            # Get constraints from registrations since get_available_constraints might not exist
                            constraints = list(factory.get_registrations().keys())
                                
                            factory.validate_constraint_compatibility(constraints)
                            logger.info("Constraint compatibility validation successful")
                        except Exception as compat_error:
                            logger.warning(f"Constraint compatibility validation issue: {compat_error}")
                
                # Configure the standard constraint manager
                try:
                    # Get or create a constraint manager instance
                    try:
                        constraint_manager = container.resolve(ConstraintManager)
                    except KeyError:
                        constraint_manager = ConstraintManager()
                        container.register_instance(ConstraintManager, constraint_manager)
                    
                    # Set the factory if possible
                    if hasattr(constraint_manager, 'set_factory'):
                        constraint_manager.set_factory(factory)
                        
                    logger.info("Constraint manager configured successfully")
                except Exception as manager_error:
                    logger.warning(f"Error configuring constraint manager: {manager_error}")
                    
            except ImportError as auto_import_error:
                logger.warning(f"Auto-registration not available: {auto_import_error}. Using manual constraint registration.")
                # Fall through to manual registration
        else:
            logger.warning(f"Factory missing required methods for enhanced constraint system. Using basic constraints.")
    except Exception as e:
        logger.warning(f"Could not initialize modular constraint system: {e}. Falling back to basic constraints.")
    
    # Register basic constraints (this will run if registration fails)
    # Use try-except for each constraint to avoid one failure affecting others
    registered_count = 0
    
    try:
        from .constraints.availability import AvailabilityConstraint
        factory.register(AvailabilityConstraint, name="availability", default_enabled=True, is_relaxable=True)
        registered_count += 1
        logger.debug("Registered AvailabilityConstraint")
    except ImportError as e:
        logger.warning(f"Could not import AvailabilityConstraint: {e}")
    
    try:
        from .constraints.single_assignment import SingleAssignmentConstraint
        factory.register(SingleAssignmentConstraint, name="single_assignment", default_enabled=True, is_relaxable=False)
        registered_count += 1
        logger.debug("Registered SingleAssignmentConstraint")
    except ImportError as e:
        logger.warning(f"Could not import SingleAssignmentConstraint: {e}")
    
    try:
        from .constraints.instructor_load import InstructorLoadConstraint
        factory.register(InstructorLoadConstraint, name="instructor_load", default_enabled=True, is_relaxable=True)
        registered_count += 1
        logger.debug("Registered InstructorLoadConstraint")
    except ImportError as e:
        logger.warning(f"Could not import InstructorLoadConstraint: {e}")
    
    # Log the results
    logger.info(f"Registered {registered_count} constraints")
