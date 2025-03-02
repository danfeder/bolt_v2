"""
Tests for the dependency injection system
"""
import pytest
from typing import Protocol, Optional

from app.scheduling.dependencies import DependencyContainer, inject


# Test classes
class TestService(Protocol):
    """Test service protocol"""
    def perform(self) -> str:
        """Perform the service operation"""
        ...


class TestServiceImpl(TestService):
    """Test service implementation"""
    def perform(self) -> str:
        """Perform the service operation"""
        return "TestServiceImpl.perform"


class TestServiceImpl2(TestService):
    """Test service implementation 2"""
    def perform(self) -> str:
        """Perform the service operation"""
        return "TestServiceImpl2.perform"


class TestDependentService:
    """Service that depends on TestService"""
    def __init__(self, service: TestService):
        self.service = service
    
    def use_dependency(self) -> str:
        """Use the dependency"""
        return f"Used dependency: {self.service.perform()}"


class TestLogger:
    """Simple logger for testing"""
    def __init__(self):
        self.logs = []
    
    def log(self, message: str) -> None:
        """Log a message"""
        self.logs.append(message)


# Decorator test function
@inject
def test_injected_function(service: TestService, logger: Optional[TestLogger] = None) -> str:
    """Test function with injected dependencies"""
    if logger:
        logger.log("test_injected_function called")
    return service.perform()


# Tests
class TestDependencyContainer:
    """Tests for the DependencyContainer class"""
    
    def test_register_and_resolve(self):
        """Test registering and resolving a service"""
        container = DependencyContainer()
        container.register(TestService, TestServiceImpl)
        
        service = container.resolve(TestService)
        
        assert isinstance(service, TestServiceImpl)
        assert service.perform() == "TestServiceImpl.perform"
    
    def test_register_instance(self):
        """Test registering an instance"""
        container = DependencyContainer()
        instance = TestServiceImpl()
        container.register_instance(TestService, instance)
        
        resolved = container.resolve(TestService)
        
        assert resolved is instance
    
    def test_singleton_scope(self):
        """Test singleton scope"""
        container = DependencyContainer()
        container.register(TestService, TestServiceImpl, singleton=True)
        
        service1 = container.resolve(TestService)
        service2 = container.resolve(TestService)
        
        assert service1 is service2
    
    def test_transient_scope(self):
        """Test transient scope"""
        container = DependencyContainer()
        container.register(TestService, TestServiceImpl, singleton=False)
        
        service1 = container.resolve(TestService)
        service2 = container.resolve(TestService)
        
        assert service1 is not service2
    
    def test_named_registrations(self):
        """Test named registrations"""
        container = DependencyContainer()
        container.register(TestService, TestServiceImpl, name="impl1")
        container.register(TestService, TestServiceImpl2, name="impl2")
        
        service1 = container.resolve(TestService, name="impl1")
        service2 = container.resolve(TestService, name="impl2")
        
        assert isinstance(service1, TestServiceImpl)
        assert isinstance(service2, TestServiceImpl2)
        assert service1.perform() == "TestServiceImpl.perform"
        assert service2.perform() == "TestServiceImpl2.perform"
    
    def test_constructor_injection(self):
        """Test constructor injection"""
        container = DependencyContainer()
        container.register(TestService, TestServiceImpl)
        container.register(TestDependentService)
        
        dependent = container.resolve(TestDependentService)
        
        assert isinstance(dependent.service, TestServiceImpl)
        assert dependent.use_dependency() == "Used dependency: TestServiceImpl.perform"
    
    def test_inject_decorator(self):
        """Test inject decorator"""
        container = DependencyContainer()
        container.register(TestService, TestServiceImpl)
        
        # Create a global container for the decorator to use
        import app.scheduling.dependencies
        app.scheduling.dependencies._container = container
        
        result = test_injected_function()
        
        assert result == "TestServiceImpl.perform"
    
    def test_inject_with_optional_dependency(self):
        """Test inject decorator with an optional dependency"""
        container = DependencyContainer()
        container.register(TestService, TestServiceImpl)
        logger = TestLogger()
        container.register_instance(TestLogger, logger)
        
        # Create a global container for the decorator to use
        import app.scheduling.dependencies
        app.scheduling.dependencies._container = container
        
        result = test_injected_function()
        
        assert result == "TestServiceImpl.perform"
        assert logger.logs == ["test_injected_function called"]
    
    def test_clear(self):
        """Test clearing the container"""
        container = DependencyContainer()
        container.register(TestService, TestServiceImpl)
        
        container.clear()
        
        with pytest.raises(KeyError):
            container.resolve(TestService)
    
    def test_missing_dependency(self):
        """Test resolving a dependency that is not registered"""
        container = DependencyContainer()
        
        with pytest.raises(KeyError):
            container.resolve(TestService)
    
    def test_register_without_implementation(self):
        """Test registering a service without specifying an implementation"""
        container = DependencyContainer()
        
        # Should use the service type as the implementation
        container.register(TestServiceImpl)
        
        service = container.resolve(TestServiceImpl)
        
        assert isinstance(service, TestServiceImpl)
        assert service.perform() == "TestServiceImpl.perform"
