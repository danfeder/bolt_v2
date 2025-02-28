from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError, BaseModel, Field
from typing import Dict, Any, List, Optional

from .models import ScheduleRequest, ScheduleResponse, WeightConfig
from .scheduling.solvers.solver import UnifiedSolver
from .scheduling.core import SolverConfig
from .scheduling.solvers.config import (
    ENABLE_WEIGHT_TUNING, 
    META_CONFIG, 
    ENABLE_CONSTRAINT_RELAXATION
)
from .scheduling.constraints.relaxation import RelaxationLevel
from .visualization.routes import router as dashboard_router

description = """
Scheduler API with configurable solver settings.

Required periods are treated as hard constraints and will always be respected.
Other scheduling preferences can be configured through the solver settings.
"""

app = FastAPI(
    title="Class Scheduler API",
    description=description,
    version="2.0.0",
    openapi_tags=[
        {
            "name": "Schedule Generation",
            "description": "Generate and compare class schedules"
        },
        {
            "name": "Solver Configuration",
            "description": "Configure solver weights and preferences. Required times are always respected."
        },
        {
            "name": "System",
            "description": "Health checks and system monitoring"
        },
        {
            "name": "Dashboard",
            "description": "Schedule analysis dashboard and visualization"
        }
    ]
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize solvers
unified_solver = UnifiedSolver()

# Create specialized solver instances for different endpoints
stable_solver = UnifiedSolver(use_genetic=False)  # Stable uses only OR-Tools
dev_solver = UnifiedSolver(use_genetic=True)      # Dev uses genetic algorithm

# Include dashboard router
app.include_router(dashboard_router)

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors gracefully"""
    errors = []
    for error in exc.errors():
        # Extract meaningful validation information
        loc = " -> ".join(str(l) for l in error["loc"])
        msg = error["msg"]
        ctx = error.get("ctx", {})
        detailed_msg = f"{msg} (at {loc})"
        if ctx:
            detailed_msg += f": {ctx}"
            
        errors.append({
            "location": loc,
            "message": detailed_msg,
            "type": error["type"]
        })
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation failed",
            "errors": errors
        }
    )

@app.post(
    "/schedule/stable",
    response_model=ScheduleResponse,
    tags=["Schedule Generation"],
    summary="Generate schedule (stable)",
    description="Create a schedule using the stable (production) solver. Required periods are enforced."
)
async def create_schedule_stable(request: ScheduleRequest) -> ScheduleResponse:
    try:
        response = stable_solver.solve(request)
        # Convert assignment date strings to UTC ISO 8601 format
        from datetime import datetime
        from app.utils.date_utils import to_utc_isoformat
        for assignment in response.assignments:
            assignment.date = to_utc_isoformat(datetime.fromisoformat(assignment.date))
        # Validate response before returning
        return ScheduleResponse(
            assignments=response.assignments,
            metadata=response.metadata
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Invalid schedule request or response",
                "errors": [{"msg": err["msg"], "loc": err["loc"]} for err in e.errors()]
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Scheduling error: {str(e)}"}
        )

@app.post(
    "/schedule/dev",
    response_model=ScheduleResponse,
    tags=["Schedule Generation"],
    summary="Generate schedule (development)",
    description="Create a schedule using the development solver for testing."
)
async def create_schedule_dev(request: ScheduleRequest) -> ScheduleResponse:
    try:
        response = dev_solver.solve(request)
        # Convert assignment date strings to UTC ISO 8601 format
        from datetime import datetime
        from app.utils.date_utils import to_utc_isoformat
        for assignment in response.assignments:
            assignment.date = to_utc_isoformat(datetime.fromisoformat(assignment.date))
        # Validate response before returning
        return ScheduleResponse(
            assignments=response.assignments,
            metadata=response.metadata
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Invalid schedule request or response",
                "errors": [{"msg": err["msg"], "loc": err["loc"]} for err in e.errors()]
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Scheduling error: {str(e)}"}
        )

@app.post(
    "/schedule/compare",
    response_model=Dict[str, Any],
    tags=["Schedule Generation"],
    summary="Compare solvers",
    description="Run both solvers and compare their results"
)
async def compare_solvers(request: ScheduleRequest) -> Dict[str, Any]:
    try:
        # Validate and create schedules
        stable_response = stable_solver.solve(request)
        dev_response = dev_solver.solve(request)
        from datetime import datetime
        from app.utils.date_utils import to_utc_isoformat
        for assignment in stable_response.assignments:
            assignment.date = to_utc_isoformat(datetime.fromisoformat(assignment.date))
        for assignment in dev_response.assignments:
            assignment.date = to_utc_isoformat(datetime.fromisoformat(assignment.date))
        
        comparison = dev_solver._compare_solutions(
            stable_response,
            dev_response
        )
        
        return {
            "stable": stable_response.dict(),
            "dev": dev_response.dict(),
            "comparison": comparison
        }
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Invalid schedule request",
                "errors": [{"msg": err["msg"], "loc": err["loc"]} for err in e.errors()]
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Comparison error: {str(e)}"}
        )

@app.get(
    "/metrics/dev",
    tags=["System"],
    summary="Development metrics",
    description="Get metrics from the last development solver run"
)
async def get_dev_metrics() -> Dict[str, Any]:
    try:
        return dev_solver.get_metrics()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Error fetching metrics: {str(e)}"}
        )
        
@app.get(
    "/metrics/relaxation",
    tags=["System"],
    summary="Constraint relaxation metrics",
    description="Get metrics about constraint relaxation status and history"
)
async def get_relaxation_metrics() -> Dict[str, Any]:
    if not ENABLE_CONSTRAINT_RELAXATION:
        return {
            "status": "disabled",
            "message": "Constraint relaxation is disabled. Enable with ENABLE_CONSTRAINT_RELAXATION=1"
        }
        
    try:
        # Create a new solver to get relaxation info
        relaxation_solver = UnifiedSolver(enable_relaxation=True)
        return relaxation_solver.get_relaxation_status()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Error fetching relaxation metrics: {str(e)}"}
        )

@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
    description="Check if the API is running and responsive"
)
async def health_check() -> Dict[str, str]:
    return {"status": "ok"}

@app.post(
    "/solver/config",
    response_model=Dict[str, Any],
    tags=["Solver Configuration"],
    summary="Update solver weights",
    description="""
    Update the weights used by the scheduler for various objectives. 
    Note: Required periods are enforced as hard constraints regardless of weights.
    """
)
async def update_solver_config(config: WeightConfig) -> Dict[str, Any]:
    from .scheduling.solvers.config import update_weights, WEIGHTS
    
    try:
        update_weights(config.weights_dict)
        return {
            "status": "success",
            "message": "Configuration updated successfully",
            "current_weights": WEIGHTS
        }
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Invalid weight configuration",
                "errors": [{"msg": err["msg"], "loc": err["loc"]} for err in e.errors()]
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Failed to update configuration: {str(e)}"}
        )

@app.post(
    "/solver/config/reset",
    response_model=Dict[str, Any],
    tags=["Solver Configuration"],
    summary="Reset solver configuration",
    description="Reset all solver weights to their default values"
)
async def reset_solver_config() -> Dict[str, Any]:
    from .scheduling.solvers.config import reset_weights, WEIGHTS
    
    try:
        reset_weights()
        return {
            "status": "success",
            "message": "Configuration reset to defaults",
            "current_weights": WEIGHTS
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Failed to reset configuration: {str(e)}"}
        )


class WeightTuningRequest(BaseModel):
    """Request for weight tuning"""
    schedule_request: ScheduleRequest
    population_size: Optional[int] = None
    generations: Optional[int] = None
    time_limit: Optional[int] = None
    parallel: Optional[bool] = None


@app.post(
    "/solver/tune-weights",
    response_model=Dict[str, Any],
    tags=["Solver Configuration"],
    summary="Tune weights automatically",
    description="""
    Use meta-optimization to automatically discover optimal weights.
    Runs multiple schedule optimizations to find the best weight configuration.
    """
)
async def tune_weights(request: WeightTuningRequest) -> Dict[str, Any]:
    if not ENABLE_WEIGHT_TUNING:
        raise HTTPException(
            status_code=400,
            detail={"message": "Weight tuning is disabled. Enable with ENABLE_WEIGHT_TUNING=1"}
        )
        
    try:
        # Create a specialized solver for weight tuning
        tuning_solver = UnifiedSolver(
            request=request.schedule_request,
            use_genetic=True,  # Need genetic algorithm for weight tuning
            use_or_tools=False  # Don't need OR-Tools for tuning
        )
        
        # Override meta-optimization parameters if provided
        if request.population_size is not None:
            META_CONFIG.POPULATION_SIZE = request.population_size
        if request.generations is not None:
            META_CONFIG.GENERATIONS = request.generations
        if request.time_limit is not None:
            META_CONFIG.EVAL_TIME_LIMIT = request.time_limit
        if request.parallel is not None:
            META_CONFIG.PARALLEL_EVALUATION = request.parallel
            
        # Run weight tuning
        best_config = tuning_solver.tune_weights()
        
        # Update global weights with discovered values
        from .scheduling.solvers.config import update_weights, WEIGHTS
        update_weights(best_config.weights_dict)
        
        return {
            "status": "success",
            "message": "Weight tuning completed successfully",
            "tuned_weights": best_config.dict(),
            "meta_config": {
                "population_size": META_CONFIG.POPULATION_SIZE,
                "generations": META_CONFIG.GENERATIONS,
                "eval_time_limit": META_CONFIG.EVAL_TIME_LIMIT,
                "parallel_evaluation": META_CONFIG.PARALLEL_EVALUATION
            }
        }
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Invalid weight tuning request",
                "errors": [{"msg": err["msg"], "loc": err["loc"]} for err in e.errors()]
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Failed to tune weights: {str(e)}"}
        )


@app.post(
    "/schedule/optimized",
    response_model=ScheduleResponse,
    tags=["Schedule Generation"],
    summary="Generate optimized schedule",
    description="""
    Create a schedule with automatic weight tuning. This endpoint:
    1. Runs meta-optimization to discover optimal weights
    2. Uses the optimized weights to generate the final schedule
    """
)
async def create_optimized_schedule(request: ScheduleRequest) -> ScheduleResponse:
    if not ENABLE_WEIGHT_TUNING:
        raise HTTPException(
            status_code=400,
            detail={"message": "Weight tuning is disabled. Enable with ENABLE_WEIGHT_TUNING=1"}
        )
        
    try:
        # Create a specialized solver for optimized scheduling
        optimized_solver = UnifiedSolver(
            request=request,
            use_genetic=True,
            use_or_tools=False
        )
        
        # Run the solver with weight tuning enabled
        response = optimized_solver.solve(tune_weights=True)
        
        # Convert assignment date strings to UTC ISO 8601 format
        from datetime import datetime
        from app.utils.date_utils import to_utc_isoformat
        for assignment in response.assignments:
            assignment.date = to_utc_isoformat(datetime.fromisoformat(assignment.date))
            
        # Validate response before returning
        return ScheduleResponse(
            assignments=response.assignments,
            metadata=response.metadata
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Invalid schedule request or response",
                "errors": [{"msg": err["msg"], "loc": err["loc"]} for err in e.errors()]
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Scheduling error: {str(e)}"}
        )


class RelaxationRequest(BaseModel):
    """Request for constraint relaxation."""
    schedule_request: ScheduleRequest
    relaxation_level: str = Field("MINIMAL", description="Relaxation level (NONE, MINIMAL, MODERATE, SIGNIFICANT, MAXIMUM)")


@app.post(
    "/schedule/relaxed",
    response_model=ScheduleResponse,
    tags=["Schedule Generation"],
    summary="Generate schedule with constraint relaxation",
    description="""
    Create a schedule with constraint relaxation. This endpoint:
    1. Tries to find a solution with the given relaxation level
    2. Returns the schedule if found, or empty if no solution
    
    Relaxation levels:
    - NONE: No relaxation, standard constraints
    - MINIMAL: Slight relaxation of less critical constraints
    - MODERATE: Moderate relaxation of constraints
    - SIGNIFICANT: Significant relaxation for difficult schedules
    - MAXIMUM: Maximum relaxation for extremely difficult cases
    """
)
async def create_relaxed_schedule(request: RelaxationRequest) -> ScheduleResponse:
    if not ENABLE_CONSTRAINT_RELAXATION:
        raise HTTPException(
            status_code=400,
            detail={"message": "Constraint relaxation is disabled. Enable with ENABLE_CONSTRAINT_RELAXATION=1"}
        )
        
    try:
        # Validate relaxation level
        try:
            level = RelaxationLevel[request.relaxation_level.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail={"message": f"Invalid relaxation level: {request.relaxation_level}. "
                                 f"Valid levels: {[l.name for l in RelaxationLevel]}"}
            )
                
        # Create solver with relaxation enabled
        relaxed_solver = UnifiedSolver(
            request=request.schedule_request,
            use_genetic=True,
            use_or_tools=True,
            enable_relaxation=True
        )
        
        # Apply relaxation before solving
        relaxed_solver.relax_constraints(level)
        
        # Solve with the relaxed constraints
        response = relaxed_solver.solve()
        
        # Convert assignment date strings to UTC ISO 8601 format
        from datetime import datetime
        from app.utils.date_utils import to_utc_isoformat
        for assignment in response.assignments:
            assignment.date = to_utc_isoformat(datetime.fromisoformat(assignment.date))
            
        # Add relaxation info to metadata
        if hasattr(response, 'metadata') and response.metadata:
            response.metadata.relaxation_level = level.name
            response.metadata.relaxation_status = relaxed_solver.get_relaxation_status()
            
        # Validate response before returning
        return ScheduleResponse(
            assignments=response.assignments,
            metadata=response.metadata
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Invalid schedule request or response",
                "errors": [{"msg": err["msg"], "loc": err["loc"]} for err in e.errors()]
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Scheduling error: {str(e)}"}
        )


@app.post(
    "/schedule/adaptive",
    response_model=ScheduleResponse,
    tags=["Schedule Generation"],
    summary="Generate schedule with adaptive constraint relaxation",
    description="""
    Create a schedule with adaptive constraint relaxation. This endpoint:
    1. Tries to find a solution with standard constraints first
    2. If no solution is found, progressively relaxes constraints until a solution is found
    3. Returns the solution with the minimum necessary relaxation
    """
)
async def create_adaptive_schedule(request: ScheduleRequest) -> ScheduleResponse:
    if not ENABLE_CONSTRAINT_RELAXATION:
        raise HTTPException(
            status_code=400,
            detail={"message": "Constraint relaxation is disabled. Enable with ENABLE_CONSTRAINT_RELAXATION=1"}
        )
        
    try:
        # Create solver with relaxation and progressive relaxation enabled
        adaptive_solver = UnifiedSolver(
            request=request,
            use_genetic=True,
            use_or_tools=True,
            enable_relaxation=True
        )
        
        # Solve with progressive relaxation
        response = adaptive_solver.solve(with_relaxation=True)
        
        # Convert assignment date strings to UTC ISO 8601 format
        from datetime import datetime
        from app.utils.date_utils import to_utc_isoformat
        for assignment in response.assignments:
            assignment.date = to_utc_isoformat(datetime.fromisoformat(assignment.date))
        
        # Add relaxation status to metadata if available
        if hasattr(response, 'metadata') and response.metadata:
            response.metadata.relaxation_status = adaptive_solver.get_relaxation_status()
            
        # Validate response before returning
        return ScheduleResponse(
            assignments=response.assignments,
            metadata=response.metadata
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Invalid schedule request or response",
                "errors": [{"msg": err["msg"], "loc": err["loc"]} for err in e.errors()]
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Scheduling error: {str(e)}"}
        )
