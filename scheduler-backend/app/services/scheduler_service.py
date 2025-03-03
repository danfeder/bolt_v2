"""
Scheduler Service

This service handles the business logic related to schedule generation and management.
It encapsulates the details of interacting with the solver implementations and provides
a clean interface for the API layer.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime

from ..models import ScheduleRequest, ScheduleResponse, WeightConfig, ScheduleMetadata
from ..scheduling.solvers.solver import UnifiedSolver
from ..scheduling.core import SolverConfig
from ..scheduling.constraints.relaxation import RelaxationLevel
from ..scheduling.solvers.config import (
    ENABLE_WEIGHT_TUNING, 
    META_CONFIG, 
    ENABLE_CONSTRAINT_RELAXATION
)
from ..utils.date_utils import to_utc_isoformat
from ..repositories.schedule_repository import ScheduleRepository
from .base_service import BaseService

# Set up logger
logger = logging.getLogger(__name__)


class SchedulerService(BaseService):
    """
    Service for handling schedule generation and related operations.
    
    This service encapsulates the business logic for creating schedules,
    tuning weights, and managing the solver configurations.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the scheduler service with default solvers.
        
        Args:
            **kwargs: Optional dependencies that can be injected
        """
        super().__init__(**kwargs)
        
        # Use injected solvers if provided, otherwise create new instances
        self._unified_solver = kwargs.get('unified_solver', UnifiedSolver())
        self._stable_solver = kwargs.get('stable_solver', UnifiedSolver(use_genetic=False))
        self._dev_solver = kwargs.get('dev_solver', UnifiedSolver(use_genetic=True))
        
        # Get repository from dependencies
        self._schedule_repository = kwargs.get('schedule_repository')
        if not self._schedule_repository:
            self._log_warning("No schedule repository provided, schedule persistence disabled")
        
        self._log_info("SchedulerService initialized with solvers")
    
    def create_stable_schedule(self, request: ScheduleRequest) -> Tuple[ScheduleResponse, Optional[Dict[str, Any]]]:
        """
        Generate a schedule using the stable solver configuration.
        
        This method uses the production solver with optimal parameters for reliable results.
        
        Args:
            request: The schedule request containing all necessary inputs
            
        Returns:
            A tuple of (ScheduleResponse, error_details)
            If error_details is not None, the operation failed
        """
        try:
            self._log_info(f"Creating stable schedule for {len(request.classes)} classes from {request.startDate} to {request.endDate}")
            
            response = self._stable_solver.solve(request)
            
            # Check if we have a valid response with assignments
            if not response.assignments or len(response.assignments) == 0:
                if hasattr(response, 'metadata') and response.metadata and response.metadata.status == "TIMEOUT":
                    self._log_warning("Solver timeout occurred")
                    return response, self._create_error_response(
                        408,  # Request Timeout
                        "The solver timed out. Try reducing the complexity of your request.",
                        "Consider fewer classes, a shorter date range, or simplifying constraints."
                    )
                elif hasattr(response, 'metadata') and response.metadata and response.metadata.status == "ERROR":
                    self._log_error(f"Solver error: {response.metadata.message}")
                    return response, self._create_error_response(
                        500,
                        "The schedule could not be generated due to an internal error.",
                        additional_info={"error": response.metadata.message}
                    )
                else:
                    self._log_warning("No feasible solution found")
                    return response, self._create_error_response(
                        422,
                        "No feasible schedule could be created with the given constraints.",
                        "Try relaxing some constraints or reducing conflicting requirements."
                    )
            
            # Convert assignment date strings to UTC ISO 8601 format
            for assignment in response.assignments:
                assignment.date = to_utc_isoformat(datetime.fromisoformat(assignment.date))
                
            # Return the successful response
            return response, None
            
        except Exception as e:
            self._log_error("Error creating stable schedule", e)
            return ScheduleResponse(assignments=[], metadata=ScheduleMetadata(status="ERROR", message=str(e))), self._create_error_response(
                500,
                f"Scheduling error: {str(e)}"
            )
    
    def create_dev_schedule(self, request: ScheduleRequest) -> Tuple[ScheduleResponse, Optional[Dict[str, Any]]]:
        """
        Generate a schedule using the development solver configuration.
        
        This method uses the genetic algorithm approach for more exploratory results.
        
        Args:
            request: The schedule request containing all necessary inputs
            
        Returns:
            A tuple of (ScheduleResponse, error_details)
            If error_details is not None, the operation failed
        """
        try:
            self._log_info(f"Creating dev schedule with genetic algorithm for {len(request.classes)} classes")
            
            response = self._dev_solver.solve(request)
            
            # Check for solution validity
            if not response.assignments or len(response.assignments) == 0:
                self._log_warning("No feasible solution found with dev solver")
                return response, self._create_error_response(
                    422,
                    "No feasible schedule could be created with the genetic algorithm.",
                    "Try using the stable solver or adjusting your constraints."
                )
            
            # Convert assignment date strings to UTC ISO 8601 format
            for assignment in response.assignments:
                assignment.date = to_utc_isoformat(datetime.fromisoformat(assignment.date))
                
            # Return the successful response
            return response, None
            
        except Exception as e:
            self._log_error("Error creating dev schedule", e)
            return ScheduleResponse(assignments=[], metadata=ScheduleMetadata(status="ERROR", message=str(e))), self._create_error_response(
                500,
                f"Scheduling error with dev solver: {str(e)}"
            )
    
    def compare_solvers(self, request: ScheduleRequest) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Compare results between different solver configurations.
        
        This method runs both the stable and development solvers and compares their results.
        
        Args:
            request: The schedule request containing all necessary inputs
            
        Returns:
            A tuple of (comparison_result, error_details)
            If error_details is not None, the operation failed
        """
        try:
            self._log_info(f"Comparing solvers for request with {len(request.classes)} classes")
            
            # Run both solvers
            stable_response = self._stable_solver.solve(request)
            dev_response = self._dev_solver.solve(request)
            
            # Format dates consistently
            for resp in [stable_response, dev_response]:
                if resp.assignments:
                    for assignment in resp.assignments:
                        assignment.date = to_utc_isoformat(datetime.fromisoformat(assignment.date))
            
            # Create comparison result
            result = {
                "stable": stable_response,
                "dev": dev_response,
                "comparison": {
                    "stable_assignment_count": len(stable_response.assignments) if stable_response.assignments else 0,
                    "dev_assignment_count": len(dev_response.assignments) if dev_response.assignments else 0,
                    "stable_runtime_seconds": stable_response.metadata.runtime_seconds if stable_response.metadata else None,
                    "dev_runtime_seconds": dev_response.metadata.runtime_seconds if dev_response.metadata else None,
                }
            }
            
            return result, None
            
        except Exception as e:
            self._log_error("Error comparing solvers", e)
            return {}, self._create_error_response(
                500,
                f"Error comparing solvers: {str(e)}"
            )
    
    def tune_weights(
        self, 
        schedule_request: ScheduleRequest, 
        population_size: Optional[int] = None,
        generations: Optional[int] = None,
        time_limit: Optional[int] = None,
        parallel: Optional[bool] = None
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Tune solver weights to optimize the schedule quality.
        
        Args:
            schedule_request: The schedule request to optimize for
            population_size: Optional custom population size for the genetic algorithm
            generations: Optional custom number of generations to run
            time_limit: Optional time limit in seconds
            parallel: Whether to use parallel processing
            
        Returns:
            A tuple of (tuning_result, error_details)
            If error_details is not None, the operation failed
        """
        try:
            if not ENABLE_WEIGHT_TUNING:
                self._log_warning("Weight tuning is disabled in configuration")
                return {}, self._create_error_response(
                    403,
                    "Weight tuning is disabled in the current configuration.",
                    "Contact the administrator to enable this feature."
                )
            
            self._log_info(f"Tuning weights for request with {len(schedule_request.classes)} classes")
            
            # Configure the solver for tuning
            solver_config = SolverConfig()
            solver_config.meta_optimizer_config = META_CONFIG.__dict__.copy()
            
            # Override with custom parameters if provided
            if population_size is not None:
                solver_config.meta_optimizer_config["POPULATION_SIZE"] = population_size
            if generations is not None:
                solver_config.meta_optimizer_config["GENERATIONS"] = generations
            if time_limit is not None:
                solver_config.meta_optimizer_config["TIME_LIMIT_SECONDS"] = time_limit
            if parallel is not None:
                solver_config.meta_optimizer_config["PARALLEL_EVALUATION"] = parallel
                
            # Run the meta-optimizer for weight tuning
            tuner = UnifiedSolver(config=solver_config)
            result = tuner.tune_weights(schedule_request)
            
            return result, None
            
        except Exception as e:
            self._log_error("Error during weight tuning", e)
            return {}, self._create_error_response(
                500,
                f"Error during weight tuning: {str(e)}"
            )
    
    def update_solver_config(self, weight_config: WeightConfig) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Update the solver configuration with new weights.
        
        Args:
            weight_config: The new weight configuration
            
        Returns:
            A tuple of (update_result, error_details)
            If error_details is not None, the operation failed
        """
        try:
            self._log_info(f"Updating solver config with weights: {weight_config.weights}")
            
            # Update the weights in the solver
            self._unified_solver.update_weights(weight_config.weights)
            self._stable_solver.update_weights(weight_config.weights)
            self._dev_solver.update_weights(weight_config.weights)
            
            return {"success": True, "message": "Solver configuration updated successfully"}, None
            
        except Exception as e:
            self._log_error("Error updating solver config", e)
            return {}, self._create_error_response(
                500,
                f"Error updating solver configuration: {str(e)}"
            )
    
    def reset_solver_config(self) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Reset the solver configuration to default values.
        
        Returns:
            A tuple of (reset_result, error_details)
            If error_details is not None, the operation failed
        """
        try:
            self._log_info("Resetting solver config to defaults")
            
            # Reset the solvers to default configuration
            self._unified_solver = UnifiedSolver()
            self._stable_solver = UnifiedSolver(use_genetic=False)
            self._dev_solver = UnifiedSolver(use_genetic=True)
            
            return {"success": True, "message": "Solver configuration reset to defaults"}, None
            
        except Exception as e:
            self._log_error("Error resetting solver config", e)
            return {}, self._create_error_response(
                500,
                f"Error resetting solver configuration: {str(e)}"
            )
    
    def create_relaxed_schedule(
        self, 
        request: ScheduleRequest, 
        relaxation_level: str = "MINIMAL"
    ) -> Tuple[ScheduleResponse, Optional[Dict[str, Any]]]:
        """
        Create a schedule with constraint relaxation.
        
        Args:
            request: The schedule request
            relaxation_level: The level of constraint relaxation to apply
            
        Returns:
            A tuple of (ScheduleResponse, error_details)
            If error_details is not None, the operation failed
        """
        try:
            if not ENABLE_CONSTRAINT_RELAXATION:
                self._log_warning("Constraint relaxation is disabled in configuration")
                return ScheduleResponse(assignments=[], metadata=ScheduleMetadata(status="ERROR", message="Constraint relaxation disabled")), self._create_error_response(
                    403,
                    "Constraint relaxation is disabled in the current configuration.",
                    "Contact the administrator to enable this feature."
                )
            
            self._log_info(f"Creating relaxed schedule with level {relaxation_level}")
            
            # Map string relaxation level to enum
            try:
                level = RelaxationLevel[relaxation_level]
            except KeyError:
                self._log_error(f"Invalid relaxation level: {relaxation_level}")
                return ScheduleResponse(assignments=[], metadata=ScheduleMetadata(status="ERROR", message=f"Invalid relaxation level: {relaxation_level}")), self._create_error_response(
                    400,
                    f"Invalid relaxation level: {relaxation_level}",
                    "Must be one of: NONE, MINIMAL, MODERATE, SIGNIFICANT, MAXIMUM"
                )
            
            # Create a solver with relaxation enabled
            solver = UnifiedSolver(use_genetic=False, enable_relaxation=True)
            
            # Solve with relaxation
            response = solver.solve_with_relaxation(request, level)
            
            # Check for valid response
            if not response.assignments or len(response.assignments) == 0:
                self._log_warning(f"No feasible solution found even with relaxation level {relaxation_level}")
                return response, self._create_error_response(
                    422,
                    f"No feasible schedule could be created even with {relaxation_level} relaxation.",
                    "Try a higher relaxation level or reduce conflicting requirements."
                )
            
            # Convert assignment date strings to UTC ISO 8601 format
            for assignment in response.assignments:
                assignment.date = to_utc_isoformat(datetime.fromisoformat(assignment.date))
                
            return response, None
            
        except Exception as e:
            self._log_error("Error creating relaxed schedule", e)
            return ScheduleResponse(assignments=[], metadata=ScheduleMetadata(status="ERROR", message=str(e))), self._create_error_response(
                500,
                f"Error creating relaxed schedule: {str(e)}"
            )
    
    def create_schedule(self, request: ScheduleRequest) -> ScheduleResponse:
        """
        Create a schedule using the default solver configuration.
        
        Args:
            request: The schedule request
            
        Returns:
            ScheduleResponse containing the created schedule
        """
        self._log_info("Creating schedule with default solver")
        
        response = self._unified_solver.create_schedule(request)
        
        # Add request ID to response metadata if not present
        if not hasattr(response, "metadata") or not response.metadata:
            response.metadata = ScheduleMetadata()
        
        # Add timestamp if not present
        if not hasattr(response.metadata, "timestamp") or not response.metadata.timestamp:
            response.metadata.timestamp = to_utc_isoformat(datetime.now())
        
        # Generate and assign schedule ID
        schedule_id = f"schedule_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        response.id = schedule_id
        
        # Save to repository if available
        if self._schedule_repository:
            # Generate request ID and save request for future reference
            request_id = f"request_{schedule_id}"
            self._schedule_repository.save_request(request_id, request)
            
            # Save the response
            try:
                saved_response = self._schedule_repository.create(response)
                self._log_info(f"Saved schedule with ID: {saved_response.id}")
            except Exception as e:
                self._log_error(f"Failed to save schedule: {str(e)}")
        
        return response
    
    def get_schedule(self, schedule_id: str) -> Optional[ScheduleResponse]:
        """
        Retrieve a previously generated schedule by ID.
        
        Args:
            schedule_id: The unique identifier of the schedule
            
        Returns:
            The schedule if found, None otherwise
        """
        if not self._schedule_repository:
            self._log_warning("No repository available, cannot retrieve schedule")
            return None
            
        return self._schedule_repository.get(schedule_id)
    
    def get_schedule_history(self, start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get a history of generated schedules with metadata.
        
        Args:
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            List of schedule metadata records
        """
        if not self._schedule_repository:
            self._log_warning("No repository available, cannot retrieve schedule history")
            return []
            
        return self._schedule_repository.get_schedule_history(start_date, end_date)
    
    def get_solver_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about the solver's performance and configurations.
        
        Returns:
            Dictionary containing solver metrics
        """
        metrics = {
            "solver_type": "unified",
            "features": {
                "or_tools_enabled": True,
                "genetic_algorithm_enabled": True,
                "weight_tuning_enabled": ENABLE_WEIGHT_TUNING,
                "constraint_relaxation_enabled": ENABLE_CONSTRAINT_RELAXATION
            }
        }
        
        # Get running metrics from the solvers if available
        if hasattr(self._stable_solver, 'get_metrics'):
            metrics["stable_solver"] = self._stable_solver.get_metrics()
        if hasattr(self._dev_solver, 'get_metrics'):
            metrics["dev_solver"] = self._dev_solver.get_metrics()
            
        return metrics
    
    def get_relaxation_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about constraint relaxation.
        
        Returns:
            Dictionary containing relaxation metrics
        """
        if not ENABLE_CONSTRAINT_RELAXATION:
            return {
                "enabled": False,
                "message": "Constraint relaxation is disabled"
            }
        
        # Create a test solver with relaxation enabled to get metrics
        solver = UnifiedSolver(enable_relaxation=True)
        
        # Get relaxation metrics
        metrics = {
            "enabled": True,
            "levels": [level.name for level in RelaxationLevel],
            "relaxable_constraints": []
        }
        
        # Add relaxable constraint information if available
        if hasattr(solver, 'get_relaxable_constraints'):
            relaxable = solver.get_relaxable_constraints()
            metrics["relaxable_constraints"] = [
                {
                    "name": constraint.name,
                    "description": constraint.description if hasattr(constraint, "description") else "",
                    "default_weight": constraint.weight if hasattr(constraint, "weight") else None
                } 
                for constraint in relaxable
            ]
            
        return metrics
