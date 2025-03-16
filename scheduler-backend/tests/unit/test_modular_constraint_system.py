"""
Unit Tests for Modular Constraint System

These tests verify the functionality of the modular constraint system,
which allows for independent management of constraints without category-based
organization.
"""

import pytest
import logging
from typing import Dict, List, Any

from app.scheduling.abstractions.modular_constraint_factory import (
    ModularConstraintFactory,
    get_modular_constraint_factory,
    register_modular_constraints
)
from app.scheduling.abstractions.modular_constraint_manager import (
    ModularConstraintManager
)
from app.services.constraint_service import ConstraintService


class TestModularConstraintFactory:
    """Tests for the ModularConstraintFactory"""
    
    def test_constraint_registration(self):
        """Test constraint registration and retrieval"""
        factory = ModularConstraintFactory()
        
        # Create a simple mock constraint class
        class MockConstraint:
            def __init__(self, enabled=True, weight=None):
                self.enabled = enabled
                self.weight = weight
                
            def apply(self, context):
                pass
                
            def validate(self, assignments, context):
                return []
        
        # Register the constraint
        factory.register(
            constraint_type=MockConstraint,
            name="mock_constraint",
            description="A mock constraint for testing",
            default_enabled=True,
            default_weight=1000,
            is_relaxable=True
        )
        
        # Verify registration
        assert "mock_constraint" in factory.get_constraint_names()
        
        # Get metadata
        metadata = factory.get_constraint_metadata("mock_constraint")
        assert metadata is not None
        assert metadata.name == "mock_constraint"
        assert metadata.description == "A mock constraint for testing"
        assert metadata.default_enabled is True
        assert metadata.default_weight == 1000
        assert metadata.is_relaxable is True
        
        # Create constraint instance
        constraint = factory.create_constraint("mock_constraint")
        assert constraint is not None
        assert constraint.enabled is True
        assert constraint.weight == 1000
        
        # Test with custom config
        constraint = factory.create_constraint(
            "mock_constraint", 
            {"enabled": False, "weight": 2000}
        )
        assert constraint is not None
        assert constraint.enabled is False
        assert constraint.weight == 2000
    
    def test_constraint_dependencies(self):
        """Test constraint dependency management"""
        factory = ModularConstraintFactory()
        
        # Create mock constraint classes
        class BaseConstraint:
            def __init__(self, enabled=True, weight=None):
                self.enabled = enabled
                self.weight = weight
                
            def apply(self, context):
                pass
                
            def validate(self, assignments, context):
                return []
        
        class MockConstraintA(BaseConstraint):
            pass
            
        class MockConstraintB(BaseConstraint):
            pass
            
        class MockConstraintC(BaseConstraint):
            pass
        
        # Register constraints
        factory.register(constraint_type=MockConstraintA, name="constraint_a")
        factory.register(constraint_type=MockConstraintB, name="constraint_b")
        factory.register(constraint_type=MockConstraintC, name="constraint_c")
        
        # Set up dependencies
        factory.set_required_constraints("constraint_b", ["constraint_a"])
        factory.set_required_constraints("constraint_c", ["constraint_b"])
        
        # Test dependency resolution
        resolved = factory.resolve_dependencies(["constraint_c"])
        assert set(resolved) == {"constraint_a", "constraint_b", "constraint_c"}
        
        # Test compatibility validation
        valid, errors, missing = factory.validate_constraint_compatibility(["constraint_c"])
        assert valid is False
        assert len(missing) == 1
        assert "constraint_c" in missing
        assert set(missing["constraint_c"]) == {"constraint_b"}
        
        valid, errors, missing = factory.validate_constraint_compatibility(
            ["constraint_a", "constraint_b", "constraint_c"]
        )
        assert valid is True
        assert len(errors) == 0
        assert len(missing) == 0
    
    def test_constraint_incompatibilities(self):
        """Test constraint incompatibility management"""
        factory = ModularConstraintFactory()
        
        # Create mock constraint classes
        class BaseConstraint:
            def __init__(self, enabled=True, weight=None):
                self.enabled = enabled
                self.weight = weight
                
            def apply(self, context):
                pass
                
            def validate(self, assignments, context):
                return []
        
        class MockConstraintX(BaseConstraint):
            pass
            
        class MockConstraintY(BaseConstraint):
            pass
        
        # Register constraints
        factory.register(constraint_type=MockConstraintX, name="constraint_x")
        factory.register(constraint_type=MockConstraintY, name="constraint_y")
        
        # Set up incompatibilities
        factory.set_incompatible_constraints("constraint_x", ["constraint_y"])
        
        # Test compatibility validation
        valid, errors, missing = factory.validate_constraint_compatibility(
            ["constraint_x", "constraint_y"]
        )
        assert valid is False
        assert len(errors) == 1
        assert "incompatible" in errors[0].lower()
        assert "constraint_x" in errors[0]
        assert "constraint_y" in errors[0]
        
    def test_deprecated_constraints(self):
        """Test deprecated constraint handling"""
        factory = ModularConstraintFactory()
        
        # Create a simple mock constraint class
        class MockConstraint:
            def __init__(self, enabled=True, weight=None):
                self.enabled = enabled
                self.weight = weight
                
            def apply(self, context):
                pass
                
            def validate(self, assignments, context):
                return []
        
        # Register a deprecated constraint with replacement
        factory.register(
            constraint_type=MockConstraint, 
            name="old_constraint",
            description="A deprecated constraint", 
            deprecated=True,
            replacement="new_constraint"
        )
        
        # Register the replacement constraint
        factory.register(MockConstraint, name="new_constraint")
        
        # Get metadata and verify deprecated status
        metadata = factory.get_constraint_metadata("old_constraint")
        assert metadata is not None
        assert metadata.deprecated is True
        assert metadata.replacement == "new_constraint"
        
        # Verify the to_dict method includes deprecation info
        metadata_dict = metadata.to_dict()
        assert metadata_dict["deprecated"] is True
        assert metadata_dict["replacement"] == "new_constraint"


