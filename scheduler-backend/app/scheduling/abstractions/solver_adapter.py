"""
Solver Adapter Module

This module provides adapter classes that bridge the existing solver implementations
with the new abstraction layer. This allows for a gradual transition to the new
architecture without disrupting existing functionality.
"""

from typing import Dict, Any, List, Optional, Set, Tuple
import logging

from ...models import ScheduleRequest, ScheduleResponse, ScheduleMetadata
from ..solvers.solver import UnifiedSolver, SolverConfig
from .solver_strategy import SolverStrategy, SolverResult
from .solver_config import SolverConfiguration, SolverType, OptimizationLevel
from .context import SchedulerContext

logger = logging.getLogger(__name__)


class UnifiedSolverAdapter(SolverStrategy):
    """
    Adapter for the UnifiedSolver class to use the SolverStrategy interface
    
    This adapter wraps the existing UnifiedSolver implementation and adapts it
    to the new SolverStrategy interface. This allows the existing solver to be
    used with the new abstraction layer while a full refactoring is in progress.
    """
    
    def __init__(self, name: str = "unified_solver_adapter", description: str = "Adapter for UnifiedSolver"):
        """
        Initialize the adapter
        
        Args:
            name: The name of the strategy
            description: A description of the strategy
        """
        super().__init__(name, description)
        self._unified_solver = None
        self._config = None
    
    def _ensure_solver_initialized(self, request: Optional[ScheduleRequest] = None) -> UnifiedSolver:
        """
        Ensure the unified solver is initialized
        
        Args:
            request: The schedule request (optional)
            
        Returns:
            The initialized unified solver
        """
        if self._unified_solver is None or (request is not None and self._unified_solver.request != request):
            # Convert the configuration to the format expected by UnifiedSolver
            use_or_tools = self._config.solver_type in (SolverType.OR_TOOLS, SolverType.HYBRID, SolverType.META)
            use_genetic = self._config.solver_type in (SolverType.GENETIC, SolverType.HYBRID, SolverType.META)
            
            # Create a solver config
            solver_config = SolverConfig()
            
            # Initialize the unified solver
            self._unified_solver = UnifiedSolver(
                request=request,
                config=solver_config,
                use_or_tools=use_or_tools,
                use_genetic=use_genetic,
                custom_weights=self._config.weights,
                enable_relaxation=self._config.enable_relaxation
            )
        
        return self._unified_solver
    
    def solve(self, request: ScheduleRequest, config: Dict[str, Any]) -> SolverResult:
        """
        Solve the scheduling problem
        
        Args:
            request: The scheduling request
            config: Configuration for the solver
            
        Returns:
            The result of the solving process
        """
        # Convert configuration dictionary to SolverConfiguration
        if not self._config:
            self._config = SolverConfiguration.from_dict(config)
        
        # Make sure the solver is initialized
        solver = self._ensure_solver_initialized(request)
        
        # Solve using the unified solver
        try:
            response = solver.solve(
                time_limit_seconds=self._config.timeout_seconds,
                max_iterations=self._config.max_iterations
            )
            
            # Create a SolverResult from the response
            return SolverResult(
                success=True,
                schedule=response,
                metadata={
                    "runtime_ms": response.metadata.duration_ms,
                    "solutions_found": response.metadata.solutions_found,
                    "score": response.metadata.score,
                    "gap": response.metadata.gap,
                    "solver_name": response.metadata.solver
                },
                assignments=response.assignments
            )
        except Exception as e:
            logger.error(f"Error solving with UnifiedSolver: {str(e)}")
            # Create a minimal valid ScheduleResponse for error case
            error_metadata = ScheduleMetadata(
                duration_ms=0,
                solutions_found=0,
                score=0,
                gap=0.0,
                solver=self._config.solver_type.value,
                status="ERROR",
                message=str(e)
            )
            
            error_response = ScheduleResponse(
                id=request.id if request else "error",
                metadata=error_metadata,
                assignments=[]
            )
            
            return SolverResult(
                success=False,
                schedule=error_response,
                error=str(e)
            )
    
    def can_solve(self, request: ScheduleRequest) -> Tuple[bool, Optional[str]]:
        """
        Check if this strategy can solve the given request
        
        Args:
            request: The scheduling request
            
        Returns:
            A tuple of (can_solve, reason) where reason is None if can_solve is True,
            otherwise it contains a string explaining why the strategy cannot solve the request
        """
        # For now, we assume the UnifiedSolver can handle all requests
        # In a more sophisticated implementation, we would check the request characteristics
        
        # Check for basic validity
        if not request or not request.classes or len(request.classes) == 0:
            return False, "Request contains no classes to schedule"
        
        if not request.instructorAvailability or len(request.instructorAvailability) == 0:
            return False, "Request contains no instructor availability information"
        
        return True, None
    
    def get_capabilities(self) -> Set[str]:
        """
        Get the capabilities of this strategy
        
        Returns:
            A set of capability strings
        """
        capabilities = {
            "constraint_relaxation",
            "distribution_optimization",
            "standard_optimization",
            "medium_scale"
        }
        
        # Add capabilities based on the configuration
        if self._config:
            if self._config.solver_type == SolverType.OR_TOOLS:
                capabilities.add("exact_solution")
            elif self._config.solver_type == SolverType.GENETIC:
                capabilities.add("approximate_solution")
                capabilities.add("large_scale")
            elif self._config.solver_type == SolverType.HYBRID:
                capabilities.add("exact_solution")
                capabilities.add("approximate_solution")
                capabilities.add("large_scale")
            
            if self._config.optimization_level == OptimizationLevel.INTENSIVE:
                capabilities.add("intensive_optimization")
                capabilities.remove("standard_optimization") if "standard_optimization" in capabilities else None
            elif self._config.optimization_level == OptimizationLevel.MINIMAL:
                capabilities.remove("standard_optimization") if "standard_optimization" in capabilities else None
                capabilities.add("minimal_optimization")
        
        return capabilities


class SolverAdapterFactory:
    """
    Factory for creating solver adapters
    
    This class creates appropriate adapters for different solver implementations,
    allowing them to be used with the new abstraction layer.
    """
    
    @staticmethod
    def create_adapter(solver_type: SolverType) -> SolverStrategy:
        """
        Create an appropriate adapter for the given solver type
        
        Args:
            solver_type: The type of solver to adapt
            
        Returns:
            A strategy adapter for the solver
        """
        # For now, we only have the UnifiedSolverAdapter
        return UnifiedSolverAdapter(f"{solver_type.name.lower()}_adapter")
