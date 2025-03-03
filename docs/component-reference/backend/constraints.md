# Constraint System

## Overview

The constraint system in the Gym Class Rotation Scheduler project is responsible for defining and enforcing scheduling rules. It has been enhanced to provide better organization, validation, and extensibility.

## Key Features

### Auto-Registration of Constraints

The constraint system supports automatic discovery and registration of constraints, making it easier to add new constraints without manual registration.

```python
# Register all default constraints
from app.scheduling.abstractions.constraint_factory import register_default_constraints
register_default_constraints()
```

The `register_default_constraints` method:
- Scans the constraints directory for constraint classes
- Extracts metadata from constraint docstrings and class attributes
- Registers each constraint with appropriate metadata
- Sets up compatibility relationships between constraints

### Constraint Categories

Constraints are organized into categories for better management and filtering:

```python
# Get constraints by category
schedule_constraints = factory.get_constraint_names_by_category("schedule")
instructor_constraints = factory.get_constraint_names_by_category("instructor")

# Get all available categories
all_categories = factory.get_all_categories()
```

Categories help to organize constraints by their purpose or domain:
- **schedule**: Constraints related to date, time, and scheduling patterns
- **instructor**: Constraints related to instructor assignments and availability
- **class**: Constraints related to class assignments and requirements
- **general**: Default category for constraints that don't fit into a specific category

### Constraint Compatibility Validation

The system supports defining compatibility relationships between constraints:

```python
# Set incompatible constraints
factory.set_incompatible_constraints("constraint_a", ["constraint_b", "constraint_c"])

# Set required dependencies
factory.set_required_constraints("constraint_x", ["constraint_y"])

# Validate compatibility
errors = factory.validate_constraints_compatibility(enabled_constraint_names)
if errors:
    for error in errors:
        print(f"Compatibility error: {error}")
```

This enables:
- Preventing incompatible constraints from being enabled simultaneously
- Ensuring dependent constraints are enabled when required
- Validating constraint configurations before running the solver

### Enhanced Validation and Contextual Error Reporting

Constraints provide richer validation information including:
- Multiple severity levels (INFO, WARNING, ERROR, CRITICAL)
- Detailed contextual information about violations
- Standardized violation reporting formats

```python
# BaseConstraint methods for creating violations
constraint.create_info_violation("Informational message")
constraint.create_warning_violation("Warning message")
constraint.create_error_violation("Error message")
constraint.create_critical_violation("Critical error message")
```

Violations include context information:
```python
violation = constraint.create_error_violation(
    "Assignment violates constraint",
    context={
        "assignment": assignment_details,
        "additional_info": {...}
    }
)
```

### Relaxable Constraints

The system includes enhanced support for relaxable constraints:
- Constraints can be gradually relaxed when a solution is difficult to find
- Relaxation levels can be adjusted with fine-grained control
- Violations include relaxation information in the context

```python
# Adjust the relaxation level
constraint.relaxation_level = 2

# Get the relaxed weight based on the current relaxation level
relaxed_weight = constraint.get_relaxed_weight()

# Create a violation with relaxation information
violation = constraint.create_relaxable_violation(
    "Constraint partially relaxed",
    severity=ConstraintSeverity.WARNING
)
```

## Architecture and Integration

### Key Classes

1. **ConstraintFactory**
   - Manages constraint registration and creation
   - Handles constraint metadata and compatibility relationships
   - Provides methods for retrieving constraints by category or name

2. **EnhancedConstraintManager**
   - Manages a collection of constraints
   - Provides methods for validation and applying constraints
   - Supports filtering by category and other criteria

3. **BaseConstraint**
   - Base class for all constraints
   - Provides common methods for validation and violation reporting
   - Implements category support and other metadata

4. **BaseRelaxableConstraint**
   - Extends BaseConstraint for constraints that can be relaxed
   - Manages relaxation levels and weights
   - Provides methods for relaxable violation reporting

### Integration with Solver

The enhanced constraint system integrates with the solver through the scheduler context:

```python
# Create a scheduler context
context = SchedulerContext(...)

# Get the constraint manager
manager = context.get_constraint_manager()

# Add constraints by category
manager.create_and_add_constraints_by_category("schedule")
manager.create_and_add_constraints_by_category("instructor")

# Apply constraints to the solver model
manager.apply_all(context)

# Validate the solution
is_valid, violations = manager.validate_all(solution, context)
```

## Creating Custom Constraints

Creating a custom constraint is straightforward:

```python
from app.scheduling.abstractions.base_constraint import BaseConstraint

class MyCustomConstraint(BaseConstraint):
    """
    My custom constraint that enforces a specific rule
    
    This constraint ensures that [description of what it does]
    """
    
    def __init__(self, name="my_custom_constraint", enabled=True):
        super().__init__(name, enabled)
        self.category = "custom"  # Set the category
        
    def apply(self, context):
        # Apply the constraint to the solver model
        if not self.enabled:
            return
            
        # Implementation of constraint logic
        for var in context.variables:
            if some_condition:
                context.model.Add(var["variable"] == 0)
        
    def validate(self, assignments, context):
        # Validate assignments against this constraint
        if not self.enabled:
            return []
            
        violations = []
        for assignment in assignments:
            if violates_constraint(assignment):
                violations.append(
                    self.create_error_violation(
                        "Detailed error message",
                        context=self.format_violation_context(
                            assignment,
                            {"additional_info": "value"}
                        )
                    )
                )
        return violations
```

## Examples

The system includes example constraints that demonstrate the enhanced features:

### Day of Week Constraint

```python
from app.scheduling.constraints.examples import DayOfWeekConstraint

# Create a constraint that only allows weekdays
constraint = DayOfWeekConstraint(
    name="weekday_only",
    allowed_days=[0, 1, 2, 3, 4]  # Monday to Friday
)

# Validate assignments
violations = constraint.validate(assignments, context)
```

### Time Window Constraint (Relaxable)

```python
from app.scheduling.constraints.examples import TimeWindowConstraint
from datetime import time

# Create a constraint for business hours
constraint = TimeWindowConstraint(
    name="business_hours",
    start_time=time(9, 0),   # 9:00 AM
    end_time=time(17, 0),    # 5:00 PM
    weight=1000,             # Soft constraint
    max_relaxation_level=3
)

# Set relaxation level
constraint.relaxation_level = 1  # Slightly relaxed
```

## Best Practices

1. **Organize constraints into meaningful categories**
   - Use the category system to organize constraints logically
   - Stick to consistent category names throughout the codebase

2. **Define compatibility relationships**
   - Identify constraints that should not be used together
   - Specify dependencies between constraints

3. **Provide detailed violation information**
   - Use the appropriate severity level for violations
   - Include contextual information to help diagnose issues

4. **Use relaxable constraints appropriately**
   - Make constraints relaxable when they could be bent in extreme cases
   - Set reasonable relaxation levels and weights

5. **Document constraints thoroughly**
   - Add detailed docstrings explaining the purpose of the constraint
   - Document any non-obvious behaviors or edge cases

## Testing

The constraint system includes comprehensive unit tests:

```bash
# Run the constraint system tests
python -m pytest -xvs tests/unit/test_constraint_system.py
```

These tests demonstrate:
- Registering and creating constraints
- Working with constraint categories
- Validating constraint compatibility
- Creating and validating example constraints

## Conclusion

The enhanced constraint system provides a robust and flexible framework for defining and enforcing scheduling rules. By leveraging these enhancements, the Gym Class Rotation Scheduler can handle complex scheduling requirements with improved organization, validation, and extensibility.
