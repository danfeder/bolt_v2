"""
Result Module

This module defines a generic result type to standardize success and error handling
across the application. The Result class is used to encapsulate operation outcomes
with relevant data, error messages, and warnings.
"""

from typing import TypeVar, Generic, Dict, Any, List, Optional, Union

# Define a type variable for the generic Result class
T = TypeVar('T')


class Result(Generic[T]):
    """
    A generic result class to standardize function returns across the application.
    
    This class provides a consistent way to return success/failure information along
    with data and error messages. It helps to avoid raising exceptions for expected
    error conditions and provides a structured way to return both data and metadata.
    
    Attributes:
        success (bool): Whether the operation was successful
        data (Optional[T]): The data returned by the operation (if successful)
        errors (List[str]): Error messages if the operation failed
        warnings (List[str]): Warning messages that don't indicate failure
        metadata (Dict[str, Any]): Additional metadata about the operation
    """
    
    def __init__(
        self,
        success: bool,
        data: Optional[T] = None,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a Result instance.
        
        Args:
            success: Whether the operation was successful
            data: The data returned by the operation (if successful)
            errors: Error messages if the operation failed
            warnings: Warning messages that don't indicate failure
            metadata: Additional metadata about the operation
        """
        self.success = success
        self.data = data
        self.errors = errors or []
        self.warnings = warnings or []
        self.metadata = metadata or {}
    
    def add_error(self, error: str) -> 'Result[T]':
        """
        Add an error message to the result.
        
        Args:
            error: The error message to add
            
        Returns:
            Self for chaining
        """
        self.errors.append(error)
        self.success = False
        return self
    
    def add_warning(self, warning: str) -> 'Result[T]':
        """
        Add a warning message to the result.
        
        Args:
            warning: The warning message to add
            
        Returns:
            Self for chaining
        """
        self.warnings.append(warning)
        return self
    
    def add_metadata(self, key: str, value: Any) -> 'Result[T]':
        """
        Add a metadata item to the result.
        
        Args:
            key: The metadata key
            value: The metadata value
            
        Returns:
            Self for chaining
        """
        self.metadata[key] = value
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the result to a dictionary suitable for API responses.
        
        Returns:
            A dictionary representation of the result
        """
        result = {
            "success": self.success,
            "data": self.data,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata
        }
        
        # Filter out empty values for cleaner responses
        return {k: v for k, v in result.items() if v or v is False or v == 0}
    
    def __bool__(self) -> bool:
        """
        Allow using the result in boolean expressions.
        
        Returns:
            True if the operation was successful, False otherwise
        """
        return self.success


def success(data: Optional[T] = None, **kwargs) -> Result[T]:
    """
    Create a successful result with the given data.
    
    Args:
        data: The data to include in the result
        **kwargs: Additional metadata to include
        
    Returns:
        A successful Result instance
    """
    metadata = kwargs.get('metadata', {})
    warnings = kwargs.get('warnings', [])
    
    return Result(
        success=True,
        data=data,
        warnings=warnings,
        metadata=metadata
    )


def error(message: str, **kwargs) -> Result[Any]:
    """
    Create an error result with the given message.
    
    Args:
        message: The error message
        **kwargs: Additional metadata to include
        
    Returns:
        An error Result instance
    """
    data = kwargs.get('data')
    metadata = kwargs.get('metadata', {})
    warnings = kwargs.get('warnings', [])
    
    return Result(
        success=False,
        data=data,
        errors=[message],
        warnings=warnings,
        metadata=metadata
    )


def warning(data: Optional[T] = None, message: str = "", **kwargs) -> Result[T]:
    """
    Create a successful result with a warning.
    
    Args:
        data: The data to include in the result
        message: The warning message
        **kwargs: Additional metadata to include
        
    Returns:
        A Result instance with a warning
    """
    metadata = kwargs.get('metadata', {})
    
    return Result(
        success=True,
        data=data,
        warnings=[message] if message else [],
        metadata=metadata
    )
