"""
Abstractions for the scheduling system

This package contains interfaces, abstract base classes, and
other foundational abstractions for the scheduling system.
"""

# Core interfaces and abstractions
from .solver_strategy import SolverStrategy, SolverResult
from .solver_config import SolverConfiguration, SolverType, OptimizationLevel, SolverConfigurationBuilder
from .constraint_manager import Constraint, ConstraintViolation, ConstraintSeverity
from .base_constraint import BaseConstraint
from .context import SchedulerContext
from .solver_factory import SolverFactory
from .solver_adapter import UnifiedSolverAdapter, SolverAdapterFactory

# Import concrete implementations
from .concrete_strategies import ORToolsStrategy, GeneticAlgorithmStrategy, HybridStrategy
