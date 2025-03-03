from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError, BaseModel, Field
from typing import Dict, Any, List, Optional, Union
import logging
import traceback

from .models import ScheduleRequest, ScheduleResponse, WeightConfig
from .scheduling.solvers.config import (
    ENABLE_WEIGHT_TUNING, 
    META_CONFIG, 
    ENABLE_CONSTRAINT_RELAXATION
)
from .visualization.routes import router as dashboard_router
from .api.v1 import v1_router
from .services.response_models import ResponseFactory

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

# Include routers
app.include_router(v1_router)
app.include_router(dashboard_router)

# Set up logger
logger = logging.getLogger(__name__)

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """
    Handle validation errors, providing detailed information about which fields failed validation.
    """
    errors = []
    for error in exc.errors():
        field_path = ".".join([str(loc) for loc in error["loc"]])
        errors.append({
            "message": error["msg"],
            "field": field_path,
            "code": "validation_error"
        })
    
    logger.warning(f"Validation error: {errors}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ResponseFactory.errors(
            errors=errors,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTP exceptions with structured responses.
    """
    detail = getattr(exc, "detail", "An error occurred")
    if isinstance(detail, dict) and "message" in detail:
        error_content = detail
    else:
        error_content = {"message": str(detail)}
    
    logger.warning(f"HTTP Exception: {exc.status_code} - {error_content}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ResponseFactory.error(
            message=error_content.get("message", str(detail)),
            status_code=exc.status_code,
            hint=error_content.get("hint"),
            code=error_content.get("code"),
            field=error_content.get("field")
        )
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions with user-friendly messaging.
    """
    logger.error(f"Unexpected error: {str(exc)}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ResponseFactory.error(
            message="An unexpected error occurred. Our team has been notified.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="internal_server_error"
        )
    )


@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
    description="Check if the API is healthy"
)
async def health_check() -> Dict[str, Any]:
    return ResponseFactory.success(
        data={"status": "ok"},
        message="Service is healthy"
    )
