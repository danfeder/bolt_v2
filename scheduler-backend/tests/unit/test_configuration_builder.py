"""
Unit tests for the ConfigurationBuilder

This module contains unit tests for the ConfigurationBuilder implementation
to ensure it correctly creates and configures SolverConfiguration objects.
"""

import unittest
import pytest

from app.scheduling.abstractions.configuration_builder import (
    ConfigurationBuilder, configure, 
    create_fast_config, create_quality_config, create_balanced_config
)
from app.scheduling.abstractions.solver_config import SolverConfiguration, SolverType, OptimizationLevel
from app.scheduling.constraints.relaxation import RelaxationLevel


class TestConfigurationBuilder(unittest.TestCase):
    """Tests for the ConfigurationBuilder implementation"""
    
    def setUp(self):
        """Set up the test environment"""
        self.builder = ConfigurationBuilder()
        
    def test_default_configuration(self):
        """Test that the default configuration is created correctly"""
        config = self.builder.build()
        
        # Check that the default configuration has the expected values
        self.assertEqual(config.solver_type, SolverType.UNIFIED)
        self.assertEqual(config.optimization_level, OptimizationLevel.BALANCED)
        self.assertEqual(config.timeout_seconds, 60)
        self.assertEqual(config.max_iterations, 1000)
        self.assertTrue(config.enable_relaxation)
        self.assertEqual(config.relaxation_level, RelaxationLevel.NONE)
        self.assertEqual(config.weights, {})
        self.assertEqual(config.options, {})
        
    def test_with_solver_type(self):
        """Test setting the solver type"""
        # Test with enum value
        config = self.builder.with_solver_type(SolverType.OR_TOOLS).build()
        self.assertEqual(config.solver_type, SolverType.OR_TOOLS)
        
        # Test with string value
        config = self.builder.with_solver_type("GENETIC").build()
        self.assertEqual(config.solver_type, SolverType.GENETIC)
        
        # Test with invalid string value (should use default)
        config = self.builder.with_solver_type("INVALID").build()
        self.assertEqual(config.solver_type, SolverType.UNIFIED)
        
    def test_with_optimization_level(self):
        """Test setting the optimization level"""
        # Test with enum value
        config = self.builder.with_optimization_level(OptimizationLevel.SPEED).build()
        self.assertEqual(config.optimization_level, OptimizationLevel.SPEED)
        
        # Test with string value
        config = self.builder.with_optimization_level("QUALITY").build()
        self.assertEqual(config.optimization_level, OptimizationLevel.QUALITY)
        
        # Test with invalid string value (should use default)
        config = self.builder.with_optimization_level("INVALID").build()
        self.assertEqual(config.optimization_level, OptimizationLevel.BALANCED)
        
    def test_with_timeout(self):
        """Test setting the timeout"""
        # Test with valid value
        config = self.builder.with_timeout(120).build()
        self.assertEqual(config.timeout_seconds, 120)
        
        # Test with invalid value (should use default)
        config = self.builder.with_timeout(-10).build()
        self.assertEqual(config.timeout_seconds, 60)
        
    def test_with_max_iterations(self):
        """Test setting the max iterations"""
        # Test with valid value
        config = self.builder.with_max_iterations(2000).build()
        self.assertEqual(config.max_iterations, 2000)
        
        # Test with invalid value (should use default)
        config = self.builder.with_max_iterations(-10).build()
        self.assertEqual(config.max_iterations, 1000)
        
    def test_with_relaxation(self):
        """Test setting the relaxation configuration"""
        # Test enabling relaxation
        config = self.builder.with_relaxation(True, RelaxationLevel.MEDIUM).build()
        self.assertTrue(config.enable_relaxation)
        self.assertEqual(config.relaxation_level, RelaxationLevel.MEDIUM)
        
        # Test disabling relaxation
        config = self.builder.with_relaxation(False).build()
        self.assertFalse(config.enable_relaxation)
        self.assertEqual(config.relaxation_level, RelaxationLevel.NONE)
        
        # Test with string value
        config = self.builder.with_relaxation(True, "HIGH").build()
        self.assertTrue(config.enable_relaxation)
        self.assertEqual(config.relaxation_level, RelaxationLevel.HIGH)
        
        # Test with invalid string value (should use default)
        config = self.builder.with_relaxation(True, "INVALID").build()
        self.assertTrue(config.enable_relaxation)
        self.assertEqual(config.relaxation_level, RelaxationLevel.NONE)
        
    def test_with_weights(self):
        """Test setting weights"""
        # Test with individual weight
        config = self.builder.with_weight("constraint1", 10).build()
        self.assertEqual(config.weights, {"constraint1": 10})
        
        # Test with multiple weights
        config = self.builder.with_weights({"constraint2": 20, "constraint3": 30}).build()
        self.assertEqual(config.weights, {"constraint1": 10, "constraint2": 20, "constraint3": 30})
        
    def test_with_options(self):
        """Test setting options"""
        # Test with individual option
        config = self.builder.with_option("option1", "value1").build()
        self.assertEqual(config.options, {"option1": "value1"})
        
        # Test with multiple options
        config = self.builder.with_options({"option2": "value2", "option3": 3}).build()
        self.assertEqual(config.options, {"option1": "value1", "option2": "value2", "option3": 3})
        
    def test_fluent_api(self):
        """Test the fluent API by chaining multiple method calls"""
        config = (self.builder
                  .with_solver_type(SolverType.HYBRID)
                  .with_optimization_level(OptimizationLevel.QUALITY)
                  .with_timeout(180)
                  .with_max_iterations(3000)
                  .with_relaxation(True, RelaxationLevel.LOW)
                  .with_weight("constraint1", 10)
                  .with_weight("constraint2", 20)
                  .with_option("option1", "value1")
                  .build())
                  
        # Check that all configurations were applied
        self.assertEqual(config.solver_type, SolverType.HYBRID)
        self.assertEqual(config.optimization_level, OptimizationLevel.QUALITY)
        self.assertEqual(config.timeout_seconds, 180)
        self.assertEqual(config.max_iterations, 3000)
        self.assertTrue(config.enable_relaxation)
        self.assertEqual(config.relaxation_level, RelaxationLevel.LOW)
        self.assertEqual(config.weights, {"constraint1": 10, "constraint2": 20})
        self.assertEqual(config.options, {"option1": "value1"})
        
    def test_build_dict(self):
        """Test building a configuration dictionary"""
        config_dict = (self.builder
                       .with_solver_type(SolverType.OR_TOOLS)
                       .with_timeout(45)
                       .build_dict())
                       
        # Check that the dictionary was built correctly
        self.assertEqual(config_dict['solver_type'], SolverType.OR_TOOLS)
        self.assertEqual(config_dict['timeout_seconds'], 45)
        
    def test_configure_function(self):
        """Test the configure function"""
        builder = configure()
        self.assertIsInstance(builder, ConfigurationBuilder)
        
    def test_fast_config_preset(self):
        """Test the fast configuration preset"""
        config = create_fast_config()
        
        # Check that the preset has the expected values
        self.assertEqual(config.solver_type, SolverType.OR_TOOLS)
        self.assertEqual(config.optimization_level, OptimizationLevel.SPEED)
        self.assertEqual(config.timeout_seconds, 30)
        self.assertEqual(config.max_iterations, 500)
        self.assertTrue(config.enable_relaxation)
        self.assertEqual(config.relaxation_level, RelaxationLevel.MEDIUM)
        
    def test_quality_config_preset(self):
        """Test the quality configuration preset"""
        config = create_quality_config()
        
        # Check that the preset has the expected values
        self.assertEqual(config.solver_type, SolverType.HYBRID)
        self.assertEqual(config.optimization_level, OptimizationLevel.QUALITY)
        self.assertEqual(config.timeout_seconds, 120)
        self.assertEqual(config.max_iterations, 2000)
        self.assertTrue(config.enable_relaxation)
        self.assertEqual(config.relaxation_level, RelaxationLevel.LOW)
        
    def test_balanced_config_preset(self):
        """Test the balanced configuration preset"""
        config = create_balanced_config()
        
        # Check that the preset has the expected values
        self.assertEqual(config.solver_type, SolverType.UNIFIED)
        self.assertEqual(config.optimization_level, OptimizationLevel.BALANCED)
        self.assertEqual(config.timeout_seconds, 60)
        self.assertEqual(config.max_iterations, 1000)
        self.assertTrue(config.enable_relaxation)
        self.assertEqual(config.relaxation_level, RelaxationLevel.LOW)


if __name__ == '__main__':
    unittest.main()
