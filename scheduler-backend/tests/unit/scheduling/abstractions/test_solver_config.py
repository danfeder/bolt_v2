"""
Tests for the solver configuration module

This module contains tests for the SolverConfiguration and SolverConfigurationBuilder
classes in the abstractions package.
"""

import pytest
import json
from datetime import datetime, timedelta

from app.models import ScheduleRequest, ScheduleConstraints
from app.scheduling.abstractions.solver_config import (
    SolverConfiguration,
    SolverConfigurationBuilder,
    SolverType,
    OptimizationLevel
)


# Example minimal ScheduleRequest for testing
@pytest.fixture
def minimal_schedule_request():
    """Create a minimal ScheduleRequest for testing"""
    start_date = datetime.now()
    end_date = start_date + timedelta(days=30)
    
    # Create constraints object
    constraints = ScheduleConstraints(
        maxClassesPerDay=4,
        maxClassesPerWeek=16,
        minPeriodsPerWeek=8,
        maxConsecutiveClasses=2,
        consecutiveClassesRule="soft",
        startDate=start_date.isoformat(),
        endDate=end_date.isoformat(),
        allowConsecutiveClasses=True,
        requiredBreakPeriods=[4]
    )
    
    return ScheduleRequest(
        classes=[],
        instructorAvailability=[],
        preferences={},
        startDate=start_date.isoformat(),
        endDate=end_date.isoformat(),
        constraints=constraints
    )


class TestSolverConfiguration:
    """Tests for the SolverConfiguration class"""
    
    def test_default_initialization(self):
        """Test default initialization of SolverConfiguration"""
        config = SolverConfiguration()
        
        # Check default values
        assert config.solver_type == SolverType.HYBRID
        assert config.optimization_level == OptimizationLevel.STANDARD
        assert config.timeout_seconds == 60
        assert config.allow_partial_solution == False
        assert config.enable_relaxation == True
        assert config.enable_distribution_optimization == True
        assert config.enable_workload_balancing == True
        assert isinstance(config.weights, dict)
        assert len(config.weights) > 0  # Default weights should be populated
    
    def test_custom_initialization(self):
        """Test custom initialization of SolverConfiguration"""
        config = SolverConfiguration(
            solver_type=SolverType.OR_TOOLS,
            optimization_level=OptimizationLevel.MINIMAL,
            timeout_seconds=30,
            allow_partial_solution=True,
            enable_relaxation=False,
            weights={"test_weight": 100}
        )
        
        # Check custom values
        assert config.solver_type == SolverType.OR_TOOLS
        assert config.optimization_level == OptimizationLevel.MINIMAL
        assert config.timeout_seconds == 30
        assert config.allow_partial_solution == True
        assert config.enable_relaxation == False
        assert "test_weight" in config.weights
        assert config.weights["test_weight"] == 100
    
    def test_validation(self):
        """Test validation of SolverConfiguration"""
        # Valid configuration
        config = SolverConfiguration()
        assert config.is_valid() == True
        assert len(config.validate()) == 0
        
        # Invalid configuration - negative timeout
        config.timeout_seconds = -10
        assert config.is_valid() == False
        errors = config.validate()
        assert len(errors) == 1
        assert "Timeout must be greater than 0 seconds" in errors[0]
        
        # Invalid configuration - invalid mutation rate
        config.timeout_seconds = 60  # Fix the timeout
        config.mutation_rate = 2.0  # Invalid rate
        assert config.is_valid() == False
        errors = config.validate()
        assert len(errors) == 1
        assert "Mutation rate must be between 0 and 1" in errors[0]
        
        # Fix the configuration
        config.mutation_rate = 0.5
        assert config.is_valid() == True
    
    def test_get_set_weight(self):
        """Test getting and setting weights"""
        config = SolverConfiguration()
        
        # Get existing weight
        weight = config.get_weight("single_assignment")
        assert weight > 0
        
        # Get non-existing weight with default
        weight = config.get_weight("non_existing", 42)
        assert weight == 42
        
        # Set weight
        config.set_weight("test_weight", 100)
        assert config.get_weight("test_weight") == 100
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        config = SolverConfiguration(
            solver_type=SolverType.GENETIC,
            optimization_level=OptimizationLevel.INTENSIVE
        )
        
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert config_dict["solver_type"] == "GENETIC"
        assert config_dict["optimization_level"] == "INTENSIVE"
    
    def test_to_from_json(self):
        """Test conversion to and from JSON"""
        config = SolverConfiguration(
            solver_type=SolverType.GENETIC,
            optimization_level=OptimizationLevel.INTENSIVE,
            timeout_seconds=120
        )
        
        # Convert to JSON
        json_str = config.to_json()
        assert isinstance(json_str, str)
        
        # Parse JSON
        parsed = json.loads(json_str)
        assert parsed["solver_type"] == "GENETIC"
        assert parsed["optimization_level"] == "INTENSIVE"
        assert parsed["timeout_seconds"] == 120
        
        # Convert back to configuration
        config2 = SolverConfiguration.from_json(json_str)
        assert config2.solver_type == SolverType.GENETIC
        assert config2.optimization_level == OptimizationLevel.INTENSIVE
        assert config2.timeout_seconds == 120
    
    def test_from_dict(self):
        """Test creation from dictionary"""
        config_dict = {
            "solver_type": "OR_TOOLS",
            "optimization_level": "MINIMAL",
            "timeout_seconds": 45,
            "allow_partial_solution": True
        }
        
        config = SolverConfiguration.from_dict(config_dict)
        assert config.solver_type == SolverType.OR_TOOLS
        assert config.optimization_level == OptimizationLevel.MINIMAL
        assert config.timeout_seconds == 45
        assert config.allow_partial_solution == True
    
    def test_standard_configurations(self):
        """Test standard configuration factory methods"""
        # Minimal configuration
        minimal = SolverConfiguration.create_minimal()
        assert minimal.solver_type == SolverType.OR_TOOLS
        assert minimal.optimization_level == OptimizationLevel.MINIMAL
        assert minimal.timeout_seconds == 10
        
        # Standard configuration
        standard = SolverConfiguration.create_standard()
        assert standard.solver_type == SolverType.HYBRID
        assert standard.optimization_level == OptimizationLevel.STANDARD
        
        # Intensive configuration
        intensive = SolverConfiguration.create_intensive()
        assert intensive.solver_type == SolverType.HYBRID
        assert intensive.optimization_level == OptimizationLevel.INTENSIVE
        assert intensive.timeout_seconds == 300


