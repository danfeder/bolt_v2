"""Unit tests for constraint relaxation system."""
import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, List, Any, Optional

from app.scheduling.constraints.relaxation import (
    RelaxationLevel,
    RelaxationResult,
    RelaxableConstraint,
    RelaxationController
)
from app.scheduling.core import SchedulerContext


class TestRelaxationLevel:
    """Tests for the RelaxationLevel enum."""
    
    def test_level_ordering(self):
        """Test level ordering and values."""
        assert RelaxationLevel.NONE.value == 0
        assert RelaxationLevel.MINIMAL.value == 1
        assert RelaxationLevel.MODERATE.value == 2
        assert RelaxationLevel.SIGNIFICANT.value == 3
        assert RelaxationLevel.MAXIMUM.value == 4
        
        # Verify ordering
        assert RelaxationLevel.NONE.value < RelaxationLevel.MINIMAL.value
        assert RelaxationLevel.MINIMAL.value < RelaxationLevel.MODERATE.value
        assert RelaxationLevel.MODERATE.value < RelaxationLevel.SIGNIFICANT.value
        assert RelaxationLevel.SIGNIFICANT.value < RelaxationLevel.MAXIMUM.value


class TestRelaxationResult:
    """Tests for the RelaxationResult dataclass."""
    
    def test_create_result(self):
        """Test creation of relaxation result."""
        result = RelaxationResult(
            constraint_name="test_constraint",
            original_level=RelaxationLevel.NONE,
            applied_level=RelaxationLevel.MINIMAL,
            success=True,
            message="Relaxation successful",
            relaxation_params={"param1": 10, "param2": "value"}
        )
        
        assert result.constraint_name == "test_constraint"
        assert result.original_level == RelaxationLevel.NONE
        assert result.applied_level == RelaxationLevel.MINIMAL
        assert result.success is True
        assert result.message == "Relaxation successful"
        assert result.relaxation_params == {"param1": 10, "param2": "value"}
    
    def test_default_params(self):
        """Test default parameters for relaxation result."""
        result = RelaxationResult(
            constraint_name="test_constraint",
            original_level=RelaxationLevel.NONE,
            applied_level=RelaxationLevel.MINIMAL,
            success=True,
            message="Relaxation successful"
        )
        
        assert result.relaxation_params == {}


class TestRelaxableConstraint:
    """Tests for the RelaxableConstraint base class."""
    
    def test_init(self):
        """Test constraint initialization."""
        # Default init
        constraint = RelaxableConstraint("test_constraint")
        assert constraint.name == "test_constraint"
        assert constraint.enabled is True
        assert constraint.can_relax is True
        assert constraint.relaxation_priority == 1
        assert constraint.never_relax is False
        assert constraint.current_relaxation_level == RelaxationLevel.NONE
        assert constraint.relaxation_params == {}
        
        # Custom init
        constraint = RelaxableConstraint(
            name="custom_constraint",
            enabled=False,
            priority=2,
            weight=1.5,
            can_relax=False,
            relaxation_priority=3,
            never_relax=True
        )
        assert constraint.name == "custom_constraint"
        assert constraint.enabled is False
        assert constraint.priority == 2
        assert constraint.weight == 1.5
        assert constraint.can_relax is False
        assert constraint.relaxation_priority == 3
        assert constraint.never_relax is True
    
    def test_relax_never_relax(self):
        """Test relax when never_relax is True."""
        constraint = RelaxableConstraint("test_constraint", never_relax=True)
        
        result = constraint.relax(RelaxationLevel.MINIMAL)
        
        assert result.constraint_name == "test_constraint"
        assert result.original_level == RelaxationLevel.NONE
        assert result.applied_level == RelaxationLevel.NONE
        assert result.success is False
        assert "never_relax" in result.message
    
    def test_relax_cannot_relax(self):
        """Test relax when can_relax is False."""
        constraint = RelaxableConstraint("test_constraint", can_relax=False)
        
        result = constraint.relax(RelaxationLevel.MINIMAL)
        
        assert result.constraint_name == "test_constraint"
        assert result.original_level == RelaxationLevel.NONE
        assert result.applied_level == RelaxationLevel.NONE
        assert result.success is False
        assert "does not support relaxation" in result.message
    
    def test_relax_lower_level(self):
        """Test relax when trying to apply a lower level."""
        constraint = RelaxableConstraint("test_constraint")
        constraint.current_relaxation_level = RelaxationLevel.MODERATE
        
        result = constraint.relax(RelaxationLevel.MINIMAL)
        
        assert result.constraint_name == "test_constraint"
        assert result.original_level == RelaxationLevel.MODERATE
        assert result.applied_level == RelaxationLevel.MODERATE
        assert result.success is False
        assert "Cannot decrease relaxation level" in result.message
    
    def test_relax_same_level(self):
        """Test relax when trying to apply the same level."""
        constraint = RelaxableConstraint("test_constraint")
        constraint.current_relaxation_level = RelaxationLevel.MINIMAL
        
        result = constraint.relax(RelaxationLevel.MINIMAL)
        
        assert result.constraint_name == "test_constraint"
        assert result.original_level == RelaxationLevel.MINIMAL
        assert result.applied_level == RelaxationLevel.MINIMAL
        assert result.success is True
        assert "already at level" in result.message
    
    def test_relax_success(self):
        """Test successful relaxation."""
        constraint = RelaxableConstraint("test_constraint")
        
        # Create a mock implementation of _apply_relaxation
        def mock_apply(level, context):
            constraint.relaxation_params["param1"] = 10
            return True, "Test relaxation applied", {"param1": 10}
        
        # Monkey-patch the _apply_relaxation method
        constraint._apply_relaxation = mock_apply
        
        result = constraint.relax(RelaxationLevel.MODERATE)
        
        assert result.constraint_name == "test_constraint"
        assert result.original_level == RelaxationLevel.NONE
        assert result.applied_level == RelaxationLevel.MODERATE
        assert result.success is True
        assert "Test relaxation applied" in result.message
        assert result.relaxation_params == {"param1": 10}
        assert constraint.current_relaxation_level == RelaxationLevel.MODERATE
    
    def test_relax_failure(self):
        """Test failed relaxation."""
        constraint = RelaxableConstraint("test_constraint")
        
        # Create a mock implementation of _apply_relaxation that fails
        def mock_apply(level, context):
            return False, "Could not apply relaxation", {}
        
        # Monkey-patch the _apply_relaxation method
        constraint._apply_relaxation = mock_apply
        
        result = constraint.relax(RelaxationLevel.MINIMAL)
        
        assert result.constraint_name == "test_constraint"
        assert result.original_level == RelaxationLevel.NONE
        assert result.applied_level == RelaxationLevel.NONE  # Unchanged
        assert result.success is False
        assert "Could not apply relaxation" in result.message
        assert constraint.current_relaxation_level == RelaxationLevel.NONE  # Unchanged


