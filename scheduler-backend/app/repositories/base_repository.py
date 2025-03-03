"""
Base Repository

This module defines the base repository interface for data access in the application.
All concrete repositories should implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

T = TypeVar('T')  # Generic type for the entity managed by the repository


class BaseRepository(Generic[T], ABC):
    """
    Base interface for all repositories.
    
    This abstract class defines the standard operations that all repositories
    should implement for CRUD operations and queries.
    """
    
    @abstractmethod
    def create(self, entity: T) -> T:
        """
        Create a new entity in the repository.
        
        Args:
            entity: The entity to create
            
        Returns:
            The created entity with any generated fields populated
        """
        pass
    
    @abstractmethod
    def get(self, entity_id: Any) -> Optional[T]:
        """
        Retrieve an entity by its ID.
        
        Args:
            entity_id: The unique identifier of the entity
            
        Returns:
            The entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        """
        Retrieve all entities matching the optional filters.
        
        Args:
            filters: Optional filtering criteria
            
        Returns:
            List of matching entities
        """
        pass
    
    @abstractmethod
    def update(self, entity_id: Any, entity: T) -> Optional[T]:
        """
        Update an existing entity.
        
        Args:
            entity_id: The unique identifier of the entity to update
            entity: The updated entity data
            
        Returns:
            The updated entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def delete(self, entity_id: Any) -> bool:
        """
        Delete an entity by its ID.
        
        Args:
            entity_id: The unique identifier of the entity to delete
            
        Returns:
            True if the entity was deleted, False if it wasn't found
        """
        pass


class AggregateRepository(ABC):
    """
    Base interface for repositories that manage aggregate roots.
    
    This abstract class extends the standard repository interface with
    methods specific to managing aggregate roots in domain-driven design.
    """
    
    @abstractmethod
    def save_aggregate(self, aggregate_root: Any) -> Any:
        """
        Save an aggregate root, creating it if it doesn't exist or
        updating it if it does.
        
        Args:
            aggregate_root: The aggregate root to save
            
        Returns:
            The saved aggregate root
        """
        pass
    
    @abstractmethod
    def get_aggregate(self, aggregate_id: Any) -> Optional[Any]:
        """
        Retrieve an aggregate root by its ID.
        
        Args:
            aggregate_id: The unique identifier of the aggregate root
            
        Returns:
            The aggregate root if found, None otherwise
        """
        pass
