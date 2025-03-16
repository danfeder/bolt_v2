"""
Dependency Injection Module

This module provides a centralized container for managing and injecting dependencies
throughout the scheduling system. It decouples components from their dependencies,
making the system more testable, maintainable, and extensible.
"""

from typing import Dict, Any, Type, TypeVar, Generic, Optional, Callable, cast
import inspect
import logging
from functools import wraps

# Type variables for the container
T = TypeVar('T')
TService = TypeVar('TService')
TImplementation = TypeVar('TImplementation', bound=TService)

logger = logging.getLogger(__name__)


class DependencyContainer:
    """
    Container for managing dependencies and their lifetime
    
    This class provides a simple dependency injection container that supports
    registering and resolving dependencies with different lifetimes.
    """
    
    def __init__(self):
        """Initialize the container"""
        self._services: Dict[Type, Dict[str, Any]] = {}
        self._instances: Dict[Type, Dict[str, Any]] = {}
        
    def register(
        self,
        service_type: Type[TService],
        implementation_type: Optional[Type[TImplementation]] = None,
        *,
        singleton: bool = True,
        name: str = "default"
    ) -> None:
        """
        Register a service with the container
        
        Args:
            service_type: The service type (usually an interface or abstract class)
            implementation_type: The concrete implementation type (optional if same as service_type)
            singleton: Whether the service should have a singleton lifetime
            name: Optional name for the registration when multiple implementations exist
        """
        if implementation_type is None:
            implementation_type = service_type
            
        if service_type not in self._services:
            self._services[service_type] = {}
            
        self._services[service_type][name] = {
            "type": implementation_type,
            "singleton": singleton
        }
        
        logger.debug(f"Registered {implementation_type.__name__} for {service_type.__name__} (name={name}, singleton={singleton})")
    
    def register_instance(
        self,
        service_type: Type[TService],
        instance: TService,
        name: str = "default"
    ) -> None:
        """
        Register an existing instance with the container
        
        Args:
            service_type: The service type
            instance: The service instance
            name: Optional name for the registration when multiple implementations exist
        """
        if service_type not in self._instances:
            self._instances[service_type] = {}
            
        self._instances[service_type][name] = instance
        
        logger.debug(f"Registered instance of {type(instance).__name__} for {service_type.__name__} (name={name})")
    
    def resolve(
        self,
        service_type: Type[TService],
        name: str = "default",
        **kwargs
    ) -> TService:
        """
        Resolve a service from the container
        
        Args:
            service_type: The service type to resolve
            name: The registration name
            **kwargs: Additional arguments to pass to the constructor
            
        Returns:
            An instance of the service
            
        Raises:
            KeyError: If the service type or name is not registered
            ValueError: If constructor arguments cannot be resolved
        """
        # Check if an instance already exists for singleton services
        if service_type in self._instances and name in self._instances[service_type]:
            return self._instances[service_type][name]
        
        # Check if the service type is registered with enhanced error reporting
        if service_type not in self._services or name not in self._services[service_type]:
            # Create a list of available services for better diagnostics
            available_services = []
            for svc_type, registrations in self._services.items():
                for reg_name in registrations:
                    available_services.append(f"{svc_type.__name__} (name: '{reg_name}')")
            
            available_msg = "\nAvailable services:\n - " + "\n - ".join(available_services) if available_services else "No services registered"
            
            # Provide more helpful error message with available services list
            raise KeyError(f"Service {service_type.__name__} with name '{name}' is not registered. {available_msg}")
        
        # Get the registration
        registration = self._services[service_type][name]
        implementation_type = registration["type"]
        singleton = registration["singleton"]
        
        # Create the instance using constructor injection with enhanced error handling
        try:
            instance = self._create_instance(implementation_type, **kwargs)
        except Exception as e:
            # Add more detailed error information
            import traceback
            error_details = traceback.format_exc()
            
            # Log detailed error information
            logger.error(f"Error creating instance of {implementation_type.__name__}: {e}")
            logger.debug(f"Error details: {error_details}")
            
            # Get registration info for better context
            reg_info = "\nRegistration information:\n"
            reg_info += f" - Service: {service_type.__name__}\n"
            reg_info += f" - Implementation: {implementation_type.__name__}\n"
            reg_info += f" - Singleton: {singleton}\n"
            reg_info += f" - Name: {name}"
            
            raise ValueError(f"Failed to create instance of {implementation_type.__name__}: {e}\n{reg_info}")
        
        # Store the instance for singleton services
        if singleton:
            if service_type not in self._instances:
                self._instances[service_type] = {}
                
            self._instances[service_type][name] = instance
        
        return instance
    
    def _create_instance(self, implementation_type: Type[T], **explicit_kwargs) -> T:
        """
        Create an instance of a type, injecting dependencies as needed
        
        Args:
            implementation_type: The type to instantiate
            **explicit_kwargs: Explicit arguments to pass to the constructor
            
        Returns:
            An instance of the type
        """
        # Get the constructor signature
        sig = inspect.signature(implementation_type.__init__)
        
        # Prepare the arguments
        kwargs = {}
        missing_params = []
        unresolvable_params = []
        
        for param_name, param in sig.parameters.items():
            # Skip self
            if param_name == "self":
                continue
                
            # Use explicit arguments if provided
            if param_name in explicit_kwargs:
                kwargs[param_name] = explicit_kwargs[param_name]
                logger.debug(f"Using explicitly provided '{param_name}' for {implementation_type.__name__}")
                continue
                
            # Try to inject the dependency if it has a type annotation
            if param.annotation != inspect.Parameter.empty and param.annotation != Any:
                try:
                    # Resolve the dependency recursively
                    dependency_type = param.annotation
                    kwargs[param_name] = self.resolve(dependency_type)
                    logger.debug(f"Successfully injected dependency '{param_name}' of type {dependency_type.__name__} for {implementation_type.__name__}")
                except KeyError:
                    # If the dependency is not registered and has a default value, use it
                    if param.default != inspect.Parameter.empty:
                        kwargs[param_name] = param.default
                        logger.debug(f"Using default value for '{param_name}' in {implementation_type.__name__}")
                    # Otherwise, if it's not required, skip it
                    elif param.kind == inspect.Parameter.KEYWORD_ONLY:
                        logger.debug(f"Skipping optional keyword parameter '{param_name}' in {implementation_type.__name__}")
                        continue
                    # Otherwise, record the error for detailed diagnostics
                    else:
                        param_type_name = getattr(param.annotation, '__name__', str(param.annotation))
                        error_msg = f"Cannot resolve parameter '{param_name}' of type {param_type_name} for constructor of {implementation_type.__name__}"
                        logger.error(error_msg)
                        unresolvable_params.append(f"{param_name}: {param_type_name}")
            # If no type annotation but has a default value, use it
            elif param.default != inspect.Parameter.empty:
                kwargs[param_name] = param.default
                logger.debug(f"Using default value for non-annotated parameter '{param_name}' in {implementation_type.__name__}")
            # If it's a keyword-only parameter, it's optional
            elif param.kind == inspect.Parameter.KEYWORD_ONLY:
                logger.debug(f"Skipping optional non-annotated keyword parameter '{param_name}' in {implementation_type.__name__}")
                continue
            # Otherwise, we can't resolve it - record the error
            else:
                error_msg = f"Cannot resolve parameter '{param_name}' with no type annotation for constructor of {implementation_type.__name__}"
                logger.error(error_msg)
                missing_params.append(param_name)
        
        # Report any missing or unresolvable parameters
        if missing_params or unresolvable_params:
            error_msg = f"Cannot create instance of {implementation_type.__name__} due to dependency resolution issues:\n"
            if missing_params:
                error_msg += f"- Missing type annotations: {', '.join(missing_params)}\n"
            if unresolvable_params:
                error_msg += f"- Unresolvable dependencies: {', '.join(unresolvable_params)}"
            
            # Also log currently registered services for diagnostic purposes
            available_services = []
            for svc_type, registrations in self._services.items():
                for reg_name in registrations:
                    available_services.append(f"{svc_type.__name__} (name: '{reg_name}')")
            
            logger.debug(f"Available services when resolving {implementation_type.__name__}:\n - {', '.join(available_services)}")
            raise ValueError(error_msg)
        
        # Create the instance
        return implementation_type(**kwargs)
    
    def clear(self) -> None:
        """Clear all registrations and instances"""
        self._services.clear()
        self._instances.clear()


