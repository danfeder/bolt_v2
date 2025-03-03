"""
Test Response Handler

This module contains tests for the API response handler.
"""

import pytest
from typing import Dict, Any, Tuple, Optional
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from pydantic import ValidationError

from app.api.response_handler import (
    handle_response,
    handle_service_result,
    create_error_response
)


class TestResponseHandler:
    """Tests for the response handler functions."""
    
    def test_handle_response_success(self):
        """Test handling a successful response."""
        # Test with data only
        response = handle_response(
            response_data={"test": "data"},
            error_details=None
        )
        assert response["success"] is True
        assert response["data"] == {"test": "data"}
        assert response["message"] is None
        
        # Test with data and success message
        response = handle_response(
            response_data={"test": "data"},
            error_details=None,
            success_message="Operation succeeded"
        )
        assert response["success"] is True
        assert response["data"] == {"test": "data"}
        assert response["message"] == "Operation succeeded"
    
    def test_handle_response_error(self):
        """Test handling an error response."""
        # Create error details
        error_details = {
            "status_code": 400,
            "detail": {
                "message": "Test error",
                "hint": "This is a hint"
            }
        }
        
        # Test that it raises HTTPException
        with pytest.raises(HTTPException) as excinfo:
            handle_response(
                response_data=None,
                error_details=error_details
            )
        
        # Check the exception
        assert excinfo.value.status_code == 400
        
        # Check the detail content
        detail = excinfo.value.detail
        assert detail["success"] is False
        assert len(detail["errors"]) == 1
        assert detail["errors"][0]["message"] == "Test error"
        assert detail["errors"][0]["hint"] == "This is a hint"
    
    def test_handle_service_result_success(self):
        """Test handling a successful service result."""
        # Create a success result
        result: Tuple[Any, Optional[Dict[str, Any]]] = ({"test": "data"}, None)
        
        # Handle the result
        response = handle_service_result(
            result=result,
            success_message="Operation succeeded"
        )
        
        # Check the response
        assert response["success"] is True
        assert response["data"] == {"test": "data"}
        assert response["message"] == "Operation succeeded"
    
    def test_handle_service_result_error(self):
        """Test handling an error service result."""
        # Create an error result
        error_details = {
            "status_code": 400,
            "detail": {
                "message": "Test error",
                "hint": "This is a hint"
            }
        }
        result: Tuple[Any, Optional[Dict[str, Any]]] = (None, error_details)
        
        # Test that it raises HTTPException
        with pytest.raises(HTTPException) as excinfo:
            handle_service_result(result)
        
        # Check the exception
        assert excinfo.value.status_code == 400
        
        # Check the detail content
        detail = excinfo.value.detail
        assert detail["success"] is False
        assert len(detail["errors"]) == 1
        assert detail["errors"][0]["message"] == "Test error"
        assert detail["errors"][0]["hint"] == "This is a hint"
    
    def test_create_error_response(self):
        """Test creating an error response."""
        # Test that it raises HTTPException
        with pytest.raises(HTTPException) as excinfo:
            create_error_response(
                message="Test error",
                status_code=403,
                hint="This is a hint"
            )
        
        # Check the exception
        assert excinfo.value.status_code == 403
        
        # Check the detail content
        detail = excinfo.value.detail
        assert detail["success"] is False
        assert len(detail["errors"]) == 1
        assert detail["errors"][0]["message"] == "Test error"
        assert detail["errors"][0]["hint"] == "This is a hint"


# Custom exception handler for integration tests
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Custom exception handler that returns the exception detail directly."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )


# Integration test for response handler in an actual FastAPI app
class TestResponseHandlerIntegration:
    """Integration tests for the response handler with FastAPI."""
    
    @pytest.fixture
    def test_app(self):
        """Create a test FastAPI app."""
        # Create a new FastAPI app
        app = FastAPI()
        
        # Add custom exception handler
        app.add_exception_handler(HTTPException, custom_http_exception_handler)
        
        # Add a success endpoint
        @app.get("/success")
        def success_endpoint():
            return handle_response(
                response_data={"message": "Success"},
                error_details=None,
                success_message="Operation succeeded"
            )
        
        # Add an error endpoint
        @app.get("/error")
        def error_endpoint():
            error_details = {
                "status_code": 400,
                "detail": {
                    "message": "Test error",
                    "hint": "This is a hint"
                }
            }
            return handle_response(
                response_data=None,
                error_details=error_details
            )
        
        # Add a service result endpoint
        @app.get("/service-success")
        def service_success_endpoint():
            result = ({"data": "value"}, None)
            return handle_service_result(result, "Service operation succeeded")
        
        # Add a service error endpoint
        @app.get("/service-error")
        def service_error_endpoint():
            error_details = {
                "status_code": 422,
                "detail": {
                    "message": "Service error",
                    "hint": "Fix service issue"
                }
            }
            result = (None, error_details)
            return handle_service_result(result)
        
        # Add a direct error endpoint
        @app.get("/direct-error")
        def direct_error_endpoint():
            create_error_response(
                message="Direct error",
                status_code=403,
                hint="You don't have permission"
            )
            return {}  # This will never be reached
        
        return app
    
    def test_success_endpoint(self, test_app):
        """Test a success endpoint."""
        client = TestClient(test_app)
        response = client.get("/success")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == {"message": "Success"}
        assert data["message"] == "Operation succeeded"
    
    def test_error_endpoint(self, test_app):
        """Test an error endpoint."""
        client = TestClient(test_app)
        response = client.get("/error")
        
        # Check response
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert len(data["errors"]) == 1
        assert data["errors"][0]["message"] == "Test error"
        assert data["errors"][0]["hint"] == "This is a hint"
    
    def test_service_success_endpoint(self, test_app):
        """Test a service success endpoint."""
        client = TestClient(test_app)
        response = client.get("/service-success")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == {"data": "value"}
        assert data["message"] == "Service operation succeeded"
    
    def test_service_error_endpoint(self, test_app):
        """Test a service error endpoint."""
        client = TestClient(test_app)
        response = client.get("/service-error")
        
        # Check response
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert len(data["errors"]) == 1
        assert data["errors"][0]["message"] == "Service error"
        assert data["errors"][0]["hint"] == "Fix service issue"
    
    def test_direct_error_endpoint(self, test_app):
        """Test a direct error endpoint."""
        client = TestClient(test_app)
        response = client.get("/direct-error")
        
        # Check response
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert len(data["errors"]) == 1
        assert data["errors"][0]["message"] == "Direct error"
        assert data["errors"][0]["hint"] == "You don't have permission"