class TestModularConstraintManager:
    """Tests for the ModularConstraintManager"""
    
    def test_constraint_management(self):
        """Test adding, enabling, and disabling constraints"""
        factory = ModularConstraintFactory()
        
        # Create a simple mock constraint class
        class MockConstraint:
            def __init__(self, enabled=True, weight=None):
                self.enabled = enabled
                self.weight = weight
                
            def apply(self, context):
                pass
                
            def validate(self, assignments, context):
                return []
        
        # Register the constraint
        factory.register(
            constraint_type=MockConstraint,
            name="mock_constraint",
            description="A mock constraint for testing",
            default_enabled=True,
            default_weight=1000,
            is_relaxable=True
        )
        
        # Create manager with factory
        manager = ModularConstraintManager(factory)
        
        # Add constraint
        constraint = manager.add_constraint("mock_constraint")
        assert constraint is not None
        assert "mock_constraint" in manager.get_all_constraints()
        
        # Enable/disable constraint
        manager.disable_constraint("mock_constraint")
        constraint = manager.get_constraint("mock_constraint")
        assert constraint.enabled is False
        
        manager.enable_constraint("mock_constraint")
        constraint = manager.get_constraint("mock_constraint")
        assert constraint.enabled is True
        
        # Get enabled constraints
        enabled = manager.get_enabled_constraints()
        assert "mock_constraint" in enabled
        
        # Remove constraint
        manager.remove_constraint("mock_constraint")
        assert "mock_constraint" not in manager.get_all_constraints()
    
    def test_constraint_configuration(self):
        """Test configuring constraints"""
        factory = ModularConstraintFactory()
        
        # Create a constraint class with configurable properties
        class ConfigurableConstraint:
            def __init__(self, enabled=True, weight=None, threshold=10, name="default"):
                self.enabled = enabled
                self.weight = weight
                self.threshold = threshold
                self.name = name
                
            def apply(self, context):
                pass
                
            def validate(self, assignments, context):
                return []
        
        # Register the constraint
        factory.register(
            constraint_type=ConfigurableConstraint,
            name="configurable_constraint",
            default_enabled=True,
            default_weight=1000
        )
        
        # Create manager
        manager = ModularConstraintManager(factory)
        
        # Add constraint with custom config
        constraint = manager.add_constraint(
            "configurable_constraint", 
            {"threshold": 20, "name": "custom"}
        )
        assert constraint.threshold == 20
        assert constraint.name == "custom"
        
        # Update configuration
        manager.configure_constraints({
            "configurable_constraint": {
                "threshold": 30,
                "name": "updated"
            }
        })
        
        # Check updated configuration
        constraint = manager.get_constraint("configurable_constraint")
        assert constraint.threshold == 30
        assert constraint.name == "updated"
        
        # Get configuration
        config = manager.get_constraint_configuration()
        assert "configurable_constraint" in config
        assert config["configurable_constraint"]["threshold"] == 30
        assert config["configurable_constraint"]["name"] == "updated"


