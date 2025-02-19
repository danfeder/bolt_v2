import pytest
from datetime import datetime, timedelta

from app.scheduling.constraints.assignment import SingleAssignmentConstraint, NoOverlapConstraint
from app.scheduling.constraints.instructor import (
    InstructorAvailabilityConstraint, ConsecutivePeriodConstraint, InstructorLoadConstraint
)
from app.scheduling.constraints.limits import DailyLimitConstraint, WeeklyLimitConstraint, MinimumPeriodsConstraint
from app.scheduling.constraints.periods import RequiredPeriodsConstraint, ConflictPeriodsConstraint
from tests.utils.constraint_harness import create_test_harness
from app.models import ScheduleRequest, Class, TimeSlot

class TestAssignmentConstraints:
    """Tests for assignment-related constraints"""
    
    def test_single_assignment_success(self):
        """Test that each class is scheduled exactly once when constraint is applied"""
        harness = create_test_harness()
        context = harness.create_context(num_classes=3, num_weeks=1)
        
        constraint = SingleAssignmentConstraint()
        harness.apply_constraint(constraint, context)
        
        assert harness.solve(), "Failed to find feasible solution"
        
        assignments = harness.get_solution_assignments(context)
        violations = harness.validate_constraint(constraint, context)
        
        # Check each class appears exactly once
        class_counts = {}
        for assignment in assignments:
            class_name = assignment["name"]
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
            
        for class_name, count in class_counts.items():
            assert count == 1, f"Class {class_name} was scheduled {count} times instead of once"
        
        assert len(violations) == 0, f"Found unexpected violations: {violations}"
        
    def test_single_assignment_violation(self):
        """Test that violations are detected when classes are scheduled multiple times"""
        harness = create_test_harness()
        context = harness.create_context(num_classes=2, num_weeks=1)
        
        # Don't apply the constraint - this should allow multiple assignments
        constraint = SingleAssignmentConstraint()
        harness.apply_constraint(constraint, context, enabled=False)
        
        assert harness.solve(), "Failed to find feasible solution"
        
        assignments = harness.get_solution_assignments(context)
        violations = harness.validate_constraint(constraint, context)
        
        assert len(violations) > 0, "Expected violations when constraint not applied"
        assert any(v.severity == "error" for v in violations), "Expected at least one error severity violation"
        
    def test_no_overlap_success(self):
        """Test that no two classes are scheduled in the same time slot"""
        harness = create_test_harness()
        context = harness.create_context(num_classes=3, num_weeks=1)
        
        constraint = NoOverlapConstraint()
        harness.apply_constraint(constraint, context)
        
        assert harness.solve(), "Failed to find feasible solution"
        
        assignments = harness.get_solution_assignments(context)
        violations = harness.validate_constraint(constraint, context)
        
        assert len(violations) == 0, f"Found unexpected violations: {violations}"
        
    def test_no_overlap_violation(self):
        """Test that violations are detected when classes overlap"""
        harness = create_test_harness()
        context = harness.create_context(num_classes=2, num_weeks=1)
        
        # Don't apply the constraint - this should allow overlaps
        constraint = NoOverlapConstraint()
        harness.apply_constraint(constraint, context, enabled=False)
        
        assert harness.solve(), "Failed to find feasible solution"
        
        assignments = harness.get_solution_assignments(context)
        violations = harness.validate_constraint(constraint, context)
        
        assert len(violations) > 0, "Expected violations when constraint not applied"

