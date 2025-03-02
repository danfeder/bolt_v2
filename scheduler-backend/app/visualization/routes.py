"""API routes for visualization and dashboard."""
from typing import Dict, List, Any, Optional
import traceback
import logging
from fastapi import APIRouter, HTTPException, Body, Query, Depends
from pydantic import ValidationError

from ..models import ScheduleRequest, ScheduleResponse
from ..scheduling.solvers.solver import UnifiedSolver
from .dashboard import (
    create_dashboard_data,
    compare_schedules
)
from .models import (
    DashboardData,
    ChartData,
    ScheduleComparisonResult,
    ScheduleQualityMetrics
)

# Set up logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    responses={
        404: {"description": "Not found"},
        422: {"description": "Validation error"},
        500: {"description": "Server error"}
    }
)

# Create solver instances
stable_solver = UnifiedSolver(use_genetic=False)  # Stable uses only OR-Tools
dev_solver = UnifiedSolver(use_genetic=True)      # Dev uses genetic algorithm

# Store recent schedules for history
schedule_history: Dict[str, Dict[str, Any]] = {}


@router.post(
    "/analyze",
    response_model=DashboardData,
    summary="Analyze schedule",
    description="Analyze a schedule and generate dashboard data"
)
async def analyze_schedule(
    request: ScheduleRequest = Body(...),
    solver_type: str = Query("stable", description="Solver type (stable or dev)")
) -> DashboardData:
    """
    Analyze a schedule and generate dashboard data.
    
    Args:
        request: Schedule request to analyze
        solver_type: Solver type to use (stable or dev)
        
    Returns:
        Dashboard data with visualizations and metrics
    """
    try:
        # Choose solver based on type
        solver = stable_solver if solver_type == "stable" else dev_solver
        
        # Debugging: Print request details
        logger.info(f"Analyzing schedule with {len(request.classes)} classes from {request.startDate} to {request.endDate}")
        
        schedule = None
        try:
            # Create schedule
            logger.info("About to call solver.solve()")
            schedule = solver.solve(request)
            logger.info("Solver.solve() completed successfully")
            
            # Debugging: Print schedule metadata
            if hasattr(schedule, 'metadata') and schedule.metadata:
                logger.info(f"Schedule metadata: {schedule.metadata}")
                metadata_info = str(schedule.metadata)
            else:
                logger.info("No schedule metadata available")
                metadata_info = "None"
            
            if not schedule:
                logger.error("Solver returned None for schedule")
                raise HTTPException(
                    status_code=500,
                    detail=f"Solver failed to generate a schedule"
                )
            
            if not hasattr(schedule, 'assignments') or not schedule.assignments:
                logger.error("Schedule has no assignments")
                logger.error(f"Schedule: {schedule}")
                logger.error(f"Metadata: {metadata_info}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Solver generated a schedule with no assignments"
                )
            
            # Create dashboard data
            logger.info("About to create dashboard data")
            dashboard_data = create_dashboard_data(
                schedule=schedule,
                classes=request.classes,
            )
            logger.info("Dashboard data created successfully")
            
            # Store in history
            schedule_history[dashboard_data.schedule_id] = {
                "schedule": schedule,
                "request": request,
                "dashboard": dashboard_data
            }
            
            return dashboard_data
                
        except Exception as e:
            logger.error(f"Error solving schedule: {str(e)}")
            logger.error(f"Schedule: {schedule}")
            logger.error(f"Request: {request}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Error solving schedule: {str(e)}"
            )
    
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Invalid schedule request",
                "errors": [{"msg": err["msg"], "loc": err["loc"]} for err in e.errors()]
            }
        )
    except Exception as e:
        # Print metadata for debugging
        import inspect
        metadata_info = "None"
        if 'schedule' in locals() and hasattr(schedule, 'metadata'):
            metadata_info = str(vars(schedule.metadata))
        
        print(f"DEBUG - Error in analyze_schedule: {str(e)}")
        print(f"DEBUG - Metadata: {metadata_info}")
        print(f"DEBUG - Exception location: {inspect.trace()[-1][1:3]}")
        
        raise HTTPException(
            status_code=500,
            detail={"message": f"Analysis error: {str(e)}"}
        )


