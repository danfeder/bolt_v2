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
from ..dependencies import inject, get_container
from ..core import ConstraintManager
from .unified_strategy import UnifiedSolverStrategy

logger = logging.getLogger(__name__)


class UnifiedSolverAdapter(SolverStrategy):
    """
    Adapter for the UnifiedSolver class to use the SolverStrategy interface
    
    This adapter wraps the existing UnifiedSolver implementation and adapts it
    to the new SolverStrategy interface. This allows the existing solver to be
    used with the new abstraction layer while a full refactoring is in progress.
    
    Note: This adapter is now delegating to the UnifiedSolverStrategy, which is
    the proper implementation of the SolverStrategy interface. This adapter is
    maintained for backward compatibility.
    """
    
    def __init__(
        self, 
        name: str = "unified_solver_adapter", 
        description: str = "Adapter for UnifiedSolver",
        constraint_manager: Optional[ConstraintManager] = None
    ):
        """
        Initialize the adapter
        
        Args:
            name: The name of the strategy
            description: A description of the strategy
            constraint_manager: Optional constraint manager instance
        """
        super().__init__(name, description)
        self._strategy = UnifiedSolverStrategy(
            name="unified_delegated",
            description="Delegated unified solver strategy",
            constraint_manager=constraint_manager
        )
        self._config = None
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the strategy with the provided configuration
        
        Args:
            config: The configuration dictionary
        """
        # Store the configuration
        self._config = config
        
        # Configure the underlying strategy
        self._strategy.configure(config)
    
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
            self._config = config
            self._strategy.configure(config)
        
        # Solve using the delegated strategy
        return self._strategy.solve(request, config)
    
    def can_solve(self, request: ScheduleRequest) -> Tuple[bool, Optional[str]]:
        """
        Check if this strategy can solve the given request
        
        Args:
            request: The scheduling request
            
        Returns:
            A tuple of (can_solve, reason)
        """
        return self._strategy.can_solve(request)
    
    def get_capabilities(self) -> Set[str]:
        """
        Get the capabilities of this strategy
        
        Returns:
            A set of capability strings
        """
        capabilities = self._strategy.get_capabilities()
        
        # Add the 'adapter' capability to indicate this is an adapter
        capabilities.add("adapter")
        
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