class TestInstructorConstraints:
    """Tests for instructor-related constraints"""
    
    def test_instructor_availability_success(self):
        """Test that classes are only scheduled during instructor availability"""
        harness = create_test_harness()
        context = harness.create_context(num_classes=2, num_weeks=1)
        
        constraint = InstructorAvailabilityConstraint()
        harness.apply_constraint(constraint, context)
        
        assert harness.solve(), "Failed to find feasible solution"
        
        assignments = harness.get_solution_assignments(context)
        violations = harness.validate_constraint(constraint, context)
        
        assert len(violations) == 0, f"Found unexpected violations: {violations}"
        
    def test_instructor_availability_violation(self):
        """Test that violations are detected when classes are scheduled outside availability"""
        harness = create_test_harness()
        context = harness.create_context(num_classes=1, num_weeks=1)
        
        # Don't apply the constraint
        constraint = InstructorAvailabilityConstraint()
        harness.apply_constraint(constraint, context, enabled=False)
        
        assert harness.solve(), "Failed to find feasible solution"
        
        assignments = harness.get_solution_assignments(context)
        violations = harness.validate_constraint(constraint, context)
        
        assert len(violations) > 0, "Expected violations when constraint not applied"
        
    def test_consecutive_period_success(self):
        """Test that instructors are not scheduled for consecutive periods"""
        harness = create_test_harness()
        context = harness.create_context(num_classes=3, num_weeks=1)
        
        constraint = ConsecutivePeriodConstraint()
        harness.apply_constraint(constraint, context)
        
        assert harness.solve(), "Failed to find feasible solution"
        
        assignments = harness.get_solution_assignments(context)
        violations = harness.validate_constraint(constraint, context)
        
        assert len(violations) == 0, f"Found unexpected violations: {violations}"
        
    def test_consecutive_period_violation(self):
        """Test that violations are detected when instructors have consecutive periods"""
        harness = create_test_harness()
        context = harness.create_context(num_classes=2, num_weeks=1)
        
        # Don't apply the constraint
        constraint = ConsecutivePeriodConstraint()
        harness.apply_constraint(constraint, context, enabled=False)
        
        assert harness.solve(), "Failed to find feasible solution"
        
        assignments = harness.get_solution_assignments(context)
        violations = harness.validate_constraint(constraint, context)
        
        assert len(violations) > 0, "Expected violations when constraint not applied"

    def test_instructor_load_success(self):
        """Test that instructors do not exceed maximum classes per day/week"""
        harness = create_test_harness()
        context = harness.create_context(num_classes=5, num_weeks=1)
        
        constraint = InstructorLoadConstraint(max_classes_per_day=3, max_classes_per_week=12)
        harness.apply_constraint(constraint, context)
        
        assert harness.solve(), "Failed to find feasible solution"
        
        assignments = harness.get_solution_assignments(context)
        violations = harness.validate_constraint(constraint, context)
        
        assert len(violations) == 0, f"Found unexpected violations: {violations}"
        
    def test_instructor_load_violation(self):
        """Test that violations are detected when instructor load limits are exceeded"""
        harness = create_test_harness()
        context = harness.create_context(num_classes=10, num_weeks=1)
        
        # Don't apply the constraint - this should allow exceeding the limits
        constraint = InstructorLoadConstraint(max_classes_per_day=2, max_classes_per_week=8)
        harness.apply_constraint(constraint, context, enabled=False)
        
        assert harness.solve(), "Failed to find feasible solution"
        
        assignments = harness.get_solution_assignments(context)
        violations = harness.validate_constraint(constraint, context)
        
        assert len(violations) > 0, "Expected violations when constraint not applied"

class TestDailyLimitConstraint:
    """Tests for daily limit constraints"""
    
    def test_daily_limit_success(self):
        """Test that class scheduling respects daily limits"""
        harness = create_test_harness()
        context = harness.create_context(num_classes=5, num_weeks=1)
        
        constraint = DailyLimitConstraint()
        harness.apply_constraint(constraint, context)
        
        assert harness.solve(), "Failed to find feasible solution"
        
        assignments = harness.get_solution_assignments(context)
        violations = harness.validate_constraint(constraint, context)
        
        assert len(violations) == 0, f"Found unexpected violations: {violations}"
        
    def test_daily_limit_violation(self):
        """Test that violations are detected when daily limits are exceeded"""
        harness = create_test_harness()
        context = harness.create_context(num_classes=10, num_weeks=1)
        
        # Don't apply the constraint
        constraint = DailyLimitConstraint()
        harness.apply_constraint(constraint, context, enabled=False)
        
        assert harness.solve(), "Failed to find feasible solution"
        
        assignments = harness.get_solution_assignments(context)
        violations = harness.validate_constraint(constraint, context)
        
        assert len(violations) > 0, "Expected violations when constraint not applied"

class TestWeeklyLimitConstraint:
    """Tests for weekly limit constraints"""
    
    def test_weekly_limit_success(self):
        """Test that class scheduling respects weekly limits"""
        harness = create_test_harness()
        context = harness.create_context(num_classes=5, num_weeks=1)
        
        constraint = WeeklyLimitConstraint()
        harness.apply_constraint(constraint, context)
        
        assert harness.solve(), "Failed to find feasible solution"
        
        assignments = harness.get_solution_assignments(context)
        violations = harness.validate_constraint(constraint, context)
        
        assert len(violations) == 0, f"Found unexpected violations: {violations}"
        
    def test_weekly_limit_violation(self):
        """Test that violations are detected when weekly limits are exceeded"""
        harness = create_test_harness()
        context = harness.create_context(num_classes=10, num_weeks=1)
        
        # Don't apply the constraint
        constraint = WeeklyLimitConstraint()
        harness.apply_constraint(constraint, context, enabled=False)
        
        assert harness.solve(), "Failed to find feasible solution"
        
        assignments = harness.get_solution_assignments(context)
        violations = harness.validate_constraint(constraint, context)
        
        assert len(violations) > 0, "Expected violations when constraint not applied"

