# Dependency Injection Usage Guide

This guide explains how to use the dependency injection system in the scheduler backend. The dependency injection system allows for more loosely coupled code, making it easier to test, extend, and maintain the codebase.

## Table of Contents

1. [Introduction](#introduction)
2. [Basic Usage](#basic-usage)
3. [Advanced Usage](#advanced-usage)
4. [Testing with Dependency Injection](#testing-with-dependency-injection)
5. [Best Practices](#best-practices)

## Introduction

Dependency injection is a design pattern that allows a class to receive its dependencies from external sources rather than creating them internally. This makes the code more modular, testable, and maintainable. The scheduler backend implements a simple but powerful dependency injection system through the `DependencyContainer` class.

The main components of the dependency injection system are:

- **DependencyContainer**: Central registry for services and their implementations
- **inject decorator**: Automatic dependency resolution for functions and methods
- **Container initialization**: Centralized configuration of dependencies

## Basic Usage

### Resolving Dependencies

The simplest way to use the dependency injection system is to resolve dependencies from the container:

```python
from app.scheduling.dependencies import get_container

# Get the container
container = get_container()

# Resolve a dependency
constraint_manager = container.resolve(ConstraintManager)

# Use the dependency
constraint_manager.add_constraint(my_constraint)
```

### Using the Inject Decorator

The `inject` decorator automatically resolves dependencies for function and method parameters:

```python
from app.scheduling.dependencies import inject
from app.scheduling.core import ConstraintManager

@inject
def create_schedule(request: ScheduleRequest, constraint_manager: ConstraintManager):
    # constraint_manager will be automatically injected
    constraint_manager.apply_all(context)
    # ...
```

## Advanced Usage

### Registering Services

You can register your own services with the container:

```python
from app.scheduling.dependencies import get_container

# Get the container
container = get_container()

# Register a service with a concrete implementation
container.register(MyServiceInterface, MyServiceImplementation)

# Register a singleton service
container.register(LoggingService, singleton=True)

# Register a named service when multiple implementations exist
container.register(SolverStrategy, ORToolsSolverStrategy, name="or_tools")
container.register(SolverStrategy, GeneticSolverStrategy, name="genetic")
```

### Registering Instances

You can also register existing instances:

```python
from app.scheduling.dependencies import get_container

# Get the container
container = get_container()

# Create and configure an instance
config = SolverConfig()
config.timeout_seconds = 120

# Register the instance
container.register_instance(SolverConfig, config)
```

## Testing with Dependency Injection

Dependency injection makes testing easier by allowing you to substitute real implementations with mocks or stubs:

```python
from unittest.mock import Mock
from app.scheduling.dependencies import get_container

def test_solver_adapter():
    # Get the container
    container = get_container()
    
    # Create a mock constraint manager
    mock_constraint_manager = Mock(spec=ConstraintManager)
    
    # Register the mock with the container
    container.register_instance(ConstraintManager, mock_constraint_manager)
    
    # The system under test will now use the mock constraint manager
    solver_adapter = container.resolve(SolverStrategy, name="unified")
    
    # Test the adapter
    solver_adapter.solve(request, config)
    
    # Verify the mock was used correctly
    mock_constraint_manager.apply_all.assert_called_once()
```

## Best Practices

1. **Use constructor injection when possible**:
   ```python
   def __init__(self, constraint_manager: ConstraintManager):
       self._constraint_manager = constraint_manager
   ```

2. **Provide fallback mechanisms**:
   ```python
   def __init__(self, constraint_manager: Optional[ConstraintManager] = None):
       self._constraint_manager = constraint_manager or self._resolve_constraint_manager()
   
   def _resolve_constraint_manager(self):
       try:
           return get_container().resolve(ConstraintManager)
       except KeyError:
           return ConstraintManager()  # Fallback
   ```

3. **Keep the container initialization centralized**:
   Use the `container_init.py` module to register all dependencies in one place.

4. **Use meaningful names for registrations**:
   When registering multiple implementations of the same interface, use descriptive names.

5. **Avoid service locator pattern**:
   Prefer constructor injection over directly resolving from the container throughout your code.
