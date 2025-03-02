# Scheduling package
"""
Scheduling Package

This package provides the functionality for creating and managing class schedules.
It includes solvers, constraints, and utilities for working with schedule data.
"""

import logging

# Configure logging
logger = logging.getLogger(__name__)

# Initialize the dependency injection container
try:
    from .container_init import initialize_container, register_strategies, register_constraints
    
    # Initialize the container
    container = initialize_container()
    
    # Register solver strategies
    register_strategies(container)
    
    # Register constraints
    register_constraints(container)
    
    logger.info("Scheduling package initialized with dependency injection")
except ImportError:
    logger.warning("Could not initialize dependency injection container")
