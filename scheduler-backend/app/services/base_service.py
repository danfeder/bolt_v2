"""
Base Service

This module provides a base class for all service implementations to ensure
consistent behavior and dependency management across services.
"""

import logging
from typing import Dict, Any, Optional

# Set up logger
logger = logging.getLogger(__name__)


class BaseService:
    """
    Base class for all services in the application.
    
    This class provides common functionality for all services, including:
    - Consistent initialization
    - Dependency management
    - Logging
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the service with optional dependencies.
        
        Args:
            **kwargs: Optional dependencies that can be injected
        """
        # Store all dependencies
        self._dependencies = kwargs
        
        # Set up service-specific logger
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._logger.debug(f"Initialized {self.__class__.__name__}")
    
    def _get_dependency(self, name: str, default: Any = None) -> Any:
        """
        Get a dependency by name.
        
        Args:
            name: The name of the dependency
            default: Default value if the dependency is not found
            
        Returns:
            The dependency value or the default
        """
        return self._dependencies.get(name, default)
    
    def _log_error(self, message: str, exc: Optional[Exception] = None) -> None:
        """
        Log an error message and optionally include exception details.
        
        Args:
            message: The error message
            exc: Optional exception to include in the log
        """
        if exc:
            self._logger.error(f"{message}: {str(exc)}", exc_info=True)
        else:
            self._logger.error(message)
    
    def _log_info(self, message: str) -> None:
        """
        Log an informational message.
        
        Args:
            message: The message to log
        """
        self._logger.info(message)
    
    def _log_warning(self, message: str) -> None:
        """
        Log a warning message.
        
        Args:
            message: The message to log
        """
        self._logger.warning(message)
    
    def _create_error_response(
        self, 
        status_code: int, 
        message: str, 
        hint: Optional[str] = None,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized error response.
        
        Args:
            status_code: The HTTP status code
            message: The error message
            hint: Optional hint for resolving the error
            additional_info: Optional additional information to include
            
        Returns:
            A dictionary with the error response
        """
        error_detail = {"message": message}
        
        if hint:
            error_detail["hint"] = hint
            
        if additional_info:
            error_detail.update(additional_info)
            
        return {
            "status_code": status_code,
            "detail": error_detail
        }
