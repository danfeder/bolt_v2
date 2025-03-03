"""
API Response Handler

This module provides utility functions for creating consistent API responses
with standardized formats for both success and error cases.
"""

import logging
from typing import Dict, Any, Tuple, Optional, List, Generic, TypeVar
from fastapi import HTTPException, status

from ..services.response_models import ResponseFactory

# Set up logger
logger = logging.getLogger(__name__)

# Type variable for generic responses
T = TypeVar('T')


def handle_response(
    response_data: Any,
    error_details: Optional[Dict[str, Any]],
    success_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Handle an API response with standardized format and error handling.
    
    Args:
        response_data: Data to return on success
        error_details: Error details if any, or None on success
        success_message: Optional message to include on success
        
    Returns:
        A standardized response dictionary
        
    Raises:
        HTTPException: If error_details is not None
    """
    if error_details:
        status_code = error_details.get("status_code", status.HTTP_400_BAD_REQUEST)
        detail = error_details.get("detail", {})
        
        message = detail.get("message", "An error occurred")
        hint = detail.get("hint")
        
        # Log the error
        log_msg = f"API Error ({status_code}): {message}"
        if hint:
            log_msg += f" - Hint: {hint}"
        logger.error(log_msg)
        
        # Raise HTTP exception with standardized format
        raise HTTPException(
            status_code=status_code,
            detail=ResponseFactory.error(
                message=message,
                status_code=status_code,
                hint=hint
            )
        )
    
    # Return success response
    return ResponseFactory.success(
        data=response_data,
        message=success_message
    )


def handle_service_result(
    result: Tuple[Any, Optional[Dict[str, Any]]],
    success_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Handle a service result tuple with standardized response handling.
    
    This is a convenience wrapper for handle_response that works with
    the standard (result, error) tuple returned by service methods.
    
    Args:
        result: Tuple of (data, error_details)
        success_message: Optional message to include on success
        
    Returns:
        A standardized response dictionary
        
    Raises:
        HTTPException: If error_details is not None
    """
    data, error_details = result
    return handle_response(data, error_details, success_message)


def create_error_response(
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    hint: Optional[str] = None
) -> None:
    """
    Create and raise an error response as an HTTPException.
    
    Args:
        message: Error message
        status_code: HTTP status code
        hint: Optional hint for resolving the error
        
    Raises:
        HTTPException: Always raised with the specified details
    """
    # Log the error
    log_msg = f"API Error ({status_code}): {message}"
    if hint:
        log_msg += f" - Hint: {hint}"
    logger.error(log_msg)
    
    # Raise HTTP exception with standardized format
    raise HTTPException(
        status_code=status_code,
        detail=ResponseFactory.error(
            message=message,
            status_code=status_code,
            hint=hint
        )
    )
