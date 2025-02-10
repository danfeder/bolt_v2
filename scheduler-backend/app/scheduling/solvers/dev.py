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

class DevSolver(BaseSolver):
    """
    Development solver with advanced optimization features:
    1. All features from stable solver
    2. Enhanced distribution optimization:
       - Improved weekly load balancing
       - Better period spread within days
       - Smarter handling of consecutive classes
    3. Multi-objective optimization
       - Weighted combination of objectives
       - Pareto-optimal solutions tracking
    
    Weights:
    - RequiredPeriodsObjective: 1000 (maintaining same weight for stability)
    - DistributionObjective: 500 (same base weight, but with enhanced terms)
    """
    
    def __init__(self):
        super().__init__("cp-sat-dev")
        
        # Add same constraints as stable solver
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
        
    def compare_with_stable(self, stable_response: ScheduleResponse, dev_response: ScheduleResponse) -> Dict[str, Any]:
        """Compare dev solver results with stable solver"""
        
        # Find assignments that differ between solutions
        stable_assignments = {
            (a.classId, a.date, a.timeSlot.dayOfWeek, a.timeSlot.period): a 
            for a in stable_response.assignments
        }
        dev_assignments = {
            (a.classId, a.date, a.timeSlot.dayOfWeek, a.timeSlot.period): a 
            for a in dev_response.assignments
        }
        
        # Calculate differences
        differences = []
        stable_keys = set(stable_assignments.keys())
        dev_keys = set(dev_assignments.keys())
        
        # Find assignments missing from stable
        for key in dev_keys - stable_keys:
            differences.append({
                "type": "missing_in_stable",
                "classId": key[0],
                "dev": dev_assignments[key],
            })
        
        # Find assignments missing from dev
        for key in stable_keys - dev_keys:
            differences.append({
                "type": "missing_in_dev",
                "classId": key[0],
                "stable": stable_assignments[key],
            })
        
        # Find assignments that differ in timing
        for key in stable_keys & dev_keys:
            if (stable_assignments[key].timeSlot.dayOfWeek != dev_assignments[key].timeSlot.dayOfWeek or
                stable_assignments[key].timeSlot.period != dev_assignments[key].timeSlot.period):
                differences.append({
                    "type": "different_assignment",
                    "classId": key[0],
                    "stable": stable_assignments[key],
                    "dev": dev_assignments[key],
                })
        
        # Compare metrics
        stable_score = stable_response.metadata.distribution.totalScore if stable_response.metadata.distribution else 0
        dev_score = dev_response.metadata.distribution.totalScore if dev_response.metadata.distribution else 0
        
        return {
            "assignment_differences": {
                "total_differences": len(differences),
                "differences": differences
            },
            "metric_differences": {
                "score": dev_score - stable_score,
                "duration": dev_response.metadata.duration - stable_response.metadata.duration,
                "distribution": {
                    "score_difference": dev_score - stable_score,
                    "weekly_variance_difference": (
                        (dev_response.metadata.distribution.weekly["variance"] if dev_response.metadata.distribution else 0) -
                        (stable_response.metadata.distribution.weekly["variance"] if stable_response.metadata.distribution else 0)
                    ),
                    "average_period_spread_difference": (
                        sum(
                            dev_response.metadata.distribution.daily[date]["periodSpread"] if dev_response.metadata.distribution else 0
                            for date in dev_response.metadata.distribution.daily
                        ) / len(dev_response.metadata.distribution.daily) -
                        sum(
                            stable_response.metadata.distribution.daily[date]["periodSpread"] if stable_response.metadata.distribution else 0
                            for date in stable_response.metadata.distribution.daily
                        ) / len(stable_response.metadata.distribution.daily)
                        if stable_response.metadata.distribution and dev_response.metadata.distribution
                        else 0
                    )
                }
            }
        }