# Global container instance
_container = DependencyContainer()

def get_container() -> DependencyContainer:
    """Get the global dependency container"""
    return _container


def inject(func):
    """
    Decorator for automatically injecting dependencies
    
    This decorator inspects the function's parameters and injects
    dependencies from the container as needed.
    
    Example:
    ```python
    @inject
    def process_data(data_processor: DataProcessor, logger: Logger):
        # data_processor and logger will be automatically injected
        pass
    ```
    """
    sig = inspect.signature(func)
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        container = get_container()
        final_kwargs = {}
        
        # Determine which parameters need injection
        params = list(sig.parameters.values())
        
        # Adjust for instance methods (skip self/cls)
        offset = 0
        if inspect.ismethod(func) or (args and inspect.isclass(args[0])):
            offset = 1
        
        # Process positional arguments
        for i, arg in enumerate(args[offset:], offset):
            if i < len(params):
                final_kwargs[params[i].name] = arg
        
        # Process keyword arguments
        final_kwargs.update(kwargs)
        
        # Inject missing dependencies
        for param in params[offset if offset > 0 else 0:]:
            if param.name not in final_kwargs and param.annotation != inspect.Parameter.empty:
                try:
                    final_kwargs[param.name] = container.resolve(param.annotation)
                except KeyError:
                    # If the dependency is not registered and has a default value, use it
                    if param.default != inspect.Parameter.empty:
                        final_kwargs[param.name] = param.default
                    # Otherwise, if it's not required, skip it
                    elif param.kind == inspect.Parameter.KEYWORD_ONLY:
                        continue
                    # Otherwise, skip it and let Python raise the error
                    else:
                        continue
        
        return func(**final_kwargs)
    
    return wrapper
