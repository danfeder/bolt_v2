from abc import ABC, abstractmethod
from typing import List

from ortools.sat.python import cp_model

from ..core import SchedulerContext

class BaseObjective(ABC):
    """Base class for implementing scheduling objectives"""
    
    def __init__(self, name: str, weight: int):
        self._name = name
        self._weight = weight
        
    @property
    def name(self) -> str:
        """Get the objective's name for logging"""
        return self._name
    
    @property
    def weight(self) -> int:
        """Get the objective's weight for the solver"""
        return self._weight
    
    @abstractmethod
    def create_terms(self, context: SchedulerContext) -> List[cp_model.LinearExpr]:
        """Create objective terms for the solver"""
        pass
