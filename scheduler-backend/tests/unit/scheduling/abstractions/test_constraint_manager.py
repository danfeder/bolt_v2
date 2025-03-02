"""
Tests for the constraint management system

This module contains tests for the constraint management system classes
in the abstractions package.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from app.models import (
    ScheduleRequest,
    Class,
    TimeSlot,
    InstructorAvailability,
    ScheduleConstraints
)
from app.scheduling.abstractions.context import SchedulerContext
from app.scheduling.abstractions.constraint_manager import (
    ConstraintSeverity,
    ConstraintViolation,
    ConstraintFactory,
    ConstraintRegistry,
    EnhancedConstraintManager
)
from app.scheduling.abstractions.base_constraint import (
    BaseConstraint,
    BaseRelaxableConstraint
)


# Simple test implementation of a constraint
class TestConstraint(BaseConstraint):
    """Test constraint implementation"""
    
    def __init__(self, name: str, enabled: bool = True, weight: Optional[float] = None):
        super().__init__(name, enabled, weight)
        self.apply_called = False
        self.validate_called = False
        self.violation_to_return = []
    
    def apply(self, context: SchedulerContext) -> None:
        """Apply the constraint"""
        self.apply_called = True
        self.context = context
    
    def validate(
        self, 
        assignments: List[Dict[str, Any]], 
        context: SchedulerContext
    ) -> List[ConstraintViolation]:
        """Validate the constraint"""
        self.validate_called = True
        self.assignments = assignments
        self.context = context
        return self.violation_to_return


# Simple test implementation of a relaxable constraint
class TestRelaxableConstraint(BaseRelaxableConstraint):
    """Test relaxable constraint implementation"""
    
    def __init__(
        self, 
        name: str, 
        enabled: bool = True, 
        weight: Optional[float] = None,
        max_relaxation_level: int = 3
    ):
        super().__init__(name, enabled, weight, max_relaxation_level)
        self.apply_called = False
        self.validate_called = False
        self.violation_to_return = []
    
    def apply(self, context: SchedulerContext) -> None:
        """Apply the constraint"""
        self.apply_called = True
        self.context = context
    
    def validate(
        self, 
        assignments: List[Dict[str, Any]], 
        context: SchedulerContext
    ) -> List[ConstraintViolation]:
        """Validate the constraint"""
        self.validate_called = True
        self.assignments = assignments
        self.context = context
        return self.violation_to_return


# Simple test implementation of a constraint factory
class TestConstraintFactory(ConstraintFactory):
    """Test constraint factory implementation"""
    
    def create(self, name: str, **kwargs) -> TestConstraint:
        """Create a test constraint"""
        return TestConstraint(name, **kwargs)


# Fixture for minimal schedule request
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


# Fixture for scheduler context
@pytest.fixture
def scheduler_context(minimal_schedule_request):
    """Create a SchedulerContext for testing"""
    return SchedulerContext(
        request=minimal_schedule_request,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 31)
    )


class TestConstraintViolation:
    """Tests for the ConstraintViolation class"""
    
    def test_initialization(self):
        """Test initialization of ConstraintViolation"""
        violation = ConstraintViolation(
            constraint_name="test_constraint",
            message="Test violation",
            severity=ConstraintSeverity.ERROR,
            context={"class_id": "class1"}
        )
        
        assert violation.constraint_name == "test_constraint"
        assert violation.message == "Test violation"
        assert violation.severity == ConstraintSeverity.ERROR
        assert violation.context == {"class_id": "class1"}
    
    def test_string_representation(self):
        """Test string representation of ConstraintViolation"""
        violation = ConstraintViolation(
            constraint_name="test_constraint",
            message="Test violation",
            severity=ConstraintSeverity.WARNING
        )
        
        str_repr = str(violation)
        assert "WARNING" in str_repr
        assert "test_constraint" in str_repr
        assert "Test violation" in str_repr


class TestBaseConstraint:
    """Tests for the BaseConstraint class"""
    
    def test_initialization(self):
        """Test initialization of BaseConstraint"""
        constraint = TestConstraint(
            name="test_constraint",
            enabled=True,
            weight=10.0
        )
        
        assert constraint.name == "test_constraint"
        assert constraint.enabled == True
        assert constraint.weight == 10.0
        assert constraint.is_hard_constraint == False
    
    def test_hard_constraint(self):
        """Test hard constraint (weight=None)"""
        constraint = TestConstraint(
            name="hard_constraint",
            weight=None
        )
        
        assert constraint.is_hard_constraint == True
    
    def test_enabled_setter(self):
        """Test enabled setter"""
        constraint = TestConstraint("test_constraint")
        assert constraint.enabled == True
        
        constraint.enabled = False
        assert constraint.enabled == False
    
    def test_weight_setter(self):
        """Test weight setter"""
        constraint = TestConstraint("test_constraint", weight=5.0)
        assert constraint.weight == 5.0
        
        constraint.weight = 10.0
        assert constraint.weight == 10.0
        
        # Change to hard constraint
        constraint.weight = None
        assert constraint.is_hard_constraint == True
    
    def test_string_representation(self):
        """Test string representation"""
        constraint = TestConstraint("test_constraint", weight=5.0)
        str_repr = str(constraint)
        
        assert "Soft constraint" in str_repr
        assert "test_constraint" in str_repr
        assert "Enabled" in str_repr
        assert "weight=5.0" in str_repr
        
        # Hard constraint
        constraint = TestConstraint("hard_constraint", weight=None)
        str_repr = str(constraint)
        
        assert "Hard constraint" in str_repr
        assert "hard_constraint" in str_repr


class TestBaseRelaxableConstraint:
    """Tests for the BaseRelaxableConstraint class"""
    
    def test_initialization(self):
        """Test initialization of BaseRelaxableConstraint"""
        constraint = TestRelaxableConstraint(
            name="relaxable_constraint",
            weight=10.0,
            max_relaxation_level=5
        )
        
        assert constraint.name == "relaxable_constraint"
        assert constraint.weight == 10.0
        assert constraint.relaxation_level == 0
        assert constraint.max_relaxation_level == 5
    
    def test_relaxation_level_setter(self):
        """Test relaxation level setter"""
        constraint = TestRelaxableConstraint("test_constraint", max_relaxation_level=5)
        assert constraint.relaxation_level == 0
        
        # Set within bounds
        constraint.relaxation_level = 3
        assert constraint.relaxation_level == 3
        
        # Set above max
        constraint.relaxation_level = 10
        assert constraint.relaxation_level == 5  # Should be capped at max
        
        # Set below min
        constraint.relaxation_level = -2
        assert constraint.relaxation_level == 0  # Should be capped at min
    
    def test_get_relaxed_weight_hard_constraint(self):
        """Test get_relaxed_weight for hard constraints"""
        constraint = TestRelaxableConstraint("hard_constraint", weight=None)
        
        # With relaxation level 0, should return a very high weight
        assert constraint.get_relaxed_weight() > 100000
        
        # With relaxation level > 0, should return a reduced weight
        constraint.relaxation_level = 1
        relaxed_weight = constraint.get_relaxed_weight()
        assert relaxed_weight < 100000
        assert relaxed_weight > 0
        
        # Higher relaxation level should result in lower weight
        constraint.relaxation_level = 2
        assert constraint.get_relaxed_weight() < relaxed_weight
    
    def test_get_relaxed_weight_soft_constraint(self):
        """Test get_relaxed_weight for soft constraints"""
        constraint = TestRelaxableConstraint("soft_constraint", weight=1000)
        
        # With relaxation level 0, should return the original weight
        assert constraint.get_relaxed_weight() == 1000
        
        # With relaxation level > 0, should return a reduced weight
        constraint.relaxation_level = 1
        relaxed_weight = constraint.get_relaxed_weight()
        assert relaxed_weight < 1000
        assert relaxed_weight > 0
        
        # Higher relaxation level should result in lower weight
        constraint.relaxation_level = 2
        assert constraint.get_relaxed_weight() < relaxed_weight
    
    def test_string_representation(self):
        """Test string representation"""
        constraint = TestRelaxableConstraint("test_constraint", weight=5.0, max_relaxation_level=5)
        constraint.relaxation_level = 2
        str_repr = str(constraint)
        
        assert "Soft constraint" in str_repr
        assert "test_constraint" in str_repr
        assert "relaxation=2/5" in str_repr


class TestConstraintRegistry:
    """Tests for the ConstraintRegistry class"""
    
    def test_initialization(self):
        """Test initialization of ConstraintRegistry"""
        registry = ConstraintRegistry()
        assert len(registry.get_registered_types()) == 0
    
    def test_register_get_factory(self):
        """Test registering and getting factories"""
        registry = ConstraintRegistry()
        factory = TestConstraintFactory()
        
        # Register a factory
        registry.register("test_type", factory)
        assert len(registry.get_registered_types()) == 1
        assert "test_type" in registry.get_registered_types()
        
        # Get the factory
        retrieved_factory = registry.get_factory("test_type")
        assert retrieved_factory is factory
        
        # Get a non-existing factory
        assert registry.get_factory("non_existing") is None
    
    def test_create_constraint(self):
        """Test creating constraints through the registry"""
        registry = ConstraintRegistry()
        factory = TestConstraintFactory()
        registry.register("test_type", factory)
        
        # Create a constraint
        constraint = registry.create_constraint("test_type", "test_constraint", weight=5.0)
        assert isinstance(constraint, TestConstraint)
        assert constraint.name == "test_constraint"
        assert constraint.weight == 5.0
        
        # Try to create with a non-existing type
        constraint = registry.create_constraint("non_existing", "test_constraint")
        assert constraint is None


class TestEnhancedConstraintManager:
    """Tests for the EnhancedConstraintManager class"""
    
    def test_initialization(self):
        """Test initialization of EnhancedConstraintManager"""
        manager = EnhancedConstraintManager()
        assert len(manager.get_all_constraints()) == 0
        assert isinstance(manager.registry, ConstraintRegistry)
    
    def test_add_remove_constraint(self):
        """Test adding and removing constraints"""
        manager = EnhancedConstraintManager()
        constraint1 = TestConstraint("constraint1")
        constraint2 = TestConstraint("constraint2")
        
        # Add constraints
        manager.add_constraint(constraint1)
        manager.add_constraint(constraint2)
        
        assert len(manager.get_all_constraints()) == 2
        assert constraint1 in manager.get_all_constraints()
        assert constraint2 in manager.get_all_constraints()
        
        # Remove a constraint
        manager.remove_constraint("constraint1")
        assert len(manager.get_all_constraints()) == 1
        assert constraint1 not in manager.get_all_constraints()
        assert constraint2 in manager.get_all_constraints()
    
    def test_get_constraint(self):
        """Test getting a constraint by name"""
        manager = EnhancedConstraintManager()
        constraint = TestConstraint("test_constraint")
        manager.add_constraint(constraint)
        
        # Get existing constraint
        retrieved = manager.get_constraint("test_constraint")
        assert retrieved is constraint
        
        # Get non-existing constraint
        assert manager.get_constraint("non_existing") is None
    
    def test_get_enabled_constraints(self):
        """Test getting enabled constraints"""
        manager = EnhancedConstraintManager()
        constraint1 = TestConstraint("constraint1", enabled=True)
        constraint2 = TestConstraint("constraint2", enabled=False)
        constraint3 = TestConstraint("constraint3", enabled=True)
        
        manager.add_constraint(constraint1)
        manager.add_constraint(constraint2)
        manager.add_constraint(constraint3)
        
        enabled = manager.get_enabled_constraints()
        assert len(enabled) == 2
        assert constraint1 in enabled
        assert constraint2 not in enabled
        assert constraint3 in enabled
    
    def test_apply_all(self, scheduler_context):
        """Test applying all constraints"""
        manager = EnhancedConstraintManager()
        constraint1 = TestConstraint("constraint1", weight=None)  # Hard constraint
        constraint2 = TestConstraint("constraint2", weight=10.0)  # Soft constraint
        constraint3 = TestConstraint("constraint3", enabled=False)  # Disabled constraint
        
        manager.add_constraint(constraint1)
        manager.add_constraint(constraint2)
        manager.add_constraint(constraint3)
        
        # Apply all constraints
        manager.apply_all(scheduler_context)
        
        # Check that enabled constraints were applied
        assert constraint1.apply_called == True
        assert constraint2.apply_called == True
        assert constraint3.apply_called == False
    
    def test_validate_all(self, scheduler_context):
        """Test validating all constraints"""
        manager = EnhancedConstraintManager()
        
        # Create constraints with violations
        constraint1 = TestConstraint("constraint1")
        violation1 = ConstraintViolation(
            constraint_name="constraint1",
            message="Violation 1",
            severity=ConstraintSeverity.WARNING
        )
        constraint1.violation_to_return = [violation1]
        
        constraint2 = TestConstraint("constraint2")
        violation2 = ConstraintViolation(
            constraint_name="constraint2",
            message="Violation 2",
            severity=ConstraintSeverity.CRITICAL
        )
        constraint2.violation_to_return = [violation2]
        
        manager.add_constraint(constraint1)
        manager.add_constraint(constraint2)
        
        # Validate all constraints
        assignments = [{"class_id": "class1", "instructor_id": "instructor1"}]
        is_valid, violations = manager.validate_all(assignments, scheduler_context)
        
        # Check that constraints were validated
        assert constraint1.validate_called == True
        assert constraint2.validate_called == True
        
        # Check validation results
        assert is_valid == False  # Should be invalid due to CRITICAL violation
        assert len(violations) == 2
        assert violation1 in violations
        assert violation2 in violations
