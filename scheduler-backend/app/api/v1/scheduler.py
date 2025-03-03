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
    tags=["Schedule Generation"],
    responses={
        404: {"description": "Not found"},
        422: {"description": "Validation error"},
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


@router.post(
    "/schedule/stable", 
    response_model_exclude_none=True,
    summary="Generate schedule using stable solver",
    description="""
    Generate a schedule using the stable solver configuration.
    
    This endpoint uses the CP-SAT solver which provides reliable and consistent
    results. It handles all constraints properly but may be slower for
    complex schedules.
    
    The stable solver is recommended for production use.
    """,
    response_description="A standardized response with the generated schedule or error details",
    status_code=200,
    responses={
        200: {
            "description": "Successful schedule generation",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Schedule generated successfully",
                        "data": {
                            "assignments": [
                                {
                                    "name": "PK207",
                                    "classId": "class-123",
                                    "date": "2025-02-12T00:00:00Z",
                                    "timeSlot": {
                                        "dayOfWeek": 1,
                                        "period": 1
                                    }
                                }
                            ],
                            "metadata": {
                                "duration_ms": 1000,
                                "solutions_found": 1,
                                "score": -857960000,
                                "gap": -1.13,
                                "solver": "cp-sat-stable"
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "No solution found",
                        "errors": [
                            {"message": "Schedule constraints are too restrictive"}
                        ]
                    }
                }
            }
        }
    }
)
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


@router.post(
    "/schedule/dev",
    response_model_exclude_none=True,
    summary="Generate schedule using genetic algorithm",
    description="""
    Generate a schedule using the development solver configuration.
    
    This endpoint uses the genetic algorithm for schedule generation,
    which may provide better results in some cases but is still experimental.
    The genetic algorithm is particularly good at optimizing for balanced
    distribution and handling complex preferences.
    
    Note: This solver may take longer to run but can find solutions when
    the stable solver fails due to tight constraints.
    """,
    response_description="A standardized response with the generated schedule or error details",
    status_code=200,
    responses={
        200: {
            "description": "Successful schedule generation",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Schedule generated successfully",
                        "data": {
                            "assignments": [
                                {
                                    "name": "PK207",
                                    "classId": "class-123",
                                    "date": "2025-02-12T00:00:00Z",
                                    "timeSlot": {
                                        "dayOfWeek": 1,
                                        "period": 1
                                    }
                                }
                            ],
                            "metadata": {
                                "duration_ms": 3500,
                                "solutions_found": 1,
                                "score": -750000000,
                                "gap": -2.05,
                                "solver": "genetic-algorithm"
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "No valid solution found",
                        "errors": [
                            {"message": "Failed to find a solution after 100 generations"}
                        ]
                    }
                }
            }
        }
    }
)
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


@router.post(
    "/schedule/relaxed/{relaxation_level}",
    response_model_exclude_none=True,
    summary="Generate schedule with constraint relaxation",
    description="""
    Generate a schedule with specific constraint relaxation level.
    
    This endpoint allows for generating schedules with relaxed constraints
    when a fully constrained schedule is not feasible. You can specify
    the exact relaxation level to apply.
    
    Available relaxation levels:
    - minimal: Relax only soft constraints
    - moderate: Relax soft constraints and some teacher preferences
    - significant: Relax most constraints except required periods
    - maximum: Relax all constraints except absolute requirements
    
    Use this endpoint when standard solvers fail to find a solution.
    """,
    response_description="A standardized response with the generated schedule or error details",
    status_code=200,
    responses={
        200: {
            "description": "Successful schedule generation with relaxation",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Schedule generated successfully with relaxed constraints",
                        "data": {
                            "assignments": [
                                {
                                    "name": "PK207",
                                    "classId": "class-123",
                                    "date": "2025-02-12T00:00:00Z",
                                    "timeSlot": {
                                        "dayOfWeek": 1,
                                        "period": 1
                                    }
                                }
                            ],
                            "metadata": {
                                "duration_ms": 1200,
                                "solutions_found": 1,
                                "score": -650000000,
                                "solver": "cp-sat-unified",
                                "relaxation_level": "moderate",
                                "relaxation_status": {
                                    "relaxed_constraints": ["consecutive_classes", "preferred_periods"],
                                    "preserved_constraints": ["required_periods", "conflicts"]
                                }
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "Invalid relaxation level",
                        "errors": [
                            {"message": "Relaxation level must be one of: minimal, moderate, significant, maximum"}
                        ]
                    }
                }
            }
        }
    }
)
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


