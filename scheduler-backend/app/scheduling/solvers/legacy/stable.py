"""Stable solver implementation using shared configuration"""
from typing import List
import traceback
from dateutil import parser

from ..core import SchedulerContext
from ...models import ScheduleRequest, ScheduleResponse
from .base import BaseSolver
from .config import get_base_constraints, get_base_objectives

class StableSolver(BaseSolver):
    """Production-ready solver using tried and tested configuration"""
    
    def __init__(self):
        super().__init__("cp-sat-stable")
        
        # Add base constraints and objectives
        for constraint in get_base_constraints():
            self.add_constraint(constraint)
            
        for objective in get_base_objectives():
            self.add_objective(objective)
        
    def create_schedule(self, request: ScheduleRequest) -> ScheduleResponse:
        """Create a schedule using the stable solver configuration"""
        print(f"\nStarting stable solver for {len(request.classes)} classes...")
        print("\nSolver configuration:")
        print("Constraints:")
        for constraint in self.constraints:
            print(f"- {constraint.name}")
        print("\nObjectives:")
        for objective in self.objectives:
            print(f"- {objective.name} (weight: {objective.weight})")
            
        try:
            # Validate dates
            start_date = parser.parse(request.startDate)
            end_date = parser.parse(request.endDate)
            
            # Create schedule using base solver
            response = super().create_schedule(request)
            
            # Validate solution
            print("\nValidating constraints...")
            all_violations = []
            context = SchedulerContext(
                model=None,  # Not needed for validation
                solver=None,  # Not needed for validation
                request=request,
                start_date=start_date,
                end_date=end_date
            )
            
            for constraint in self.constraints:
                violations = constraint.validate(
                    response.assignments,
                    context
                )
                if violations:
                    print(f"\nViolations for {constraint.name}:")
                    for v in violations:
                        print(f"- {v.message}")
                    all_violations.extend(violations)
            
            if all_violations:
                raise Exception(
                    f"Schedule validation failed with {len(all_violations)} violations"
                )
            
            print("\nAll constraints satisfied!")
            return response
            
        except Exception as e:
            print(f"Scheduling error in stable solver: {str(e)}")
            print("Full traceback:")
            print(traceback.format_exc())
            raise
