import pytest
from app.scheduling.constraints.assignment import SingleAssignmentConstraint
from tests.utils.constraint_harness import create_test_harness

def test_single_assignment_constraint_with_harness():
    """Test SingleAssignmentConstraint using the constraint test harness"""
    
    # Create test harness with 2 classes over 1 week
    harness = create_test_harness()
    context = harness.create_context(num_classes=2, num_weeks=1)
    
    # Create and apply the constraint
    constraint = SingleAssignmentConstraint()
    harness.apply_constraint(constraint, context)
    
    # Solve the model
    assert harness.solve(), "Failed to find feasible solution"
    
    # Get assignments and validate
    assignments = harness.get_solution_assignments(context)
    violations = harness.validate_constraint(constraint, context)
    
    # Verify each class is scheduled exactly once
    class_counts = {}
    for assignment in assignments:
        class_name = assignment["name"]
        class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
    for class_name, count in class_counts.items():
        assert count == 1, f"Class {class_name} was scheduled {count} times instead of once"
        
    # Verify no violations were found
    assert len(violations) == 0, f"Found constraint violations: {violations}"
    
    # Print solution for visibility
    print("\nTest Solution:")
    for assignment in sorted(assignments, key=lambda x: (x["date"], x["timeSlot"]["period"])):
        print(f"{assignment['name']}: {assignment['date'].date()} period {assignment['timeSlot']['period']}")

def test_single_assignment_constraint_violation_detection():
    """Test that the harness can detect constraint violations"""
    
    # Create test harness with just 1 class
    harness = create_test_harness()
    context = harness.create_context(num_classes=1, num_weeks=1)
    
    # Create but don't apply the constraint - this should lead to no assignments
    constraint = SingleAssignmentConstraint()
    
    # Solve the unconstrained model
    assert harness.solve(), "Failed to find feasible solution"
    
    # Get assignments and validate
    assignments = harness.get_solution_assignments(context)
    violations = harness.validate_constraint(constraint, context)
    
    # Without the constraint applied, we expect a violation
    assert len(violations) > 0, "Expected violations when constraint not applied"
    assert violations[0].severity == "error", "Expected error severity for violation"
    print(f"\nExpected Violation: {violations[0].message}")