class TestSolverConfigurationBuilder:
    """Tests for the SolverConfigurationBuilder class"""
    
    def test_builder_pattern(self):
        """Test the builder pattern for creating configurations"""
        builder = SolverConfigurationBuilder()
        
        # Build a configuration using method chaining
        config = (builder
            .with_solver_type(SolverType.GENETIC)
            .with_optimization_level("INTENSIVE")
            .with_timeout(180)
            .allow_partial_solution(True)
            .with_relaxation(False)
            .with_weight("single_assignment", 5000)
            .with_ga_params(150, 0.2)
            .with_debug(True)
            .build())
        
        # Check the configuration
        assert config.solver_type == SolverType.GENETIC
        assert config.optimization_level == OptimizationLevel.INTENSIVE
        assert config.timeout_seconds == 180
        assert config.allow_partial_solution == True
        assert config.enable_relaxation == False
        assert config.get_weight("single_assignment") == 5000
        assert config.population_size == 150
        assert config.mutation_rate == 0.2
        assert config.debug_mode == True
    
    def test_builder_with_string_enums(self):
        """Test the builder with string enum values"""
        builder = SolverConfigurationBuilder()
        
        # Use string values for enums
        config = (builder
            .with_solver_type("genetic")
            .with_optimization_level("minimal")
            .build())
        
        assert config.solver_type == SolverType.GENETIC
        assert config.optimization_level == OptimizationLevel.MINIMAL
    
    def test_builder_with_weights_dict(self):
        """Test the builder with a weights dictionary"""
        builder = SolverConfigurationBuilder()
        
        weights = {
            "single_assignment": 9000,
            "no_overlap": 8500,
            "custom_weight": 1000
        }
        
        config = builder.with_weights(weights).build()
        
        assert config.get_weight("single_assignment") == 9000
        assert config.get_weight("no_overlap") == 8500
        assert config.get_weight("custom_weight") == 1000
