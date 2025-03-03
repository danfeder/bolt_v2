"""
Scheduler API Router

This module contains the API endpoints for schedule generation and management.
It uses the SchedulerService to handle business logic and provides standardized
response handling.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query

from ...models import ScheduleRequest, ScheduleResponse, WeightConfig
from ...services.service_factory import get_service_factory, ServiceFactory
from ...services.scheduler_service import SchedulerService
from ..response_handler import handle_service_result, create_error_response

# Set up logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/scheduler",
    tags=["scheduler"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)


def get_scheduler_service(
    service_factory: ServiceFactory = Depends(get_service_factory)
) -> SchedulerService:
    """
    Dependency to get the scheduler service instance.
    
    Args:
        service_factory: The service factory instance
        
    Returns:
        The SchedulerService instance
    """
    return service_factory.get_scheduler_service()


@router.post("/schedule/stable", response_model_exclude_none=True)
async def create_schedule_stable(
    request: ScheduleRequest,
    scheduler_service: SchedulerService = Depends(get_scheduler_service)
) -> Dict[str, Any]:
    """
    Generate a schedule using the stable solver configuration.
    
    This endpoint uses the stable solver with production-ready parameters
    for reliable schedule generation.
    
    Args:
        request: The schedule request containing all necessary inputs
        scheduler_service: The scheduler service dependency
        
    Returns:
        A standardized response with the generated schedule or error details
    """
    logger.info(f"API: Creating stable schedule for {len(request.classes)} classes")
    result = scheduler_service.create_stable_schedule(request)
    return handle_service_result(result, "Schedule generated successfully")


@router.post("/schedule/dev", response_model_exclude_none=True)
async def create_schedule_dev(
    request: ScheduleRequest,
    scheduler_service: SchedulerService = Depends(get_scheduler_service)
) -> Dict[str, Any]:
    """
    Generate a schedule using the development solver configuration.
    
    This endpoint uses the genetic algorithm for schedule generation,
    which may provide better results in some cases but is still experimental.
    
    Args:
        request: The schedule request containing all necessary inputs
        scheduler_service: The scheduler service dependency
        
    Returns:
        A standardized response with the generated schedule or error details
    """
    logger.info(f"API: Creating dev schedule for {len(request.classes)} classes")
    result = scheduler_service.create_dev_schedule(request)
    return handle_service_result(result, "Development schedule generated successfully")


@router.post("/schedule/relaxed/{relaxation_level}", response_model_exclude_none=True)
async def create_schedule_relaxed(
    relaxation_level: str,
    request: ScheduleRequest,
    scheduler_service: SchedulerService = Depends(get_scheduler_service)
) -> Dict[str, Any]:
    """
    Generate a schedule with constraint relaxation.
    
    This endpoint allows for generating schedules with relaxed constraints
    when a fully constrained schedule is not feasible.
    
    Args:
        relaxation_level: The level of constraint relaxation to apply
        request: The schedule request containing all necessary inputs
        scheduler_service: The scheduler service dependency
        
    Returns:
        A standardized response with the generated schedule or error details
    """
    logger.info(f"API: Creating relaxed schedule with level {relaxation_level}")
    result = scheduler_service.create_relaxed_schedule(relaxation_level, request)
    return handle_service_result(result, f"Relaxed schedule generated with {relaxation_level} relaxation")


@router.post("/compare", response_model_exclude_none=True)
async def compare_solvers(
    request: ScheduleRequest,
    scheduler_service: SchedulerService = Depends(get_scheduler_service)
) -> Dict[str, Any]:
    """
    Compare the results of different solvers.
    
    This endpoint runs both the stable and development solvers on the same
    request and compares the results.
    
    Args:
        request: The schedule request containing all necessary inputs
        scheduler_service: The scheduler service dependency
        
    Returns:
        A standardized response with the comparison results or error details
    """
    logger.info(f"API: Comparing solvers for {len(request.classes)} classes")
    result = scheduler_service.compare_solvers(request)
    return handle_service_result(result, "Solver comparison completed")


@router.post("/tune", response_model_exclude_none=True)
async def tune_weights(
    request: ScheduleRequest,
    iterations: int = Query(5, ge=1, le=20),
    scheduler_service: SchedulerService = Depends(get_scheduler_service)
) -> Dict[str, Any]:
    """
    Tune the solver weights for a specific request.
    
    This endpoint runs the weight tuning algorithm to find optimal
    weights for the given schedule request.
    
    Args:
        request: The schedule request containing all necessary inputs
        iterations: Number of tuning iterations to run
        scheduler_service: The scheduler service dependency
        
    Returns:
        A standardized response with the tuned weights or error details
    """
    logger.info(f"API: Tuning weights for {len(request.classes)} classes with {iterations} iterations")
    result = scheduler_service.tune_weights(request, iterations)
    return handle_service_result(result, "Weight tuning completed")


@router.post("/config/update", response_model_exclude_none=True)
async def update_solver_config(
    weight_config: WeightConfig,
    scheduler_service: SchedulerService = Depends(get_scheduler_service)
) -> Dict[str, Any]:
    """
    Update the solver configuration with new weights.
    
    This endpoint allows updating the weights used by the solver for
    constraint satisfaction.
    
    Args:
        weight_config: The new weight configuration to apply
        scheduler_service: The scheduler service dependency
        
    Returns:
        A standardized response indicating success or failure
    """
    logger.info("API: Updating solver configuration")
    result = scheduler_service.update_solver_config(weight_config)
    return handle_service_result(result, "Solver configuration updated")


@router.post("/config/reset", response_model_exclude_none=True)
async def reset_solver_config(
    scheduler_service: SchedulerService = Depends(get_scheduler_service)
) -> Dict[str, Any]:
    """
    Reset the solver configuration to defaults.
    
    This endpoint resets all solver parameters to their default values.
    
    Args:
        scheduler_service: The scheduler service dependency
        
    Returns:
        A standardized response indicating success or failure
    """
    logger.info("API: Resetting solver configuration")
    result = scheduler_service.reset_solver_config()
    return handle_service_result(result, "Solver configuration reset to defaults")


@router.get("/metrics", response_model_exclude_none=True)
async def get_solver_metrics(
    scheduler_service: SchedulerService = Depends(get_scheduler_service)
) -> Dict[str, Any]:
    """
    Get solver performance metrics.
    
    This endpoint returns metrics about solver performance and usage.
    
    Args:
        scheduler_service: The scheduler service dependency
        
    Returns:
        A standardized response with the solver metrics
    """
    logger.info("API: Getting solver metrics")
    try:
        metrics = scheduler_service.get_solver_metrics()
        return {"success": True, "data": metrics}
    except Exception as e:
        logger.error(f"Error getting solver metrics: {str(e)}")
        return create_error_response(
            status_code=500,
            message=f"Failed to retrieve metrics: {str(e)}"
        )
