"""Development solver with experimental optimizations"""
from typing import Dict, Any, List
import traceback
from dateutil import parser

from ..core import SchedulerContext
from ..objectives.distribution import DistributionObjective
from .base import BaseSolver
from .config import get_base_constraints, get_base_objectives, WEIGHTS
from ...models import ScheduleRequest, ScheduleResponse, TimeSlot

class DevSolver(BaseSolver):
    """Development solver for testing new optimization strategies"""
    
    def __init__(self):
        super().__init__("cp-sat-dev")
        self._last_run_metadata = None
        
        # Add base constraints and objectives
        for constraint in get_base_constraints():
            self.add_constraint(constraint)
            
        for objective in get_base_objectives():
            self.add_objective(objective)
            
        # Add experimental distribution optimization with configured weight
        self.add_objective(
            DistributionObjective()
        )

    def get_last_run_metrics(self) -> Dict[str, Any]:
        """Get metrics from last solver run"""
        if not self._last_run_metadata:
            return {
                "status": "No runs available",
                "metrics": None
            }
        return {
            "status": "success",
            "metrics": {
                "duration": self._last_run_metadata.duration,
                "score": self._last_run_metadata.score,
                "solutions_found": self._last_run_metadata.solutions_found,
                "optimization_gap": self._last_run_metadata.optimization_gap,
                "distribution": self._last_run_metadata.distribution.dict() if self._last_run_metadata.distribution else None
            }
        }

    def create_schedule(self, request: ScheduleRequest) -> ScheduleResponse:
        """Create a schedule using the development solver configuration"""
        print(f"\nStarting development solver for {len(request.classes)} classes...")
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
            self._last_run_metadata = response.metadata
            return response

        except Exception as e:
            print(f"Scheduling error in development solver: {str(e)}")
            print("Full traceback:")
            print(traceback.format_exc())
            raise
        
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