# Create a concrete implementation of RelaxableConstraint for testing
class TestConstraint(RelaxableConstraint):
    """Concrete implementation of RelaxableConstraint for testing."""
    
    def __init__(self, name="test_constraint", **kwargs):
        super().__init__(name, **kwargs)
        self.apply_called = False
        self.validate_called = False
    
    def apply(self, context: Optional[SchedulerContext]) -> None:
        """Mock apply method."""
        self.apply_called = True
    
    def validate(self, assignments: List[Dict[str, Any]], context: Optional[SchedulerContext]) -> List[Any]:
        """Mock validate method."""
        self.validate_called = True
        return []
    
    def _apply_relaxation(self, level: RelaxationLevel, context: Optional[SchedulerContext]) -> tuple:
        """Apply test relaxation."""
        if level == RelaxationLevel.NONE:
            return False, "Cannot relax to NONE level", {}
        
        # Always succeed for testing
        return True, f"Test relaxation to {level.name}", {"test_param": level.value}


class TestRelaxationController:
    """Tests for the RelaxationController class."""
    
    def test_init(self):
        """Test controller initialization."""
        controller = RelaxationController()
        assert controller.relaxable_constraints == {}
        assert controller.relaxation_results == []
        assert controller.never_relax_constraints == set()
    
    def test_register_constraint(self):
        """Test constraint registration."""
        controller = RelaxationController()
        constraint1 = TestConstraint("constraint1")
        constraint2 = TestConstraint("constraint2", never_relax=True)
        
        controller.register_constraint(constraint1)
        controller.register_constraint(constraint2)
        
        assert "constraint1" in controller.relaxable_constraints
        assert "constraint2" in controller.relaxable_constraints
        assert controller.relaxable_constraints["constraint1"] == constraint1
        assert controller.relaxable_constraints["constraint2"] == constraint2
        assert "constraint2" in controller.never_relax_constraints
    
    def test_relax_constraints_empty(self):
        """Test relaxation with no constraints."""
        controller = RelaxationController()
        
        results = controller.relax_constraints(RelaxationLevel.MINIMAL)
        
        assert results == []
    
    def test_relax_constraints_all(self):
        """Test relaxation of all constraints."""
        controller = RelaxationController()
        
        # Register constraints
        constraint1 = TestConstraint("constraint1")
        constraint2 = TestConstraint("constraint2", relaxation_priority=2)
        constraint3 = TestConstraint("constraint3", never_relax=True)
        
        controller.register_constraint(constraint1)
        controller.register_constraint(constraint2)
        controller.register_constraint(constraint3)
        
        # Relax all constraints
        results = controller.relax_constraints(RelaxationLevel.MINIMAL)
        
        # Should have 2 results (constraint3 is never_relax)
        assert len(results) == 3
        
        # Check first result (highest priority)
        assert results[0].constraint_name == "constraint1"
        assert results[0].success is True
        
        # Check second result (lower priority)
        assert results[1].constraint_name == "constraint2"
        assert results[1].success is True
        
        # Check third result (never_relax)
        assert results[2].constraint_name == "constraint3"
        assert results[2].success is False
        
        # Verify results are stored
        assert len(controller.relaxation_results) == 3
    
    def test_relax_constraints_specific(self):
        """Test relaxation of specific constraints by name."""
        controller = RelaxationController()
        
        # Register constraints
        constraint1 = TestConstraint("constraint1")
        constraint2 = TestConstraint("constraint2")
        constraint3 = TestConstraint("constraint3")
        
        controller.register_constraint(constraint1)
        controller.register_constraint(constraint2)
        controller.register_constraint(constraint3)
        
        # Relax only constraint2
        results = controller.relax_constraints(
            RelaxationLevel.MODERATE,
            constraint_names=["constraint2"]
        )
        
        # Should have 1 result
        assert len(results) == 1
        assert results[0].constraint_name == "constraint2"
        assert results[0].success is True
        assert results[0].applied_level == RelaxationLevel.MODERATE
        
        # Verify only constraint2 was relaxed
        assert constraint1.current_relaxation_level == RelaxationLevel.NONE
        assert constraint2.current_relaxation_level == RelaxationLevel.MODERATE
        assert constraint3.current_relaxation_level == RelaxationLevel.NONE
    
    def test_relax_constraints_multiple_levels(self):
        """Test sequential relaxation at different levels."""
        controller = RelaxationController()
        
        # Register constraint
        constraint = TestConstraint("test_constraint")
        controller.register_constraint(constraint)
        
        # First relaxation - MINIMAL
        results1 = controller.relax_constraints(RelaxationLevel.MINIMAL)
        assert len(results1) == 1
        assert results1[0].success is True
        assert results1[0].applied_level == RelaxationLevel.MINIMAL
        assert constraint.current_relaxation_level == RelaxationLevel.MINIMAL
        assert constraint.relaxation_params["test_param"] == 1
        
        # Second relaxation - MODERATE
        results2 = controller.relax_constraints(RelaxationLevel.MODERATE)
        assert len(results2) == 1
        assert results2[0].success is True
        assert results2[0].applied_level == RelaxationLevel.MODERATE
        assert constraint.current_relaxation_level == RelaxationLevel.MODERATE
        assert constraint.relaxation_params["test_param"] == 2
        
        # Third relaxation - MAXIMUM (should fail)
        results3 = controller.relax_constraints(RelaxationLevel.MAXIMUM)
        assert len(results3) == 1
        assert results3[0].success is False
        assert results3[0].applied_level == RelaxationLevel.MODERATE  # Unchanged
        assert constraint.current_relaxation_level == RelaxationLevel.MODERATE  # Unchanged
    
    def test_get_relaxation_status(self):
        """Test getting relaxation status."""
        controller = RelaxationController()
        
        # Register constraints with different relaxation levels
        constraint1 = TestConstraint("constraint1")
        constraint2 = TestConstraint("constraint2")
        
        controller.register_constraint(constraint1)
        controller.register_constraint(constraint2)
        
        # Relax to different levels
        controller.relax_constraints(RelaxationLevel.MINIMAL, constraint_names=["constraint1"])
        controller.relax_constraints(RelaxationLevel.MODERATE, constraint_names=["constraint2"])
        
        # Get status
        status = controller.get_relaxation_status()
        
        assert len(status) == 2
        assert status["constraint1"] == RelaxationLevel.MINIMAL
        assert status["constraint2"] == RelaxationLevel.MODERATE
    
    def test_reset_relaxation(self):
        """Test resetting relaxation levels."""
        controller = RelaxationController()
        
        # Register and relax constraints
        constraint1 = TestConstraint("constraint1")
        constraint2 = TestConstraint("constraint2")
        
        controller.register_constraint(constraint1)
        controller.register_constraint(constraint2)
        
        controller.relax_constraints(RelaxationLevel.MODERATE)
        
        # Verify relaxation was applied
        assert constraint1.current_relaxation_level == RelaxationLevel.MODERATE
        assert constraint2.current_relaxation_level == RelaxationLevel.MODERATE
        
        # Reset relaxation
        controller.reset_relaxation()
        
        # Verify reset
        assert constraint1.current_relaxation_level == RelaxationLevel.NONE
        assert constraint2.current_relaxation_level == RelaxationLevel.NONE
        assert controller.relaxation_results == []
