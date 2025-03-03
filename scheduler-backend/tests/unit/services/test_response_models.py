"""
Test Response Models

This module contains tests for the response models used for standardizing API responses.
"""

import pytest
from typing import Dict, Any, List, Optional
from pydantic import ValidationError

from app.services.response_models import (
    ErrorDetail,
    ErrorResponse,
    SuccessResponse,
    PaginatedResponse,
    ResponseFactory
)


class TestErrorDetail:
    """Tests for the ErrorDetail model."""
    
    def test_creation(self):
        """Test creating an error detail."""
        # Create with just a message
        error = ErrorDetail(message="Test error")
        assert error.message == "Test error"
        assert error.hint is None
        assert error.code is None
        assert error.field is None
        
        # Create with all fields
        error = ErrorDetail(
            message="Test error",
            hint="This is a hint",
            code="TEST_ERROR",
            field="test_field"
        )
        assert error.message == "Test error"
        assert error.hint == "This is a hint"
        assert error.code == "TEST_ERROR"
        assert error.field == "test_field"


class TestErrorResponse:
    """Tests for the ErrorResponse model."""
    
    def test_creation(self):
        """Test creating an error response."""
        # Create with a single error
        response = ErrorResponse(
            errors=[ErrorDetail(message="Test error")],
            status_code=400
        )
        assert response.success is False
        assert len(response.errors) == 1
        assert response.errors[0].message == "Test error"
        assert response.status_code == 400
        
        # Create with multiple errors
        response = ErrorResponse(
            errors=[
                ErrorDetail(message="Error 1", field="field1"),
                ErrorDetail(message="Error 2", field="field2")
            ],
            status_code=422
        )
        assert response.success is False
        assert len(response.errors) == 2
        assert response.errors[0].message == "Error 1"
        assert response.errors[1].message == "Error 2"
        assert response.status_code == 422
    
    def test_validation(self):
        """Test validation of error responses."""
        # Test status code validation (must be 400+)
        with pytest.raises(ValidationError):
            ErrorResponse(
                errors=[ErrorDetail(message="Test error")],
                status_code=200  # Not an error status code
            )
        
        # Test validation with a valid error status code
        try:
            ErrorResponse(
                errors=[ErrorDetail(message="Test error")],
                status_code=500
            )
        except ValidationError:
            pytest.fail("ValidationError raised with valid status code")


class TestSuccessResponse:
    """Tests for the SuccessResponse model."""
    
    def test_creation(self):
        """Test creating a success response."""
        # Create with data only
        response = SuccessResponse(data={"key": "value"})
        assert response.success is True
        assert response.data == {"key": "value"}
        assert response.message is None
        
        # Create with data and message
        response = SuccessResponse(
            data={"key": "value"},
            message="Operation successful"
        )
        assert response.success is True
        assert response.data == {"key": "value"}
        assert response.message == "Operation successful"
        
        # Create with list data
        response = SuccessResponse(data=[1, 2, 3])
        assert response.success is True
        assert response.data == [1, 2, 3]


class TestPaginatedResponse:
    """Tests for the PaginatedResponse model."""
    
    def test_creation(self):
        """Test creating a paginated response."""
        response = PaginatedResponse(
            data=[{"id": 1}, {"id": 2}, {"id": 3}],
            page=1,
            page_size=10,
            total_items=23,
            total_pages=3
        )
        assert response.success is True
        assert len(response.data) == 3
        assert response.page == 1
        assert response.page_size == 10
        assert response.total_items == 23
        assert response.total_pages == 3


class TestResponseFactory:
    """Tests for the ResponseFactory."""
    
    def test_success(self):
        """Test creating a success response."""
        # Create with data only
        response = ResponseFactory.success(data={"key": "value"})
        assert response["success"] is True
        assert response["data"] == {"key": "value"}
        assert response["message"] is None
        
        # Create with data and message
        response = ResponseFactory.success(
            data={"key": "value"},
            message="Operation successful"
        )
        assert response["success"] is True
        assert response["data"] == {"key": "value"}
        assert response["message"] == "Operation successful"
    
    def test_error(self):
        """Test creating an error response."""
        # Create with message only
        response = ResponseFactory.error(message="Test error")
        assert response["success"] is False
        assert len(response["errors"]) == 1
        assert response["errors"][0]["message"] == "Test error"
        assert response["status_code"] == 400  # Default
        
        # Create with all fields
        response = ResponseFactory.error(
            message="Test error",
            status_code=422,
            hint="This is a hint",
            code="TEST_ERROR",
            field="test_field"
        )
        assert response["success"] is False
        assert len(response["errors"]) == 1
        assert response["errors"][0]["message"] == "Test error"
        assert response["errors"][0]["hint"] == "This is a hint"
        assert response["errors"][0]["code"] == "TEST_ERROR"
        assert response["errors"][0]["field"] == "test_field"
        assert response["status_code"] == 422
    
    def test_errors(self):
        """Test creating an error response with multiple errors."""
        response = ResponseFactory.errors(
            errors=[
                {"message": "Error 1", "field": "field1"},
                {"message": "Error 2", "field": "field2"}
            ],
            status_code=422
        )
        assert response["success"] is False
        assert len(response["errors"]) == 2
        assert response["errors"][0]["message"] == "Error 1"
        assert response["errors"][1]["message"] == "Error 2"
        assert response["status_code"] == 422
    
    def test_paginated(self):
        """Test creating a paginated response."""
        response = ResponseFactory.paginated(
            data=[{"id": 1}, {"id": 2}, {"id": 3}],
            page=1,
            page_size=10,
            total_items=23
        )
        assert response["success"] is True
        assert len(response["data"]) == 3
        assert response["page"] == 1
        assert response["page_size"] == 10
        assert response["total_items"] == 23
        assert response["total_pages"] == 3  # Calculated