class TestMinimumPeriodsConstraint:
    """Tests for minimum periods constraints"""
    
    def test_minimum_periods_single_day(self):
        """Test that minimum periods constraint properly enforces minimums with limited schedule"""
        harness = create_test_harness()
        context = harness.create_context(num_classes=1, num_weeks=1)
        
        # Set a base minimum of 5 periods per week
        context.request.constraints.minPeriodsPerWeek = 5
        
        # Should require at least 2 periods even with one day (threshold rule)
        constraint = MinimumPeriodsConstraint()
        harness.apply_constraint(constraint, context, enabled=False)  # Force under-assignment
        
        assert harness.solve(), "Failed to find feasible solution"
        
        assignments = harness.get_solution_assignments(context)
        violations = harness.validate_constraint(constraint, context)
        
        assert len(violations) > 0, "Expected violation with single assignment"
        assert any(v.severity == "error" for v in violations), "Expected error severity violation"
        assert len(assignments) == 1, "Expected exactly one assignment"

    def test_minimum_periods_success(self):
        """Test that class scheduling respects minimum periods requirement"""
        harness = create_test_harness()
        context = harness.create_context(num_classes=5, num_weeks=1)
        
        constraint = MinimumPeriodsConstraint()
        harness.apply_constraint(constraint, context)
        
        assert harness.solve(), "Failed to find feasible solution"
        
        assignments = harness.get_solution_assignments(context)
        violations = harness.validate_constraint(constraint, context)
        
        assert len(violations) == 0, f"Found unexpected violations: {violations}"
        
    def test_minimum_periods_violation(self):
        """Test that violations are detected when minimum periods are not met"""
        harness = create_test_harness()
        context = harness.create_context(num_classes=1, num_weeks=1)
        
        # Don't apply the constraint
        constraint = MinimumPeriodsConstraint()
        harness.apply_constraint(constraint, context, enabled=False)
        
        assert harness.solve(), "Failed to find feasible solution"
        
        assignments = harness.get_solution_assignments(context)
        violations = harness.validate_constraint(constraint, context)
        
        assert len(violations) > 0, "Expected violations when constraint not applied"

class TestPeriodsConstraints:
    """Tests for period-related constraints"""
    
    def test_required_periods_multiple(self):
        """Test that violations are detected when multiple required periods are not met"""
        harness = create_test_harness()
        context = harness.create_context(num_classes=1, num_weeks=1)
        
        # Don't apply constraint to allow forced violations
        constraint = RequiredPeriodsConstraint()
        harness.apply_constraint(constraint, context, enabled=False)
        
        assert harness.solve(), "Failed to find feasible solution"
        
        assignments = harness.get_solution_assignments(context)
        violations = harness.validate_constraint(constraint, context)
        
        # Should have generated required periods for both Monday and Tuesday
        assert len(violations) == 2, "Expected violations for both required periods"
        # Should have one assignment in a non-required period
        assert len(assignments) == 1, "Expected one assignment in a non-required period"
        # Verify assignment is in period 8 (our forced non-required period)
        assert all(a["timeSlot"]["period"] == 8 for a in assignments), "Assignment should be in period 8"
    
    def test_required_periods_success(self):
        """Test that classes are scheduled in required periods"""
        harness = create_test_harness()
        context = harness.create_context(num_classes=2, num_weeks=1)
        
        constraint = RequiredPeriodsConstraint()
        harness.apply_constraint(constraint, context)
        
        assert harness.solve(), "Failed to find feasible solution"
        
        assignments = harness.get_solution_assignments(context)
        violations = harness.validate_constraint(constraint, context)
        
        assert len(violations) == 0, f"Found unexpected violations: {violations}"
        
    def test_required_periods_violation(self):
        """Test that violations are detected when required periods are not met"""
        harness = create_test_harness()
        context = harness.create_context(num_classes=1, num_weeks=1)
        
        # Don't apply the constraint
        constraint = RequiredPeriodsConstraint()
        harness.apply_constraint(constraint, context, enabled=False)
        
        assert harness.solve(), "Failed to find feasible solution"
        
        assignments = harness.get_solution_assignments(context)
        violations = harness.validate_constraint(constraint, context)
        
        assert len(violations) > 0, "Expected violations when constraint not applied"
        
    def test_conflict_periods_success(self):
        """Test that classes are not scheduled in conflicting periods"""
        harness = create_test_harness()
        context = harness.create_context(num_classes=2, num_weeks=1)
        
        constraint = ConflictPeriodsConstraint()
        harness.apply_constraint(constraint, context)
        
        assert harness.solve(), "Failed to find feasible solution"
        
        assignments = harness.get_solution_assignments(context)
        violations = harness.validate_constraint(constraint, context)
        
        assert len(violations) == 0, f"Found unexpected violations: {violations}"
        
    def test_conflict_periods_violation(self):
        """Test that violations are detected when classes are scheduled in conflicting periods"""
        harness = create_test_harness()
        context = harness.create_context(num_classes=1, num_weeks=1)
        
        # Don't apply the constraint
        constraint = ConflictPeriodsConstraint()
        harness.apply_constraint(constraint, context, enabled=False)
        
        assert harness.solve(), "Failed to find feasible solution"
        
        assignments = harness.get_solution_assignments(context)
        violations = harness.validate_constraint(constraint, context)
        
        assert len(violations) == 1, "Expected exactly one conflict violation"
        # Should have both a conflict assignment and non-conflict assignment
        assert len(assignments) == 2, "Expected two assignments (conflict and non-conflict)"
        
        # Verify periods used
        periods = [a["timeSlot"]["period"] for a in assignments]
        assert 1 in periods, "Should have assignment in conflict period (1)"
        assert any(p > 1 for p in periods), "Should have assignment in non-conflict period"