class TestConstraintService:
    """Tests for the ConstraintService"""
    
    def test_service_initialization(self):
        """Test service initialization with default constraints"""
        service = ConstraintService()
        
        # Get all constraints
        result = service.get_all_constraints()
        assert result.success
        
        # Verify essential constraints are present
        constraints = result.data["constraints"]
        assert "single_assignment" in constraints
        assert "no_overlap" in constraints
        assert "instructor_availability" in constraints
        
        # Check for default constraint configuration
        active = service.get_active_constraints()
        assert active.success
        assert len(active.data) >= 3  # At least the essential constraints
    
    def test_constraint_validation(self):
        """Test constraint validation"""
        service = ConstraintService()
        
        # Create a result object from validate_constraints method
        result = service.validate_constraints([
            "single_assignment", 
            "no_overlap"
        ])
        
        # Test should pass with compatible constraints
        assert result.success
        assert result.data["valid"] is True
        
        # Create incompatible constraints for testing
        factory = service._factory
        
        # Create mock constraint classes
        class BaseConstraint:
            def __init__(self, enabled=True, weight=None):
                self.enabled = enabled
                self.weight = weight
                
            def apply(self, context):
                pass
                
            def validate(self, assignments, context):
                return []
        
        class TestConstraintA(BaseConstraint):
            pass
            
        class TestConstraintB(BaseConstraint):
            pass
        
        # Register incompatible constraints
        factory.register(constraint_type=TestConstraintA, name="test_a")
        factory.register(constraint_type=TestConstraintB, name="test_b")
        factory.set_incompatible_constraints("test_a", ["test_b"])
        
        # Test incompatible constraints
        result = service.validate_constraints(["test_a", "test_b"])
        assert result.success  # Result is success to indicate validation completed
        assert result.data["valid"] is False
        assert len(result.data["errors"]) > 0
    
    def test_constraint_configuration_update(self):
        """Test updating constraint configuration"""
        service = ConstraintService()
        
        # Create a simple configuration update
        # Use constraints that don't have dependency relationships
        config = {
            "single_assignment": {"enabled": True},
            "daily_limit": {"enabled": True}  # Changed from no_overlap which had dependencies
        }
        
        # Apply configuration
        result = service.update_constraint_configuration(config)
        assert result.success
        
        # Verify configuration was applied
        active = service.get_active_constraints()
        assert "single_assignment" in active.data
        assert "daily_limit" in active.data
        
        # Disable a constraint
        result = service.disable_constraint("daily_limit")
        # Debug output to understand what's happening
        print(f"\nDEBUG: Disable constraint result: {result.__dict__}")
        assert result.success
        
        # Verify constraint was disabled
        active = service.get_active_constraints()
        assert "daily_limit" not in active.data


    def test_deprecated_constraint_handling(self):
        """Test deprecated constraint handling in the constraint service"""
        # Create a service with a factory that has a deprecated constraint
        factory = ModularConstraintFactory()
        
        # Create a simple mock constraint class
        class MockConstraint:
            def __init__(self, enabled=True, weight=None):
                self.enabled = enabled
                self.weight = weight
                
            def apply(self, context):
                pass
                
            def validate(self, assignments, context):
                return []
        
        # Register regular and deprecated constraints
        factory.register(
            MockConstraint, 
            name="standard_constraint",
            description="A standard constraint"
        )
        
        factory.register(
            MockConstraint, 
            name="deprecated_constraint",
            description="A deprecated constraint", 
            deprecated=True,
            replacement="standard_constraint"
        )
        
        # Create constraint service with our factory
        service = ConstraintService()
        service._factory = factory  # Inject our test factory
        service._manager = ModularConstraintManager(factory)
        
        # Test enabling a deprecated constraint
        result = service.enable_constraint("deprecated_constraint")
        
        # Should return warning with deprecation info
        assert result.success is True
        assert len(result.warnings) > 0  # Should have warnings
        assert any("deprecated" in warning.lower() for warning in result.warnings)
        # The warning message should also be in the warning data
        assert any("standard_constraint" in warning for warning in result.warnings)
        
        # Get constraint info
        result = service.get_constraint("deprecated_constraint")
        
        # Should include deprecation metadata
        assert result.success is True
        assert result.data["metadata"]["deprecated"] is True
        assert result.data["metadata"]["replacement"] == "standard_constraint"


if __name__ == "__main__":
    # Run tests if called directly
    pytest.main(["-xvs", __file__])