@router.post(
    "/compare",
    response_model_exclude_none=True,
    summary="Compare results from different solvers",
    description="""
    Compare the results of different solvers for the same schedule request.
    
    This endpoint runs both the stable (CP-SAT) and development (genetic algorithm)
    solvers on the same request and generates a detailed comparison of results,
    including:
    - Assignment differences
    - Score differences
    - Performance metrics
    - Quality metrics
    
    This is useful for:
    - Evaluating which solver works best for your specific use case
    - Debugging scheduling issues
    - Understanding tradeoffs between different solving approaches
    """,
    response_description="A standardized response with comparison results between solvers",
    status_code=200,
    responses={
        200: {
            "description": "Successful solver comparison",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Solver comparison complete",
                        "data": {
                            "stable": {
                                "assignments": [{"truncated": "for brevity"}],
                                "metadata": {
                                    "duration_ms": 1500,
                                    "solutions_found": 1,
                                    "score": -857960000,
                                    "solver": "cp-sat-stable"
                                }
                            },
                            "development": {
                                "assignments": [{"truncated": "for brevity"}],
                                "metadata": {
                                    "duration_ms": 3500,
                                    "solutions_found": 1,
                                    "score": -750000000,
                                    "solver": "genetic-algorithm"
                                }
                            },
                            "comparison": {
                                "assignment_differences": 5,
                                "score_difference_pct": 12.6,
                                "speed_ratio": 0.43,
                                "recommendation": "stable"
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "Failed to compare solvers",
                        "errors": [
                            {"message": "One or both solvers failed to generate a valid schedule"}
                        ]
                    }
                }
            }
        }
    }
)
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


@router.post(
    "/tune-weights",
    response_model_exclude_none=True,
    summary="Tune solver weights for optimal results",
    description="""
    Tune the solver weights for a specific schedule request.
    
    This endpoint runs the weight tuning algorithm to find optimal
    weights for the given schedule request. It performs a meta-optimization
    process that:
    1. Tries multiple weight configurations
    2. Evaluates solution quality for each configuration
    3. Searches for the best weights that maximize solution quality
    
    The tuning process uses a genetic algorithm to explore the
    weight configuration space efficiently.
    
    You can specify the number of iterations to run using the 'iterations'
    query parameter (1-20, default is 5).
    """,
    response_description="A standardized response with the tuned weights and performance metrics",
    status_code=200,
    responses={
        200: {
            "description": "Successful weight tuning",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Weight tuning completed successfully",
                        "data": {
                            "weights": {
                                "final_week_compression": 3500,
                                "day_usage": 2200,
                                "daily_balance": 1800,
                                "preferred_periods": 1200,
                                "distribution": 1500,
                                "avoid_periods": -600,
                                "earlier_dates": 15
                            },
                            "metrics": {
                                "iterations": 5,
                                "initial_score": -750000000,
                                "tuned_score": -850000000,
                                "improvement": "13.3%",
                                "duration_ms": 12500
                            },
                            "sample_schedule": {
                                "assignments": [{"truncated": "for brevity"}],
                                "metadata": {"truncated": "for brevity"}
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "Weight tuning failed",
                        "errors": [
                            {"message": "Failed to find valid solutions during tuning process"}
                        ]
                    }
                }
            }
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "Validation error",
                        "errors": [
                            {"message": "iterations must be between 1 and 20", "field": "iterations"}
                        ]
                    }
                }
            }
        }
    }
)
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


