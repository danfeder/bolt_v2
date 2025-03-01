from .base import BaseConstraint, ConstraintViolation
from ..core import ConstraintManager
from .assignment import SingleAssignmentConstraint, NoOverlapConstraint
from .instructor import InstructorAvailabilityConstraint
from .periods import RequiredPeriodsConstraint, ConflictPeriodsConstraint
from .teacher_workload import ConsecutiveClassesConstraint, TeacherBreakConstraint
from .relaxation import (
    RelaxableConstraint, 
    RelaxationLevel, 
    RelaxationResult, 
    RelaxationController
)
from .relaxable_limits import (
    RelaxableDailyLimitConstraint,
    RelaxableWeeklyLimitConstraint
)

__all__ = [
    'BaseConstraint',
    'ConstraintViolation',
    'ConstraintManager',
    'SingleAssignmentConstraint',
    'NoOverlapConstraint',
    'InstructorAvailabilityConstraint',
    'RequiredPeriodsConstraint',
    'ConflictPeriodsConstraint',
    'ConsecutiveClassesConstraint',
    'TeacherBreakConstraint',
    'RelaxableConstraint',
    'RelaxationLevel',
    'RelaxationResult',
    'RelaxationController',
    'RelaxableDailyLimitConstraint',
    'RelaxableWeeklyLimitConstraint'
]
