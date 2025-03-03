"""
Response Models

This module defines standardized response models for the API layer.
These models help ensure consistent response formatting across the application.
"""

from typing import Dict, Any, List, Optional, Union, Generic, TypeVar
from pydantic import BaseModel, Field

# Define a generic type variable for the data payload
T = TypeVar('T')


class ErrorDetail(BaseModel):
    """
    Model for error details in API responses.
    
    Attributes:
        message: Main error message
        hint: Optional hint for resolving the error
        code: Optional error code for client-side identification
        field: Optional field name if the error is related to a specific field
    """
    message: str
    hint: Optional[str] = None
    code: Optional[str] = None
    field: Optional[str] = None


class ErrorResponse(BaseModel):
    """
    Model for standardized error responses.
    
    Attributes:
        success: Always False for error responses
        errors: List of error details
        status_code: HTTP status code
    """
    success: bool = False
    errors: List[ErrorDetail]
    status_code: int = Field(
        description="HTTP status code",
        ge=400,  # Must be at least 400 (client error)
        le=599   # Must be at most 599 (network connect timeout)
    )


class SuccessResponse(BaseModel, Generic[T]):
    """
    Model for standardized success responses.
    
    Attributes:
        success: Always True for success responses
        data: Response payload
        message: Optional success message
    """
    success: bool = True
    data: T
    message: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Model for paginated responses.
    
    Attributes:
        success: Always True for success responses
        data: List of result items
        page: Current page number
        page_size: Number of items per page
        total_items: Total number of items available
        total_pages: Total number of pages available
    """
    success: bool = True
    data: List[T]
    page: int
    page_size: int
    total_items: int
    total_pages: int


class ResponseFactory:
    """
    Factory for creating standardized responses.
    """
    
    @staticmethod
    def success(data: Any, message: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a standardized success response.
        
        Args:
            data: Response payload
            message: Optional success message
            
        Returns:
            A dictionary representing a SuccessResponse
        """
        return {
            "success": True,
            "data": data,
            "message": message
        }
    
    @staticmethod
    def error(
        message: str,
        status_code: int = 400,
        hint: Optional[str] = None,
        code: Optional[str] = None,
        field: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized error response.
        
        Args:
            message: Main error message
            status_code: HTTP status code
            hint: Optional hint for resolving the error
            code: Optional error code for client-side identification
            field: Optional field name if the error is related to a specific field
            
        Returns:
            A dictionary representing an ErrorResponse
        """
        error_detail = {"message": message}
        if hint:
            error_detail["hint"] = hint
        if code:
            error_detail["code"] = code
        if field:
            error_detail["field"] = field
            
        return {
            "success": False,
            "errors": [error_detail],
            "status_code": status_code
        }
    
    @staticmethod
    def errors(
        errors: List[Dict[str, Any]],
        status_code: int = 400
    ) -> Dict[str, Any]:
        """
        Create a standardized error response with multiple errors.
        
        Args:
            errors: List of error details
            status_code: HTTP status code
            
        Returns:
            A dictionary representing an ErrorResponse
        """
        return {
            "success": False,
            "errors": errors,
            "status_code": status_code
        }
    
    @staticmethod
    def paginated(
        data: List[Any],
        page: int,
        page_size: int,
        total_items: int
    ) -> Dict[str, Any]:
        """
        Create a standardized paginated response.
        
        Args:
            data: List of result items
            page: Current page number
            page_size: Number of items per page
            total_items: Total number of items available
            
        Returns:
            A dictionary representing a PaginatedResponse
        """
        total_pages = (total_items + page_size - 1) // page_size if page_size > 0 else 0
        
        return {
            "success": True,
            "data": data,
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages
        }
