"""
Test Service Factory

This module contains tests for the service factory and base service classes.
"""

import pytest
from typing import Dict, Any, Optional

from app.services.base_service import BaseService
from app.services.service_factory import ServiceFactory, get_service_factory
from app.services.scheduler_service import SchedulerService


class MockService(BaseService):
    """Mock service for testing."""
    
    def __init__(self, **kwargs):
        """Initialize the mock service."""
        super().__init__(**kwargs)
        self.init_called = True
        
    def get_test_value(self) -> str:
        """Get a test value."""
        return "test_value"
    
    def get_dependency(self, name: str) -> Optional[Any]:
        """Get a dependency by name for testing."""
        return self._get_dependency(name)


class TestBaseService:
    """Tests for the BaseService class."""
    
    def test_init(self):
        """Test initialization of the base service."""
        # Create a service with dependencies
        service = MockService(test_dep="test_value", another_dep=123)
        
        # Check that initialization was successful
        assert hasattr(service, "init_called")
        assert service.init_called
        
        # Check dependency access
        assert service.get_dependency("test_dep") == "test_value"
        assert service.get_dependency("another_dep") == 123
        assert service.get_dependency("non_existent") is None
        assert service.get_dependency("non_existent", "default") == "default"


class TestServiceFactory:
    """Tests for the ServiceFactory class."""
    
    def test_create_service(self):
        """Test creating a service instance."""
        # Create a factory
        factory = ServiceFactory()
        
        # Register our mock service
        factory._service_types["mock"] = MockService
        
        # Create a service
        service = factory.create_service("mock", test_dep="factory_test")
        
        # Check that the service was created correctly
        assert isinstance(service, MockService)
        assert service.get_dependency("test_dep") == "factory_test"
    
    def test_get_service(self):
        """Test getting a service instance."""
        # Create a factory
        factory = ServiceFactory()
        
        # Register our mock service
        factory._service_types["mock"] = MockService
        
        # Get a service
        service1 = factory.get_service("mock", test_dep="singleton_test")
        
        # Get the same service again
        service2 = factory.get_service("mock")
        
        # Check that they are the same instance
        assert service1 is service2
        assert service1.get_dependency("test_dep") == "singleton_test"
    
    def test_get_typed_service(self):
        """Test getting a typed service instance."""
        # Create a factory
        factory = ServiceFactory()
        
        # Register our mock service
        factory._service_types["mock"] = MockService
        
        # Get a typed service
        service = factory.get_typed_service("mock", MockService, test_dep="typed_test")
        
        # Check that the service has the correct type
        assert isinstance(service, MockService)
        assert service.get_dependency("test_dep") == "typed_test"
        
        # Check that type checking works
        with pytest.raises(ValueError):
            factory.get_typed_service("scheduler", MockService)
    
    def test_create_scheduler_service(self):
        """Test creating a scheduler service."""
        # Create a factory
        factory = ServiceFactory()
        
        # Create a scheduler service
        service = factory.create_scheduler_service(test_dep="scheduler_test")
        
        # Check that the service was created correctly
        assert isinstance(service, SchedulerService)
        
    def test_get_scheduler_service(self):
        """Test getting the scheduler service singleton."""
        # Create a factory
        factory = ServiceFactory()
        
        # Get the scheduler service
        service1 = factory.get_scheduler_service(test_dep="scheduler_singleton")
        
        # Get it again
        service2 = factory.get_scheduler_service()
        
        # Check that they are the same instance
        assert service1 is service2
        assert isinstance(service1, SchedulerService)
    
    def test_get_service_factory(self):
        """Test getting the service factory singleton."""
        # Get the factory
        factory1 = get_service_factory()
        
        # Get it again
        factory2 = get_service_factory()
        
        # Check that they are the same instance
        assert factory1 is factory2
        assert isinstance(factory1, ServiceFactory)
