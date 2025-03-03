"""
Solver Configuration Module

This module defines the configuration classes for the scheduler solvers.
It provides a standardized way to configure solvers with validation and defaults.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Any, List, Optional, Set, Type, ClassVar, Union
import copy
import json
import logging

logger = logging.getLogger(__name__)

class OptimizationLevel(Enum):
    """Optimization level for solvers"""
    MINIMAL = auto()    # Fast, basic solution
    STANDARD = auto()   # Balanced performance and quality
    INTENSIVE = auto()  # Higher quality, slower
    MAXIMUM = auto()    # Best possible solution, very slow


class SolverType(Enum):
    """Types of solvers available"""
    OR_TOOLS = auto()   # Google OR-Tools CP-SAT solver
    GENETIC = auto()    # Genetic algorithm solver
    HYBRID = auto()     # Hybrid solver (combines multiple approaches)
    META = auto()       # Meta-optimizer that selects the best solver


@dataclass
class SolverConfiguration:
    """
    Configuration for solvers with validation and defaults
    
    This class encapsulates all configuration options for the solvers,
    provides validation, and sets sensible defaults.
    """
    # Solver selection and basic behavior
    solver_type: SolverType = SolverType.HYBRID
    optimization_level: OptimizationLevel = OptimizationLevel.STANDARD
    timeout_seconds: int = 60
    allow_partial_solution: bool = False
    
    # Feature flags
    enable_relaxation: bool = True
    enable_distribution_optimization: bool = True
    enable_workload_balancing: bool = True
    
    # Weights for different objectives and constraints
    weights: Dict[str, int] = field(default_factory=dict)
    
    # Performance tuning
    max_iterations: int = 10000
    population_size: int = 100  # For genetic algorithm
    mutation_rate: float = 0.1  # For genetic algorithm
    
    # Advanced options
    debug_mode: bool = False
    parallel_execution: bool = True
    experimental_features: bool = False
    
    # Default weights for common objectives and constraints
    DEFAULT_WEIGHTS: ClassVar[Dict[str, int]] = {
        "single_assignment": 10000,
        "no_overlap": 10000,
        "instructor_availability": 9000,
        "required_periods": 8000,
        "avoid_periods": 2000,
        "preferred_periods": 5000,
        "distribution": 3000,
        "workload_balance": 2500,
        "consecutive_classes": 2000,
        "grade_mixing": 1500,
        "earlier_dates": 100
    }
    
    def __post_init__(self):
        """Initialize default weights if not provided"""
        if not self.weights:
            self.weights = copy.deepcopy(self.DEFAULT_WEIGHTS)
    
    def validate(self) -> List[str]:
        """
        Validate the configuration
        
        Returns:
            A list of validation errors, empty if valid
        """
        errors = []
        
        # Validate timeout
        if self.timeout_seconds <= 0:
            errors.append("Timeout must be greater than 0 seconds")
        
        # Validate genetic algorithm parameters
        if self.solver_type in (SolverType.GENETIC, SolverType.HYBRID):
            if self.population_size <= 0:
                errors.append("Population size must be greater than 0")
            if not 0 <= self.mutation_rate <= 1:
                errors.append("Mutation rate must be between 0 and 1")
        
        # Validate weights
        for key, value in self.weights.items():
            if key not in self.DEFAULT_WEIGHTS:
                errors.append(f"Unknown weight key: {key}")
        
        return errors
    
    def is_valid(self) -> bool:
        """
        Check if the configuration is valid
        
        Returns:
            True if valid, False otherwise
        """
        return len(self.validate()) == 0
    
    def get_weight(self, key: str, default: Optional[int] = None) -> int:
        """
        Get a weight value
        
        Args:
            key: The weight key
            default: Default value if not found
            
        Returns:
            The weight value
        """
        if default is None:
            default = self.DEFAULT_WEIGHTS.get(key, 0)
        return self.weights.get(key, default)
    
    def set_weight(self, key: str, value: int) -> None:
        """
        Set a weight value
        
        Args:
            key: The weight key
            value: The weight value
        """
        self.weights[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary
        
        Returns:
            Dictionary representation of the configuration
        """
        return {
            "solver_type": self.solver_type.name,
            "optimization_level": self.optimization_level.name,
            "timeout_seconds": self.timeout_seconds,
            "allow_partial_solution": self.allow_partial_solution,
            "enable_relaxation": self.enable_relaxation,
            "enable_distribution_optimization": self.enable_distribution_optimization,
            "enable_workload_balancing": self.enable_workload_balancing,
            "weights": self.weights,
            "max_iterations": self.max_iterations,
            "population_size": self.population_size,
            "mutation_rate": self.mutation_rate,
            "debug_mode": self.debug_mode,
            "parallel_execution": self.parallel_execution,
            "experimental_features": self.experimental_features
        }
    
    def to_json(self) -> str:
        """
        Convert to JSON string
        
        Returns:
            JSON string representation of the configuration
        """
        # Convert enum values to strings for JSON serialization
        config_dict = self.to_dict()
        return json.dumps(config_dict, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SolverConfiguration':
        """
        Create a configuration from a dictionary
        
        Args:
            data: Dictionary with configuration values
            
        Returns:
            A new SolverConfiguration instance
        """
        config = cls()
        
        # Convert string enum values to enum instances
        if "solver_type" in data:
            try:
                config.solver_type = SolverType[data["solver_type"]]
            except KeyError:
                pass
        
        if "optimization_level" in data:
            try:
                config.optimization_level = OptimizationLevel[data["optimization_level"]]
            except KeyError:
                pass
        
        # Set other fields
        for key, value in data.items():
            if key not in ("solver_type", "optimization_level") and hasattr(config, key):
                setattr(config, key, value)
        
        return config
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SolverConfiguration':
        """
        Create a configuration from a JSON string
        
        Args:
            json_str: JSON string with configuration values
            
        Returns:
            A new SolverConfiguration instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def create_minimal(cls) -> 'SolverConfiguration':
        """
        Create a minimal configuration for fast solving
        
        Returns:
            A minimal SolverConfiguration instance
        """
        return cls(
            solver_type=SolverType.OR_TOOLS,
            optimization_level=OptimizationLevel.MINIMAL,
            timeout_seconds=10,
            enable_distribution_optimization=False,
            enable_workload_balancing=False,
            parallel_execution=False
        )
    
    @classmethod
    def create_standard(cls) -> 'SolverConfiguration':
        """
        Create a standard configuration for balanced performance and quality
        
        Returns:
            A standard SolverConfiguration instance
        """
        return cls()
    
    @classmethod
    def create_intensive(cls) -> 'SolverConfiguration':
        """
        Create an intensive configuration for higher quality
        
        Returns:
            An intensive SolverConfiguration instance
        """
        return cls(
            solver_type=SolverType.HYBRID,
            optimization_level=OptimizationLevel.INTENSIVE,
            timeout_seconds=300,
            max_iterations=50000,
            population_size=200
        )


class SolverConfigurationBuilder:
    """
    Builder for SolverConfiguration
    
    This class provides a fluent interface for building SolverConfiguration instances.
    It includes preset configurations for common use cases and validates the configuration
    as it's being built.
    """
    
    def __init__(self):
        """Initialize with default configuration"""
        self._config = SolverConfiguration()
        self._validation_errors: List[str] = []
    
    def with_solver_type(self, solver_type: Union[SolverType, str]) -> 'SolverConfigurationBuilder':
        """
        Set the solver type
        
        Args:
            solver_type: The solver type (enum or string name)
            
        Returns:
            Self for method chaining
        """
        if isinstance(solver_type, str):
            try:
                solver_type = SolverType[solver_type.upper()]
            except KeyError:
                self._validation_errors.append(f"Invalid solver type: {solver_type}")
                return self
        
        self._config.solver_type = solver_type
        return self
    
    def with_optimization_level(self, level: Union[OptimizationLevel, str]) -> 'SolverConfigurationBuilder':
        """
        Set the optimization level
        
        Args:
            level: The optimization level (enum or string name)
            
        Returns:
            Self for method chaining
        """
        if isinstance(level, str):
            try:
                level = OptimizationLevel[level.upper()]
            except KeyError:
                self._validation_errors.append(f"Invalid optimization level: {level}")
                return self
        
        self._config.optimization_level = level
        return self
    
    def with_timeout(self, seconds: int) -> 'SolverConfigurationBuilder':
        """
        Set the timeout in seconds
        
        Args:
            seconds: Timeout in seconds
            
        Returns:
            Self for method chaining
        """
        if seconds <= 0:
            self._validation_errors.append("Timeout must be greater than 0 seconds")
        
        self._config.timeout_seconds = seconds
        return self
    
    def allow_partial_solution(self, allow: bool = True) -> 'SolverConfigurationBuilder':
        """
        Allow partial solutions
        
        Args:
            allow: Whether to allow partial solutions
            
        Returns:
            Self for method chaining
        """
        self._config.allow_partial_solution = allow
        return self
    
    def with_relaxation(self, enable: bool = True) -> 'SolverConfigurationBuilder':
        """
        Enable or disable constraint relaxation
        
        Args:
            enable: Whether to enable relaxation
            
        Returns:
            Self for method chaining
        """
        self._config.enable_relaxation = enable
        return self
    
    def with_distribution_optimization(self, enable: bool = True) -> 'SolverConfigurationBuilder':
        """
        Enable or disable distribution optimization
        
        Args:
            enable: Whether to enable distribution optimization
            
        Returns:
            Self for method chaining
        """
        self._config.enable_distribution_optimization = enable
        return self
    
    def with_workload_balancing(self, enable: bool = True) -> 'SolverConfigurationBuilder':
        """
        Enable or disable workload balancing
        
        Args:
            enable: Whether to enable workload balancing
            
        Returns:
            Self for method chaining
        """
        self._config.enable_workload_balancing = enable
        return self
    
    def with_weight(self, key: str, value: int) -> 'SolverConfigurationBuilder':
        """
        Set a weight value
        
        Args:
            key: The weight key
            value: The weight value
            
        Returns:
            Self for method chaining
        """
        if key not in SolverConfiguration.DEFAULT_WEIGHTS:
            self._validation_errors.append(f"Unknown weight key: {key}")
        
        self._config.weights[key] = value
        return self
    
    def with_weights(self, weights: Dict[str, int]) -> 'SolverConfigurationBuilder':
        """
        Set multiple weight values
        
        Args:
            weights: Dictionary of weight values
            
        Returns:
            Self for method chaining
        """
        for key, value in weights.items():
            self.with_weight(key, value)
        return self
    
    def with_ga_params(self, population_size: int, mutation_rate: float) -> 'SolverConfigurationBuilder':
        """
        Set genetic algorithm parameters
        
        Args:
            population_size: Population size
            mutation_rate: Mutation rate (0-1)
            
        Returns:
            Self for method chaining
        """
        if population_size <= 0:
            self._validation_errors.append("Population size must be greater than 0")
        
        if not 0 <= mutation_rate <= 1:
            self._validation_errors.append("Mutation rate must be between 0 and 1")
        
        self._config.population_size = population_size
        self._config.mutation_rate = mutation_rate
        return self
    
    def with_debug(self, enable: bool = True) -> 'SolverConfigurationBuilder':
        """
        Enable or disable debug mode
        
        Args:
            enable: Whether to enable debug mode
            
        Returns:
            Self for method chaining
        """
        self._config.debug_mode = enable
        return self
    
    def with_parallel(self, enable: bool = True) -> 'SolverConfigurationBuilder':
        """
        Enable or disable parallel execution
        
        Args:
            enable: Whether to enable parallel execution
            
        Returns:
            Self for method chaining
        """
        self._config.parallel_execution = enable
        return self
    
    # New methods to enhance the builder
    
    def for_or_tools_strategy(self) -> 'SolverConfigurationBuilder':
        """
        Configure for the OR-Tools strategy
        
        Returns:
            Self for method chaining
        """
        self.with_solver_type(SolverType.OR_TOOLS)
        return self
    
    def for_genetic_strategy(self) -> 'SolverConfigurationBuilder':
        """
        Configure for the Genetic Algorithm strategy
        
        Returns:
            Self for method chaining
        """
        self.with_solver_type(SolverType.GENETIC)
        self.with_ga_params(population_size=100, mutation_rate=0.1)
        return self
    
    def for_hybrid_strategy(self) -> 'SolverConfigurationBuilder':
        """
        Configure for the Hybrid strategy
        
        Returns:
            Self for method chaining
        """
        self.with_solver_type(SolverType.HYBRID)
        return self
    
    def optimize_for_speed(self) -> 'SolverConfigurationBuilder':
        """
        Optimize configuration for speed over quality
        
        Returns:
            Self for method chaining
        """
        self.with_optimization_level(OptimizationLevel.MINIMAL)
        self.with_timeout(10)
        self.with_distribution_optimization(False)
        self.with_workload_balancing(False)
        return self
    
    def optimize_for_quality(self) -> 'SolverConfigurationBuilder':
        """
        Optimize configuration for quality over speed
        
        Returns:
            Self for method chaining
        """
        self.with_optimization_level(OptimizationLevel.INTENSIVE)
        self.with_timeout(300)
        if self._config.solver_type == SolverType.GENETIC:
            self.with_ga_params(population_size=200, mutation_rate=0.1)
        return self
    
    def adapt_to_problem_size(self, request_size: int) -> 'SolverConfigurationBuilder':
        """
        Adapt configuration based on problem size
        
        Args:
            request_size: Size metric for the problem (e.g., number of classes)
            
        Returns:
            Self for method chaining
        """
        if request_size < 10:
            # Small problem - use OR-Tools with intensive optimization
            self.for_or_tools_strategy()
            self.with_optimization_level(OptimizationLevel.INTENSIVE)
        elif request_size < 50:
            # Medium problem - use Hybrid with standard optimization
            self.for_hybrid_strategy()
            self.with_optimization_level(OptimizationLevel.STANDARD)
        else:
            # Large problem - use Genetic with minimal optimization
            self.for_genetic_strategy()
            self.with_optimization_level(OptimizationLevel.MINIMAL)
        return self
    
    def validate(self) -> List[str]:
        """
        Validate the configuration being built
        
        Returns:
            List of validation errors, empty if valid
        """
        # Reset validation errors
        self._validation_errors = []
        
        # Perform validation
        self._validate_timeout()
        self._validate_genetic_params()
        self._validate_weights()
        
        # Return all validation errors
        return self._validation_errors
    
    def _validate_timeout(self) -> None:
        """Validate timeout settings"""
        if self._config.timeout_seconds <= 0:
            self._validation_errors.append("Timeout must be greater than 0 seconds")
    
    def _validate_genetic_params(self) -> None:
        """Validate genetic algorithm parameters"""
        if self._config.solver_type in (SolverType.GENETIC, SolverType.HYBRID):
            if self._config.population_size <= 0:
                self._validation_errors.append("Population size must be greater than 0")
            if not 0 <= self._config.mutation_rate <= 1:
                self._validation_errors.append("Mutation rate must be between 0 and 1")
    
    def _validate_weights(self) -> None:
        """Validate weights"""
        for key in self._config.weights:
            if key not in self._config.DEFAULT_WEIGHTS:
                self._validation_errors.append(f"Unknown weight key: {key}")
    
    def build(self) -> SolverConfiguration:
        """
        Build the configuration
        
        Validates the configuration before building it. If there are validation errors,
        a ValueError is raised.
        
        Returns:
            The built SolverConfiguration instance
            
        Raises:
            ValueError: If the configuration is invalid
        """
        # Validate the configuration
        errors = self.validate()
        if errors:
            raise ValueError(f"Invalid configuration: {'; '.join(errors)}")
        
        # Create a copy to avoid modifying the builder's instance
        return copy.deepcopy(self._config)
    
    def build_or_default(self) -> SolverConfiguration:
        """
        Build the configuration or return a valid default
        
        Similar to build(), but returns a valid default configuration if
        the current configuration is invalid instead of raising an exception.
        
        Returns:
            The built SolverConfiguration instance or a default instance
        """
        # Validate the configuration
        errors = self.validate()
        if errors:
            # Log the errors and return a default configuration
            logger.warning(f"Configuration validation failed: {'; '.join(errors)}. Using default configuration.")
            return SolverConfiguration.create_standard()
        
        # Create a copy to avoid modifying the builder's instance
        return copy.deepcopy(self._config)