@router.post(
    "/compare",
    response_model=List[ScheduleComparisonResult],
    summary="Compare schedules",
    description="Compare two schedules and return detailed comparison metrics"
)
async def compare_schedule_analysis(
    baseline_id: str = Query(..., description="ID of baseline schedule"),
    comparison_id: str = Query(..., description="ID of comparison schedule")
) -> List[ScheduleComparisonResult]:
    """
    Compare two schedules and return detailed comparison metrics.
    
    Args:
        baseline_id: ID of baseline schedule
        comparison_id: ID of comparison schedule
        
    Returns:
        List of comparison results for different metrics
    """
    try:
        # Check if schedules exist in history
        if baseline_id not in schedule_history:
            raise HTTPException(
                status_code=404,
                detail={"message": f"Baseline schedule {baseline_id} not found"}
            )
            
        if comparison_id not in schedule_history:
            raise HTTPException(
                status_code=404,
                detail={"message": f"Comparison schedule {comparison_id} not found"}
            )
            
        # Get schedules from history
        baseline = schedule_history[baseline_id]["schedule"]
        comparison = schedule_history[comparison_id]["schedule"]
        
        # Get classes from history
        classes = schedule_history[baseline_id]["request"].classes
        
        # Compare schedules
        comparison_results = compare_schedules(
            baseline=baseline,
            comparison=comparison,
            classes=classes
        )
        
        return comparison_results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Comparison error: {str(e)}"}
        )


@router.get(
    "/history",
    response_model=List[Dict[str, Any]],
    summary="Get schedule history",
    description="Get list of previously analyzed schedules"
)
async def get_schedule_history() -> List[Dict[str, Any]]:
    """
    Get list of previously analyzed schedules.
    
    Returns:
        List of schedule history entries
    """
    try:
        # Format history for response
        history = []
        for schedule_id, data in schedule_history.items():
            dashboard = data["dashboard"]
            history.append({
                "schedule_id": schedule_id,
                "timestamp": dashboard.timestamp,
                "quality_metrics": dashboard.quality_metrics,
                "assignment_count": len(data["schedule"].assignments),
                "class_count": len(data["request"].classes)
            })
            
        # Sort by timestamp (newest first)
        history.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return history
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Error retrieving history: {str(e)}"}
        )


@router.get(
    "/metrics/{schedule_id}",
    response_model=ScheduleQualityMetrics,
    summary="Get schedule metrics",
    description="Get quality metrics for a specific schedule"
)
async def get_schedule_metrics(schedule_id: str) -> ScheduleQualityMetrics:
    """
    Get quality metrics for a specific schedule.
    
    Args:
        schedule_id: ID of schedule to get metrics for
        
    Returns:
        Schedule quality metrics
    """
    try:
        # Check if schedule exists in history
        if schedule_id not in schedule_history:
            raise HTTPException(
                status_code=404,
                detail={"message": f"Schedule {schedule_id} not found"}
            )
            
        # Get metrics from history
        dashboard = schedule_history[schedule_id]["dashboard"]
        
        return dashboard.quality_metrics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Error retrieving metrics: {str(e)}"}
        )


@router.get(
    "/chart/{chart_type}/{schedule_id}",
    response_model=ChartData,
    summary="Get chart data",
    description="Get specific chart data for a schedule"
)
async def get_chart_data(
    chart_type: str,
    schedule_id: str
) -> ChartData:
    """
    Get specific chart data for a schedule.
    
    Args:
        chart_type: Type of chart (daily, period, grade)
        schedule_id: ID of schedule to get chart for
        
    Returns:
        Chart data for the specified chart type
    """
    try:
        # Check if schedule exists in history
        if schedule_id not in schedule_history:
            raise HTTPException(
                status_code=404,
                detail={"message": f"Schedule {schedule_id} not found"}
            )
            
        # Get dashboard from history
        dashboard = schedule_history[schedule_id]["dashboard"]
        
        # Return requested chart
        if chart_type == "daily":
            return dashboard.daily_distribution
        elif chart_type == "period":
            return dashboard.period_distribution
        elif chart_type == "grade":
            return dashboard.grade_distribution
        else:
            raise HTTPException(
                status_code=400,
                detail={"message": f"Invalid chart type: {chart_type}. Valid types: daily, period, grade"}
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Error retrieving chart data: {str(e)}"}
        )