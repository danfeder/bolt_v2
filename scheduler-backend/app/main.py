from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from typing import Dict, Any

from .models import ScheduleRequest, ScheduleResponse, WeightConfig
from .scheduling.solvers.stable import StableSolver
from .scheduling.solvers.dev import DevSolver

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
stable_solver = StableSolver()
dev_solver = DevSolver()

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
        response = stable_solver.create_schedule(request)
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
        response = dev_solver.create_schedule(request)
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
        stable_response = stable_solver.create_schedule(request)
        dev_response = dev_solver.create_schedule(request)
        
        comparison = dev_solver.compare_with_stable(
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
        return dev_solver.get_last_run_metrics()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Error fetching metrics: {str(e)}"}
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
