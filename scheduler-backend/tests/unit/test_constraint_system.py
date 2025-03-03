"""
Unit tests for the enhanced constraint system

This module contains tests for the enhanced constraint system, including
the ConstraintFactory, EnhancedConstraintManager, and example constraints.
"""

import unittest
from datetime import datetime, time
from typing import Dict, Any, List

from app.scheduling.abstractions.constraint_factory import (
    ConstraintFactory, 
    get_constraint_factory,
    register_default_constraints
)
from app.scheduling.abstractions.constraint_manager import (
    EnhancedConstraintManager,
    ConstraintViolation,
    ConstraintSeverity
)
from app.scheduling.abstractions.base_constraint import BaseConstraint
from app.scheduling.constraints.examples import DayOfWeekConstraint, TimeWindowConstraint
from app.scheduling.core import SchedulerContext


class TestConstraintFactory(unittest.TestCase):
    """Tests for the enhanced ConstraintFactory"""
    
    def setUp(self):
        """Set up the test"""
        # Create a new factory for each test
        self.factory = ConstraintFactory()
        
    def test_register_and_create_constraint(self):
        """Test registering and creating a constraint"""
        # Register a constraint
        self.factory.register(
            constraint_type=DayOfWeekConstraint,
            name="test_day_constraint",
            description="Test day constraint",
            default_enabled=True,
            default_weight=None,
            is_relaxable=False,
            category="test"
        )
        
        # Verify the constraint was registered
        self.assertIn("test_day_constraint", self.factory.get_constraint_names())
        self.assertIn("test", self.factory.get_all_categories())
        self.assertIn("test_day_constraint", self.factory.get_constraint_names_by_category("test"))
        
        # Create the constraint
        constraint = self.factory.create_constraint("test_day_constraint")
        
        # Verify the constraint was created correctly
        self.assertIsNotNone(constraint)
        self.assertEqual(constraint.name, "test_day_constraint")
        self.assertTrue(constraint.enabled)
        self.assertIsNone(constraint.weight)
        
    def test_constraint_categories(self):
        """Test constraint categorization"""
        # Register constraints in different categories
        self.factory.register(
            constraint_type=DayOfWeekConstraint,
            name="day_constraint_1",
            category="schedule"
        )
        
        self.factory.register(
            constraint_type=DayOfWeekConstraint,
            name="day_constraint_2",
            category="schedule"
        )
        
        self.factory.register(
            constraint_type=TimeWindowConstraint,
            name="time_constraint",
            category="time"
        )
        
        # Verify categories
        self.assertIn("schedule", self.factory.get_all_categories())
        self.assertIn("time", self.factory.get_all_categories())
        
        # Verify constraints by category
        schedule_constraints = self.factory.get_constraint_names_by_category("schedule")
        self.assertEqual(len(schedule_constraints), 2)
        self.assertIn("day_constraint_1", schedule_constraints)
        self.assertIn("day_constraint_2", schedule_constraints)
        
        time_constraints = self.factory.get_constraint_names_by_category("time")
        self.assertEqual(len(time_constraints), 1)
        self.assertIn("time_constraint", time_constraints)
        
    def test_constraint_compatibility(self):
        """Test constraint compatibility validation"""
        # Register constraints with compatibility relationships
        self.factory.register(
            constraint_type=DayOfWeekConstraint,
            name="constraint_a",
            category="test"
        )
        
        self.factory.register(
            constraint_type=TimeWindowConstraint,
            name="constraint_b",
            category="test"
        )
        
        self.factory.register(
            constraint_type=DayOfWeekConstraint,
            name="constraint_c",
            category="test"
        )
        
        # Set up incompatibility
        self.factory.set_incompatible_constraints("constraint_a", ["constraint_b"])
        
        # Set up dependency
        self.factory.set_required_constraints("constraint_c", ["constraint_a"])
        
        # Validate compatible constraints
        errors = self.factory.validate_constraints_compatibility(["constraint_a", "constraint_c"])
        self.assertEqual(len(errors), 0)
        
        # Validate incompatible constraints
        errors = self.factory.validate_constraints_compatibility(["constraint_a", "constraint_b"])
        self.assertEqual(len(errors), 1)
        self.assertIn("incompatible", errors[0].lower())
        
        # Validate missing dependency
        errors = self.factory.validate_constraints_compatibility(["constraint_c"])
        self.assertEqual(len(errors), 1)
        self.assertIn("requires", errors[0].lower())


