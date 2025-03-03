"""
Schedule Repository

This module defines the interface and implementations for accessing and storing schedule data.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..models import ScheduleRequest, ScheduleResponse
from .base_repository import BaseRepository

# Set up logger
logger = logging.getLogger(__name__)


class ScheduleRepository(BaseRepository[ScheduleResponse]):
    """
    Interface for schedule data persistence operations.
    
    This interface defines methods for storing and retrieving schedule data,
    including requests, responses, and configuration information.
    """
    
    def create(self, entity: ScheduleResponse) -> ScheduleResponse:
        """
        Create a new schedule record.
        
        Args:
            entity: The schedule response to save
            
        Returns:
            The saved schedule response with any additional fields populated
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def get(self, entity_id: str) -> Optional[ScheduleResponse]:
        """
        Retrieve a schedule by its ID.
        
        Args:
            entity_id: The unique identifier of the schedule
            
        Returns:
            The schedule if found, None otherwise
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[ScheduleResponse]:
        """
        Retrieve all schedules matching the optional filters.
        
        Args:
            filters: Optional filtering criteria
            
        Returns:
            List of matching schedules
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def update(self, entity_id: str, entity: ScheduleResponse) -> Optional[ScheduleResponse]:
        """
        Update an existing schedule.
        
        Args:
            entity_id: The unique identifier of the schedule to update
            entity: The updated schedule data
            
        Returns:
            The updated schedule if found, None otherwise
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def delete(self, entity_id: str) -> bool:
        """
        Delete a schedule by its ID.
        
        Args:
            entity_id: The unique identifier of the schedule to delete
            
        Returns:
            True if the schedule was deleted, False if it wasn't found
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def save_request(self, request_id: str, request: ScheduleRequest) -> str:
        """
        Save a schedule request for future reference.
        
        Args:
            request_id: Unique identifier for the request
            request: The schedule request to save
            
        Returns:
            The ID of the saved request
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_request(self, request_id: str) -> Optional[ScheduleRequest]:
        """
        Retrieve a saved schedule request.
        
        Args:
            request_id: The unique identifier of the request
            
        Returns:
            The schedule request if found, None otherwise
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_schedule_history(self, start_date: Optional[datetime] = None, 
                             end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get a history of generated schedules with metadata.
        
        Args:
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            List of schedule metadata records
        """
        raise NotImplementedError("Subclasses must implement this method")


class FileScheduleRepository(ScheduleRepository):
    """
    File-based implementation of ScheduleRepository.
    
    This implementation stores schedule data in JSON files on the filesystem.
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the repository with the data directory.
        
        Args:
            data_dir: Directory where schedule data files will be stored
        """
        self._data_dir = Path(data_dir)
        self._schedules_dir = self._data_dir / "schedules"
        self._requests_dir = self._data_dir / "requests"
        
        # Create directories if they don't exist
        self._schedules_dir.mkdir(parents=True, exist_ok=True)
        self._requests_dir.mkdir(parents=True, exist_ok=True)
        
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._logger.debug(f"Initialized with data directory: {data_dir}")
        
    def create(self, entity: ScheduleResponse) -> ScheduleResponse:
        """
        Create a new schedule record in the file system.
        
        Args:
            entity: The schedule response to save
            
        Returns:
            The saved schedule response with any additional fields populated
        """
        # Ensure entity has an ID
        if not getattr(entity, "id", None):
            entity.id = f"schedule_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Save to file
        file_path = self._schedules_dir / f"{entity.id}.json"
        
        try:
            # Convert to dict and save as JSON
            with open(file_path, 'w') as f:
                json.dump(entity.dict(), f, indent=2)
                
            self._logger.debug(f"Saved schedule {entity.id} to {file_path}")
            return entity
        except Exception as e:
            self._logger.error(f"Error saving schedule {entity.id}: {str(e)}")
            raise
    
    def get(self, entity_id: str) -> Optional[ScheduleResponse]:
        """
        Retrieve a schedule from the file system by its ID.
        
        Args:
            entity_id: The unique identifier of the schedule
            
        Returns:
            The schedule if found, None otherwise
        """
        file_path = self._schedules_dir / f"{entity_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                return ScheduleResponse(**data)
        except Exception as e:
            self._logger.error(f"Error reading schedule {entity_id}: {str(e)}")
            return None
    
    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[ScheduleResponse]:
        """
        Retrieve all schedules from the file system matching the optional filters.
        
        Args:
            filters: Optional filtering criteria
            
        Returns:
            List of matching schedules
        """
        # Default filters
        filters = filters or {}
        
        result = []
        
        # List all JSON files in the schedules directory
        for file_path in self._schedules_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                # Apply filters if any
                include = True
                for key, value in filters.items():
                    if key in data and data[key] != value:
                        include = False
                        break
                
                if include:
                    result.append(ScheduleResponse(**data))
            except Exception as e:
                self._logger.error(f"Error reading schedule from {file_path}: {str(e)}")
        
        return result
    
    def update(self, entity_id: str, entity: ScheduleResponse) -> Optional[ScheduleResponse]:
        """
        Update an existing schedule in the file system.
        
        Args:
            entity_id: The unique identifier of the schedule to update
            entity: The updated schedule data
            
        Returns:
            The updated schedule if found, None otherwise
        """
        file_path = self._schedules_dir / f"{entity_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            # Ensure the entity has the correct ID
            entity.id = entity_id
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(entity.dict(), f, indent=2)
                
            self._logger.debug(f"Updated schedule {entity_id}")
            return entity
        except Exception as e:
            self._logger.error(f"Error updating schedule {entity_id}: {str(e)}")
            raise
    
    def delete(self, entity_id: str) -> bool:
        """
        Delete a schedule from the file system by its ID.
        
        Args:
            entity_id: The unique identifier of the schedule to delete
            
        Returns:
            True if the schedule was deleted, False if it wasn't found
        """
        file_path = self._schedules_dir / f"{entity_id}.json"
        
        if not file_path.exists():
            return False
        
        try:
            file_path.unlink()
            self._logger.debug(f"Deleted schedule {entity_id}")
            return True
        except Exception as e:
            self._logger.error(f"Error deleting schedule {entity_id}: {str(e)}")
            return False
    
    def save_request(self, request_id: str, request: ScheduleRequest) -> str:
        """
        Save a schedule request to the file system for future reference.
        
        Args:
            request_id: Unique identifier for the request
            request: The schedule request to save
            
        Returns:
            The ID of the saved request
        """
        file_path = self._requests_dir / f"{request_id}.json"
        
        try:
            # Convert to dict and save as JSON
            with open(file_path, 'w') as f:
                json.dump(request.dict(), f, indent=2)
                
            self._logger.debug(f"Saved request {request_id} to {file_path}")
            return request_id
        except Exception as e:
            self._logger.error(f"Error saving request {request_id}: {str(e)}")
            raise
    
    def get_request(self, request_id: str) -> Optional[ScheduleRequest]:
        """
        Retrieve a saved schedule request from the file system.
        
        Args:
            request_id: The unique identifier of the request
            
        Returns:
            The schedule request if found, None otherwise
        """
        file_path = self._requests_dir / f"{request_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                return ScheduleRequest(**data)
        except Exception as e:
            self._logger.error(f"Error reading request {request_id}: {str(e)}")
            return None
    
    def get_schedule_history(self, start_date: Optional[datetime] = None, 
                             end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get a history of generated schedules with metadata from the file system.
        
        Args:
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            List of schedule metadata records
        """
        result = []
        
        # List all JSON files in the schedules directory
        for file_path in self._schedules_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Extract metadata
                metadata = {
                    "id": data.get("id", file_path.stem),
                    "created_at": data.get("metadata", {}).get("timestamp", None),
                    "solver_type": data.get("metadata", {}).get("solver_type", "unknown"),
                    "score": data.get("metadata", {}).get("score", 0),
                    "duration_ms": data.get("metadata", {}).get("duration_ms", 0),
                    "num_assignments": len(data.get("assignments", [])),
                    "filename": file_path.name
                }
                
                # Apply date filters if specified
                if metadata["created_at"]:
                    created_at = datetime.fromisoformat(metadata["created_at"].replace("Z", "+00:00"))
                    
                    if start_date and created_at < start_date:
                        continue
                        
                    if end_date and created_at > end_date:
                        continue
                
                result.append(metadata)
            except Exception as e:
                self._logger.error(f"Error reading schedule metadata from {file_path}: {str(e)}")
        
        # Sort by creation date, newest first
        result.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return result
