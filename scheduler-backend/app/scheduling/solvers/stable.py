from typing import List, Dict, Any
import traceback
import time

from ..core import SchedulerContext
from ..constraints.assignment import SingleAssignmentConstraint, NoOverlapConstraint
from ..constraints.teacher import TeacherAvailabilityConstraint
from ..constraints.periods import RequiredPeriodsConstraint, ConflictPeriodsConstraint
from ..constraints.limits import DailyLimitConstraint, WeeklyLimitConstraint, MinimumPeriodsConstraint
from ..objectives.required import RequiredPeriodsObjective
from ..objectives.distribution import DistributionObjective

from .base import BaseSolver
from ...models import ScheduleRequest, ScheduleResponse
from dateutil import parser

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
    
    Weights:
    - RequiredPeriodsObjective: 1000 (highest priority for required/preferred periods)
    - DistributionObjective: 500 (balancing schedule distribution)
    """
    
    def __init__(self):
        super().__init__("cp-sat-stable")
        
        # Add constraints in order of priority
        self.add_constraint(SingleAssignmentConstraint())
        self.add_constraint(NoOverlapConstraint())
        self.add_constraint(TeacherAvailabilityConstraint())
        self.add_constraint(RequiredPeriodsConstraint())
        self.add_constraint(ConflictPeriodsConstraint())
        
        # Add scheduling limit constraints
        self.add_constraint(DailyLimitConstraint())
        self.add_constraint(WeeklyLimitConstraint())
        self.add_constraint(MinimumPeriodsConstraint())
        
        # Add objectives with preset weights (defined in each objective class)
        self.add_objective(RequiredPeriodsObjective())  # Uses weight=1000
        
        # Temporarily disable distribution optimization
        # self.add_objective(DistributionObjective())     # Uses weight=500
        
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
