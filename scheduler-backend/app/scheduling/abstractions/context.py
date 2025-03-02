"""
Scheduler Context Module

This module defines the context classes for the scheduler system.
The context classes provide a shared state for the scheduler components.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Set, TypeVar, Generic, Union
import logging

from ...models import (
    ScheduleRequest,
    Class,
    TimeSlot,
    InstructorAvailability
)

logger = logging.getLogger(__name__)


class SchedulerContext:
    """
    Enhanced context for the scheduler system
    
    This class provides a shared context for the scheduler components,
    including the request, model variables, and other state.
    """
    
    def __init__(
        self,
        request: ScheduleRequest,
        start_date: datetime,
        end_date: datetime,
        model: Optional[Any] = None,
        solver: Optional[Any] = None
    ):
        """
        Initialize the context
        
        Args:
            request: The schedule request
            start_date: The start date of the schedule
            end_date: The end date of the schedule
            model: The solver model (optional)
            solver: The solver instance (optional)
        """
        self.request = request
        self.start_date = start_date
        self.end_date = end_date
        self.model = model
        self.solver = solver
        
        # Extra state for the scheduler
        self.variables: Dict[str, Any] = {}
        self.debug_info: Dict[str, Any] = {}
        self.metrics: Dict[str, Any] = {}
        
        # Index classes and instructors by ID for quick lookup
        self._initialize_indices()
    
    def _initialize_indices(self) -> None:
        """Initialize indices for quick lookup"""
        # Classes by ID and name
        self.classes_by_id: Dict[str, Class] = {}
        self.classes_by_name: Dict[str, Class] = {}
        
        for c in self.request.classes:
            self.classes_by_id[c.id] = c
            self.classes_by_name[c.name] = c
        
        # Instructor availability by ID, date, and time slot
        self.instructor_by_id: Dict[str, List[InstructorAvailability]] = {}
        self.unavailable_timeslots: Dict[str, Set[TimeSlot]] = {}
        self.preferred_timeslots: Dict[str, Set[TimeSlot]] = {}
        
        for avail in self.request.instructorAvailability:
            # Add to instructor by ID index
            if avail.instructorId not in self.instructor_by_id:
                self.instructor_by_id[avail.instructorId] = []
            self.instructor_by_id[avail.instructorId].append(avail)
            
            # Add to unavailable time slots index
            for slot in avail.unavailableSlots:
                key = f"{avail.instructorId}:{slot.dayOfWeek}:{slot.period}"
                if key not in self.unavailable_timeslots:
                    self.unavailable_timeslots[key] = set()
                self.unavailable_timeslots[key].add(slot)
            
            # Add to preferred time slots index
            for slot in avail.preferredSlots:
                key = f"{avail.instructorId}:{slot.dayOfWeek}:{slot.period}"
                if key not in self.preferred_timeslots:
                    self.preferred_timeslots[key] = set()
                self.preferred_timeslots[key].add(slot)
    
    def is_instructor_available(self, instructor_id: str, time_slot: TimeSlot) -> bool:
        """
        Check if an instructor is available at a time slot
        
        Args:
            instructor_id: The instructor ID
            time_slot: The time slot
            
        Returns:
            True if the instructor is available, False otherwise
        """
        key = f"{instructor_id}:{time_slot.dayOfWeek}:{time_slot.period}"
        return key not in self.unavailable_timeslots
    
    def is_time_slot_preferred(self, instructor_id: str, time_slot: TimeSlot) -> bool:
        """
        Check if a time slot is preferred by an instructor
        
        Args:
            instructor_id: The instructor ID
            time_slot: The time slot
            
        Returns:
            True if the time slot is preferred, False otherwise
        """
        key = f"{instructor_id}:{time_slot.dayOfWeek}:{time_slot.period}"
        return key in self.preferred_timeslots
    
    def add_variable(self, name: str, var: Any) -> None:
        """
        Add a variable to the context
        
        Args:
            name: The variable name
            var: The variable value
        """
        self.variables[name] = var
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """
        Get a variable from the context
        
        Args:
            name: The variable name
            default: Default value if not found
            
        Returns:
            The variable value, or default if not found
        """
        return self.variables.get(name, default)
    
    def add_debug_info(self, key: str, value: Any) -> None:
        """
        Add debug information to the context
        
        Args:
            key: The debug info key
            value: The debug info value
        """
        self.debug_info[key] = value
    
    def add_metric(self, key: str, value: Any) -> None:
        """
        Add a metric to the context
        
        Args:
            key: The metric key
            value: The metric value
        """
        self.metrics[key] = value
