"""
Service Factory

This module provides a factory for creating service instances with proper dependency injection.
It ensures that services are created consistently and with the correct dependencies.
"""

import logging
from typing import Dict, Any, Type, Optional, TypeVar, Generic, cast
from ..repositories.repository_factory import RepositoryFactory

from .base_service import BaseService
from .scheduler_service import SchedulerService

# Set up type variables for better type hinting
T = TypeVar('T', bound=BaseService)
ServiceType = Type[T]

# Set up logger
logger = logging.getLogger(__name__)


class ServiceFactory:
    """
    Factory for creating and managing service instances.
    
    This factory provides methods for creating services with proper dependency injection
    and manages singleton instances of services when appropriate.
    """
    
    def __init__(self):
        """Initialize the service factory."""
        self._services: Dict[str, BaseService] = {}
        self._service_types: Dict[str, Type[BaseService]] = {
            'scheduler': SchedulerService,
            # Add more services here as they are created
        }
        logger.debug("ServiceFactory initialized")
    
    def create_service(self, service_type: str, **kwargs) -> BaseService:
        """
        Create a new instance of the specified service type.
        
        Args:
            service_type: The type of service to create
            **kwargs: Dependencies to inject into the service
            
        Returns:
            A new instance of the requested service
            
        Raises:
            ValueError: If the service type is not registered
        """
        if service_type not in self._service_types:
            raise ValueError(f"Unknown service type: {service_type}")
        
        service_class = self._service_types[service_type]
        return service_class(**kwargs)
    
    def get_service(self, service_type: str, **kwargs) -> BaseService:
        """
        Get an existing service instance or create a new one.
        
        This method returns a singleton instance of the requested service type,
        creating it if it doesn't already exist.
        
        Args:
            service_type: The type of service to get
            **kwargs: Dependencies to inject if creating a new instance
            
        Returns:
            The requested service instance
            
        Raises:
            ValueError: If the service type is not registered
        """
        if service_type not in self._services:
            self._services[service_type] = self.create_service(service_type, **kwargs)
        
        return self._services[service_type]
    
    def get_typed_service(self, service_type: str, service_class: ServiceType, **kwargs) -> T:
        """
        Get a service instance with the correct type.
        
        This is a typed version of get_service that returns the service with the specified type.
        
        Args:
            service_type: The type of service to get
            service_class: The class of the service for type checking
            **kwargs: Dependencies to inject if creating a new instance
            
        Returns:
            The requested service instance with the correct type
            
        Raises:
            ValueError: If the service type is not registered or is not of the expected type
        """
        service = self.get_service(service_type, **kwargs)
        
        if not isinstance(service, service_class):
            raise ValueError(f"Service {service_type} is not an instance of {service_class.__name__}")
        
        return cast(T, service)
    
    def create_scheduler_service(self, **kwargs) -> SchedulerService:
        """
        Create a scheduler service with the specified dependencies.
        
        Args:
            **kwargs: Dependencies to inject
            
        Returns:
            A new SchedulerService instance
        """
        return cast(SchedulerService, self.create_service('scheduler', **kwargs))
    
    def get_scheduler_service(self, **kwargs) -> SchedulerService:
        """
        Get the scheduler service singleton instance.
        
        Args:
            **kwargs: Dependencies to inject if creating a new instance
            
        Returns:
            The SchedulerService singleton instance
        """
        if 'scheduler' not in self._services:
            schedule_repository = RepositoryFactory.get_schedule_repository()
            self._services['scheduler'] = SchedulerService(schedule_repository=schedule_repository)
        
        return self.get_typed_service('scheduler', SchedulerService, **kwargs)


# Create a singleton instance of the service factory
_factory_instance: Optional[ServiceFactory] = None


def get_service_factory() -> ServiceFactory:
    """
    Get the singleton instance of the service factory.
    
    Returns:
        The ServiceFactory singleton instance
    """
    global _factory_instance
    
    if _factory_instance is None:
        _factory_instance = ServiceFactory()
    
    return _factory_instance
