"""
Repository Factory

This module provides a factory for creating repository instances with appropriate
dependencies and configuration.
"""

import logging
import os
from typing import Dict, Type, Optional, Any

from .base_repository import BaseRepository
from .schedule_repository import ScheduleRepository, FileScheduleRepository

# Set up logger
logger = logging.getLogger(__name__)


class RepositoryFactory:
    """
    Factory for creating repository instances.
    
    This factory creates and manages repository instances, ensuring proper
    configuration and dependency injection. It follows the singleton pattern
    to avoid creating multiple instances of the same repository.
    """
    
    # Class variable to store singleton instances
    _instances: Dict[Type[BaseRepository], BaseRepository] = {}
    
    @classmethod
    def get_schedule_repository(cls) -> ScheduleRepository:
        """
        Get or create a ScheduleRepository instance.
        
        Returns:
            A ScheduleRepository instance
        """
        return cls._get_repository(ScheduleRepository, FileScheduleRepository)
    
    @classmethod
    def _get_repository(cls, interface_type: Type[BaseRepository], 
                        implementation_type: Type[BaseRepository], 
                        **kwargs) -> BaseRepository:
        """
        Get or create a repository instance of the specified type.
        
        Args:
            interface_type: The repository interface type
            implementation_type: The concrete repository implementation type
            **kwargs: Additional arguments to pass to the constructor
            
        Returns:
            A repository instance
        """
        if interface_type not in cls._instances:
            # Get repository configuration from environment variables
            config = cls._get_repository_config(interface_type)
            
            # Create repository instance with configuration and additional arguments
            cls._instances[interface_type] = implementation_type(**config, **kwargs)
            logger.debug(f"Created new repository instance: {implementation_type.__name__}")
        
        return cls._instances[interface_type]
    
    @classmethod
    def _get_repository_config(cls, repo_type: Type[BaseRepository]) -> Dict[str, Any]:
        """
        Get configuration for a repository type from environment variables.
        
        Args:
            repo_type: The repository type
            
        Returns:
            Dictionary of configuration parameters
        """
        config = {}
        
        # Handle specific repository types
        if repo_type == ScheduleRepository:
            # Get data directory from environment or use default
            data_dir = os.environ.get("SCHEDULER_DATA_DIR", "data")
            config["data_dir"] = data_dir
        
        return config


# Convenience functions for dependency injection in FastAPI
def get_schedule_repository() -> ScheduleRepository:
    """
    Dependency injection function for FastAPI to get a ScheduleRepository.
    
    Returns:
        A ScheduleRepository instance
    """
    return RepositoryFactory.get_schedule_repository()
