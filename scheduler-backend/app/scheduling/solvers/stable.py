from typing import List
import traceback
import time

from ..core import SchedulerContext
from ..constraints.assignment import SingleAssignmentConstraint, NoOverlapConstraint
from ..constraints.teacher import TeacherAvailabilityConstraint
from ..constraints.periods import RequiredPeriodsConstraint, ConflictPeriodsConstraint
from ..objectives.required import RequiredPeriodsObjective
from ..objectives.distribution import DistributionObjective

from .base import BaseSolver
from ...models import ScheduleRequest, ScheduleResponse

class StableSolver(BaseSolver):
    """
    Production-ready solver implementing all scheduling features:
    1. Basic scheduling constraints
       - Single assignment per class
       - No overlapping classes
       - Only weekdays periods 1-8
    2. Required scheduling rules
       - Required period assignments
       - Teacher availability
       - Conflict periods
    3. Distribution optimization
       - Even distribution across weeks
       - Even distribution within days
       - Balanced teacher workload
    4. Preference satisfaction
       - Preferred period assignments
       - Avoided period penalties
       - Earlier date preference
    """
    
    def __init__(self):
        super().__init__(name="cp-sat-stable")
        
        # Add constraints in order of priority
        self.add_constraint(SingleAssignmentConstraint())
        self.add_constraint(NoOverlapConstraint())
        self.add_constraint(TeacherAvailabilityConstraint())
        self.add_constraint(RequiredPeriodsConstraint())
        self.add_constraint(ConflictPeriodsConstraint())
        
        # Add objectives in order of priority
        self.add_objective(RequiredPeriodsObjective())
        self.add_objective(DistributionObjective())
        
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
            # Create schedule using base solver
            response = super().create_schedule(request)
            
            # Validate constraints
            print("\nValidating constraints...")
            all_violations = []
            for constraint in self.constraints:
                violations = constraint.validate(
                    response.assignments,
                    SchedulerContext(
                        model=None,  # Not needed for validation
                        solver=None,  # Not needed for validation
                        request=request,
                        start_date=None,  # Not needed for validation
                        end_date=None  # Not needed for validation
                    )
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
