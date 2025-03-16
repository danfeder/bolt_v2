"""
Constraints API Router

This module provides API endpoints for managing the modular constraint system.
It exposes operations to list, configure, and validate constraints without
relying on category-based organization.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException

from ...services.service_factory import get_service_factory, ServiceFactory
from ...services.constraint_service import ConstraintService
from ..response_handler import handle_service_result, create_error_response
from ...scheduling.abstractions.modular_constraint_factory import (
    get_modular_constraint_factory, 
    ConstraintMetadata
)

# Set up logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/constraints",
    tags=["Scheduling Constraints"],
    responses={
        404: {"description": "Not found"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"},
    },
)


def get_constraint_service(
    service_factory: ServiceFactory = Depends(get_service_factory)
) -> ConstraintService:
    """
    Dependency to get the constraint service instance.
    
    Args:
        service_factory: The service factory instance
        
    Returns:
        The ConstraintService instance
    """
    return service_factory.get_constraint_service()


@router.get(
    "",
    summary="Get all available constraints",
    description="""
    Lists all available constraints in the system.
    
    This endpoint returns information about all registered constraints, including
    their names, descriptions, compatibility relationships, and configuration options.
    """
)
async def get_all_constraints(
    constraint_service: ConstraintService = Depends(get_constraint_service)
) -> Dict[str, Any]:
    """
    Get all available constraints
    
    Args:
        constraint_service: The constraint service
        
    Returns:
        A list of all available constraints with their metadata
    """
    logger.info("API: Getting all available constraints")
    result = constraint_service.get_all_constraints()
    return handle_service_result(result, "Constraints retrieved successfully")


@router.get(
    "/active",
    summary="Get active constraints",
    description="""
    Lists all currently active constraints in the system.
    
    This endpoint returns information about which constraints are currently
    enabled and their configurations.
    """
)
async def get_active_constraints(
    constraint_service: ConstraintService = Depends(get_constraint_service)
) -> Dict[str, Any]:
    """
    Get active constraints
    
    Args:
        constraint_service: The constraint service
        
    Returns:
        A list of active constraints with their configurations
    """
    logger.info("API: Getting active constraints")
    result = constraint_service.get_active_constraints()
    return handle_service_result(result, "Active constraints retrieved successfully")


@router.get(
    "/{constraint_name}",
    summary="Get constraint details",
    description="""
    Get detailed information about a specific constraint.
    
    This endpoint returns metadata, compatibility information, and
    current configuration for the specified constraint.
    """
)
async def get_constraint(
    constraint_name: str,
    constraint_service: ConstraintService = Depends(get_constraint_service)
) -> Dict[str, Any]:
    """
    Get information about a specific constraint
    
    Args:
        constraint_name: The name of the constraint
        constraint_service: The constraint service
        
    Returns:
        Detailed information about the constraint
    """
    logger.info(f"API: Getting constraint details for {constraint_name}")
    result = constraint_service.get_constraint(constraint_name)
    return handle_service_result(result, f"Constraint {constraint_name} retrieved successfully")


@router.post(
    "/validate",
    summary="Validate constraint configuration",
    description="""
    Validate a set of constraints for compatibility.
    
    This endpoint checks if the provided constraints can be used together
    and returns any compatibility issues or dependency requirements.
    """
)
async def validate_constraints(
    constraints: List[str],
    constraint_service: ConstraintService = Depends(get_constraint_service)
) -> Dict[str, Any]:
    """
    Validate a set of constraints for compatibility
    
    Args:
        constraints: List of constraint names to validate
        constraint_service: The constraint service
        
    Returns:
        Validation result with any compatibility issues
    """
    logger.info(f"API: Validating constraints: {constraints}")
    result = constraint_service.validate_constraints(constraints)
    return handle_service_result(result, "Constraints validated successfully")


@router.post(
    "/configuration",
    summary="Update constraint configuration",
    description="""
    Update the configuration for multiple constraints.
    
    This endpoint allows for enabling, disabling, and configuring
    specific parameters for constraints. The configuration is validated
    before being applied.
    """
)
async def update_constraints_configuration(
    config: Dict[str, Dict[str, Any]],
    constraint_service: ConstraintService = Depends(get_constraint_service)
) -> Dict[str, Any]:
    """
    Update constraint configuration
    
    Args:
        config: Dictionary mapping constraint names to configurations
        constraint_service: The constraint service
        
    Returns:
        Result of the update operation
    """
    logger.info(f"API: Updating constraint configuration for {len(config)} constraints")
    result = constraint_service.update_constraint_configuration(config)
    return handle_service_result(result, "Constraint configuration updated successfully")


@router.post(
    "/{constraint_name}/enable",
    summary="Enable a constraint",
    description="""
    Enable a specific constraint.
    
    This endpoint enables a constraint and optionally updates its configuration.
    """
)
async def enable_constraint(
    constraint_name: str,
    config: Optional[Dict[str, Any]] = None,
    constraint_service: ConstraintService = Depends(get_constraint_service)
) -> Dict[str, Any]:
    """
    Enable a constraint
    
    Args:
        constraint_name: The name of the constraint to enable
        config: Optional configuration for the constraint
        constraint_service: The constraint service
        
    Returns:
        Result of the enable operation
    """
    logger.info(f"API: Enabling constraint {constraint_name}")
    result = constraint_service.enable_constraint(constraint_name, config)
    return handle_service_result(result, f"Constraint {constraint_name} enabled successfully")


@router.post(
    "/{constraint_name}/disable",
    summary="Disable a constraint",
    description="Disable a specific constraint."
)
async def disable_constraint(
    constraint_name: str,
    constraint_service: ConstraintService = Depends(get_constraint_service)
) -> Dict[str, Any]:
    """
    Disable a constraint
    
    Args:
        constraint_name: The name of the constraint to disable
        constraint_service: The constraint service
        
    Returns:
        Result of the disable operation
    """
    logger.info(f"API: Disabling constraint {constraint_name}")
    result = constraint_service.disable_constraint(constraint_name)
    return handle_service_result(result, f"Constraint {constraint_name} disabled successfully")


@router.post(
    "/reset",
    summary="Reset constraints to defaults",
    description="""
    Reset all constraints to their default configurations.
    
    This endpoint resets the enabled/disabled status and configuration
    parameters of all constraints to their default values.
    """
)
async def reset_constraints(
    constraint_service: ConstraintService = Depends(get_constraint_service)
) -> Dict[str, Any]:
    """
    Reset all constraints to defaults
    
    Args:
        constraint_service: The constraint service
        
    Returns:
        Result of the reset operation
    """
    logger.info("API: Resetting all constraints to defaults")
    result = constraint_service.reset_constraints()
    return handle_service_result(result, "Constraints reset to defaults successfully")
