from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .models import ScheduleRequest, ScheduleResponse
from .scheduling.solvers.stable import StableSolver
from .scheduling.solvers.dev import DevSolver

app = FastAPI()

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
        location = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "location": location,
            "message": error["msg"],
            "type": error["type"]
        })
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": errors
        }
    )

@app.post("/schedule/stable")
async def create_schedule_stable(request: ScheduleRequest) -> ScheduleResponse:
    """Create schedule using stable (production) solver"""
    try:
        return stable_solver.create_schedule(request)
    except ValidationError as e:
        # This should be caught by the global handler, but just in case
        raise HTTPException(
            status_code=422,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scheduling error: {str(e)}"
        )

@app.post("/schedule/dev")
async def create_schedule_dev(request: ScheduleRequest) -> ScheduleResponse:
    """Create schedule using development solver"""
    try:
        return dev_solver.create_schedule(request)
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scheduling error: {str(e)}"
        )

@app.post("/schedule/compare")
async def compare_solvers(request: ScheduleRequest) -> dict:
    """Run both solvers and compare results"""
    try:
        stable_response = stable_solver.create_schedule(request)
        dev_response = dev_solver.create_schedule(request)
        
        comparison = dev_solver.compare_with_stable(
            stable_response,
            dev_response
        )
        
        return {
            "stable": stable_response,
            "dev": dev_response,
            "comparison": comparison
        }
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Comparison error: {str(e)}"
        )

@app.get("/metrics/dev")
async def get_dev_metrics() -> dict:
    """Get metrics from last development solver run"""
    return dev_solver.get_last_run_metrics()

@app.get("/health")
async def health_check() -> dict:
    """Simple health check endpoint"""
    return {"status": "ok"}
