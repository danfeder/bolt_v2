# Scheduling package
"""
Scheduling Package

This package provides the functionality for creating and managing class schedules.
It includes solvers, constraints, and utilities for working with schedule data.
"""

import logging
import traceback
import sys

# Configure logging
logger = logging.getLogger(__name__)

# Initialize the dependency injection container with robust error handling
try:
    # Step 1: Import container initialization functions
    from .container_init import initialize_container, register_strategies, register_constraints
    
    # Step 2: Initialize the container with detailed exception handling
    try:
        container = initialize_container()
        logger.info("Dependency container initialized successfully")
        
        # Step 3: Register solver strategies
        try:
            register_strategies(container)
            logger.info("Solver strategies registered successfully")
        except Exception as strategy_error:
            error_details = traceback.format_exc()
            logger.error(f"Error registering solver strategies: {strategy_error}")
            logger.debug(f"Strategy registration error details: {error_details}")
            # Continue despite errors to allow partial functionality
        
        # Step 4: Register constraints with modular constraint system support
        try:
            # Initialize constraint factory before registration
            from .abstractions.constraint_factory import get_constraint_factory, register_default_constraints
            constraint_factory = get_constraint_factory()
            
            # Ensure default constraints are registered
            register_default_constraints()
            
            # Register constraints with the container
            register_constraints(container)
            
            # Verify the constraint system initialization
            try:
                # Try to get available constraints if the method exists
                if hasattr(constraint_factory, 'get_available_constraints'):
                    available_constraints = constraint_factory.get_available_constraints()
                    logger.info(f"Successfully registered {len(available_constraints)} constraints")
                elif hasattr(constraint_factory, 'get_constraint_names'):
                    # Fall back to get_constraint_names if available
                    constraint_names = constraint_factory.get_constraint_names()
                    logger.info(f"Successfully registered {len(constraint_names)} constraints")
                elif hasattr(constraint_factory, 'get_registrations'):
                    # Fall back to get_registrations as another alternative
                    registrations = constraint_factory.get_registrations()
                    logger.info(f"Successfully registered {len(registrations)} constraints")
                else:
                    logger.info("Constraints initialized successfully (count unavailable)")
            except Exception as verify_error:
                logger.warning(f"Could not verify constraint registration: {verify_error}")
                logger.info("Constraints initialized with minimal verification")
            
            # Verify modular constraint system functionality is available
            if hasattr(constraint_factory, 'validate_constraint_compatibility'):
                logger.info("Constraint compatibility validation is available")
        except Exception as constraint_error:
            error_details = traceback.format_exc()
            logger.error(f"Error registering constraints: {constraint_error}")
            logger.debug(f"Constraint registration error details: {error_details}")
            # Continue despite errors to allow partial functionality
        
        logger.info("Scheduling package initialized with dependency injection")
    except Exception as init_error:
        error_details = traceback.format_exc()
        logger.error(f"Container initialization error: {init_error}")
        logger.debug(f"Initialization error details: {error_details}")
        
        # Provide fallback container for basic functionality
        from .dependencies import get_container
        container = get_container()
        logger.warning("Using fallback container with limited functionality")
except ImportError as import_error:
    logger.warning(f"Could not initialize dependency injection container: {import_error}")