@router.put(
    "/config",
    response_model_exclude_none=True,
    summary="Update solver configuration",
    description="""
    Update the solver configuration with new weights.
    
    This endpoint allows updating the weights used by the solver for
    constraint satisfaction. The weight configuration controls how
    the solver prioritizes different aspects of the schedule quality.
    
    Weight parameters:
    - final_week_compression: Higher values prefer utilizing the earlier weeks
    - day_usage: Higher values prefer distributing classes across more days
    - daily_balance: Higher values prefer balanced distribution across periods
    - preferred_periods: Higher values prioritize teacher preferred periods
    - distribution: Higher values emphasize balanced class distribution
    - avoid_periods: More negative values increase penalty for avoided periods
    - earlier_dates: Higher values prefer scheduling classes earlier
    """,
    response_description="A standardized response indicating success or failure of the update",
    status_code=200,
    responses={
        200: {
            "description": "Configuration successfully updated",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Solver configuration updated successfully",
                        "data": {
                            "final_week_compression": 3000,
                            "day_usage": 2000,
                            "daily_balance": 1500,
                            "preferred_periods": 1000,
                            "distribution": 1000,
                            "avoid_periods": -500,
                            "earlier_dates": 10
                        }
                    }
                }
            }
        },
        400: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "Invalid configuration",
                        "errors": [
                            {"message": "Weight values out of allowed range"}
                        ]
                    }
                }
            }
        }
    }
)
async def update_solver_config(
    weight_config: WeightConfig,
    scheduler_service: SchedulerService = Depends(get_scheduler_service)
) -> Dict[str, Any]:
    """
    Update the solver configuration with new weights.
    
    Args:
        weight_config: The new weight configuration to apply
        scheduler_service: The scheduler service dependency
        
    Returns:
        A standardized response indicating success or failure
    """
    result = scheduler_service.update_solver_config(weight_config)
    return handle_service_result(result, "Solver configuration updated successfully")


@router.post(
    "/config/reset",
    response_model_exclude_none=True,
    summary="Reset solver configuration to defaults",
    description="""
    Reset the solver configuration to defaults.
    
    This endpoint resets all solver parameters to their default values.
    Default values are designed to work well for most scheduling scenarios
    and provide a balanced approach to constraint satisfaction.
    
    Use this endpoint when you want to start fresh after experimenting
    with custom weight configurations.
    """,
    response_description="A standardized response with the default configuration values",
    status_code=200,
    responses={
        200: {
            "description": "Configuration successfully reset",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Solver configuration reset to defaults",
                        "data": {
                            "final_week_compression": 3000,
                            "day_usage": 2000,
                            "daily_balance": 1500,
                            "preferred_periods": 1000,
                            "distribution": 1000,
                            "avoid_periods": -500,
                            "earlier_dates": 10
                        }
                    }
                }
            }
        }
    }
)
async def reset_solver_config(
    scheduler_service: SchedulerService = Depends(get_scheduler_service)
) -> Dict[str, Any]:
    """
    Reset the solver configuration to defaults.
    
    Args:
        scheduler_service: The scheduler service dependency
        
    Returns:
        A standardized response indicating success or failure
    """
    result = scheduler_service.reset_solver_config()
    return handle_service_result(result, "Solver configuration reset to defaults")


@router.get(
    "/metrics",
    response_model_exclude_none=True,
    summary="Get solver performance metrics",
    description="""
    Get solver performance metrics.
    
    This endpoint returns metrics about solver performance and usage, including:
    - Success/failure rates
    - Average solution times
    - Distribution quality statistics
    - Constraint satisfaction metrics
    - Usage patterns
    
    These metrics help monitor solver performance and identify potential
    optimization opportunities.
    """,
    response_description="A standardized response with the solver metrics",
    status_code=200,
    responses={
        200: {
            "description": "Metrics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Solver metrics retrieved successfully",
                        "data": {
                            "performance": {
                                "avg_duration_ms": 1850,
                                "success_rate": 0.95,
                                "attempts": 120,
                                "failures": 6
                            },
                            "distribution": {
                                "avg_period_balance": 0.85,
                                "avg_day_balance": 0.92
                            },
                            "constraints": {
                                "relaxation_frequency": 0.15,
                                "preferred_periods_satisfaction": 0.88
                            },
                            "usage": {
                                "stable_solver_usage": 95,
                                "dev_solver_usage": 25
                            }
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "Failed to retrieve solver metrics",
                        "errors": [
                            {"message": "Error accessing metrics database"}
                        ]
                    }
                }
            }
        }
    }
)
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
