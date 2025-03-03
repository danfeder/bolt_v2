"""
Integration tests for schedule repository and service layer.

These tests verify that the repository pattern and service layer work 
together correctly to persist and retrieve schedule data.
"""

import os
import pytest
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any, Generator

from app.models import ScheduleRequest, ScheduleResponse, ScheduleMetadata
from app.repositories.schedule_repository import FileScheduleRepository
from app.services.scheduler_service import SchedulerService
from tests.utils.generators import ScheduleRequestGenerator
from tests.utils.assertions import assert_valid_schedule


@pytest.fixture
def temp_data_dir() -> Generator[str, None, None]:
    """
    Create a temporary directory for test data.
    
    Yields:
        Path to the temporary directory
    """
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_repository(temp_data_dir) -> FileScheduleRepository:
    """
    Create a test repository with a temporary data directory.
    
    Args:
        temp_data_dir: Path to temporary directory from fixture
        
    Returns:
        A FileScheduleRepository instance for testing
    """
    return FileScheduleRepository(data_dir=temp_data_dir)


@pytest.fixture
def test_service(test_repository) -> SchedulerService:
    """
    Create a test service with the test repository.
    
    Args:
        test_repository: Repository from fixture
        
    Returns:
        A SchedulerService instance for testing
    """
    return SchedulerService(schedule_repository=test_repository)


def test_repository_save_and_retrieve():
    """Test basic save and retrieve operations in the repository"""
    # Create a temporary data directory
    temp_dir = tempfile.mkdtemp()
    try:
        # Create repository
        repo = FileScheduleRepository(data_dir=temp_dir)
        
        # Create a simple schedule response
        response = ScheduleResponse(
            id="test_schedule_1",
            assignments=[],
            metadata=ScheduleMetadata(
                timestamp=datetime.now().isoformat(),
                solver_type="test",
                score=100,
                duration_ms=50
            )
        )
        
        # Save to repository
        saved = repo.create(response)
        assert saved.id == "test_schedule_1"
        
        # Retrieve from repository
        retrieved = repo.get("test_schedule_1")
        assert retrieved is not None
        assert retrieved.id == "test_schedule_1"
        assert retrieved.metadata.solver_type == "test"
        
        # Save a request too
        request = ScheduleRequestGenerator.create_request(num_classes=1)
        request_id = repo.save_request("test_request_1", request)
        assert request_id == "test_request_1"
        
        # Retrieve request
        retrieved_request = repo.get_request("test_request_1")
        assert retrieved_request is not None
        assert len(retrieved_request.classes) == 1
        
        # Get history
        history = repo.get_schedule_history()
        assert len(history) == 1
        assert history[0]["id"] == "test_schedule_1"
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir)


def test_service_with_repository(test_service, test_repository):
    """Test the integration between service and repository"""
    # Create a schedule request
    request = ScheduleRequestGenerator.create_request(
        num_classes=1,  # Small number for quick testing
        num_weeks=1
    )
    
    # Create a schedule through the service
    response = test_service.create_schedule(request)
    
    # Verify the response
    assert response is not None
    assert response.id is not None
    
    # Try to retrieve it through the service
    retrieved = test_service.get_schedule(response.id)
    assert retrieved is not None
    assert retrieved.id == response.id
    
    # Verify the request was also saved
    history = test_service.get_schedule_history()
    assert len(history) == 1
    assert history[0]["id"] == response.id


def test_end_to_end_schedule_persistence(test_service, test_repository):
    """Test end-to-end schedule creation, persistence, and retrieval"""
    # Create a more complex schedule request
    request = ScheduleRequestGenerator.create_request(
        num_classes=2,
        num_weeks=1
    )
    
    # Relax constraints for testing
    request.constraints.minPeriodsPerWeek = 1
    
    # Create schedule
    response = test_service.create_schedule(request)
    
    # Verify created schedule is valid
    assert_valid_schedule(response, request)
    
    # Save the schedule ID
    schedule_id = response.id
    
    # Retrieve from repository directly to verify it was saved correctly
    retrieved_from_repo = test_repository.get(schedule_id)
    assert retrieved_from_repo is not None
    assert retrieved_from_repo.id == schedule_id
    
    # Verify the retrieved schedule is also valid
    assert_valid_schedule(retrieved_from_repo, request)
    
    # Get schedule history
    history = test_service.get_schedule_history()
    assert len(history) == 1
    assert history[0]["id"] == schedule_id
    
    # Update schedule metadata
    if not hasattr(retrieved_from_repo.metadata, "notes"):
        retrieved_from_repo.metadata.notes = "Test update"
    else:
        retrieved_from_repo.metadata.notes = "Test update"
    
    updated = test_repository.update(schedule_id, retrieved_from_repo)
    assert updated is not None
    assert hasattr(updated.metadata, "notes")
    assert updated.metadata.notes == "Test update"
    
    # Retrieve again to confirm update
    re_retrieved = test_service.get_schedule(schedule_id)
    assert re_retrieved is not None
    assert hasattr(re_retrieved.metadata, "notes")
    assert re_retrieved.metadata.notes == "Test update"