class TestEnhancedConstraintManager(unittest.TestCase):
    """Tests for the EnhancedConstraintManager"""
    
    def setUp(self):
        """Set up the test"""
        # Create a new factory and manager for each test
        self.factory = ConstraintFactory()
        self.manager = EnhancedConstraintManager(self.factory)
        
        # Register test constraints
        self.factory.register(
            constraint_type=DayOfWeekConstraint,
            name="weekday_only",
            description="Only allow weekdays",
            category="schedule"
        )
        
        self.factory.register(
            constraint_type=TimeWindowConstraint,
            name="business_hours",
            description="Only allow business hours",
            category="schedule"
        )
        
    def test_create_and_add_constraint(self):
        """Test creating and adding a constraint to the manager"""
        # Create and add a constraint
        constraint = self.manager.create_and_add_constraint("weekday_only")
        
        # Verify the constraint was added correctly
        self.assertIsNotNone(constraint)
        self.assertEqual(constraint.name, "weekday_only")
        self.assertIn(constraint, self.manager.get_all_constraints())
        self.assertIn(constraint, self.manager.get_enabled_constraints())
        
    def test_create_and_add_constraints_by_category(self):
        """Test creating and adding all constraints in a category"""
        # Create and add all schedule constraints
        constraints = self.manager.create_and_add_constraints_by_category("schedule")
        
        # Verify all schedule constraints were added
        self.assertEqual(len(constraints), 2)
        self.assertEqual(len(self.manager.get_constraints_by_category("schedule")), 2)
        
        # Check that constraints were created correctly
        constraint_names = [c.name for c in constraints]
        self.assertIn("weekday_only", constraint_names)
        self.assertIn("business_hours", constraint_names)
        
    def test_validate_by_category(self):
        """Test validating constraints by category"""
        # Create a mock scheduler context
        context = MockSchedulerContext()
        
        # Create test assignments
        weekday_assignment = {
            "name": "Class A",
            "date": datetime(2025, 3, 3),  # Monday
            "period": 2,
            "instructor": "Instructor 1"
        }
        
        weekend_assignment = {
            "name": "Class B",
            "date": datetime(2025, 3, 8),  # Saturday
            "period": 2,
            "instructor": "Instructor 2"
        }
        
        # Add constraints
        weekday_constraint = self.manager.create_and_add_constraint("weekday_only")
        
        # Test validation with a valid assignment
        is_valid, violations = self.manager.validate_by_category(
            "schedule", [weekday_assignment], context
        )
        self.assertTrue(is_valid)
        self.assertEqual(len(violations), 0)
        
        # Test validation with an invalid assignment
        is_valid, violations = self.manager.validate_by_category(
            "schedule", [weekend_assignment], context
        )
        self.assertFalse(is_valid)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].severity, ConstraintSeverity.CRITICAL)
        self.assertIn("Saturday", violations[0].message)
        
        # Test validation with mixed assignments
        is_valid, violations = self.manager.validate_by_category(
            "schedule", [weekday_assignment, weekend_assignment], context
        )
        self.assertFalse(is_valid)
        self.assertEqual(len(violations), 1)


class TestExampleConstraints(unittest.TestCase):
    """Tests for the example constraints"""
    
    def setUp(self):
        """Set up the test"""
        # Create a mock scheduler context
        self.context = MockSchedulerContext()
        
    def test_day_of_week_constraint(self):
        """Test the DayOfWeekConstraint"""
        # Create a weekday-only constraint
        constraint = DayOfWeekConstraint(
            name="weekday_only",
            allowed_days=[0, 1, 2, 3, 4]  # Monday to Friday
        )
        
        # Create test assignments
        monday_assignment = {
            "name": "Class A",
            "date": datetime(2025, 3, 3),  # Monday
            "period": 2,
            "instructor": "Instructor 1"
        }
        
        saturday_assignment = {
            "name": "Class B",
            "date": datetime(2025, 3, 8),  # Saturday
            "period": 2,
            "instructor": "Instructor 2"
        }
        
        # Test validation with a valid assignment
        violations = constraint.validate([monday_assignment], self.context)
        self.assertEqual(len(violations), 0)
        
        # Test validation with an invalid assignment
        violations = constraint.validate([saturday_assignment], self.context)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].severity, ConstraintSeverity.CRITICAL)
        self.assertIn("Saturday", violations[0].message)
        
        # Verify the context information in the violation
        self.assertIn("day_of_week", violations[0].context)
        self.assertEqual(violations[0].context["day_of_week"], 5)  # Saturday = 5
        
    def test_time_window_constraint(self):
        """Test the TimeWindowConstraint"""
        # Create a business hours constraint
        constraint = TimeWindowConstraint(
            name="business_hours",
            start_time=time(9, 0),   # 9:00 AM
            end_time=time(17, 0),    # 5:00 PM
            weight=1000
        )
        
        # Create test assignments
        valid_assignment = {
            "name": "Class A",
            "date": datetime(2025, 3, 3),
            "period": 2,  # 10:00 AM
            "instructor": "Instructor 1"
        }
        
        invalid_assignment = {
            "name": "Class B",
            "date": datetime(2025, 3, 3),
            "period": 12,  # 8:00 PM
            "instructor": "Instructor 2"
        }
        
        # Test validation with a valid assignment
        violations = constraint.validate([valid_assignment], self.context)
        self.assertEqual(len(violations), 0)
        
        # Test validation with an invalid assignment
        violations = constraint.validate([invalid_assignment], self.context)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].severity, ConstraintSeverity.ERROR)
        
        # Test relaxation
        constraint.relaxation_level = 2
        violations = constraint.validate([invalid_assignment], self.context)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].severity, ConstraintSeverity.WARNING)
        
        # Verify relaxation information in the violation
        self.assertIn("relaxation", violations[0].context)
        self.assertEqual(violations[0].context["relaxation"]["current_level"], 2)
        self.assertEqual(violations[0].context["relaxation"]["max_level"], 3)
        

class MockSchedulerContext:
    """Mock scheduler context for testing"""
    
    def __init__(self):
        """Initialize the context"""
        self.request = MockScheduleRequest()
        self.model = MockModel()
        self.variables = []
        

class MockScheduleRequest:
    """Mock schedule request for testing"""
    
    def __init__(self):
        """Initialize the request"""
        self.classes = []
        self.instructorAvailability = []
        

class MockModel:
    """Mock model for testing"""
    
    def __init__(self):
        """Initialize the model"""
        pass
        
    def Add(self, constraint):
        """Add a constraint to the model"""
        return MockBooleanClause()
        
    def AddWeightedSumInRange(self, variables, weights, lower_bound, upper_bound):
        """Add a weighted sum constraint to the model"""
        pass
        

class MockBooleanClause:
    """Mock boolean clause for testing"""
    
    def __init__(self):
        """Initialize the clause"""
        pass
        
    def OnlyEnforceIf(self, variable):
        """Add a condition to the clause"""
        return self


if __name__ == "__main__":
    unittest.main()
